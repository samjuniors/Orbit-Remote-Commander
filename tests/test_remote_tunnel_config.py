"""No-network tests for fail-closed Cloudflare Tunnel config and remote settings."""
from pathlib import Path
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from orbit_rc_remote_config import (
    ConfigurationError, RemoteSettings, SCOPE_READ, cloudflare_ingress,
)
from importlib.util import module_from_spec, spec_from_file_location

SCRIPT = SRC.parent / "tools" / "remote_tunnel.py"
spec = spec_from_file_location("remote_tunnel_test", SCRIPT)
tunnel = module_from_spec(spec)
spec.loader.exec_module(tunnel)

TUNNEL_ID = "5f10f6b7-147b-4eb1-a58a-bb2fc37f24b9"


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        self.options = {
            "project_root": str(self.root),
            "public_url": "https://orbit.example.com/mcp",
            "issuer": "https://login.example.com",
            "jwks_url": "https://login.example.com/.well-known/jwks.json",
            "owner_subject": "owner-123",
            "port": 8765,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def new_settings(self, **overrides):
        return RemoteSettings(**(self.options | overrides))

    def test_explicit_required_values_only(self):
        obj = self.new_settings()
        self.assertEqual(obj.public_url, "https://orbit.example.com/mcp")
        self.assertEqual(obj.project_root, str(self.root.resolve()))
        self.assertEqual(SCOPE_READ, "orbit:pc:read")

    def test_no_implicit_remote_exposure(self):
        with self.assertRaises(ConfigurationError):
            RemoteSettings.from_env({})

    def test_fail_closed_malformed_config(self):
        cases = [
            {"public_url": "http://orbit.example.com/mcp"},
            {"public_url": "https://orbit.example.com/foo"},
            {"public_url": "https://orbit.example.com/mcp?token=abc"},
            {"public_url": "https://127.0.0.1/mcp"},
            {"issuer": "http://login.example.com"},
            {"jwks_url": "https://evil.example.com/jwks"},
            {"owner_subject": ""},
            {"owner_subject": "owner\ninvalid"},
            {"port": 80},
            {"port": True},
            {"project_root": str(Path(self.tmp.name) / "missing")},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ConfigurationError):
                self.new_settings(**case)

    def test_tunnel_config_exact_route_localhost_and_deny_fallback(self):
        obj = self.new_settings()
        text = cloudflare_ingress(obj, TUNNEL_ID, str(Path(self.tmp.name) / "tunnel.json"))
        self.assertIn("tunnel: " + TUNNEL_ID, text)
        self.assertIn("hostname: orbit.example.com", text)
        self.assertIn("service: http://127.0.0.1:8765", text)
        self.assertTrue(text.rstrip().endswith("service: http_status:404"))
        self.assertNotIn("owner-123", text)
        self.assertNotIn("orbit:pc:read", text)

    def test_reject_untrusted_cloudflare_inputs(self):
        settings = self.new_settings()
        for tunnel_id, creds in [
            ("bad-id", "/tmp/tunnel.json"),
            (TUNNEL_ID, "relative.json"),
            (TUNNEL_ID, "/tmp/secrets.yaml"),
            (TUNNEL_ID, "/tmp/abc.json\n- service: https://bad"),
        ]:
            with self.subTest(tunnel_id=tunnel_id, creds=creds), self.assertRaises(ConfigurationError):
                cloudflare_ingress(settings, tunnel_id, creds)

    def test_windows_path_allowed_as_data_not_executed(self):
        text = cloudflare_ingress(self.new_settings(), TUNNEL_ID, r"C:\Users\owner\.cloudflared\tunnel.json")
        self.assertIn(r"C:\Users\owner\.cloudflared\tunnel.json", text)

    def test_preview_and_create_are_opt_in_and_non_destructive(self):
        new_config = Path(self.tmp.name) / "orbit.yml"
        preview = tunnel.write_new_config(new_config, "ingress:\n  - service: http_status:404\n")
        self.assertEqual(preview["status"], "PREVIEW_ONLY")
        self.assertFalse(new_config.exists())
        made = tunnel.write_new_config(new_config, "ingress:\n  - service: http_status:404\n", apply=True)
        self.assertEqual(made["status"], "CONFIG_CREATED_ONLY")
        self.assertFalse(made["tunnel_started"])
        with self.assertRaises(ConfigurationError):
            tunnel.write_new_config(new_config, "overwrite", apply=True)
        self.assertEqual(new_config.read_text(), "ingress:\n  - service: http_status:404\n")

    def test_refuse_write_into_symlink(self):
        dest = Path(self.tmp.name) / "config.yml"
        actual = Path(self.tmp.name) / "target"
        actual.write_text("keep")
        try:
            dest.symlink_to(actual)
        except (OSError, NotImplementedError):
            self.skipTest("No symlink privilege")
        with self.assertRaises(ConfigurationError):
            tunnel.write_new_config(dest, "replacement", apply=True)
        self.assertEqual(actual.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
