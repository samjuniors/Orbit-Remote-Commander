"""Validate OAuth access JWTs issued for a single Orbit remote MCP resource.

No tokens are minted here. Never trust a Cloudflare tunnel or MCP tool metadata
as authentication. Only RS256, explicit issuer/audience/owner, required scope,
expiry and signed JWKS from the configured issuer are accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import jwt

from orbit_rc_remote_config import RemoteSettings, SCOPE_READ


@dataclass(frozen=True)
class ValidatedPrincipal:
    subject: str
    client_id: str
    scopes: list[str]
    expires_at: int
    issuer: str
    resource: str


class OIDCAccessVerifier:
    """OIDC provider access-token verifier; PyJWT handles signature checking.

    JWKS URL is pinned in RemoteSettings and MUST be an HTTPS endpoint hosted
    by the configured issuer. JWKS key fetching never uses a token claim URL.
    The optional jwk_client parameter is for isolated test-key injection.
    """

    def __init__(self, settings: RemoteSettings, *, jwk_client: Any = None):
        self.settings = settings
        self.client = jwk_client if jwk_client is not None else jwt.PyJWKClient(
            settings.jwks_url, cache_jwk_set=True, lifespan=300, timeout=5
        )

    def verify(self, token: str) -> ValidatedPrincipal | None:
        if not isinstance(token, str) or not 20 <= len(token) <= 8192:
            return None
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                return None
            if not 1 <= len(header["kid"]) <= 128:
                return None
            key = self.client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token, key, algorithms=["RS256"],
                issuer=self.settings.issuer,
                audience=self.settings.public_url,
                leeway=15,
                options={"require": ["iss", "aud", "sub", "exp", "iat"]},
            )
            now = time.time()
            exp = claims.get("exp")
            issued = claims.get("iat")
            sub = claims.get("sub")
            if (type(exp) is not int or type(issued) is not int
                    or exp <= now or exp - issued > 3600
                    or issued > now + 15
                    or not isinstance(sub, str) or sub != self.settings.owner_subject):
                return None
            client_id = claims.get("client_id") or claims.get("azp")
            if not isinstance(client_id, str) or not 1 <= len(client_id) <= 256:
                return None
            raw_scope = claims.get("scope")
            if not isinstance(raw_scope, str):
                return None
            scopes = raw_scope.split()
            if SCOPE_READ not in scopes:
                return None
            return ValidatedPrincipal(
                subject=sub, client_id=client_id,
                scopes=scopes, expires_at=exp,
                issuer=self.settings.issuer,
                resource=self.settings.public_url,
            )
        except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError, OSError):
            return None
