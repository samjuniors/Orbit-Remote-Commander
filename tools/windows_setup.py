#!/usr/bin/env python3
"""Orbit Remote Commander per-user Windows/local setup (preview-first).

Installs only an isolated copy of this project's stdio files. It does NOT
pair ChatGPT, install tunnel-client, register MCP hosts or open network ports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

SOURCE_DIR = Path(__file__).resolve().parents[1] / "src"
FILES = ("orbit_remote_commander.py", "orbit_remote_fallback.py", "run_orbit_rc.py")
CONFIG_FILE = "config.json"
MANIFEST_FILE = ".orbit_rc_install.json"


def location() -> Path:
    configured = os.environ.get("ORBIT_RC_INSTALL_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    if os.name == "nt":
        return Path(os.environ["LOCALAPPDATA"]) / "OrbitRemoteCommander"
    return Path.home() / ".local" / "share" / "OrbitRemoteCommander"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scoped_root(path: str) -> str:
    # Reuse the same root validation as the live stdio executor.
    sys.path.insert(0, str(SOURCE_DIR))
    try:
        from orbit_remote_commander import Commander
        return str(Commander(path).root)
    finally:
        sys.path.remove(str(SOURCE_DIR))


def load_manifest(home: Path) -> dict:
    path = home / MANIFEST_FILE
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Existing installer manifest is unreadable") from exc
    if doc.get("schema") != 1 or not isinstance(doc.get("checksums"), dict):
        raise ValueError("Unknown installer manifest; refusing changes")
    return doc


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".orbitrc-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def plan_install(home: Path, project: str | None) -> dict:
    old = load_manifest(home)
    checksums = old.get("checksums", {})
    if home.is_symlink():
        raise ValueError("Installation root may not be a symlink")
    for name in FILES:
        dest = home / name
        if not (SOURCE_DIR / name).is_file():
            raise ValueError(f"Missing packaged source: {name}")
        if dest.is_symlink():
            raise ValueError(f"Refusing symlink in installation: {name}")
        if dest.exists():
            existing = digest(dest.read_bytes())
            if name not in checksums or existing != checksums[name]:
                raise ValueError(f"Existing customized/unowned file: {name}")
    conf = home / CONFIG_FILE
    if conf.is_symlink():
        raise ValueError("Refusing symlink config")
    if conf.exists():
        if not old:
            raise ValueError("Existing unowned config; refusing overwrite")
        try:
            data = json.loads(conf.read_text(encoding="utf-8"))
            project = scoped_root(data["root"])
        except (OSError, ValueError, KeyError) as exc:
            raise ValueError("Existing config invalid; refusing overwrite") from exc
    elif not project:
        raise ValueError("Project folder required for first install")
    project = scoped_root(project)
    return {
        "home": str(home),
        "project": project,
        "files": list(FILES),
        "preserve_config": conf.exists(),
        "write_enabled": False,
        "checks_enabled": False,
        "auto_start": False,
        "network_listener": False,
    }


def install(home: Path, project: str | None, apply: bool) -> dict:
    plan = plan_install(home, project)
    if not apply:
        return {"status": "PREVIEW_ONLY", **plan}
    home.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        atomic_bytes(home / name, (SOURCE_DIR / name).read_bytes())
    if not plan["preserve_config"]:
        data = {"schema": 1, "root": plan["project"], "allow_write": False,
                "allow_checks": False}
        atomic_bytes(home / CONFIG_FILE, (json.dumps(data, indent=2) + "\n").encode())
    checksums = {name: digest((home / name).read_bytes()) for name in FILES}
    atomic_bytes(home / MANIFEST_FILE, (json.dumps({"schema": 1, "checksums": checksums}, indent=2) + "\n").encode())
    return {"status": "INSTALLED_LOCAL_ONLY", **plan}


def status(home: Path) -> dict:
    doc = load_manifest(home)
    if not doc:
        return {"status": "NOT_INSTALLED", "home": str(home)}
    files = {p: ((home / p).is_file() and not (home / p).is_symlink() and
                 digest((home / p).read_bytes()) == doc["checksums"][p])
             for p in FILES if p in doc["checksums"]}
    return {"status": "LOCAL_FILES_VERIFIED" if len(files) == len(FILES) and all(files.values())
            else "FILES_MODIFIED", "home": str(home), "files": files,
            "remote_connected": False, "chatgpt_connected": False}


def uninstall(home: Path, apply: bool, remove_config: bool = False) -> dict:
    doc = load_manifest(home)
    if not doc:
        return {"status": "NOT_INSTALLED", "home": str(home)}
    for name in FILES:
        dest = home / name
        if name not in doc["checksums"] or dest.is_symlink() or not dest.is_file():
            raise ValueError(f"Missing or untrusted installed file: {name}")
        if digest(dest.read_bytes()) != doc["checksums"][name]:
            raise ValueError(f"Customized installed file; refusing removal: {name}")
    config = home / CONFIG_FILE
    if config.is_symlink():
        raise ValueError("Refusing symlink config")
    result = {"status": "PREVIEW_ONLY" if not apply else "UNINSTALLED",
              "home": str(home), "remove_config": bool(remove_config)}
    if apply:
        for name in FILES:
            (home / name).unlink()
        (home / MANIFEST_FILE).unlink()
        if remove_config and config.is_file():
            config.unlink()
        # Do not recursively delete an install folder: it could contain user files.
        try:
            home.rmdir()
        except OSError:
            pass
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orbit Remote Commander local-only setup")
    parser.add_argument("action", choices=("install", "status", "uninstall"))
    parser.add_argument("--project", help="existing scoped project root for first install")
    parser.add_argument("--apply", action="store_true", help="explicit permission to write/remove local files")
    parser.add_argument("--remove-config", action="store_true", help="opt in to removing saved project scope on uninstall")
    opts = parser.parse_args(argv)
    home = location()
    try:
        if opts.action == "install":
            result = install(home, opts.project, opts.apply)
        elif opts.action == "uninstall":
            result = uninstall(home, opts.apply, opts.remove_config)
        else:
            result = status(home)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
