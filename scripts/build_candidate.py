#!/usr/bin/env python3
"""Build an auditable, deterministic *candidate* ZIP. No release is published."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    "Orbit Remote Setup.cmd",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "SECURITY.md",
    "docs/ARCHITECTURE-AND-ROADMAP.md",
    "docs/CHATGPT-COMPATIBILITY.md",
    "src/orbit_remote_commander.py",
    "src/orbit_remote_fallback.py",
    "src/orbit_rc_text_ops.py",
    "src/run_orbit_rc.py",
    "tools/windows_setup.py",
    "tools/windows_setup_gui.pyw",
)
NAME = "Orbit-Remote-Commander-CANDIDATE.zip"


def build(output: Path) -> tuple[Path, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    for name in PAYLOAD:
        if not (ROOT / name).is_file() or (ROOT / name).is_symlink():
            raise ValueError(f"Missing/untrusted package input: {name}")
    # Python zipfile doesn't promise deterministic entry metadata by default.
    # Set fixed POSIX permissions and timestamps, sorted paths and no extra data.
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(PAYLOAD):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            info.extra = b""
            archive.writestr(info, (ROOT / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(f"{sha}  {output.name}\n", encoding="ascii")
    return output, sha


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(ROOT / "dist" / NAME))
    args = p.parse_args()
    path, sha = build(Path(args.output))
    print(f"UNSIGNED DEVELOPMENT CANDIDATE ONLY: {path} SHA256 {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
