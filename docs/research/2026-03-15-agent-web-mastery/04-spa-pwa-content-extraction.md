# From Flaky to Fail-Safe: SPA/PWA Content Extraction

**Source run:** `trun_...a26d6a581881fe0d`
**Date:** 2026-03-15

## Key Concepts

- **MutationObserver quiet window** — Monitor DOM mutations; declare the page "loaded" after N milliseconds of no mutations. More reliable than `networkidle` for SPAs that fetch data incrementally.
- **PerformanceObserver LCP** — Listen for Largest Contentful Paint events via `PerformanceObserver`. LCP firing signals the main content is rendered, regardless of background network activity.
- **serviceWorkers: 'block'** — Playwright context option that blocks service worker registration. Prevents PWAs from serving cached/stale content, ensuring fresh extraction every run.
- **page.accessibility.snapshot()** — Returns the accessibility tree as structured JSON. Captures semantic content (headings, links, text) without parsing raw HTML. Works through Shadow DOM and iframes.
- **Shadow DOM piercing** — Use `page.locator('css:light=...')` or `element.shadowRoot` to reach into Shadow DOM. Standard CSS selectors stop at shadow boundaries; piercing selectors cross them.
- **Virtual scroll extraction** — Virtualized lists (React Virtualized, AG Grid) only render visible rows. Extract by programmatically scrolling, collecting rows at each position, and deduplicating by key.
- **Stagehand v3 raw CDP 44% faster** — Stagehand v3's direct Chrome DevTools Protocol path skips Playwright's abstraction layer. 44% faster for bulk extraction tasks at the cost of portability.
- **Skyvern vision 85.85% WebVoyager** — Skyvern uses vision models to interact with web pages without selectors. Scored 85.85% on the WebVoyager benchmark. Best for pages with unpredictable/dynamic layouts.
- **Framework hydration markers** — Detect when SPAs finish hydrating: React checks `__REACT_DEVTOOLS_GLOBAL_HOOK__` or Suspense boundaries resolving; Next.js checks `__NEXT_DATA__` presence; Svelte checks `onMount` completion via custom injection.

## Top 5 References

1. Playwright API: accessibility snapshot — `playwright.dev/docs/api/class-page#page-accessibility`
2. Web Performance: Largest Contentful Paint — `web.dev/articles/lcp`
3. Stagehand browser automation — `github.com/browserbase/stagehand`
4. Skyvern visual web agent — `github.com/Skyvern-AI/skyvern`
5. MutationObserver API — `developer.mozilla.org/en-US/docs/Web/API/MutationObserver`
