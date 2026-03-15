# Making AI Browser Agents Self-Adapting

**Source run:** `trun_...a2f508c1d97ad560`
**Date:** 2026-03-15

## Key Concepts

- **Wappalyzer 0.47ms detection** — Run Wappalyzer's detection logic in-browser to identify the site's tech stack (React, Angular, WordPress, Cloudflare, etc.) in under 0.5ms. The detected stack drives strategy selection.
- **Fingerprint-to-strategy Redis cache** — Hash the site fingerprint (domain + tech stack + layout features) and cache the winning extraction strategy in Redis. On revisit, skip exploration and use the known-good approach.
- **UCB bandit for strategy selection** — Upper Confidence Bound algorithm balances exploration (trying new strategies) vs exploitation (using known-good ones). Each strategy's success rate updates after every extraction attempt.
- **5-step retry ladder** — Graduated retry strategy: (1) retry same method, (2) switch selector engine, (3) add wait/scroll, (4) fall back to accessibility tree, (5) fall back to vision model. Each step is more expensive but more robust.
- **Content quality scoring** — Score extracted content on completeness (expected fields present), freshness (timestamps reasonable), and coherence (no truncation, encoding correct). Scores below threshold trigger the retry ladder.
- **MCP Strategy Registry** — An MCP server that stores and serves extraction strategies per domain. Agents query it before extraction and report results back, creating a shared learning loop across agent instances.
- **Context pooling (1 browser, many contexts)** — Launch one Chromium instance with multiple `BrowserContext` objects. Each context has isolated cookies/storage but shares the browser process. 10x memory savings vs separate browsers.
- **page.addLocatorHandler() overlay dismissal** — Register handlers that automatically dismiss cookie banners, login modals, and newsletter popups when they appear. Runs before each action, preventing overlay-blocked interactions.
- **S3 signed bundles for edge sync** — Package strategy updates as signed bundles uploaded to S3. Edge agents poll for new bundles, verify signatures, and hot-reload strategies without restarting.

## Top 5 References

1. Wappalyzer technology detection — `github.com/wappalyzer/wappalyzer`
2. Multi-armed bandit algorithms (UCB) — `banditalgs.com/2016/09/18/the-upper-confidence-bound-algorithm`
3. Playwright BrowserContext isolation — `playwright.dev/docs/browser-contexts`
4. Playwright locator handlers — `playwright.dev/docs/api/class-page#page-add-locator-handler`
5. MCP specification (tool registration) — `spec.modelcontextprotocol.io/specification/server/tools`
