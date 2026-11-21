"""Offline RSA-signed JWT tests for Orbit's independent OAuth resource server."""
from pathlib import Path
import sys
import tempfile
import time
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from orbit_rc_oidc import OIDCAccessVerifier
from orbit_rc_remote_config import RemoteSettings, SCOPE_READ


class _FakeKey:
    def __init__(self, key):
        self.key = key


class _FixedJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, token):
        return _FakeKey(self.key)


class OIDCTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name) / "project"
        folder.mkdir()
        self.settings = RemoteSettings(
            project_root=str(folder),
            public_url="https://orbit.example.com/mcp",
            issuer="https://login.example.com",
            jwks_url="https://login.example.com/jwks",
            owner_subject="owner-test",
        )
        self.verifier = OIDCAccessVerifier(
            self.settings,
            jwk_client=_FixedJwks(self.private.public_key()),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def claims(self, **overrides):
        now = int(time.time())
        return {
            "iss": self.settings.issuer,
            "aud": self.settings.public_url,
            "sub": self.settings.owner_subject,
            "scope": SCOPE_READ,
            "iat": now - 1,
            "exp": now + 180,
            "client_id": "chatgpt-client",
        } | overrides

    def token(self, claims=None, **kwargs):
        return jwt.encode(
            self.claims() if claims is None else claims,
            kwargs.pop("private_key", self.private),
            algorithm=kwargs.pop("algorithm", "RS256"),
            headers=kwargs.pop("headers", {"kid": "testkey"}),
        )

    def test_good_signature_and_owner_scope(self):
        v = self.verifier.verify(self.token())
        self.assertIsNotNone(v)
        self.assertEqual(v.subject, "owner-test")
        self.assertEqual(v.scopes, [SCOPE_READ])
        self.assertEqual(v.resource, self.settings.public_url)
        self.assertEqual(v.client_id, "chatgpt-client")

    def test_denies_invalid_claims(self):
        now = int(time.time())
        bad = [
            {"iss": "https://other.example.com"},
            {"aud": "https://other.example.com/mcp"},
            {"sub": "other-user"},
            {"scope": "other:scope"},
            {"scope": ["orbit:pc:read"]},
            {"client_id": ""},
            {"exp": now - 10},
            {"exp": now + 7200},
            {"iat": now + 100},
        ]
        for override in bad:
            with self.subTest(case=override):
                self.assertIsNone(self.verifier.verify(self.token(self.claims(**override))))

    def test_denies_missing_required_claims(self):
        for key in ("iss", "aud", "sub", "exp", "iat", "client_id", "scope"):
            with self.subTest(key=key):
                claims = self.claims()
                del claims[key]
                self.assertIsNone(self.verifier.verify(self.token(claims)))

    def test_denies_alternate_signature_or_algorithm(self):
        self.assertIsNone(self.verifier.verify(self.token(private_key=self.other_private)))
        hs = jwt.encode(self.claims(), "secret", algorithm="HS256", headers={"kid": "testkey"})
        self.assertIsNone(self.verifier.verify(hs))

    def test_denies_missing_kid_and_invalid_tokens(self):
        self.assertIsNone(self.verifier.verify(self.token(headers={})))
        self.assertIsNone(self.verifier.verify("plain-text"))
        self.assertIsNone(self.verifier.verify("x" * 9000))
        self.assertIsNone(self.verifier.verify(None))

    def test_no_jwks_network_is_required_for_unit_tests(self):
        # The fixed key simulates a previously validated issuer JWKS set.
        self.assertEqual(self.verifier.verify(self.token()).issuer, "https://login.example.com")


if __name__ == "__main__":
    unittest.main()
