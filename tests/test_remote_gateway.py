"""Offline SDK acceptance for the read-only OAuth MCP resource server."""
import asyncio
from pathlib import Path
import sys
import tempfile
import time
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from starlette.testclient import TestClient

from orbit_rc_gateway import OIDCTokenVerifier, create_server
from orbit_rc_oidc import ValidatedPrincipal
from orbit_rc_remote_config import RemoteSettings, SCOPE_READ


class FakeJWTVerifier:
    def __init__(self, settings):
        self.settings = settings

    def verify(self, token):
        if token != "TEST-ONLY-VALID-TOKEN":
            return None
        return ValidatedPrincipal(
            subject=self.settings.owner_subject,
            client_id="test-client",
            scopes=[SCOPE_READ],
            expires_at=int(time.time()) + 180,
            issuer=self.settings.issuer,
            resource=self.settings.public_url,
        )


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "project"
        root.mkdir()
        (root / "hello.txt").write_text("hello", encoding="utf-8")
        self.settings = RemoteSettings(
            project_root=str(root),
            public_url="https://orbit.example.com/mcp",
            issuer="https://login.example.com",
            jwks_url="https://login.example.com/.well-known/jwks.json",
            owner_subject="owner-test",
        )
        self.server = create_server(
            self.settings, jwt_verifier=FakeJWTVerifier(self.settings)
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_remote_tool_surface_is_read_only(self):
        names = {tool.name for tool in self.server.list_tools()}
        self.assertEqual(names, {
            "orbit_rc_status",
            "orbit_rc_list",
            "orbit_rc_read",
            "orbit_rc_search",
            "orbit_rc_preview_edit",
        })
        self.assertNotIn("orbit_rc_write", names)
        self.assertNotIn("orbit_rc_edit_block", names)
        self.assertNotIn("orbit_rc_check", names)

    def test_jwt_adapter_returns_sdk_access_token(self):
        adapter = OIDCTokenVerifier(self.settings, jwt_verifier=FakeJWTVerifier(self.settings))
        good = asyncio.run(adapter.verify_token("TEST-ONLY-VALID-TOKEN"))
        self.assertEqual(good.subject, self.settings.owner_subject)
        self.assertEqual(good.resource, self.settings.public_url)
        self.assertIn(SCOPE_READ, good.scopes)
        bad = asyncio.run(adapter.verify_token("INVALID"))
        self.assertIsNone(bad)

    def test_direct_in_memory_calls_do_not_bypass_owner_check(self):
        # The SDK documents that direct/in-memory calls skip HTTP OAuth;
        # our handler must still reject them.
        with self.assertRaises(Exception):
            asyncio.run(self.server.call_tool("orbit_rc_read", {"path": "hello.txt"}))

    def test_http_mcp_rejects_requests_without_bearer(self):
        app = self.server.streamable_http_app(
            json_response=True,
            stateless_http=True,
            host="127.0.0.1",
        )
        with TestClient(app) as client:
            response = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2026-07-28",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Host": "orbit.example.com",
                },
            )
        self.assertEqual(response.status_code, 401)

    def test_oauth_protected_resource_metadata_contains_issuer(self):
        app = self.server.streamable_http_app(
            json_response=True, stateless_http=True, host="127.0.0.1"
        )
        with TestClient(app) as client:
            response = client.get("/.well-known/oauth-protected-resource/mcp")
        self.assertEqual(response.status_code, 200)
        obj = response.json()
        self.assertEqual(obj["resource"], self.settings.public_url)
        self.assertTrue(any(self.settings.issuer in x for x in obj["authorization_servers"]))


if __name__ == "__main__":
    unittest.main()
