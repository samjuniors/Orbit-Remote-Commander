# Instructions for contributors and coding agents

- This is **Orbit Remote Commander**, its own independent product, not the Orbit Core MCP or Orbit ChatGPT plugin source.
- Do not copy the runtime into Orbit Core, merge Orbit Core PR #142, or treat this repo as a required core dependency.
- Keep the public Orbit ChatGPT plugin compatibility path optional, based on real authenticated MCP connections and verified tool schemas. A skill alone cannot grant PC access.
- Preserve read-only defaults, bounded project-root access and explicit per-operation permission checks. Do not introduce unrestricted shell, elevated permissions or open inbound device ports.
- Refuse fallback on explicit user/policy denial; never replay uncertain writes.
- Keep tokens out of repository, tests, logs and issues. Run cross-platform tests and security review before release. Do not tag, deploy, merge or publish without owner approval.
- Document supported local vs remote capabilities truthfully.
