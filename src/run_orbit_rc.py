#!/usr/bin/env python3
"""Launch only the explicitly installed, project-scoped stdio commander."""
import json
import os
from pathlib import Path
import sys

def main() -> int:
    here = Path(__file__).resolve().parent
    config = here / "config.json"
    if config.is_symlink() or not config.is_file():
        print("Orbit RC config unavailable", file=sys.stderr)
        return 2
    try:
        opts = json.loads(config.read_text(encoding="utf-8"))
        if opts.get("schema") != 1 or not isinstance(opts.get("root"), str):
            raise ValueError("Unsupported config")
        # This launcher intentionally starts in read-only mode, irrespective
        # of stale or edited settings. Additional privileges require a
        # separately reviewed host/device consent workflow.
        os.environ["ORBIT_RC_ROOT"] = opts["root"]
        os.environ["ORBIT_RC_ALLOW_WRITE"] = "0"
        os.environ["ORBIT_RC_ALLOW_CHECKS"] = "0"
        from orbit_remote_commander import main as serve
        return serve()
    except (OSError, ValueError) as exc:
        print(f"Orbit RC launcher refused to start: {type(exc).__name__}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
