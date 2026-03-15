# Stealth-by-Design: Passing 2026 Bot Defenses

**Source run:** `trun_...92e5e3af722acd83`
**Date:** 2026-03-15

## Key Concepts

- **Chrome 112+ unified headless** — Chrome 112 merged `--headless=new` with the full browser engine. Old headless had detectable differences (missing codecs, missing PDF printer). New headless is indistinguishable from headed Chrome.
- **CDP side-effect detection (Runtime.enable)** — Anti-bot scripts detect Chrome DevTools Protocol usage by checking side effects of commands like `Runtime.enable` (adds `__proto__` changes). Minimize CDP calls; prefer Playwright's higher-level API which batches them.
- **JA4 TLS fingerprinting** — Successor to JA3. Fingerprints the TLS ClientHello (cipher suites, extensions, ALPN). Headless Chrome's TLS fingerprint must match real Chrome exactly. Mismatches trigger Cloudflare/Akamai blocks.
- **Stable personas > randomization** — Anti-detection systems flag entropy. A consistent persona (same viewport, timezone, language, fonts) across sessions scores lower on bot probability than randomized values each request.
- **Browserbase stealth mode** — Managed browser service that handles fingerprinting, proxy rotation, and CAPTCHA solving. Abstracts stealth complexity into an API call. Trade-off: cost per session vs DIY maintenance.
- **storageState() persistence** — Playwright's `storageState()` serializes cookies + localStorage to JSON. Restore on next session to maintain login state, avoiding repeated authentication flows that trigger security alerts.
- **Coherent geo-IP / timezone / locale** — The IP's geolocation, the browser's `Intl.DateTimeFormat().resolvedOptions().timeZone`, and `navigator.language` must all agree. A US IP with Asia/Tokyo timezone is an instant bot signal.
- **bot.sannysoft.com + CreepJS verification** — Two test suites for validating stealth. bot.sannysoft.com checks basic fingerprint leaks. CreepJS performs deep analysis (canvas, WebGL, audio context fingerprinting). Run both before deploying a new stealth configuration.
- **Cloudflare / Akamai / DataDome bypass strategies** — Cloudflare: solve Turnstile with managed challenges + residential proxies. Akamai: match sensor data timing patterns. DataDome: requires full browser rendering + human-like mouse movement injection.

## Top 5 References

1. Chrome headless detection tests — `bot.sannysoft.com`
2. CreepJS fingerprint analysis — `github.com/nicedayfor/AreYouACreep`
3. JA4 TLS fingerprinting — `github.com/FoxIO-LLC/ja4`
4. Playwright stealth (community) — `github.com/nicedayfor/puppeteer-extra-plugin-stealth`
5. Browserbase managed browsers — `browserbase.com/docs`
