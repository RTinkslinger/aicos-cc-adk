# Web Strategy Skill

Instructions for choosing the right web extraction method for any URL.

---

## Decision Tree: Scrape vs Browse vs Search

Follow this sequence for every web task:

### Step 0: Check the Strategy Cache

Before doing anything, query the UCB bandit cache for the target domain:

```
check_strategy(domain="example.com")
```

If a cached strategy exists with `source: "ucb"` and `success_rate > 0.7`, use it. The bandit has learned what works.

If `source: "unexplored"` or `source: "default"`, proceed with the decision tree below.

### Step 1: Do you need to find URLs first?

If yes: `web_search(query)` first, then scrape/browse the result URLs.

### Step 2: Classify the site

Use `fingerprint(url)` for unknown domains. It returns:
- `is_spa` (boolean) -- React, Vue, Next.js, etc.
- `auth_required` (boolean) -- login wall detected
- `framework` -- detected framework name

**Or use these heuristics for common domains:**

| Domain Pattern | Type | Best Method |
|---------------|------|-------------|
| `github.com`, `*.readthedocs.io`, `docs.*` | Static docs | scrape (Jina) |
| `medium.com`, `substack.com`, `*.blog.*` | Blog/article | scrape (Jina) |
| `twitter.com/x.com`, `linkedin.com` | Auth-required SPA | browse + auth ladder |
| `*.vercel.app`, `*.netlify.app` | SPA | browse (auto readiness) |
| `youtube.com` | Video platform | extract_youtube / extract_transcript |
| News sites (`nytimes`, `wsj`, etc.) | Paywall | scrape (Jina) first, browse if blocked |
| Government/academic | Static HTML | scrape (Jina) |

### Step 3: Choose from the cost ladder

Always start cheapest. Escalate only on failure.

```
1. scrape (Jina Reader, free)     -- Static HTML, articles, docs
2. scrape (Firecrawl, API key)    -- Better JS handling than Jina
3. browse (Playwright, headless)  -- SPAs, JS-heavy, interactive
4. interact (Playwright actions)  -- Forms, clicks, multi-step
5. screenshot (visual capture)    -- When text extraction fails
```

---

## Readiness Ladder for `browse`

When using `browse` on SPA or JS-heavy pages, choose the readiness mode:

### `none` -- No wait (fastest)
Use for: Static pages served via CDN. Page is complete on DOMContentLoaded.

### `auto` -- MutationObserver (default, recommended)
Use for: Most SPAs. Waits for DOM to stabilize (500ms quiet window).
Fallback chain: check text length > 500 → MutationObserver quiet window → framework markers (__NEXT_DATA__, #root) → 3s time fallback.

### `selector:<css>` -- Wait for specific element
Use for: Known page structures. Example: `selector:.article-body`, `selector:[data-testid="post-content"]`.
Times out after 10s and falls through to auto.

### `time:<ms>` -- Fixed wait
Use for: Sites that load in bursts. Example: `time:5000` for heavy dashboards.
Capped at 30s maximum. Non-blocking (asyncio.sleep).

---

## UCB Bandit Interpretation

The strategy cache uses Upper Confidence Bound (UCB1) algorithm to balance exploitation (use what works) vs exploration (try alternatives).

### What the response fields mean

```json
{
  "strategy_name": "jina_reader",      // Method to use
  "config": {"method": "jina"},        // Configuration details
  "success_rate": 0.85,                // Historical win rate
  "attempts": 20,                      // Times tried
  "source": "ucb"                      // Selection method
}
```

- `source: "ucb"` -- Bandit selected this based on history. Trust it.
- `source: "unexplored"` -- Never tried. Will be explored first.
- `source: "default"` -- No data at all. Seed strategies from fingerprint.

### When to override the bandit

1. **Auth state changed** -- You just saved fresh storageState. Try browser_with_cookies even if bandit prefers jina.
2. **Content type mismatch** -- Bandit says scrape but you need interactive content (form results, paginated lists).
3. **Rate limited** -- Bandit's top strategy got rate-limited. Drop to next.

### Seeded strategies by site type

**SPA detected:**
1. `jina_reader` (method: jina)
2. `browser_mutation_observer` (method: browse, readiness: auto)
3. `browser_time_wait` (method: browse, readiness: time:5000)

**Static site:**
1. `jina_reader` (method: jina)
2. `browser_fast` (method: browse, readiness: none)

**Auth required (appended to either):**
3/4. `browser_with_cookies` (method: browse, readiness: auto, cookies: true)

---

## Diagnostic Queries

Check what the bandit has learned:

```bash
# All strategies across all domains
sqlite3 /opt/agents/data/strategy.db "SELECT origin, strategy_name, successes, failures, total_attempts, ROUND(CAST(successes AS REAL)/MAX(total_attempts,1), 2) as win_rate FROM strategies ORDER BY origin, win_rate DESC;"

# Best strategy per domain
sqlite3 /opt/agents/data/strategy.db "SELECT origin, strategy_name, successes, total_attempts FROM strategies WHERE total_attempts > 0 ORDER BY origin, CAST(successes AS REAL)/total_attempts DESC;"

# Recently used strategies
sqlite3 /opt/agents/data/strategy.db "SELECT origin, strategy_name, last_used FROM strategies WHERE last_used IS NOT NULL ORDER BY last_used DESC LIMIT 20;"
```

---

## Recording Outcomes

Strategy outcomes are recorded automatically by the `record_strategy_outcome` hook after every browse, scrape, and search call. You do not need to record outcomes manually.

The hook records:
- `origin` -- domain of the URL
- `strategy_name` -- which method was used
- `success` -- boolean (based on content quality score >= 70)
- `latency_ms` -- how long the extraction took

Over time this builds a per-domain profile of what works.
