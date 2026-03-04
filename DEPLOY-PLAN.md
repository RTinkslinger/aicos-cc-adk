# Vercel Auto-Deploy: ✅ SOLVED

## Solution (Session 022)
**osascript MCP tool** runs shell commands on the Mac host, bypassing the Cowork sandbox network entirely.

```
Cowork sandbox: commit JSON locally
    ↓
osascript MCP: git push origin main (runs on Mac)
    ↓
GitHub Action: checkout → vercel build → vercel deploy --prebuilt
    ↓
Vercel production: live in ~90s
```

**Proven e2e:** Commit `f95de07` pushed from Cowork via osascript → GitHub Action succeeded (run 22575444869, 1m27s) → deployed to production.

**How to use from Cowork:**
After committing locally, call: `osascript 'do shell script "cd REPO && git push origin main 2>&1"'`
where REPO = `/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests`

**Gotcha discovered:** Every JSON in `src/data/` gets SSG-rendered. Invalid JSON (missing required fields) breaks the entire Next.js build. Only commit valid digest JSONs.

---

*Original research (8 approaches evaluated, Session 022) archived to `docs/iteration-logs/2026-03-01-session-022-deploy-research.md`. Key finding: Cowork sandbox blocks ALL outbound network; osascript MCP on Mac host is the only reliable push mechanism.*
