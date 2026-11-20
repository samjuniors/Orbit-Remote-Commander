# Architecture and release gates

## Current local prototype (implemented)

```text
Local MCP-capable host
   └─ (stdio, explicit opt-in)
      ├─ orbit_rc_status/list/read/search/preview_edit/write/edit_block/check
      ├─ project-root validation + secret-pattern guardrails
      ├─ MIT-attributed exact block edit and line-ending preservation
      ├─ bounded literal project search, without subprocess/regex
      ├─ optional SHA-guarded existing-file edits
      └─ optional fixed diagnostic subprocesses

Pure capability selector (does not start a process, perform pairing or grant permission)
   ├─ primary: online/authorized Desktop Commander
   ├─ fallback: separately connected/authorized Orbit Remote Commander
   └─ otherwise: BLOCKED
```

Source of truth: `src/`. The `tests/` folder checks local behavior. Research pinned to DesktopCommanderMCP commit `9a101b17`: [adoption decisions and security boundaries](RESEARCH-DESKTOPCOMMANDER-MCP.md). Upstream MIT copyright/licensing notice is carried with source and all installed/archived copies. No auto-install, web relay, direct network socket, browser UI, or device registry exists.

## Future remote path (NOT implemented)

```text
Orbit ChatGPT plugin (private now, public later)
    ↓ independently authenticated MCP user session
Secure MCP gateway / OAuth resource server (separate deployment)
    ↓ validated user ↔ approved device ↔ project grants
Outbound-authenticated device channel
    ↓ locally enforced ACL + OS permissions + explicit approvals
Windows Orbit Remote Commander companion
```

Use the current OpenAI Plugins MCP and authentication docs, MCP protocol spec, and OWASP security guidance before implementing. A public endpoint must never expose raw command execution. The device should connect outbound, not open a public Windows port. Use per-session authorization, expiry and local device revocation. All user-issued requests and file data crossing a provider boundary require explicit disclosed consent.

## Milestones / acceptance

1. **M0 Standalone migration:** separate source/tests/docs/CI and explicit plugin compatibility contract. Run Linux/Windows tests; no Orbit Core dependency, no merge into Orbit Core.
2. **M1 Local Windows:** tested installer/uninstall/update preview, scope configuration, read-only status and file access, revocation and OS ACLs on disposable Windows environments. No global auto-start without consent.
3. **M2 Secure relay:** independent gateway, OAuth 2.1, protected resource metadata, verified principal/device/project binding on each call, session expiry, requests/receipts, rate limits, TLS, audit and error handling. Adversarial tests required.
4. **M3 ChatGPT integration:** connect through approved public/private ChatGPT plugin support, validate tool schemas and permissions, test two fresh chats, test offline Desktop Commander → authorized Orbit fallback, and denial/no-retry controls.
5. **M4 Public readiness:** independent security audit, documentation/privacy notices, threat model, code signing and distribution provenance, regression/Windows matrix, compatibility matrix, support/revocation and owner approval before public plugin announcement.

No milestone is complete solely because its source or docs exist. Record test dates, tested commits, actual device observations and unresolved risks. Release as its own product independently of Orbit Core and the Orbit ChatGPT plugin.
