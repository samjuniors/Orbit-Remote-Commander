# Research: wonderwhy-er/DesktopCommanderMCP

**Research date:** 2026-11-20
**Pinned upstream:** [DesktopCommanderMCP @ 9a101b17](https://github.com/wonderwhy-er/DesktopCommanderMCP/tree/9a101b17e44577f0baefa4c7120f087881c5cc56)
**License:** MIT (see our [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md); upstream copyright (c) 2024-2025 Eduard Ruzga and Desktop Commander Contributors)

## Objective

Use the source code from the local Desktop Commander MCP to make a useful
**Orbit-owned, standalone** MCP executor which can later be connected to
the private Orbit ChatGPT plugin and, after separate security gates,
a publicly distributed plugin. Do not copy the Desktop Commander brand,
credentials, remote service or unrestricted shell into Orbit.

## Upstream inventory and architectural takeaways

| DesktopCommanderMCP implementation | Orbit status / decision | Reason |
| --- | --- | --- |
| Local MCP over stdio (src/server.ts and src/index.ts) | Adopt protocol shape in our Python stdio service | No remote infrastructure needed for local use; do not present local as a ChatGPT cloud connection |
| File read/list and allowed folders (src/tools/filesystem.ts) | Already scoped to one opt-in project; strengthen canonical symlink and sensitive path checks | Scope is a guardrail, not an OS sandbox |
| File content search (src/search-manager.ts) | Adapt concept to a bounded, literal, dependency-free project search | Avoid introducing background ripgrep, cross-drive scope and unbounded regex output |
| Exact search/replace (src/tools/edit.ts) | **Adapted** occurrence count, exact replacement and preview behavior | Abort on ambiguous match; no auto fuzzy correction |
| Newline preservation (src/utils/lineEndingHandler.ts) | **Ported** detection/normalization into src/orbit_rc_text_ops.py | Preserve CRLF/CR/LF in surgical edits |
| Crash-safe write (src/utils/atomic-write.ts) | Preserve existing Orbit fsync-then-same-dir replace; further OS/transactional review | OS filesystem permissions and concurrent symlink swaps are still high-risk |
| Fuzzy matching (src/tools/fuzzySearchCore.ts) | Reject automatic fuzzy edits; read-only suggestions could come later | A near-match can silently edit wrong code |
| Arbitrary shell/interactive terminal/process kill (src/terminal-manager.ts, src/tools/process.ts) | **Not imported into remote-capable product** | An authenticated model/tool remains high privilege; command restrictions are bypassable |
| PDF/Excel/DOCX write handlers and file preview UI | Defer to separate opt-in modules | Large dependency and attack surface; not required for core remote fallback |
| Remote device/mqtt/OAuth and hosted relay (src/remote-device/) | Research design only; do not clone account/transport | It depends on Desktop Commander's service and trust relationships; public Orbit requires independent OAuth/device pairing |
| Config changes, CLI auto setup, telemetry | Preserve Orbit preview-first installer; **do not import telemetry** | The standalone product needs independent privacy/distribution controls |

## Exact implementation boundaries

1. Original/ported behavior inside **src/orbit_rc_text_ops.py**:
   - Upstream line-ending detection and conversion, including mixed-style
     normalization of the *replacement block* to target file style.
   - Exact, non-overlapping match counts and conservative replace-all only
     when user-specified \`expected_replacements\` matches the actual count.
   - Result preview, bounded output and size validation added by Orbit.
2. Orbit's **src/orbit_remote_commander.py** registers:
   - \`orbit_rc_search\` — read-only literal filename/text search, project
     ACL enforced before scanning, max 600 directory entries, 128 files,
     1 MB bytes scanned and 40 result items. No process launch.
   - \`orbit_rc_preview_edit\` — return count, proposed digest and partial
     preview without writing; works while the device is read-only.
   - \`orbit_rc_edit_block\` — available in protocol but requires device write
     mode, separately verified approval, prior digest and exact count;
     the Windows one-click launcher **forces all writes off**.
3. Existing tools \`orbit_rc_status/list/read/write/check\` are retained
   without weakening their defaults. Permissions cannot be inferred from
   the MCP tool list. The code must still be reviewed for local TOCTOU
   and OS-level isolation.
4. **License compliance:** retain pinned upstream attribution and full MIT
   notice in source repository, all code-bearing distribution archives and
   installed program directories. Do not mistake upstream MIT for a blanket
   license for all Orbit-original code.

## Risk controls before further feature adoption

- No arbitrary command/Powershell/SSH/terminal exposed to remote model
  without a separate, audited privilege boundary and per-action consent.
- No persistent tunnel, Windows service or startup mutation from source install.
- Any future remote operation must check authenticated
  user-to-device-to-project grants at gateway **and device**.
- Denied permission is never a fallback trigger; uncertain write effects
  must be inspected, not replayed.
- Tests should cover traversal/UNC/drive-relative paths, secret aliases,
  symlinks, match cardinality, stale digest, large directories/files,
  CRLF, device launcher write-off behavior and MCP tool listing.
- Current project and upstream restrict filesystem paths through checks
  that are advisory. Use low-privilege OS users, VMs or containers as
  actual isolation when untrusted code can be present.

## Follow-up architecture, not implemented here

- Private testing via supported Secure MCP Tunnel with explicit owner connection,
  not an automatic dependency on Desktop Commander.
- Public Orbit ChatGPT plugin connection through a standalone
  HTTPS Streamable MCP gateway, proven OAuth, per-user device pairing,
  expiration and revocation, consent UX, independent security review,
  privacy notice and signed distribution.
- Consider standalone optional modules for file stats, deeper search,
  local process listing and precise line-range reads **only after** the
  above safety and resource budgets are validated. Avoid wholesale vendoring
  of 100+ upstream modules.

## Primary references

- [Pinned upstream source](https://github.com/wonderwhy-er/DesktopCommanderMCP/tree/9a101b17e44577f0baefa4c7120f087881c5cc56)
- [Upstream MIT LICENSE](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/LICENSE)
- [Upstream SECURITY.md](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/SECURITY.md)
- [Upstream edit.ts](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/src/tools/edit.ts)
- [Upstream lineEndingHandler.ts](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/src/utils/lineEndingHandler.ts)
- [Upstream search-manager.ts](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/src/search-manager.ts)
- [Upstream remote-device design](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/9a101b17e44577f0baefa4c7120f087881c5cc56/src/remote-device/README.md)
