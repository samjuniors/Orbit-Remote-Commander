# Orbit ChatGPT Plugin — interoperability contract

**Target:** current private `orbit-workspace-orchestrator` ChatGPT plugin v0.26.3 and any future public Orbit ChatGPT plugin release. This is a **planned, optional integration**, not a live authorization, pairing, or ChatGPT endpoint.

## Capability mapping

| ChatGPT Orbit request | First-party tool on independently connected Orbit Remote Commander |
| --- | --- |
| Check device/project access | `orbit_rc_status` |
| List a bounded project directory | `orbit_rc_list` |
| Read non-secret UTF-8 project text | `orbit_rc_read` |
| Edit a previously read text file (opt-in, separately approved) | `orbit_rc_write` |
| Fixed Git diagnostics only (opt-in) | `orbit_rc_check` |

Tool names are provisional but intentionally stable throughout the v0.x local prototype. When the production gateway is built, keep documented operation meanings and introduce explicit version and capability negotiation; no silent changes to approval or scoping contracts. The public ChatGPT plugin must **not** need this repo installed for its general planning, research, GitHub, Notion, or Orbit Core functions.

## Provider-selection rules

1. Prefer a more specific authorized API/connector. For PC actions prefer a live, authorized Desktop Commander if it can operate within the approved project.
2. If primary is **absent, offline, unreachable, or quota unavailable**, inspect an **independently connected** Orbit Remote Commander endpoint and actual target device/project authorization.
3. Select Orbit only when the tool and device are online, project scope matches, and required operation is permitted.
4. User/organization policy denial is **never** a failover trigger. On uncertain write completion, stop and inspect exact effects before a new attempt; never replay automatically.
5. If no provider is authorized, report BLOCKED. A source file, plugin instruction, tool listing, or prior-session device state does not count as live connectivity.

The private plugin v0.26.3 contains routing *instructions* and a bundled local prototype; its current connection status is not proof that ChatGPT can invoke any of these tools on a PC.

## Requirements before a public Orbit ChatGPT plugin can offer this feature

- **Independent auth and consent:** connect a real remote MCP resource from ChatGPT with OAuth 2.1, appropriate protected-resource/authorization-server discovery, account identity checks, per-user grants, revocation and scoped write authorization. Current OpenAI guidance: https://developers.openai.com/plugins/build/auth and https://developers.openai.com/plugins/build/mcp-server .
- **Device pairing:** opt-in installed Windows companion, outbound-only encrypted connectivity, owner confirmation, device identity, short-lived scoped grants, local revocation/uninstall and clear device status. Never borrow another provider's accounts or keys.
- **Server design:** verified Streamable HTTP with up-to-date MCP protocol negotiation (do not hardcode the local demo's protocol version), bounded output, rate limits, secrets redaction, denial of traversal, replay protection and auditable authorization.
- **Public privacy UX:** disclose what PC files may be read/sent to the selected model, who processes data, what operations require approval, how disconnect/revocation works, logging/retention, and default read-only permissions.
- **Compatibility tests:** automated schema and policy contract tests; Windows host read/write/revoke; ChatGPT plugin connection smoke; primary-offline failover; wrong-device rejection; stale-write prevention; fresh-chat repeatability; independent security review.
- **Distribution:** independent versioned releases and signed/verified Windows packages before offering installation. Public Orbit plugin may list this as optional integration; never enable implicitly.

## Compatibility levels

- `DOCUMENTED` — shared tool names and intended semantics; **current**.
- `LOCAL_VERIFIED` — tests passed when explicitly launched in a supported local stdio host; not ChatGPT remote.
- `REMOTE_CONNECTED` — real OAuth/HTTPS MCP, paired Windows device, working private ChatGPT session.
- `PUBLIC_VERIFIED` — public plugin install, separate user consent, revocation, device isolation and production security acceptance.

**Do not describe DOCUMENTED as REMOTE_CONNECTED or PUBLIC_VERIFIED.**

## Product separation

- This repository: first-party remote commander, Windows companion, gateway, tests and versioned releases.
- Orbit ChatGPT plugin: conversation UX, device capability selection, plugin metadata, user controls, future optional integration.
- Orbit Core: independent local-first orchestrator; no required dependency on this remote commander.
- Desktop Commander: optional third-party primary, never a dependency or an authentication/transport component.

The future publicly distributed ChatGPT plugin can interoperate with this project via the documented MCP tools, but compatibility must be proven against each actual release and connection type.
