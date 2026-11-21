# Orbit Remote Commander — optional Cloudflare Tunnel connection

**Status:** standalone single-owner, read-only remote MCP resource-server foundation. This is not a live ChatGPT-to-PC connection or a public-plugin release.

## Cost and hosting

- Cloudflare supports published tunnels without a paid Cloudflare Access subscription.
- A named tunnel with a stable publicly reachable hostname requires a domain on Cloudflare. Domain registration may cost money if you do not own one. Temporary Quick Tunnel URLs are **not** suitable for private PC access or a public plugin.
- An OAuth identity provider may have independent fees or free-tier limits. ChatGPT eligibility, API model billing and any purchased domain are also separate from tunnel pricing.

Sources: [Cloudflare published application](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/), [named tunnel configuration](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/configuration-file/), [OpenAI plugin MCP](https://developers.openai.com/plugins/build/mcp-server), [OpenAI OAuth](https://developers.openai.com/plugins/build/auth).

## Security architecture

    ChatGPT / Orbit plugin (only if authorized and supported)
      ↓ OAuth authorization code + PKCE with independent established IdP
      ↓ HTTPS MCP + signed access token (audience, owner, expiry and scope verified)
    Cloudflare named tunnel (network transport, not an authorization check)
      ↓ outbound connection from Windows, no home-router inbound port
    Orbit MCP resource server on 127.0.0.1:8765
      ↓ official MCP Python SDK v2; JWKS RS256 token validation
    One approved local project (read/list/search/preview only)
      X no write, shell, process kill, Git diagnostics or desktop control

A public tunnel URL **does not** grant permission to use any PC capability. Only the external issuer can sign access tokens; Orbit validates them and checks the exact user subject and dedicated read scope. There is no homemade token-issuing service. All tools enforce authentication independently of MCP transport middleware.

## Controlled private setup (operator-owned PC only)

1. Review the source and CI artifact. On the owner's online Windows machine, use Python 3.10+ and a verified cloudflared binary. Do not install from unknown URLs or change another product's setup.
2. In a disposable project clone, create a Python virtual environment and install optional dependencies from requirements-remote.txt. The normal local stdio commander requires no remote dependencies.
3. In your own Cloudflare account, configure a **named** tunnel and stable hostname using official Cloudflare Tunnel instructions. The typical commands are cloudflared tunnel login, cloudflared tunnel create orbit-remote, and cloudflared tunnel route dns orbit-remote orbit.example.com. Never commit credentials, tunnel tokens or the JSON credential file.
4. Configure an existing OAuth 2.1 identity provider supporting ChatGPT's required authorization-server discovery, authorization code + PKCE and CIMD/DCR registration where needed. It must issue **RS256 JWT access tokens** with issuer, exact MCP resource audience, owner sub, client_id/azp, iat, exp and dedicated orbit:pc:read scope. Its JWKS must be reachable at an HTTPS endpoint on the issuer's hostname. An OAuth ID token or static API key is not a substitute.
5. Set these environment variables **on the owner's PC** (examples are not secrets): 
   - ORBIT_RC_ROOT: existing approved project folder (not a drive or home root)
   - ORBIT_RC_PUBLIC_URL: https://orbit.example.com/mcp
   - ORBIT_RC_OIDC_ISSUER: exact HTTPS OAuth issuer
   - ORBIT_RC_OIDC_JWKS_URL: HTTPS JWKS URL on the same host as issuer
   - ORBIT_RC_OWNER_SUBJECT: exact owner sub from valid access token
   - ORBIT_RC_LOCAL_PORT: 8765 (optional)
   Do not put passwords, API tokens, Cloudflare credentials or private keys into the repository or environment variable values shown above.
6. Preview an ingress YAML without running any tunnel: invoke the Python tools/remote_tunnel.py with --tunnel-id UUID, --credentials-file ABSOLUTE_JSON_PATH, and --output NEW_CONFIG.yml. The default mode only prints a preview. The separate --apply flag creates that **new** YAML but will never overwrite, configure DNS or start any service.
7. Verify the config using cloudflared tunnel ingress validate and inspect the exact hostname mapping. The generated route only forwards to http://127.0.0.1:8765 and ends with a 404 catch-all. A public hostname does not bypass OAuth.
8. Run Python src/orbit_rc_gateway.py under the configured environment from a trusted terminal. Before starting cloudflared, confirm the local HTTP /mcp endpoint returns **401 Unauthorized** without a bearer token. Verify incorrect Host, audience, owner, scope, signature or expiry are rejected.
9. Only with explicit computer-owner consent, run cloudflared tunnel --config NEW_CONFIG.yml run TUNNEL_UUID from a second terminal. Do not auto-start it or configure a Windows service. From another device confirm the public HTTPS endpoint refuses unauthenticated requests.
10. In a supported ChatGPT workspace, connect the custom MCP URL https://orbit.example.com/mcp with the established OAuth provider. Test status, bounded list, read, search and edit preview against **disposable files**, then disconnect/revoke. Verify write, shell and process tools are not offered.
11. Stop both local processes when finished. Revoke grants with the identity provider and Cloudflare account. Persistent pairing, automatic revocation of previously issued JWTs and production session management remain future work.

These steps require access to the actual online Windows PC and account owner approval. The repository does **not** create a Cloudflare account, domain, tunnel, OAuth credentials, or working ChatGPT connection automatically.

## Public-plugin limitations

This is a **single-owner personal connector foundation**. A future publicly distributed Orbit ChatGPT plugin must use multi-user/device pairing, independent OAuth grants, revocation, device identity, audit, consent, privacy and support processes. Publishing a Cloudflare tunnel for one PC is **not** equivalent to a public multi-user gateway. A public plugin also needs a stable HTTPS MCP endpoint, security review and verified ChatGPT compatibility.

## Security acceptance gates

- Signed access tokens from independently configured trusted OAuth issuer only; signature, issuer, resource, sub, client, scope and expiry validated
- Never trust the public tunnel URL as an authorization decision
- Gateway only listens on 127.0.0.1; Host and Origin checks enabled
- Tools are read-only; no write, terminal, process, GUI, system-control tool remotely exposed
- Exact project root with traversal and secret-file guardrails; use an OS sandbox for untrusted work
- Transport disconnected by default and tunnel config generated with preview-only behavior
- No secrets checked into git; no real PC installation or tunnel started without owner approval
- Live Windows/ChatGPT connection must be observed before being marked connected
