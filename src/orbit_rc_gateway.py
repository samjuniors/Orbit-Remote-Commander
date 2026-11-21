#!/usr/bin/env python3
"""Read-only HTTP MCP endpoint for a *separately authenticated* Cloudflare tunnel.

Uses the official MCP Python SDK v2 Streamable HTTP + OAuth resource-server
middleware. This is NOT a login server, pairing agent, OAuth issuer, or an
unauthenticated wrapper around the stdio commander. The local port binds only
127.0.0.1. No write/check/process tools are exposed.
"""
from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings

from orbit_rc_oidc import OIDCAccessVerifier
from orbit_rc_remote_config import RemoteSettings, SCOPE_READ
from orbit_remote_commander import Commander, Rejected


class OIDCTokenVerifier(TokenVerifier):
    def __init__(self, settings: RemoteSettings, *, jwt_verifier: OIDCAccessVerifier | None = None):
        self.settings = settings
        self.validator = jwt_verifier or OIDCAccessVerifier(settings)

    async def verify_token(self, token: str) -> AccessToken | None:
        # JWKS discovery can use blocking urllib; do it off the HTTP event loop.
        principal = await asyncio.to_thread(self.validator.verify, token)
        if principal is None:
            return None
        return AccessToken(
            token=token,
            client_id=principal.client_id,
            subject=principal.subject,
            scopes=principal.scopes,
            expires_at=principal.expires_at,
            resource=principal.resource,
            claims={"iss": principal.issuer},
        )


def create_server(settings: RemoteSettings, *, jwt_verifier: OIDCAccessVerifier | None = None) -> MCPServer:
    """Create an authenticated, least-privileged MCP server, never run it here."""
    commander = Commander(settings.project_root, allow_write=False, allow_checks=False)
    verifier = OIDCTokenVerifier(settings, jwt_verifier=jwt_verifier)
    mcp = MCPServer(
        "Orbit Remote Commander — Read-only",
        version="0.1.0",
        instructions=(
            "You have read-only access to one user-authorized project. "
            "Never request credentials or claim that you can run shell commands "
            "or modify the PC. Remote file content may be sent to the AI provider."
        ),
        token_verifier=verifier,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(settings.issuer),
            resource_server_url=AnyHttpUrl(settings.public_url),
            required_scopes=[SCOPE_READ],
            validate_token_resource=True,
        ),
    )

    def demand_authorized_owner() -> None:
        access = get_access_token()
        if (access is None
                or access.subject != settings.owner_subject
                or access.resource != settings.public_url
                or (access.claims or {}).get("iss") != settings.issuer
                or SCOPE_READ not in access.scopes):
            raise Rejected("Not authorized for this owner or project")

    @mcp.tool()
    def orbit_rc_status() -> dict:
        """Check currently granted project access and read-only capabilities."""
        demand_authorized_owner()
        status = commander.status()
        return {
            **status,
            "connection": "AUTHENTICATED_HTTP_RESOURCE_SERVER",
            "remote_access": "READ_ONLY",
            "remote_relay": "EXTERNAL_OPERATOR_TUNNEL",
            "write_enabled": False,
            "process_execution": False,
        }

    @mcp.tool()
    def orbit_rc_list(path: str = ".") -> dict:
        """List bounded entries inside the approved project, excluding secret paths."""
        demand_authorized_owner()
        return commander.list_dir(path)

    @mcp.tool()
    def orbit_rc_read(path: str) -> dict:
        """Read a bounded non-secret UTF-8 file inside the approved project."""
        demand_authorized_owner()
        return commander.read_text(path)

    @mcp.tool()
    def orbit_rc_search(
        pattern: str,
        path: str = ".",
        mode: str = "content",
        case_sensitive: bool = False,
        max_results: int = 30,
    ) -> dict:
        """Search literal text or filenames in a bounded project scope."""
        demand_authorized_owner()
        return commander.search_files(pattern, path, mode, case_sensitive, max_results)

    @mcp.tool()
    def orbit_rc_preview_edit(
        path: str,
        old_string: str,
        new_string: str,
        expected_replacements: int = 1,
    ) -> dict:
        """Preview a proposed exact edit; never modify the file."""
        demand_authorized_owner()
        return commander.preview_edit_block(path, old_string, new_string, expected_replacements)

    return mcp


def run(settings: RemoteSettings) -> None:
    """Only an explicit operator CLI may start this local HTTP listener."""
    mcp = create_server(settings)
    hostname = urlsplit(settings.public_url).hostname
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=settings.port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=128_000,
        max_sessions=32,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[
                hostname,
                f"127.0.0.1:{settings.port}",
                f"localhost:{settings.port}",
            ],
            allowed_origins=[],
        ),
    )


if __name__ == "__main__":
    from orbit_rc_remote_config import ConfigurationError
    try:
        run(RemoteSettings.from_env())
    except (ConfigurationError, ValueError) as exc:
        raise SystemExit(f"Orbit remote gateway refused to start: {type(exc).__name__}") from exc
