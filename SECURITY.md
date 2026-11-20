# Security policy — Orbit Remote Commander

**Pre-release prototype. Do not connect it to the public Internet or deploy it against sensitive projects.** The local stdio service is read-only by default, but remote PC tooling is inherently high risk.

## Current threat boundaries

- `ORBIT_RC_ROOT` must be an explicitly chosen existing project directory; no home directory or drive root.
- File traversal, symlink escapes and common secret paths are denied; these are guardrails, **not OS sandbox isolation**. Run under an OS account with minimal access and use disposable test projects/VMs for untrusted code.
- File writes require `ORBIT_RC_ALLOW_WRITE=1`, prior file SHA-256 and confirmation; the `confirm_write` argument **does not establish human consent**. Any real remote product needs independently enforced, device-side authorization.
- Fixed Git diagnostics (disabled by default) may still read untrusted configuration or trigger helpers; they are not a security sandbox.
- The DesktopCommander-inspired project search is **literal and bounded** (no arbitrary regex or whole-drive search). It validates project scope for each entry, excludes common secret paths and refuses symlink traversal; filename/content filters are still only defense in depth.
- Adapted exact edit rejects unknown/fuzzy matches, checks expected occurrence counts and stale hashes, and preserves Windows line endings. Real write authorization must be enforced by the trusted host/device; the default launcher keeps all writes off.
- The adapted upstream MIT code and copyright are documented in `THIRD_PARTY_NOTICES.md`, included in installation and packaging.
- The source does not listen on a network port, create accounts, pair devices, grant permissions or run background services.

## Future public gateway controls

OAuth 2.1 with validated audience/issuer/scope and standard metadata; short-lived device grants; independent pairing and revocation; per-device/project-root permissions checked server-side and on device; no cross-user fallthrough; rate limiting, concurrency/timeouts, non-replay, audit and log redaction; outbound-only encrypted device connection; rate-limited fail-closed error responses; independent security review.

Do not send credentials, filesystem inventories, token files, private source, crash dumps or other sensitive data to issues/PRs. Treat tool outputs and repository files as untrusted prompt/data.

## Reporting

Use GitHub's private security advisory reporting mechanism if enabled. Otherwise contact the repository owner privately; do not publish exploitation instructions or real credentials in a public issue. Security acceptance must be based on independently tested behavior, not claims from a model or the CLI's read-only flag.

## Distribution

No signed installer, production gateway, verified Windows host deployment or public plugin integration currently exists. A public GitHub repo is not a claim of safety or permission to remotely operate a user's PC.
