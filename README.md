# Orbit Remote Commander

**Independent, optional PC-access companion for Orbit — separate from [Orbit Core](https://github.com/samjuniors/Orbit-Core) and designed for future compatibility with the [Orbit ChatGPT plugin](docs/CHATGPT-COMPATIBILITY.md).**

**Status: local stdio MCP plus an experimental OAuth-protected read-only HTTP MCP gateway. Live ChatGPT-to-PC access and automatic failover are NOT yet connected or verified.**

Orbit Remote Commander aims to let authorized users inspect and, with additional approval, modify files in a selected project when a preferred device connector (such as Desktop Commander) is unavailable. It is not a fork of Desktop Commander and does not use Desktop Commander credentials or infrastructure.

## What works today

- Bounded file inventory, UTF-8 file reads and **literal filename/content search** within one explicitly approved project root.
- Read-only exact block-edit previews with occurrence checks, SHA-256 digests and preserved CRLF/LF/CR line endings; editing remains disabled by default.
- Optional, disabled-by-default edits of existing text files with SHA-256 stale-write protection.
- Optional, disabled-by-default fixed Git diagnostics (not arbitrary terminal access).
- A pure fallback-selection policy: prefer an online/authorized primary, use an independently connected Orbit fallback only for actual availability failures, never circumvent denials or replay uncertain writes.
- Local stdio MCP tools: `orbit_rc_status`, `orbit_rc_list`, `orbit_rc_read`, `orbit_rc_search`, `orbit_rc_preview_edit`, `orbit_rc_write`, `orbit_rc_edit_block`, `orbit_rc_check`.

## Optional remote MCP over Cloudflare Tunnel

The standalone source now has an optional **read-only HTTP MCP gateway**, built using the official MCP Python SDK v2 and an externally configured OAuth provider. It verifies access-token signature, issuer, exact resource audience, owner subject, scope and expiry. It runs on localhost, and an independently authorized Cloudflare named tunnel may forward HTTPS requests to it. It never exposes editing, shell or process tools.

Cloudflare's tunnel transport can use a free plan, but a stable hostname needs a domain you control, and OAuth-provider and ChatGPT plan costs are separate. [Architecture, cost, setup and strict security gates](docs/CLOUDFLARE-REMOTE-MCP.md). No tunnel, authentication provider or PC connection is created automatically.

## Getting started (local development only)

Requires Python 3.10+ (no third-party runtime packages). Use a **disposable** project directory, never a drive root or home directory. On Windows, set environment variables in the trusted local MCP client configuration:

```json
{
  "command": "python",
  "args": ["C:\\path\\to\\Orbit-Remote-Commander\\src\\orbit_remote_commander.py"],
  "env": {
    "ORBIT_RC_ROOT": "D:\\Projects\\orbit-remote-test",
    "ORBIT_RC_ALLOW_WRITE": "0",
    "ORBIT_RC_ALLOW_CHECKS": "0"
  }
}
```

This illustrates the command and environment only; local MCP host configuration keys differ. No installation or host registration occurs by cloning the repository. Read-only status should return `READY_LOCAL_STDIO` with `remote_relay: NOT_CONFIGURED`. The local server is **not** automatically accessible to ChatGPT on the web.

Run tests:

```bash
python -m unittest discover -s tests -p 'test_remote_*.py' -v
```

## Windows local setup (development candidate)

The repository now includes a **preview-first one-click local installer**, independent of Orbit Core. After an authorized review of the source or CI artifact, a Windows user can open **Orbit Remote Setup.cmd**, select one trusted project folder, preview the file changes and explicitly install. The program files go under the current user's LOCALAPPDATA/OrbitRemoteCommander folder. The setup never changes other IDEs, installs a background daemon, opens ports or silently enables writes. It also provides Status and Uninstall controls. Keep important user files outside that install folder.

For terminal-only setup, use Python 3.10+:

~~~text
python tools/windows_setup.py install --project "C:\full\path\to\disposable-project"
python tools/windows_setup.py install --project "C:\full\path\to\disposable-project" --apply
python tools/windows_setup.py status
python tools/windows_setup.py uninstall
python tools/windows_setup.py uninstall --apply
~~~

A local stdio MCP host can then invoke the installed run_orbit_rc.py in that per-user directory. **No actual ChatGPT connection is created by installing these files.** The launcher forces read-only mode even when the JSON config contains unsupported privilege flags.

To make an eligible private ChatGPT connection, review the [Secure MCP Tunnel setup and prerequisites](docs/PRIVATE-TUNNEL-SETUP.md). A separate public OAuth HTTPS gateway is still required before publicly distributing the Orbit ChatGPT plugin with this remote-access capability.

The standalone CI builds a reproducible **unsigned development candidate ZIP** with SHA-256 as a short-lived reviewer artifact; this is not a signed public release.

## Orbit ChatGPT plugin compatibility

The current private Orbit ChatGPT plugin v0.26.3 and later documents an optional fallback using these `orbit_rc_*` tool names. **The tool contract is aligned at the source/instruction level, not yet proven in live ChatGPT remote sessions.** For future public-plugin support, this project will provide an independently authenticated, opt-in device integration rather than asking users to install or connect Desktop Commander. See [ChatGPT compatibility](docs/CHATGPT-COMPATIBILITY.md), including planned OAuth, pairing, privacy and release gates.

## Independent product boundaries

This repository owns the remote-command companion, tests, security controls and any future device agent/gateway/installer. Orbit Core remains a separate, optional consumer. No code from this repository should be copied into Orbit Core's runtime, and there is no mandatory Orbit Core dependency. Releases and versioning will be independent. A public repository does not imply production security or a published, verified installer.

## Security and roadmap

Read [SECURITY.md](SECURITY.md) and [architecture/acceptance](docs/ARCHITECTURE-AND-ROADMAP.md) before enabling writes or expanding the protocol. A local preview-first Windows setup exists, including optional remote source files. No public inbound server port, hosted multi-user relay, device pairing, desktop GUI automation or unrestricted remote shell ships today. The read-only OAuth server only binds to localhost and requires separately authorized outbound tunnel setup.

**Third-party source:** We researched and adapted **MIT-licensed** code from [wonderwhy-er/DesktopCommanderMCP at pinned commit 9a101b17](https://github.com/wonderwhy-er/DesktopCommanderMCP/tree/9a101b17e44577f0baefa4c7120f087881c5cc56). Its newline-handling and exact text-match logic are ported into `src/orbit_rc_text_ops.py`, with the upstream copyright and MIT license in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), included in installed files and the review ZIP. See [research and capability comparison](docs/RESEARCH-DESKTOPCOMMANDER-MCP.md).

**Orbit-original code licensing:** No project-wide open-source license has been selected; GitHub visibility is not an automatic redistribution grant for Orbit-original files. Choose an explicit license before distributing public packages or accepting substantive outside contributions.

**Initial source:** migrated from unmerged Orbit Core draft [PR #142](https://github.com/samjuniors/Orbit-Core/pull/142); changes here have their own independent development and review process.
