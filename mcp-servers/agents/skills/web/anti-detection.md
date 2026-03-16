# Anti-Detection Skill

Instructions for avoiding bot detection when browsing. The core principle: **coherence beats randomization**. A stable, consistent persona is harder to detect than random fingerprint rotation.

---

## Principle: Fingerprint Coherence

Detection systems look for inconsistency, not specific values. A Linux user-agent with a macOS screen resolution and a Tokyo timezone is an obvious bot. A consistent Linux/US persona is invisible.

**What triggers detection:**
- User-agent says Windows but viewport is 1440x900 (Mac resolution)
- Timezone says America/New_York but locale is ja-JP
- Chrome 146 user-agent but missing Chrome-specific JS APIs
- Rotating user-agents between requests in the same session
- No mouse movement or scroll events
- Request timing that is perfectly uniform (e.g., exactly 1000ms between requests)

**What avoids detection:**
- Consistent persona across all signals (UA, viewport, timezone, locale)
- Human-like timing variation (not uniform delays)
- Realistic viewport sizes for the claimed OS
- Stable session identity (same persona for entire task)

---

## Persona Profiles

Use ONE persona per task. Never mix. Default is `linux_us` (matches droplet environment).

### linux_us (DEFAULT -- matches droplet)
```
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
Viewport:   1920 x 1080
Locale:     en-US
Timezone:   America/New_York
```

### mac_us
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
Viewport:   1440 x 900
Locale:     en-US
Timezone:   America/Los_Angeles
```

### win_us
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
Viewport:   1920 x 1080
Locale:     en-US
Timezone:   America/Chicago
```

### When to switch personas

- **Default to `linux_us`** -- it matches the droplet's actual environment, maximizing coherence.
- **Switch to `mac_us`** if using storageState saved from Aakash's Mac (the cookies were set in a Mac browser context).
- **Switch to `win_us`** only for sites known to block Linux user agents (rare).

---

## Browser Launch Configuration

Chrome is launched with these anti-detection args:

```
--no-sandbox
--disable-gpu
--disable-blink-features=AutomationControlled
```

`AutomationControlled` is the key one -- it removes the `navigator.webdriver` flag that headless detection scripts check.

---

## Timing Patterns

### Between pages (navigation delays)
- Add 1-3 seconds of random delay between page navigations.
- Never navigate faster than a human could click.
- For multi-page scraping, vary delays: 1.2s, 2.7s, 1.8s -- not 2s, 2s, 2s.

### Within a page (interaction delays)
- Between typing characters: 50-150ms random (human typing speed).
- Between click and next action: 500-1500ms.
- Before submitting a form after filling it: 1-3 seconds.

### Rate limiting
- Maximum 10 requests per minute per domain (enforced by rate_limit_check hook).
- If rate-limited by the target site, wait the full cooldown period before retrying.
- Space requests to the same domain by at least 2 seconds.

---

## Header Consistency

When using scrape (HTTP requests via Jina/Firecrawl), headers are handled by the proxy service. No manual header management needed.

When using browse (Playwright), the browser context automatically sets headers consistent with the persona. Do not override individual headers unless you have a specific reason -- partial overrides break coherence.

**Never do:**
- Set a custom `User-Agent` header while using Playwright (conflicts with context UA)
- Add `X-Requested-With: XMLHttpRequest` to non-AJAX requests
- Set `Referer` to a domain you haven't visited in this session

---

## Detection Recovery

If you suspect you've been detected (CAPTCHA page, 403, "unusual activity" message):

1. **Stop immediately** -- do not retry with the same method.
2. **Switch to a different extraction method** (e.g., Jina if browse was detected).
3. **Wait at least 60 seconds** before trying the same domain again.
4. **Try a different persona** if browse is required.
5. **Check cookie freshness** -- stale cookies can trigger re-authentication flows that look like detection.
6. **Escalate to human** if all methods fail (Step 5 of auth ladder).
