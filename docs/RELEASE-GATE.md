# Release gate and acceptance ledger

**Product:** Orbit Remote Commander (standalone repository)
**Development branch:** feature/standalone-foundation
**Policy:** No automatic merge, release, deployment or installation; preserve Orbit Core main unchanged.

| Gate | Status | Required evidence |
| --- | --- | --- |
| Separate source repository, no Orbit Core dependency | PASS | Independent source/tests/docs/CI in this repository; Orbit Core PR #142 closed unmerged |
| Local read/list, secret/traversal limits, SHA write guard | PASS (simulated tests) | Python unit tests and MCP stdio framing; local write remains disabled by Windows launcher |
| Source annotations for read/write tool safety | PASS (source) | MCP tools include readOnlyHint/destructiveHint; host permissions are independent |
| Cross-platform CI with Windows | PASS (CI, see exact-head GitHub Actions) | GitHub Actions checks for Python 3.10–3.13 on Linux, 3.12 Windows; 40 tests each at implementation commit fa554576 (GitHub Actions run 44742777125) |
| Windows preview/install/status/uninstall | PASS (disposable CI only) | Per-user install tests; no personal machine installation or GUI manual acceptance |
| SHA-256 reproducible unsigned review package | PASS (unsigned candidate CI artifact) | CI artifact; not a signed or released installer |
| Owner's actual Windows device installed and paired | NOT RUN | Currently remote device unavailable; requires operator consent |
| Private OpenAI Secure MCP Tunnel | NOT RUN | Requires user's Platform tunnel ID, locally stored runtime key, eligible ChatGPT workspace, real tool call |
| Production HTTPS MCP gateway with OAuth | NOT IMPLEMENTED | Required for public plugin distribution; established IdP, access controls, threat model |
| Multi-user/device pairing, revoke, expiry, replay protection | NOT IMPLEMENTED | Independent gateway and device tests, per-user project scoping |
| Public plugin compatibility and consent | DOCUMENTED ONLY | ChatGPT plugin v0.26.3 and later instructions align with the local tools; live full MCP eligibility and tests must be confirmed |
| Independent security review and signed public binaries | NOT RUN | External review, SBOM/provenance and Windows signing |
| Owner release/merge approval | NOT GIVEN | Preserve draft PR; do not publish |

## Known limitations and safe behavior

- No remote PC access is enabled by cloning this repo or running the setup GUI. The verified source is a **local stdio MCP server**.
- Secure MCP Tunnel is an OpenAI transport for private testing only. It is **not** a public-plugin publication solution, and workspace/plan availability is separately governed.
- The Windows setup launcher disables write and Git diagnostics even if untrusted local config requests broader permissions. A future write feature needs actual device-side consent, not just an LLM parameter.
- No full desktop GUI/screenshot, arbitrary terminal, process manager or privilege elevation.
- Filename/path guardrails are defense in depth, not an OS sandbox. Even Git read commands can have side effects from untrusted configuration; keep diagnostics disabled on untrusted repositories.
- Current private Orbit ChatGPT plugin has only the **routing instructions** until a real independent MCP endpoint exists. Its presence alone is not device pairing.

## Next approval-bound work

1. Verify the branch at exact head and run read-only GUI/manual Windows smoke in a disposable VM.
2. When a PC is connected, install the candidate only after user approves selected project root and exact file preview. Do not touch user project settings otherwise.
3. Use an authorized Secure MCP Tunnel for private ChatGPT read-only acceptance, where eligible.
4. Implement independent public HTTPS OAuth MCP gateway and device pairing only after choosing host/IdP, threat model and least-privilege grants. No homemade OAuth or default-open shell.
5. Review license and distribution policy, security, privacy, signing and public plugin eligibility before publishing.
