"""Validated, transport-independent settings for a read-only Orbit remote MCP.

This module is dependency-free. It does not start Cloudflare, create tunnels,
issue credentials, authorize users, or expose a port. No remote mode starts
without explicit user, issuer, audience and project configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PureWindowsPath
import re
from urllib.parse import urlsplit
from uuid import UUID

SCOPE_READ = "orbit:pc:read"
HOSTNAME = re.compile(r"(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


class ConfigurationError(ValueError):
    pass


def secure_https_url(value: str, *, exact_path: str | None = None) -> str:
    if not isinstance(value, str) or len(value) > 512 or not value:
        raise ConfigurationError("HTTPS URL missing or too long")
    u = urlsplit(value)
    if (u.scheme != "https" or not u.hostname or u.username or u.password
            or u.port is not None or u.query or u.fragment
            or not HOSTNAME.fullmatch(u.hostname)
            or any(ch in value for ch in "\r\n\t\\")):
        raise ConfigurationError("A stable HTTPS hostname without port, query or fragment is required")
    if exact_path is not None and u.path != exact_path:
        raise ConfigurationError(f"The MCP public URL must end exactly at {exact_path}")
    if u.hostname != u.hostname.lower() or value != value.lower():
        # JWT audience and issuer string comparisons must be exact; avoid
        # hostname canonicalization surprises and ambiguous casing.
        raise ConfigurationError("Use lowercase canonical HTTPS URLs")
    return value


@dataclass(frozen=True)
class RemoteSettings:
    project_root: str
    public_url: str
    issuer: str
    jwks_url: str
    owner_subject: str
    port: int = 8765

    def __post_init__(self) -> None:
        from orbit_remote_commander import Commander
        try:
            project = Commander(self.project_root).root
        except (OSError, ValueError) as exc:
            raise ConfigurationError("An existing, scoped project folder is required") from exc
        object.__setattr__(self, "project_root", str(project))
        public = secure_https_url(self.public_url, exact_path="/mcp")
        issuer = secure_https_url(self.issuer)
        jwks = secure_https_url(self.jwks_url)
        if urlsplit(issuer).hostname != urlsplit(jwks).hostname:
            raise ConfigurationError("JWKS endpoint must be on the configured issuer host")
        if not isinstance(self.owner_subject, str) or not 1 <= len(self.owner_subject) <= 256:
            raise ConfigurationError("Owner OAuth subject is required")
        if any(ord(c) < 33 or ord(c) > 126 for c in self.owner_subject):
            raise ConfigurationError("Owner subject must contain only visible ASCII characters")
        if type(self.port) is not int or not 1024 <= self.port <= 65535:
            raise ConfigurationError("Local port must be an integer from 1024 to 65535")
        if urlsplit(public).hostname in ("localhost", "127.0.0.1"):
            raise ConfigurationError("Use a stable externally resolvable HTTPS MCP hostname")
        if not issuer:
            raise ConfigurationError("Issuer is required")

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "RemoteSettings":
        env = os.environ if environ is None else environ
        return cls(
            project_root=env.get("ORBIT_RC_ROOT", ""),
            public_url=env.get("ORBIT_RC_PUBLIC_URL", ""),
            issuer=env.get("ORBIT_RC_OIDC_ISSUER", ""),
            jwks_url=env.get("ORBIT_RC_OIDC_JWKS_URL", ""),
            owner_subject=env.get("ORBIT_RC_OWNER_SUBJECT", ""),
            port=int(env.get("ORBIT_RC_LOCAL_PORT", "8765")),
        )


def cloudflare_ingress(settings: RemoteSettings, tunnel_id: str, credentials_file: str) -> str:
    """Generate a narrow named-tunnel config; NEVER launch anything.

    The hostname is routed to a localhost-only OAuth MCP server. Cloudflare
    handles transport, NOT authorization. The catch-all returns HTTP 404.
    """
    try:
        tunnel = str(UUID(tunnel_id))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ConfigurationError("An existing named Cloudflare tunnel UUID is required") from exc
    if not isinstance(credentials_file, str) or not credentials_file.endswith(".json"):
        raise ConfigurationError("Enter the absolute location of your local tunnel credentials JSON")
    if len(credentials_file) > 500 or any(ord(c) < 32 for c in credentials_file):
        raise ConfigurationError("Invalid credentials path")
    win_path = PureWindowsPath(credentials_file)
    if not Path(credentials_file).is_absolute() and not win_path.is_absolute():
        raise ConfigurationError("Credentials path must be absolute")
    hostname = urlsplit(settings.public_url).hostname
    # YAML single quotes are escaped by doubling. Strict URL/UUID checks keep
    # this generated routing config free of user-injected keys.
    quoted_path = "'" + credentials_file.replace("'", "''") + "'"
    return (
        f"tunnel: {tunnel}\n"
        f"credentials-file: {quoted_path}\n"
        "ingress:\n"
        f"  - hostname: {hostname}\n"
        f"    service: http://127.0.0.1:{settings.port}\n"
        "  - service: http_status:404\n"
    )
