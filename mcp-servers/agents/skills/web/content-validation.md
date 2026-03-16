# Content Validation Skill

Instructions for validating extracted web content quality. Always validate before returning content to the caller.

---

## Validation Protocol

Call `validate(content, url, expected_type?)` on every piece of extracted content before returning it. This is mandatory -- never skip validation.

---

## Quality Score (0-100)

The validator scores content on a 0-100 scale. Deductions are cumulative.

### Scoring Criteria

| Check | Deduction | Condition |
|-------|-----------|-----------|
| **Empty content** | -100 (instant fail) | No content or only whitespace |
| **Very short** | -60 | Fewer than 10 words |
| **Short** | -30 | Fewer than 50 words |
| **Login wall** | -50 | 2+ login signals AND < 200 words |
| **Cookie consent overlay** | -40 | 2+ consent signals AND < 100 words |
| **Error page** | -30 | Error signals present AND < 100 words |
| **No structure** | -10 | No line breaks AND > 100 words |

### Score Thresholds and Actions

| Score | Verdict | Action |
|-------|---------|--------|
| **>= 70** | `good` | Return the content immediately. Quality is acceptable. |
| **40-69** | `acceptable` | Content is marginal. Retry with a different method if time permits. Note the quality issues in your response. |
| **< 40** | `poor` | **Must retry.** Do not return this content without trying an alternative extraction method first. |

---

## Detection Patterns

### Login Wall Signals

The validator checks for these keywords in the extracted text (case-insensitive):

- "sign in"
- "log in"
- "create account"
- "forgot password"
- "enter your email"
- "enter your password"

**Trigger rule:** 2 or more login signals present AND total word count < 200.

This means you extracted the login page, not the actual content. Escalate to the auth ladder (load auth-escalation skill).

### Cookie/Consent Overlay Signals

- "accept cookies"
- "cookie policy"
- "we use cookies"
- "privacy preferences"
- "consent"

**Trigger rule:** 2 or more consent signals AND total word count < 100.

This means the cookie banner is covering the main content. Fix by:
1. Use `interact` to click the accept/dismiss button (common selectors: `[data-testid="cookie-banner-close"]`, `.cookie-accept`, `#accept-cookies`).
2. Re-extract content after dismissing.

### Error Page Signals

- "404"
- "page not found"
- "error occurred"
- "access denied"
- "403 forbidden"

**Trigger rule:** Any error signal present AND total word count < 100.

This means you hit an error page. Check:
- URL is correct (no typos, no URL encoding issues)
- Page actually exists (try searching for it)
- Access permissions (may need auth)

---

## Retry Strategy on Low Quality

When content scores < 40 (poor), follow this escalation:

### Attempt 1: Different extraction method
```
Failed with scrape (Jina) → Try scrape (Firecrawl)
Failed with scrape (Firecrawl) → Try browse (Playwright, auto readiness)
Failed with browse → Try browse with different readiness mode
```

### Attempt 2: Dismiss overlays, then re-extract
```
browse(url) → interact(url, action="click", selector="cookie-dismiss-button") → re-scrape
```

### Attempt 3: Return with quality warning
If all methods fail, return what you have with clear documentation:

```json
{
  "content": "<best content obtained>",
  "quality_score": 35,
  "quality_verdict": "poor",
  "quality_issues": ["Likely login wall (3 login signals)", "Short: 47 words"],
  "methods_tried": [
    {"method": "jina", "score": 35, "issue": "login wall"},
    {"method": "firecrawl", "score": 28, "issue": "empty content"},
    {"method": "browse", "score": 35, "issue": "login wall"}
  ],
  "recommendation": "Auth required. Load auth-escalation skill."
}
```

**Never return empty content without trying at least 2 methods.**

---

## Structural Quality

Beyond the automated scoring, assess these manually:

- **Markdown quality:** Does the extracted content have reasonable headings, paragraphs, lists?
- **Content completeness:** Does it seem like the full article or a truncated snippet?
- **Relevance:** Is this actually the page you intended to extract? (Check title, URL, content topic)
- **Encoding:** Are there encoding artifacts (mojibake, HTML entities like `&amp;`)?

If you notice structural issues the automated scorer misses, note them in your response.

---

## Content Length Caps

Extracted content is capped at:
- Jina Reader: 50,000 characters
- Firecrawl: 50,000 characters
- Playwright browse: 30,000 characters (body.innerText)

If the original content is longer, the cap applies. For very long pages, consider extracting specific sections rather than the full page.
