#!/usr/bin/env python3
"""Safe, preview-first named Cloudflare Tunnel configuration for Orbit RC.

No tunnel/client/key installation, domain purchase, network request or system
service is performed. The only optional write creates a NEW local YAML file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orbit_rc_remote_config import (ConfigurationError, RemoteSettings, cloudflare_ingress)


def write_new_config(output: Path, contents: str, *, apply: bool = False) -> dict:
    if not apply:
        return {"status": "PREVIEW_ONLY", "output": str(output), "config": contents}
    if not output.is_absolute() or output.is_symlink():
        raise ConfigurationError("Use a new absolute regular YAML output path")
    if output.exists():
        raise ConfigurationError("Existing config will not be overwritten")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ConfigurationError("Parent directory must already exist and not be a symlink")
    if output.suffix.lower() not in (".yml", ".yaml"):
        raise ConfigurationError("Output filename must end in .yml or .yaml")
    with output.open("x", encoding="utf-8") as dest:
        dest.write(contents)
    try:
        output.chmod(0o600)
    except OSError:
        pass  # Windows file ACLs are enforced separately.
    return {"status": "CONFIG_CREATED_ONLY", "output": str(output),
            "tunnel_started": False, "network_exposed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a *non-running* Cloudflare named-tunnel config for Orbit"
    )
    parser.add_argument("--tunnel-id", required=True, help="UUID of an existing named Cloudflare Tunnel")
    parser.add_argument("--credentials-file", required=True,
                        help="Local absolute path to cloudflared's tunnel credentials JSON (not its contents)")
    parser.add_argument("--output", help="New .yml destination; defaults to preview-only")
    parser.add_argument("--apply", action="store_true", help="Create a new YAML only; does not start the tunnel")
    args = parser.parse_args(argv)
    try:
        settings = RemoteSettings.from_env()
        config = cloudflare_ingress(settings, args.tunnel_id, args.credentials_file)
        if args.apply and not args.output:
            raise ConfigurationError("--apply requires a new --output filename")
        result = write_new_config(Path(args.output), config, apply=args.apply) if args.output else {
            "status": "PREVIEW_ONLY", "config": config, "tunnel_started": False,
        }
        print(json.dumps(result, indent=2))
        return 0
    except (ConfigurationError, ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
