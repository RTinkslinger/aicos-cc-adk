# Auth Escalation Skill

5-step authentication ladder for accessing sites that require login. Always escalate in order -- never skip steps.

---

## The 5-Step Ladder

### Step 1: storageState (fastest, zero cost)

Playwright storageState captures cookies + localStorage + sessionStorage as a single JSON blob. This is the preferred authentication method.

**Check:**
```
manage_session(action="check", domain="linkedin.com")
```

Returns `{fresh: true/false, age_days: N}`. Fresh = file exists and is less than 7 days old.

**Load:**
```
manage_session(action="load", domain="linkedin.com")
```

Returns the full storageState JSON. Pass it to Playwright via `browser.new_context(storage_state=state_json)`.

**File locations:**
- StorageState directory: `/opt/agents/data/sessions/`
- Per-domain files: `/opt/agents/data/sessions/{domain}.json`
- Example: `/opt/agents/data/sessions/linkedin.com.json`

**When storageState works:** Site uses session cookies or tokens stored in localStorage. Most modern web apps.

**When storageState fails:** Session expired (> 7 days), site invalidated the session server-side, site uses IP-bound sessions.

### Step 2: Cookie Files

Netscape-format cookie files exported from a real browser. These are injected into Playwright via `context.add_cookies()`.

**Check freshness:**
```
cookie_status()
```

Returns list of all available cookie files with age and domain.

**File locations:**
- Cookie directory: `/opt/agents/cookies/`
- Per-domain files: `/opt/agents/cookies/{domain}.txt`
- Example: `/opt/agents/cookies/youtube.com.txt`

**Cookie file format (Netscape/Mozilla):**
```
# Netscape HTTP Cookie File
.linkedin.com	TRUE	/	TRUE	1735689600	li_at	AQEDARsU...
.linkedin.com	TRUE	/	FALSE	0	JSESSIONID	"ajax:123..."
```

Fields (tab-separated): domain, include_subdomains, path, secure, expiry, name, value.

**Freshness threshold:** 7 days. Cookies older than 7 days are likely expired.

**When cookies work:** Simpler sites that only check session cookies. YouTube (with yt-dlp). Sites without CSRF token validation.

**When cookies fail:** Sites that validate session integrity beyond just cookies (LinkedIn, most modern SPAs). Use storageState instead.

### Step 3: Fresh Cookie Sync from Mac

If Step 2 files are stale (> 7 days old):

1. Note the staleness in your response.
2. The cookie sync cron runs daily at 06:00 from Aakash's Mac.
3. Manual sync: Aakash exports from Safari and rsyncs to droplet.

**You cannot trigger this yourself.** State clearly: "Cookies for {domain} are {N} days old and likely expired. Fresh cookies need to be synced from Mac."

**Cookie export command (for reference -- runs on Mac):**
```bash
yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt --skip-download "https://youtube.com/watch?v=dQw4w9WgXcQ"
rsync /tmp/cookies.txt root@aicos-droplet:/opt/agents/cookies/youtube.com.txt
```

### Step 4: Browserbase Isolated Session

For sites that aggressively block headless browsers (advanced fingerprinting, Cloudflare JS challenges):

- Uses Browserbase cloud browser with residential IP.
- Expensive -- only use when Steps 1-3 all fail.
- Requires `BROWSERBASE_API_KEY` environment variable.
- Not always available -- check environment first.

### Step 5: Escalate to Human

**Hard stop. Never proceed past this step automatically.**

When authentication requires any of:
- Two-factor authentication (2FA / MFA)
- CAPTCHA solving
- SMS verification
- Email verification links
- Manual OAuth consent screens

Return a detailed escalation message:
```json
{
  "status": "auth_required",
  "domain": "example.com",
  "steps_tried": ["storageState (expired)", "cookies (not found)", "..."],
  "escalation": "Human action needed: Log in to example.com in Safari, then run cookie sync to update storageState.",
  "what_to_do": "1. Open Safari, go to example.com. 2. Log in. 3. Run: scripts/cookie-sync.sh example.com"
}
```

---

## Post-Authentication: Always Save State

After ANY successful authenticated session (Steps 1 or 2), save the resulting state for future reuse:

```
manage_session(action="save", domain="linkedin.com", state_json=<playwright_state>)
```

This writes to `/opt/agents/data/sessions/linkedin.com.json` and makes Step 1 available for next time.

---

## Domain-Specific Notes

### YouTube
- Uses cookie files (Step 2), not storageState.
- Cookies passed via `--cookies` flag to yt-dlp.
- Datacenter IPs are blocked without cookies.
- Cookies expire every 1-2 weeks.
- Cookie path: `/opt/agents/cookies/youtube.com.txt` (or `YOUTUBE_COOKIES_PATH` env var).

### LinkedIn
- Requires storageState (Step 1) -- cookies alone are insufficient.
- Session cookies alone get blocked; localStorage tokens are needed.
- Aggressively detects headless browsers.
- Use `mac_us` persona (matches the Mac where state was saved).

### Twitter/X
- Can often be scraped via Jina without auth (public profiles/tweets).
- Auth required for: protected accounts, full thread views, search.
- storageState works when available.

---

## Decision Flowchart

```
Does the site require auth?
  |
  No → Use normal scrape/browse
  |
  Yes
  |
  manage_session(action="check", domain)
  |
  Fresh? → Yes → Load storageState → Browse → Validate → Save state → Done
  |
  No
  |
  cookie_status() for domain
  |
  Cookie exists and < 7 days? → Yes → Inject cookies → Browse → Validate → Save storageState → Done
  |
  No
  |
  Cookie exists but stale? → Note in response → Try anyway → If works, save state → Done
  |
  No cookie at all?
  |
  Can we proceed without auth? → Yes → Try scrape/browse without auth → Validate
  |
  No → Escalate to human (Step 5)
```
