# Private ChatGPT trial using Secure MCP Tunnel (NOT public distribution)

OpenAI's [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) is the recommended *private verification path*. It lets a connector on an authorized Windows PC make outbound HTTPS calls to OpenAI without a public listener. **It is not a deployed Orbit relay, an Orbit device agent, a public-plugin submission endpoint, or an entitlement guarantee.**

## Prerequisites

- A Windows machine online and under the user's control; Python 3.10+; Orbit Remote Commander development candidate independently reviewed.
- The isolated **local-only** installer from this repo installed into the current OS user (never from an unverified download).
- A project root chosen by the owner. Setup defaults to read-only and prohibits writes/diagnostics when launched by the generated local runner.
- An OpenAI Platform organization with appropriate **Tunnels Read / Manage / Use** permissions and a linked eligible ChatGPT workspace that permits custom MCP plugins. Check actual plan/workspace eligibility rather than assuming it.
- OpenAI's official, independently verified tunnel-client binary. An operator-managed tunnel ID and runtime API key entered **locally**, not into ChatGPT messages, code, ZIPs or GitHub.
- Explicit user authorization to connect selected project files to the selected AI provider; project source and output can be transferred through the service.

## Local setup (manual approval)

1. Obtain this repository's reviewed candidate from its own CI artifact or approved release when available. Verify checksums and inspect scripts first.
2. On Windows, select a **disposable** project, then open Orbit Remote Setup.cmd, click **Preview**, review paths, and **Install**. This places program files and a scoped read-only config under LOCALAPPDATA/OrbitRemoteCommander but does **not** configure ChatGPT or startup tasks.
3. Run local status using python tools/windows_setup.py status. The result LOCAL_FILES_VERIFIED confirms files only, **not remote access**.
4. Check your machine's local executable with a supported stdio MCP test host. The target is LOCALAPPDATA/OrbitRemoteCommander/run_orbit_rc.py. The server reports READY_LOCAL_STDIO, read_only=true, remote_relay=NOT_CONFIGURED.
5. Create a tunnel in your **own** Platform tunnel settings; record tunnel ID locally. Install the verified official tunnel-client. Inspect its current CLI help; configure its local stdio profile with the --mcp-command option pointing to python plus the absolute path to run_orbit_rc.py.
6. From a trusted terminal with the runtime key supplied through a secure local environment mechanism, run the official client's doctor command, then its run command. Do not put keys in repository config, terminal history or screenshots. Do not start it as a background service automatically.
7. In a supported ChatGPT workspace, choose Plugins → Add custom MCP server → Connection: **Tunnel**; connect only this authorized tunnel and review the permissions. Trigger a harmless orbit_rc_status call and a read of a disposable test file, then disconnect and revoke the tunnel. Check the tool-list snapshot if changed.
8. Record the exact device, tunnel ID (nonsecret), ChatGPT plugin release, permission scopes, test timestamps and observed results without including files or credentials.

Official starting points: [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), [Connecting custom MCP servers](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt), and [Orbit plugin compatibility](CHATGPT-COMPATIBILITY.md).

## Private/public limitation

OpenAI's secure tunnel is for a **private** server, not public plugin submission. A publicly distributed Orbit ChatGPT plugin that offers this capability needs a stable publicly reachable HTTPS MCP resource server, compatible OAuth identity provider, per-user device pairing, independent user/device/project access controls, correct privacy disclosures and a full security audit. Those components are **not shipped** by this local candidate.

For public deployment use an established OAuth provider (avoid a home-grown authorization server). Use the [official MCP Python SDK](https://py.sdk.modelcontextprotocol.io/run/authorization/) or equivalent vetted library for Streamable HTTP and resource metadata, validating scope and audience on each call. Never expose the local stdio process or a raw shell to the Internet.

## No hidden fallback

The orbit_remote_fallback.select_provider function describes policy but cannot register a ChatGPT connector, create a tunnel, pair a PC or skip user approval. A failed Desktop Commander call does not authorize a different connection. First verify the independent Orbit endpoint, exact device and project scope; only then consider an idempotent read. Never replay writes with uncertain effects.
