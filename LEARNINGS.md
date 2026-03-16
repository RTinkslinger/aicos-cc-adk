# LEARNINGS.md

Trial-and-error patterns discovered during Claude Code sessions.
Patterns confirmed 2+ times graduate to CLAUDE.md during milestone compaction.

## Active Patterns

### 2026-03-06 - Sprint 2
- Tried: Build Roadmap `notion-create-pages` with plain text select values ("Planned", "Sequential", "Core Product", "XS (<1hr)")
  Works: Must use emoji-prefixed values matching exact Notion options: "🎯 Planned", "🔴 Sequential", "🟢 Safe", "XS (< 1hr)" (note space before 1hr)
  Context: Build Roadmap DB select fields all have emoji prefixes and exact spacing. Always query the DB schema first or use known exact values.
  Confirmed: 1x (4 consecutive failures in one call sequence)

- Tried: Using CLAUDE.md Build Roadmap "Creating items" recipe with generic Epic values ("Core Product", "Data & Schema", etc.)
  Works: Actual Epic options are project-specific: "Content Pipeline v5", "Action Frontend", "Knowledge Store", "Multi-Surface", "Meeting Optimizer", "Always-On", "Infrastructure"
  Context: The Build System Protocol template in CLAUDE.md has generic placeholder Epic values. Must use actual DB options. Update CLAUDE.md recipe if this recurs.
  Confirmed: 1x

- Tried: Build Roadmap Source = "Verification Failure" (from CLAUDE.md Build System Protocol template)
  Works: Actual Source options are: "Session Insight", "AI CoS Relevance Note", "User Request", "Bug/Regression", "Architecture Decision", "External Inspiration"
  Context: CLAUDE.md Build System Protocol has generic Source values that don't match the actual DB. Always use exact DB option strings.
  Confirmed: 1x

### 2026-03-15 - Sprint 3

