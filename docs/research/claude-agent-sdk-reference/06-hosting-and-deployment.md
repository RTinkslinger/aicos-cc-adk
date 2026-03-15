# Hosting & Secure Deployment

**Source:** platform.claude.com/docs/en/agent-sdk/hosting, secure-deployment

## SDK Architecture

Unlike stateless API calls, the Agent SDK operates as a **long-running process** that:
- Executes commands in a persistent shell environment
- Manages file operations within a working directory
- Handles tool execution with context from previous interactions

The SDK spawns a bundled Claude Code CLI binary as a subprocess and communicates via JSON streaming. The CLI is bundled in the pip package (237MB) — no separate installation needed.

## Production Deployment Patterns

### Pattern 1: Ephemeral Sessions
Create a new container per task, destroy when complete.
- Bug investigation, invoice processing, translation, image processing
- Each task gets a clean environment

### Pattern 2: Persistent Sessions
Keep containers running, resume sessions across requests.
- Development environments, long-running projects
- Session ID preserved for continuity

### Pattern 3: Per-User Containers
One container per user, multiple sessions.
- SaaS applications, multi-tenant environments

### Pattern 4: Single Containers
Multiple Claude processes in one container.
- Agent simulations, collaborative agents
- Must prevent agents from overwriting each other

## Security-Hardened Container (Docker)

```bash
docker run \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --security-opt seccomp=/path/to/seccomp-profile.json \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /home/agent:rw,noexec,nosuid,size=500m \
  --network none \
  --memory 2g \
  --cpus 2 \
  --pids-limit 100 \
  --user 1000:1000 \
  -v /path/to/code:/workspace:ro \
  -v /var/run/proxy.sock:/var/run/proxy.sock:ro \
  agent-image
```

**Key hardening flags:**
- `--cap-drop ALL` — remove Linux capabilities (NET_ADMIN, SYS_ADMIN)
- `--security-opt no-new-privileges` — prevent setuid escalation
- `--read-only` — immutable root filesystem
- `--tmpfs` — writable temp that clears on stop
- `--memory 2g` — prevent resource exhaustion
- `--pids-limit 100` — prevent fork bombs
- `--user 1000:1000` — non-root user
- `--network none` — no network access (use proxy socket)
- Mount code read-only (`-v ...:/workspace:ro`)

**NEVER mount:** `~/.ssh`, `~/.aws`, `~/.config`

## Non-Container Deployment (systemd)

For our droplet use case — running directly on the host:

**Verified:** Agent SDK works as root with `dontAsk` permission mode. The `bypassPermissions` restriction is root-only; `dontAsk` + `allowed_tools` is the correct pattern for non-container autonomous agents.

**ANTHROPIC_API_KEY:** Must be in environment. Use systemd `EnvironmentFile=-/opt/web-agent/.env`.

## Permission Modes and Security

```
bypassPermissions + root = BLOCKED (CLI rejects)
bypassPermissions + non-root = works (but dangerous)
dontAsk + root = WORKS (verified on our droplet)
dontAsk + allowed_tools = GOLD STANDARD for autonomous agents
acceptEdits + root = WORKS
```

The `dontAsk` mode combined with `allowed_tools` gives:
- Only listed tools auto-approved
- Everything else denied without prompting
- No human in the loop needed
- Safe for autonomous operation

## Authentication

```bash
export ANTHROPIC_API_KEY=your-api-key
```

Also supports:
- Amazon Bedrock: `CLAUDE_CODE_USE_BEDROCK=1`
- Google Vertex AI: `CLAUDE_CODE_USE_VERTEX=1`
- Microsoft Azure: `CLAUDE_CODE_USE_FOUNDRY=1`

## Cost Controls (Production)

```python
options = ClaudeAgentOptions(
    max_turns=20,        # Cap loop iterations
    max_budget_usd=2.0,  # Dollar ceiling
    effort="medium",     # Lower = fewer tokens per turn
)
```

When limits hit, SDK returns `ResultMessage` with `error_max_turns` or `error_max_budget_usd` subtype.
