# Custom MCP Server Setup for Claude.ai

> How to expose a self-hosted FastMCP server to Claude.ai as a remote connector, using Cloudflare Tunnel for secure public access.

## Architecture Overview

```
Claude.ai (Anthropic servers)
    |
    | HTTPS (MCP spec 2025-06-18)
    v
Cloudflare Edge (TLS termination)
    |
    | Cloudflare Tunnel (encrypted, no inbound ports)
    v
Droplet (localhost:8000) — FastMCP server
```

**Why this works:** Claude.ai calls MCP tools from Anthropic's servers, not your device. Your Mac/iPhone being on Tailscale doesn't help — Anthropic's servers can't reach Tailscale IPs. Cloudflare Tunnel punches out from the droplet to Cloudflare's edge, making the MCP server publicly reachable without opening firewall ports.

## Prerequisites

- A server running your MCP server (e.g., DO droplet)
- FastMCP >= 2.0 (we use 3.1.0) with `mcp` >= 1.8.0
- A domain with DNS managed by Cloudflare (Cloudflare must be authoritative DNS — see Domain Setup below)
- Claude.ai Pro/Max plan

## Step-by-Step Setup

### 1. FastMCP Server: Streamable HTTP Transport

Claude.ai requires MCP spec 2025-06-18 (Streamable HTTP transport). In your `server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

# ... define your tools with @mcp.tool() ...

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

**Key details:**
- `transport="streamable-http"` — NOT `"sse"` or `"stdio"`. Both `"streamable-http"` and `"http"` are valid in FastMCP 3.x.
- Default endpoint path is `/mcp` (configurable via `path="/"` kwarg, but `/mcp` works fine with Claude.ai despite some docs suggesting root is required)
- FastMCP 3.x automatically handles the MCP protocol version header, session management, and spec compliance
- The server listens on `0.0.0.0:8000` — only accessible locally (Cloudflare Tunnel proxies to localhost)

**Verify locally:**
```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  http://localhost:8000/mcp
```

Expected: SSE response with `protocolVersion: "2025-06-18"` and your server info.

### 2. Domain Setup (Cloudflare as Authoritative DNS)

**Critical requirement:** Cloudflare Tunnel custom hostnames ONLY work when Cloudflare is the authoritative DNS for the domain. Adding a CNAME at an external DNS provider (e.g., Squarespace) pointing to `*.cfargotunnel.com` will NOT work — the tunnel domain resolves to a private IPv6 address that only Cloudflare's edge can route.

**Options:**
- **Best:** Buy a domain directly from Cloudflare Registrar (at-cost pricing, instant DNS setup, full API). We used a cheap dedicated domain (`3niac.com`) to avoid touching production domain DNS.
- **Alternative:** Move an existing domain's nameservers to Cloudflare. Risk: must replicate all existing DNS records (website, email, etc.) first.
- **Not recommended:** Adding CNAME at external DNS provider — will fail with SSL handshake errors or private IP resolution.

### 3. Install cloudflared on Server

```bash
# Ubuntu/Debian
curl -L --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i /tmp/cloudflared.deb
cloudflared --version
```

### 4. Authenticate and Create Named Tunnel

```bash
# Login — opens a browser URL to authorize
cloudflared tunnel login
```

This saves a certificate to `~/.cloudflared/cert.pem`. If the cert downloads to your local machine instead of the server (browser-based auth), upload it:
```bash
scp ~/Downloads/cert.pem root@your-server:~/.cloudflared/cert.pem
```

**Important:** The cert is scoped to the domain you select during authorization. If you need to use a different domain later, you must re-login (backup the old cert first: `mv cert.pem cert.pem.olddomain.bak`).

Create the tunnel:
```bash
cloudflared tunnel create my-mcp-tunnel
# Output: Tunnel credentials written to ~/.cloudflared/<TUNNEL_ID>.json
# Note the tunnel ID (UUID)
```

### 5. Route DNS

```bash
cloudflared tunnel route dns my-mcp-tunnel mcp.yourdomain.com
# Output: Added CNAME mcp.yourdomain.com which will route to this tunnel
```

This creates a CNAME record in Cloudflare DNS automatically.

### 6. Configure Tunnel

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

The catch-all `http_status:404` rule is required by cloudflared.

### 7. Install as Systemd Service

```bash
# Copy config to system location
cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml

