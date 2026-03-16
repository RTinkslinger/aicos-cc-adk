# Publishing Skill

Instructions for publishing content digests to digest.wiki and managing the deployment pipeline.

---

## Publishing Flow

```
DigestData JSON → aicos-digests/src/data/{slug}.json → git commit + push → Vercel auto-deploy (~15s) → https://digest.wiki/d/{slug}
```

---

## Step-by-Step Protocol

### 1. Generate the slug

From the content title:
- Lowercase everything
- Remove special characters: `-- : , . ! ? ' " ( ) [ ] { }`
- Replace spaces with hyphens
- Truncate to 60 characters max

**Examples:**
- "The Future of AI Agents in Enterprise" -> `the-future-of-ai-agents-in-enterprise`
- "YC W25: Top Startups & Trends" -> `yc-w25-top-startups-trends`

### 2. Write the JSON file

**Repository path:** `/opt/aicos-digests` (configurable via `AICOS_DIGESTS_REPO` env var)
**Data directory:** `src/data/`
**File path:** `src/data/{slug}.json`

### 3. Git operations

```bash
cd /opt/aicos-digests

# Always pull before editing (prevents divergence)
git pull --ff-only origin main

# Write the JSON file to src/data/{slug}.json

# Stage and commit
git add src/data/{slug}.json
git diff --cached --quiet || git commit -m "Add digest: {title}"

# Push (triggers Vercel auto-deploy)
git push origin main
```

### 4. Verify deployment

The Vercel deploy hook is also triggered as backup:
```bash
curl -X POST "https://api.vercel.com/v1/integrations/deploy/prj_v8o0adOk8rk9WrdoXAjtazwSIH0n/gQ0xBvBfQ3"
```

This is redundant with the Git Integration auto-deploy but harmless.

**Digest will be live at:** `https://digest.wiki/d/{slug}` within ~15-30 seconds.

---

## DigestData JSON Schema (Full)

Every field documented. Required fields marked with (R).

```json
{
  "slug": "url-slug",                          // (R) URL path component
  "title": "Content Title",                     // (R) Title of the analyzed content
  "channel": "Source Channel/Author",            // (R) Content creator name
  "duration": "1:23:45",                        // (R) Duration or word count
  "content_type": "Podcast",                    // (R) Podcast|Interview|Talk|Tutorial|Panel|Article
  "upload_date": "2026-03-15",                  // (R) Original publish date
  "url": "https://source-url",                  // (R) Link to original content
  "generated_at": "2026-03-15T10:30:00Z",       // (R) ISO-8601 analysis timestamp
  "relevance_score": "High",                    // (R) High|Medium|Low
  "net_newness": "Mostly New",                  // (R) Mostly New|Additive|Reinforcing|Contra|Mixed
  "connected_buckets": [                        // (R) Array of bucket names
    "New Cap Tables",
    "Thesis Evolution"
  ],
  "essence_notes": {                            // (R) Structured analysis
    "core_arguments": ["Argument 1", "..."],
    "data_points": ["Specific data 1", "..."],
    "frameworks": ["Framework 1", "..."],
    "key_quotes": ["\"Verbatim quote\" - Speaker", "..."],
    "predictions": ["Prediction with timeframe", "..."]
  },
  "watch_sections": [                           // Video timestamps worth watching
    {
      "timestamp": "12:30",
      "topic": "Enterprise MCP adoption data",
      "signal": "++"
    }
  ],
  "contra_signals": [                           // Evidence against existing beliefs
    "Counter-argument or risk identified"
  ],
  "rabbit_holes": [                             // Follow-up research topics
    "Deep-dive into X for further investigation"
  ],
  "portfolio_connections": [                    // Links to portfolio companies
    {
      "company": "Company Name",
      "relevance": "Competitive threat from new entrant",
      "signal": "?"
    }
  ],
  "thesis_connections": [                       // Links to thesis threads
    {
      "thread": "Agentic AI Infrastructure",
      "evidence": "MCP enterprise adoption data confirms harness layer value",
      "direction": "for",                       // for|against|mixed
      "strength": "Strong"                      // Strong|Moderate|Weak
    }
  ],
  "new_thesis_suggestions": [                   // Proposed new thesis threads
    {
      "name": "Suggested Thread Name",
      "core_thesis": "The investment hypothesis",
      "trigger": "What in the content triggered this suggestion"
    }
  ],
  "proposed_actions": [                         // Scored action proposals
    {
      "action": "Check with portfolio companies on MCP adoption",
      "type": "Portfolio Check-in",
      "priority": "P1",
      "reasoning": "Enterprise traction data could inform follow-on decisions",
      "score": 7.2,
      "thesis_connection": "Agentic AI Infrastructure"
    }
  ]
}
```

---

## Required vs Optional Fields

### Required (digest will fail validation without these)
- `slug`, `title`, `channel`, `duration`, `content_type`
- `upload_date`, `url`, `generated_at`
- `relevance_score`, `net_newness`, `connected_buckets`
- `essence_notes` (with at least `core_arguments` populated)

### Optional (include when available)
- `watch_sections` (video only, not for articles)
- `contra_signals` (include even if empty array)
- `rabbit_holes`
- `portfolio_connections`
- `thesis_connections`
- `new_thesis_suggestions`
- `proposed_actions`

---

## Slug Conventions

- Must be unique across all digests.
- Lowercase, hyphens only (no underscores, no special characters).
- Max 60 characters.
- Should be human-readable and hint at the content topic.
- Check for duplicates before publishing:
  ```bash
  ls /opt/aicos-digests/src/data/ | grep -i "partial-slug"
  ```

---

## Git Author

Always use: `Aakash Kumar <hi@aacash.me>`

Vercel rejects commits from unknown authors. The droplet git config should have this set globally. If not:
```bash
cd /opt/aicos-digests
git config user.name "Aakash Kumar"
git config user.email "hi@aacash.me"
```

---

## Error Handling

### Git pull fails
- If `git pull --ff-only` fails (diverged branches), do NOT force-push.
- Log the error and skip publishing for this run.
- Notify: write to notifications table that publishing failed due to git divergence.

### Git push fails
- Usually means the remote is ahead. Pull and retry once.
- If still fails, log and skip.

### Vercel deploy hook fails
- Git Integration auto-deploy should handle it.
- Log the failure but don't block -- the push itself triggers deployment.

---

## Post-Publishing Checklist

After successful publish:
1. Record the digest URL: `https://digest.wiki/d/{slug}`
2. Write the corresponding Content Digest entry to Postgres (notion_synced=FALSE).
3. Write proposed actions to Postgres actions table (notion_synced=FALSE).
4. Update thesis threads if thesis connections were identified.
5. The Sync Agent will push all unsynced rows to Notion on its next cycle.
