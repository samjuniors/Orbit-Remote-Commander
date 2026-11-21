# Remote Arc Windows acceptance — 2026-11-21

**Scope:** bounded, disposable real Windows host QA of independent Orbit Remote Commander. No Cloudflare tunnel, public listener, service or ChatGPT connector was started.

## Environment

- Authorized Remote Arc Windows device: DESKTOP-AND1FUJ, Windows build 10.0.26200.9974, x64. Remote Arc agent 0.7.3, online at test time.
- Git: 2.54.0.windows.1.
- Python: 3.12.10 via `py -3.12`. The shell's `python` resolves to a Windows Store app execution alias and **does not execute Python**; use `py -3.12` or a venv interpreter in the setup guide.
- Source checkout: `C:\Users\sumit\Orbit-Remote-Commander-test`, checked out from draft feature branch at immutable commit `ca29a995dd5254974617e71125364ff470cef735`.
- Disposable project folder: `C:\Users\sumit\Orbit-Remote-Commander-test\qa-fixture`, containing only generated `example.txt`.
- Disposable install folder (via `ORBIT_RC_INSTALL_HOME`): `C:\Users\sumit\Orbit-Remote-Commander-test\qa-install`; **not** the user's production LOCALAPPDATA install. The test copies optional remote sources but does not launch the gateway.
- This is a local acceptance observation, not an externally connected ChatGPT or public-MCP acceptance.

## Observed results

| Gate | Result | Evidence |
| --- | --- | --- |
| Remote Arc can reach owner PC | PASS | Paired device `DESKTOP-AND1FUJ` online, platform win32, `list_directory`, `read_file`, `start_process` available |
| Source checkout | PASS | `git clone --depth 1 --single-branch --branch feature/standalone-foundation`, HEAD `ca29a995dd5254974617e71125364ff470cef735` |
| Python/environment | PASS with environment caveat | `py -3.12 --version` 3.12.10; bare `python` fails due to app execution alias |
| Optional remote dependencies | PASS | Dedicated `.venv` imports `mcp` and `jwt` successfully |
| Windows Python test suite | PASS | `74 tests in 0.624s; OK (skipped=4)`; isolated RPC, OAuth HTTP, installer, tunnel configuration and local tool tests |
| Install preview | PASS | `PREVIEW_ONLY`, did not enable auto-start, write, network listener or checks |
| Disposable local install | PASS | `INSTALLED_LOCAL_ONLY` in `qa-install`; staged 9 source/license/config files |
| Local file integrity | PASS | `LOCAL_FILES_VERIFIED`; all 9 installed file hashes match the manifest |
| MCP stdio status | PASS | `READY_LOCAL_STDIO`, `read_only=true`, `checks_enabled=false`, `remote_relay=NOT_CONFIGURED` |
| Read disposable project file | PASS | `orbit_rc_read(example.txt)` returned `Orbit disposable test` |
| Attempt to write in local read-only session | PASS (denied) | `orbit_rc_write(..., confirm_write=true)` returned MCP error |
| Cloudflare account/domain inventory | PASS (read-only) | User's Cloudflare account had an active `samjuniors.com` zone. No existing Cloudflare Tunnels were found |
| Actual named tunnel | NOT RUN | `cloudflared` not found on PATH; no tunnel was created, configured, installed or run |
| Actual OAuth issuer | NOT RUN | No OAuth provider or signed production access token configured |
| ChatGPT-to-PC via Orbit | NOT RUN | No authenticated remote MCP connection or plugin pairing configured |
| Actual remote write/command/GUI | NOT IMPLEMENTED | HTTP gateway intentionally publishes read-only tools |

## Safety and distribution

- No existing Orbit Core repository or user's application project was modified.
- No Cloudflare API mutation, DNS change, inbound firewall opening, live remote service, installed Windows startup task or sensitive credential access occurred.
- The optional authenticated HTTP gateway passed **simulated** localhost/MCP acceptance in the repository tests; it was **not exposed through a real tunnel**.
- For real PC connection: use a separately approved hostname (e.g. a new subdomain under existing active domain), a working Cloudflare named tunnel, a compatible external OAuth identity provider, owner confirmation of project root and explicit ChatGPT custom MCP connector setup. Do **not** expose until auth, audience/issuer validation and revocation/consent have been verified.
- Note the `Remote Arc` connection is a temporary development/testing control plane, **not** proof of connection by the standalone Orbit ChatGPT plugin.