# Install and enable
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared

# Verify
systemctl status cloudflared
```

The tunnel now auto-starts on boot and auto-restarts on failure.

### 8. Verify Public Endpoint

```bash
# Wait ~30s for TLS cert provisioning on first setup
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  https://mcp.yourdomain.com/mcp
```

Expected: Same SSE response as local test, now over HTTPS with valid Cloudflare-issued TLS cert.

**TLS note:** Cloudflare automatically provisions and renews TLS certificates for tunnel hostnames. No Let's Encrypt, no cert management.

### 9. Add as Claude.ai Connector

1. Go to Claude.ai **Settings -> Integrations** (or **Connectors**)
2. Add new connector
3. Paste URL: `https://mcp.yourdomain.com/mcp`
4. Claude.ai will discover available tools automatically

**Auth:** On Pro/Max plans, only authless connectors work cleanly. OAuth requires Team/Enterprise. The URL is unguessable-enough for a single-user system (obscure domain + Cloudflare's DDoS protection).

### 10. Claude Code Connection (Optional)

Claude Code can connect via Tailscale (direct, no tunnel needed) or through the tunnel.

**Via Tailscale** (preferred — lower latency):
Add to `.mcp.json` in project root or user settings:
```json
{
  "mcpServers": {
    "ai-cos-mcp": {
      "type": "url",
      "url": "http://aicos-droplet:8000/mcp"
    }
  }
}
```

**Via tunnel** (if Tailscale unavailable):
```json
{
  "mcpServers": {
    "ai-cos-mcp": {
      "type": "url",
      "url": "https://mcp.yourdomain.com/mcp"
    }
  }
}
```

## Gotchas and Learnings

### Cloudflare Tunnel requires Cloudflare DNS
You cannot use a CNAME at an external DNS provider (Squarespace, GoDaddy, etc.) pointing to `<tunnel-id>.cfargotunnel.com`. That domain resolves to a private IPv6 address (`fd10:...`) that only Cloudflare's proxy edge can route. Without Cloudflare as authoritative DNS, clients get SSL handshake failures or connection refused.

### `/mcp` path works (root not required)
Some documentation suggests Claude.ai requires the MCP endpoint at root path `/`. In practice, FastMCP's default `/mcp` path works fine. No need to override.

### TLS cert provisioning takes ~30 seconds
On first tunnel setup for a new hostname, the SSL handshake will fail for about 30 seconds while Cloudflare provisions the edge certificate. Just wait and retry.

### Quick tunnels for testing
Before committing to the full setup, test with a quick tunnel (no account needed):
```bash
cloudflared tunnel --url http://localhost:8000
```
This gives a random `*.trycloudflare.com` URL — ephemeral but instant. Useful for verifying your MCP server works with Claude.ai before buying a domain or configuring DNS.

### Cert downloads to browser, not server
`cloudflared tunnel login` opens a URL in your browser. The cert downloads to wherever your browser saves files — usually your local machine, not the server. You'll need to `scp` it to the server's `~/.cloudflared/` directory.

### Cert is domain-scoped
Each cert authorizes tunnels for one domain. To use a different domain, re-run `cloudflared tunnel login`, select the new domain, and upload the new cert. Back up the old cert first.

## Our Setup (AI CoS)

| Component | Value |
|-----------|-------|
| Server | DO droplet (`aicos-droplet`) via Tailscale |
| MCP framework | FastMCP 3.1.0 / mcp 1.26.0 |
| Transport | `streamable-http` on port 8000 |
| Tunnel domain | `3niac.com` (Cloudflare Registrar) |
| Public endpoint | `https://mcp.3niac.com/mcp` |
| Tunnel ID | `a381fcd4-b7fa-4226-8615-a77cfa498d09` |
| Systemd services | `state-mcp.service` (port 8000) + `web-tools-mcp.service` (port 8001) + `orchestrator.service` + `cloudflared.service` (tunnel) |
| Tunnel routes | `mcp.3niac.com` → localhost:8000 (State MCP), `web.3niac.com` → localhost:8001 (Web Tools MCP) |
| Claude.ai | Connected as remote connectors (both endpoints) |
| Claude Code | Connected via `.mcp.json` using tunnel URLs (`type: "http"`) |