- Tried: SSH heredoc with nested Python f-strings containing quotes (e.g. `ssh host "python -c \"f'{r.get(\"key\")}'\""`
  Works: Write Python test script to a local file, rsync to remote, then `ssh host "cd /dir && uv run python script.py"`
  Context: Triple-nested quoting (shell → SSH → Python → f-string) is impossible to maintain. Always use file-based test scripts for remote Python execution.
  Confirmed: 2x (test_scrape and test_browse both failed with SyntaxError)

- Tried: macOS rsync with `--chmod=F600` flag (from cookie-sync.sh)
  Works: Remove `--chmod` — macOS bundled rsync doesn't support it. Set permissions on the source files instead (`chmod 600` during extraction).
  Context: GNU rsync has `--chmod` but macOS ships with a different rsync version. Cookie-sync.sh was written for Linux rsync.
  Confirmed: 1x

- Tried: rsync to Tailscale host without `root@` prefix (e.g. `rsync files/ aicos-droplet:/path/`)
  Works: Must use `root@aicos-droplet:/path/`. Tailscale SSH attempts local username lookup and fails with "failed to look up local user".
  Context: Tailscale SSH maps SSH users; without explicit user, it tries the local Mac username which doesn't exist on the droplet.
  Confirmed: 1x

- Tried: Playwright `wait_until="networkidle"` for JS-heavy SPAs (YouTube, X/Twitter)
  Works: Add `wait_after_ms` delay (3000ms default) after navigation. `networkidle` fires when no pending requests for 500ms, but React/Vue apps continue rendering after data loads. YouTube needs ~3-5s, X needs ~3s.
  Context: `document.body.innerText` returns empty string if called before React hydration completes. The page HTML is large (2MB YouTube, 700K X) but innerText is 0 until the framework renders.
  Confirmed: 3x (YouTube, X home, X bookmarks — all returned 0 content without delay)

- Tried: Editing `/root/.cloudflared/config.yml` and restarting cloudflared service
  Works: Edit `/etc/cloudflared/config.yml` instead. When cloudflared is installed as a systemd service, it copies config to `/etc/cloudflared/` and reads from there. Changes to `~/.cloudflared/config.yml` are silently ignored by the service.
  Context: The log line `Settings: map[config:/etc/cloudflared/config.yml ...]` shows which file is being used. Always check this log line after restart. This is a known confusing Cloudflare design — multiple community threads report the same issue.
  Confirmed: 1x

- Tried: Jina search endpoint `s.jina.ai` as free search (same as Jina Reader `r.jina.ai`)
  Works: `s.jina.ai` requires API key (returns 401 AuthenticationRequiredError). Only `r.jina.ai` (reader) is free. For search without API key, must use Firecrawl or other paid service.
  Context: Phase 0 evaluation tested Jina Reader (free) but search endpoint has different auth requirements. Design docs didn't distinguish the two.
  Confirmed: 1x

- Tried: Ubuntu 24.04 dpkg `install-info` package failing with "rm: not found" during postinst
  Works: Check `/etc/environment` — a stale `PATH=/root/.deno/bin` line (from deno install) was overwriting the full PATH. Removing line 2 fixed dpkg, apt, and all package installs.
  Context: `/usr/sbin/update-info-dir` sources `/etc/environment`, which clobbers PATH if it contains a bare `PATH=` assignment instead of appending. Always check `/etc/environment` when dpkg scripts can't find basic commands.
  Confirmed: 1x

- Tried: FastMCP `@mcp.on_startup()` and `@mcp.on_event("startup")` decorator for server lifecycle hooks
  Works: FastMCP 3.x uses `lifespan` parameter on constructor: `mcp = FastMCP("name", lifespan=my_lifespan)` where `my_lifespan` is an `@asynccontextmanager`. Code before `yield` runs on startup, after `yield` runs on shutdown.
  Context: FastMCP 2.x had `@mcp.on_startup()` decorator. v3.x (3.1.1, installed via pyproject.toml `fastmcp>=2.0.0`) removed it in favor of ASGI-standard `lifespan` pattern. Agent subagents generated code with the old API since their training data predates v3.
  Confirmed: 2x (sync/server.py `@mcp.on_startup()` + content/server.py `@mcp.on_event("startup")` both crashed)

- Tried: `ThinkingConfig(type="enabled", budget_tokens=10000)` in Agent SDK runner
  Works: Import and use `ThinkingConfigEnabled` instead. `ThinkingConfig` is a `types.UnionType` alias (`ThinkingConfigAdaptive | ThinkingConfigEnabled | ThinkingConfigDisabled`), not a class. Must use the concrete variant.
  Context: Agent SDK exports `ThinkingConfig` as a union type for type annotations. The constructors are the individual variants. Subagents generated code using `ThinkingConfig()` because the name looks like a class.
  Confirmed: 2x (content/runner.py + sync/runner.py both crashed with same TypeError)

- Tried: ALTER TABLE on `action_outcomes` as role `aicos` (via DATABASE_URL)
  Works: Connect as `postgres` superuser: `sudo -u postgres psql -d aicos_db -c "ALTER TABLE action_outcomes OWNER TO aicos;"` then re-run the ALTER as `aicos`.
  Context: The `action_outcomes` table was created by `postgres` role (not `aicos`), so only the owner or superuser can ALTER it. The DATABASE_URL connects as `aicos`. Fix ownership first via superuser, then the migration succeeds.
  Confirmed: 1x

- Tried: Notion date property with `date:Field:start` shorthand in `pages.create()` with `data_source_id` parent for Thesis Tracker DB
  Works: Standard Notion API format `{"date": {"start": "YYYY-MM-DD"}}` — works for all DBs
  Context: `date:Field:start` shorthand works for Content Digest DB but fails for Thesis Tracker with misleading validation error ("Thread Name.id should be defined"). The shorthand is a Notion client convention that doesn't work consistently across all databases when using data_source_id. Use standard format for safety.
  Confirmed: 1x
