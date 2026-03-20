# UX Elevation Study: World-Class Intelligence Tool Design Direction

**Date:** 2026-03-20
**Purpose:** Design direction document for elevating digest.wiki toward Linear/Superhuman/Bloomberg-tier UI/UX
**Status:** Research complete, ready for implementation

---

## 1. Reference Analysis

### Linear — The Gold Standard for Dark Tool UI

**What makes it world-class:**
- **Color restraint.** Shifted from cool blue-ish palette to warmer, neutral grays. Uses LCH color space (perceptually uniform) to generate themes from only 3 variables: base color, accent color, contrast level.
- **Typography.** Inter Display for headings, Inter for body. Medium (500) weight for UI labels, not bold. Font hierarchy is clean and does not shout.
- **"Don't compete for attention you haven't earned."** Navigation elements are deliberately dimmed. The sidebar recedes; content takes center stage. Icons are smaller, colored backgrounds removed from icons.
- **"Structure should be felt, not seen."** Borders are softened, dividing lines reduced. Rounded borders at subtle contrast. You sense hierarchy without seeing heavy lines.
- **Dark background:** `#121212` (dark mode base). Surface: `#1b1c1d`. Accent: `#848CD0` (muted indigo). Text: `#cccccc`.
- **Spacing is tight but not cramped.** Tab bars compact, vertical padding deliberate. No wasted whitespace.

**Key takeaway for digest.wiki:** The current design uses too many saturated accent colors and too much visual decoration. Linear proves that restraint is premium.

### Superhuman — Perceptual Contrast Mastery

**What makes it world-class:**
- **Five shades of gray.** Carbon dark mode uses exactly 5 gray levels: nearer surfaces lighter, distant surfaces darker. This mimics light cast from above.
- **Perceptual contrast, not mathematical.** Each element is adjusted individually considering text size, font weight, and line width. They use white at 65% opacity (not 60%) in dark mode to compensate for the perceptual deficit of light-on-dark.
- **Distraction-free composition.** When composing, the entire UI fades away. Nothing competes with the primary task.
- **Strategic color reduction.** Large blocks of bright color that work in light themes are problematic in dark themes. Superhuman reduces them to small, intentional accents.
- **Custom typography** (Operator Mono Book). Monospace as a design choice, not just for code.

**Key takeaway for digest.wiki:** The current `rgba(255,87,34,0.12)` backgrounds are too many and too frequent. Accent color backgrounds should be rare events, not the default state of every badge.

### Bloomberg Terminal — Maximum Density, Zero Waste

**What makes it world-class:**
- **Custom typeface** by Matthew Carter. Slightly condensed proportions, clear numerals, tabular alignment for columns of figures. Optimized for dense numerical data.
- **Black + amber identity.** Amber as base text color on black. Non-semantic information stays amber. Semantic colors (up/down) use blue/red for accessibility.
- **Tabbed panel model.** Replaced the 4-panel maximum with unlimited tabs. Users resize windows to see more/fewer rows.
- **Every pixel earns its place.** No decorative elements. No rounded corners. No shadows. Just data.
- **Information density is the feature.** Financial professionals need to see 200+ data points simultaneously. The UI serves this need, not aesthetic preferences.

**Key takeaway for digest.wiki:** The current cards use `p-5` (20px padding) with `rounded-xl` (12px radius). Bloomberg shows that for a data tool, these can be tighter: 12-16px padding, 6-8px radius. The current layout fits ~3 action cards in a viewport; it should fit 5-6.

### Arc Browser — Spatial Color as Context

**What makes it world-class:**
- **Spaces with color themes.** Each workspace has its own color, making context-switching visual and instant. Color serves function, not decoration.
- **Color variables.** background, foregroundPrimary/Secondary/Tertiary, hover, focus, contrast. A complete semantic layer.
- **Clean minimalism.** The sidebar and tab management are spatially organized, not list-based.

**Key takeaway for digest.wiki:** The current 5-color accent system (flame/amber/cyan/violet/green) is used decoratively. Arc shows color should encode meaning consistently: one color per entity type, used everywhere that entity appears.

### Raycast — Command Palette as Primary Interface

**What makes it world-class:**
- **Dynamic color.** Colors adapt to maintain high contrast regardless of theme.
- **Speed above all.** Fuzzy matching, 150ms response, keyboard-first.
- **Minimal chrome.** Input + results list. No decorative elements in the palette itself.

**Key takeaway for digest.wiki:** The command palette is well-structured but could be tighter. The footer hints area and group filter tabs add chrome that Raycast avoids.

### Notion — Typographic Clarity

**What makes it world-class:**
- **Inter as the sole typeface** across the entire interface. Consistency creates calm.
- **8px grid system.** All spacing is multiples of 8. This creates subconscious alignment.
- **Three font options** (Default/Serif/Mono) for content, but the chrome never changes.
- **16px body, large x-height.** Optimized for extended reading sessions.

**Key takeaway for digest.wiki:** Three font families (Instrument Serif + JetBrains Mono + DM Sans) is one too many for a tool UI. The serif headlines add editorial flair but reduce the tool-like density that Bloomberg/Linear achieve.

### Figma — Professional Dark Theme

**What makes it world-class:**
- **Desaturated fill colors** communicate hierarchy instead of reversing light values.
- **Material Design standard:** `#121212` as darkest base. Lighter variants maintain expressiveness without eye strain.
- **Saturated colors "vibrate" on dark backgrounds.** Figma desaturates all accent colors for dark mode.

**Key takeaway for digest.wiki:** The current accent colors (`#ff5722`, `#ffab00`, `#00e5ff`, `#b388ff`, `#69f0ae`) are at full saturation. They vibrate against `#08080c`. Every one needs to be desaturated 20-30% for the dark context.

---

## 2. Current Gaps

### Gap 1: Accent Color Overload
- **Problem:** 5 fully saturated accent colors used liberally across badges, borders, backgrounds, text, dots, bars.
- **Reference standard:** Linear uses 1 accent (muted indigo) + 2 semantic colors (green/red). Superhuman uses 1 primary blue + minimal semantic color.
- **Impact:** The eye has no resting point. Everything demands attention. Nothing is actually prioritized.

### Gap 2: Card Padding is Marketing-Site Level
- **Problem:** Cards use `p-5` (20px) with `rounded-xl` (12px). This is landing-page density.
- **Reference standard:** Linear uses ~12px internal padding, 6-8px radius. Bloomberg uses 0 decorative spacing.
- **Impact:** Only 3 action cards visible per viewport. A fund manager scanning 20+ actions needs to see 6-8 at a glance.

### Gap 3: Three Font Families Create Visual Noise
- **Problem:** Instrument Serif (headlines), JetBrains Mono (data/badges), DM Sans (body). Each has different x-height, weight, and rhythm.
- **Reference standard:** Linear uses Inter + Inter Display. Notion uses Inter only. The monospace is reserved for actual data values.
- **Impact:** Every visual boundary between font families is a micro-interruption. In a dense tool, these add up to cognitive fatigue.

### Gap 4: Secondary/Tertiary Text is Too Close Together
- **Problem:** `--color-t2: #908e9b` and `--color-t3: #8a8894` are almost indistinguishable (difference of ~6 in lightness).
- **Reference standard:** Successful tools use 3 distinct tiers with clear perceptual gaps. ~20 lightness points between tiers minimum.
- **Impact:** The hierarchy of "title > description > metadata" is blurred. Metadata and descriptions look the same.

### Gap 5: Background Levels Lack Separation
- **Problem:** `--color-bg: #08080c`, `--color-card: #0f0f16`, `--color-elevated: #16161f`. The jump from bg to card is only +7 lightness, and all have a blue tint.
- **Reference standard:** Linear uses `#121212` (neutral) to `#1b1c1d` (neutral). The neutrality is key: colored backgrounds fight with accent colors.
- **Impact:** Cards don't "float" off the background. The blue tint in all three levels creates a monochromatic wash.

### Gap 6: Atmospheric Gradients Are Decorative, Not Functional
- **Problem:** `.bg-intelligence`, `.bg-hero-thesis`, etc. add colored radial gradients to page backgrounds.
- **Reference standard:** None of the reference products use atmospheric background gradients. Linear, Superhuman, and Figma use flat, neutral backgrounds.
- **Impact:** These gradients scream "marketing site." They add visual noise without information value.

### Gap 7: Micro-Typography is Under-Specified
- **Problem:** No consistent letter-spacing scale. `tracking-[1px]`, `tracking-[1.5px]`, `tracking-[2px]`, `tracking-[0.5px]` used ad hoc.
- **Reference standard:** Design systems define 2-3 tracking values and apply them by role (label, body, caption).
- **Impact:** Inconsistent tracking creates subtle unevenness that the eye registers as "not polished."

### Gap 8: Font Sizes are Too Varied
- **Problem:** Font sizes in use: 9px, 10px, 11px, 12px, 13px, 14px, 15px, 16px, + clamp headlines. That's 8+ body-range sizes.
- **Reference standard:** Professional tools use 4-5 sizes maximum. Linear: 12, 14, 16, 22, 65. Bloomberg: basically 2 (data size + header size).
- **Impact:** Too many sizes means no clear hierarchy. The difference between 13px and 14px is imperceptible.

### Gap 9: Scrollbar and Glass-morphism are Dated
- **Problem:** Flame-colored scrollbar thumb. Glass-morphism with `backdrop-filter: blur(16px) saturate(1.2)` on nav.
- **Reference standard:** Linear and Superhuman use invisible or near-invisible scrollbars. No glass-morphism — solid, slightly transparent surfaces.
- **Impact:** Colored scrollbars and glass effects were trendy in 2022. In 2026, they read as "trying too hard."

### Gap 10: Timeline Rainbow is Anti-Pattern
- **Problem:** `.timeline-line::before` uses a 5-color gradient (flame > amber > cyan > violet > green).
- **Reference standard:** No reference product uses rainbow gradients in structural elements.
- **Impact:** Rainbow structural elements are the visual equivalent of comic sans in a financial document.

---

## 3. Color System Upgrade

### Design Principles
1. **Neutral backgrounds.** Remove all blue/purple tint from surface colors.
2. **Desaturated accents.** Every accent color drops 20-30% saturation for dark mode.
3. **Two functional accents maximum** in any single view. Others are dormant (used as text color only, never as backgrounds).
4. **Semantic color is sacred.** Green = positive/confirmed. Red/flame = negative/urgent. Amber = warning/pending. These never serve decorative purposes.

### Background Levels (4 tiers)

| Level | Role | Hex | oklch | WCAG Notes |
|-------|------|-----|-------|------------|
| **Base** | Page background, deepest layer | `#0c0c0e` | `oklch(0.08 0.005 270)` | Neutral, near-black. No blue tint. |
| **Surface** | Cards, panels, sidebar | `#141416` | `oklch(0.12 0.005 270)` | +4 lightness from base. Clear lift. |
| **Elevated** | Popovers, dropdowns, command palette | `#1c1c1f` | `oklch(0.16 0.005 270)` | +4 lightness from surface. Unmistakable float. |
| **Overlay** | Modals, sheets, dialogs | `#222225` | `oklch(0.19 0.005 270)` | +3 lightness from elevated. Maximum emphasis. |

### Text Levels (3 tiers)

| Level | Role | Hex | oklch | Contrast vs Base | Contrast vs Surface |
|-------|------|-----|-------|-----------------|-------------------|
| **Primary** | Titles, important values | `#e8e8ec` | `oklch(0.93 0.005 270)` | 15.2:1 | 12.8:1 |
| **Secondary** | Body text, descriptions | `#9b9ba4` | `oklch(0.67 0.008 270)` | 6.8:1 | 5.7:1 |
| **Tertiary** | Metadata, timestamps, hints | `#5c5c66` | `oklch(0.43 0.008 270)` | 3.4:1 | 2.8:1 |

### Accent Colors (Desaturated for dark mode)

| Name | Current Hex | New Hex | oklch | Usage Rule |
|------|-------------|---------|-------|------------|
| **Flame** (primary) | `#ff5722` | `#e8613a` | `oklch(0.65 0.18 30)` | Primary CTA, urgent items, P0 badges. The ONE accent that appears as backgrounds. |
| **Amber** (warning) | `#ffab00` | `#d4a033` | `oklch(0.73 0.14 80)` | Pending items, P1, warning states. Text color only; bg only for active states. |
| **Cyan** (info) | `#00e5ff` | `#4db8c9` | `oklch(0.73 0.10 200)` | Informational, P2, data links. Dramatically desaturated from current. |
| **Violet** (thesis) | `#b388ff` | `#9b8abf` | `oklch(0.65 0.10 290)` | Thesis connections. Text color only; never as a border or background fill. |
| **Green** (positive) | `#69f0ae` | `#5cc98f` | `oklch(0.77 0.12 160)` | Accepted, positive, confirmed. Semantic only. |

### Accent Background Rule

Accent-colored backgrounds (`rgba(color, 0.08-0.12)`) are reserved for exactly these cases:
1. **Active navigation item** (one at a time)
2. **Actionable badge that requires triage** (Proposed status only)
3. **Command palette active selection**

Everything else uses neutral backgrounds with accent-colored text.

### Border Color

| Role | Value |
|------|-------|
| **Subtle** (cards, separators) | `rgba(255, 255, 255, 0.06)` |
| **Medium** (active states, hover) | `rgba(255, 255, 255, 0.10)` |
| **Emphasis** (focus rings, selected) | `rgba(255, 255, 255, 0.16)` |

---

## 4. Typography Refinement

### Font Stack

**Remove Instrument Serif entirely.** Headlines should use the same sans-serif as body, differentiated by size and weight only. This is how Linear, Figma, Notion, and Superhuman work.

| Role | Font | Weight | Why |
|------|------|--------|-----|
| **Headlines** | Geist / Inter | 600 (Semibold) | Modern, optimized for screens. Geist is slightly rounder, more modern than Inter. |
| **Body** | Geist / Inter | 400 (Regular) | Consistent with headlines. No font-change friction. |
| **Data/Labels** | Geist Mono / JetBrains Mono | 500 (Medium) | Monospace reserved strictly for: numerical values, timestamps, status codes, keyboard shortcuts. |

**Recommendation:** Use **Geist** (Vercel's own font, already available in Next.js) as primary, with Geist Mono for data. This gives better visual coherence than mixing DM Sans + JetBrains Mono, and it's optimized for the exact rendering context (Vercel/Next.js). If Geist feels too neutral, Inter Display + Inter is the Linear-proven alternative.

### Size Scale (Strict — no ad hoc values)

| Token | Size | Line Height | Letter Spacing | Usage |
|-------|------|-------------|----------------|-------|
| `--text-xs` | 11px | 16px (1.45) | 0.01em | Timestamps, footnotes, badge counts |
| `--text-sm` | 13px | 18px (1.38) | 0 | Card body, descriptions, secondary info |
| `--text-base` | 14px | 20px (1.43) | 0 | Default body text, list items |
| `--text-md` | 16px | 22px (1.38) | -0.01em | Card titles, section labels |
| `--text-lg` | 20px | 26px (1.30) | -0.015em | Page section headers |
| `--text-xl` | 24px | 30px (1.25) | -0.02em | Page titles |
| `--text-display` | 32px | 36px (1.13) | -0.025em | Hero/command center title (one per page max) |

**Rules:**
- Headlines and page titles: no `clamp()`. Use `--text-xl` or `--text-display` at fixed sizes. The responsive scaling via clamp creates font-size values that don't match any token.
- `text-[15px]` does not exist in this scale. Round to 14 or 16.
- `text-[9px]` does not exist. The minimum is 11px. Anything below 11px is illegible on mobile.

### Label Style (for "ALL CAPS" metadata labels)

```css
.label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-t3);
}
```

This replaces the current inconsistent `tracking-[1px]`, `tracking-[1.5px]`, `tracking-[2px]` ad hoc values.

### Weight Usage

| Weight | Token | Usage |
|--------|-------|-------|
| 400 | `regular` | Body text, descriptions |
| 500 | `medium` | Navigation labels, card titles, data values in mono |
| 600 | `semibold` | Page titles, section headers, emphasis |

**Remove 700 (bold) from the system.** In dark mode, bold text at small sizes creates visual weight that is too heavy. Use 600 as the maximum. The current `font-bold` on badge counts and priority labels should become `font-medium`.

---

## 5. Spacing System

### Base Unit: 4px

All spacing derives from multiples of 4. No arbitrary pixel values.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | — |
| `--space-1` | 4px | Inline gaps (icon to text), badge internal padding-y |
| `--space-2` | 8px | Between related elements, badge padding-x, tight card sections |
| `--space-3` | 12px | Card internal padding, between card sections |
| `--space-4` | 16px | Between cards in a list, sidebar item padding |
| `--space-5` | 20px | Section separation within a page |
| `--space-6` | 24px | Major section gaps |
| `--space-8` | 32px | Page top/bottom padding |
| `--space-10` | 40px | Page margin (desktop) |

### Card Padding (Tighter)

| Current | Proposed | Reduction |
|---------|----------|-----------|
| `p-5` (20px) | `p-3` (12px) | -40% |
| `rounded-xl` (12px) | `rounded-lg` (8px) | -33% |
| `gap-3` (12px) between card sections | `gap-2` (8px) | -33% |
| `mb-2` / `mb-3` between card rows | `mb-1.5` (6px) | ~-40% |

### Page Layout

| Zone | Current | Proposed |
|------|---------|----------|
| Page horizontal padding (mobile) | `px-5` (20px) | `px-4` (16px) |
| Page horizontal padding (desktop) | `sm:px-10` (40px) | `sm:px-6` (24px) |
| Max content width | `max-w-[720px]` or `max-w-[900px]` | `max-w-[960px]` |
| Page top padding | `pt-20` (80px) | `pt-14` (56px) |

### Section Gaps

| Current | Proposed |
|---------|----------|
| `mb-8` (32px) between page header and content | `mb-5` (20px) |
| `mb-6` between sections | `mb-4` (16px) |
| `gap-6` grid gap | `gap-3` (12px) |

---

## 6. Density Patterns

### Compact Card Layout

The current ActionCard at ~180px tall should compress to ~110px:

```
+--[P0]--[RESEARCH]--[Proposed]-----+
| Title of the action goes here      |
| Reasoning preview text truncat...  |
| thesis-tag  @assigned  Score: 7.2  |
| 3h ago               View Details →|
| [Accept] [Dismiss]                 |
+------------------------------------+
```

Specific changes:
- Remove the outer `flex items-start gap-3` wrapper (the checkbox column wastes horizontal space when not in select mode)
- Combine the "Tags row" and "Date row" into one row
- Reduce badge sizes: `text-[10px]` badges become `text-[11px]` (our new minimum) with `px-1.5 py-0.5` becoming `px-1 py-px`
- Action buttons (`Accept`/`Dismiss`) use `min-h-[36px]` not `min-h-[44px]` (touch targets: keep 44px on mobile via a wrapper, but visual height can be 36px)

### Dense Table/List Pattern

For pages like Portfolio and Companies, offer a **list view** (default on desktop) alongside card view:

```
Company          Sector       Health  Today    Actions
───────────────────────────────────────────────────
Acme Corp        Fintech      ● Green Active   3 pending
Beta Inc         SaaS         ● Amber Review   1 pending
...
```

- Row height: 36px (desktop), 44px (mobile)
- Font: monospace for data columns, sans for name
- Alternating row backgrounds: `transparent` / `rgba(255,255,255,0.02)`
- No row borders; the background alternation creates the grid

### Multi-Column at Wider Breakpoints

| Breakpoint | Columns | Grid Gap |
|------------|---------|----------|
| < 640px | 1 column | 8px |
| 640-1024px | 2 columns | 12px |
| > 1024px | 3 columns | 12px |

The current `lg:grid-cols-12` with `lg:col-span-7` / `lg:col-span-5` is good for the home page dashboard layout, but individual entity pages (Actions, Thesis) should use the simpler breakpoint system above.

### Sidebar Information Density

Current sidebar is well-structured. Refinements:
- Reduce sidebar width from 220px to 200px (expanded)
- Collapsed width: 52px (from 64px)
- Nav item height: 36px (from 44px on desktop; keep 44px on mobile bottom nav)
- Section text: use `--text-xs` (11px) not `text-[13px]` for labels

---

## 7. Micro-Interactions

### Hover States

| Element | Current | Proposed |
|---------|---------|----------|
| Card | `border-color: rgba(255,255,255,0.1)` + lifted shadow | `background: rgba(255,255,255,0.02)` only. No border change, no shadow change. |
| Navigation item | Flame-colored background | `background: rgba(255,255,255,0.04)`. Active state only gets accent color. |
| Button | Various per-button | `opacity: 0.85` for all secondary buttons. Primary buttons: `filter: brightness(1.1)` |
| Link | Default browser | `color` shifts from t3 to t2 (subtle lightening). No underline change. |

**Principle:** Hover should whisper, not shout. The user knows they're hovering; the UI only needs to confirm it.

### Transitions

| Property | Duration | Easing |
|----------|----------|--------|
| Background color | 120ms | `ease-out` |
| Border color | 120ms | `ease-out` |
| Opacity | 100ms | `ease-out` |
| Transform (scale) | 150ms | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Width (sidebar collapse) | 200ms | `cubic-bezier(0.4, 0, 0.2, 1)` |

**Remove:** The 450ms reveal animations. Page content should appear instantly. If data is loading, use a skeleton; if data is ready, show it.

### Loading Patterns

- **Skeleton screens** for cards (not spinners). Background: `var(--surface)`. Animated overlay: `linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent)` at 1.5s animation.
- **Inline spinners** only inside buttons that triggered an action (triage accept/dismiss).
- **No full-page loading states.** Use React Suspense boundaries with skeleton fallbacks per section.

---

## 8. CSS Variables — Ready for globals.css

```css
@theme inline {
  /* ─── Backgrounds ─────────────────────────────── */
  --color-base: #0c0c0e;
  --color-surface: #141416;
  --color-elevated: #1c1c1f;
  --color-overlay: #222225;

  /* ─── Text ────────────────────────────────────── */
  --color-t1: #e8e8ec;
  --color-t2: #9b9ba4;
  --color-t3: #5c5c66;

  /* ─── Borders ─────────────────────────────────── */
  --color-border: rgba(255, 255, 255, 0.06);
  --color-border-medium: rgba(255, 255, 255, 0.10);
  --color-border-emphasis: rgba(255, 255, 255, 0.16);

  /* ─── Accents (desaturated for dark mode) ────── */
  --color-flame: #e8613a;
  --color-amber: #d4a033;
  --color-cyan: #4db8c9;
  --color-violet: #9b8abf;
  --color-green: #5cc98f;

  /* ─── Accent Backgrounds (10% opacity) ────────── */
  --color-flame-bg: rgba(232, 97, 58, 0.10);
  --color-amber-bg: rgba(212, 160, 51, 0.08);
  --color-cyan-bg: rgba(77, 184, 201, 0.08);
  --color-violet-bg: rgba(155, 138, 191, 0.06);
  --color-green-bg: rgba(92, 201, 143, 0.08);

  /* ─── Typography ──────────────────────────────── */
  --font-sans: 'Geist', 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'Geist Mono', 'JetBrains Mono', 'Fira Code', monospace;

  /* ─── Type Scale ──────────────────────────────── */
  --text-xs: 11px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 16px;
  --text-lg: 20px;
  --text-xl: 24px;
  --text-display: 32px;

  /* ─── Leading (Line Heights) ──────────────────── */
  --leading-xs: 16px;
  --leading-sm: 18px;
  --leading-base: 20px;
  --leading-md: 22px;
  --leading-lg: 26px;
  --leading-xl: 30px;
  --leading-display: 36px;

  /* ─── Tracking (Letter Spacing) ───────────────── */
  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide: 0.06em;

  /* ─── Spacing ─────────────────────────────────── */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  /* ─── Radii ───────────────────────────────────── */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* ─── Shadows ─────────────────────────────────── */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.5);
  --shadow-overlay: 0 24px 48px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;

  /* ─── Transitions ─────────────────────────────── */
  --transition-fast: 100ms ease-out;
  --transition-base: 120ms ease-out;
  --transition-slow: 200ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Body Defaults

```css
html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-base);
  letter-spacing: var(--tracking-normal);
  background: var(--color-base);
  color: var(--color-t1);
}
```

### Scrollbar (Invisible by Default)

```css
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.14);
}
```

### Focus Indicators

```css
:focus-visible {
  outline: 2px solid var(--color-flame);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

:focus:not(:focus-visible) {
  outline: none;
}
```

---

## 9. Component Patterns

### Action Card (Compact)

```
Structure:
├── Container: p-3, rounded-lg, border-l-2, bg-surface, border-border
│   ├── Top Row: flex items-center gap-1.5
│   │   ├── Priority Badge: text-xs mono medium, px-1 py-px, rounded-sm
│   │   ├── Type Label: text-xs mono, color-t3 (no background)
│   │   └── Status Badge: text-xs mono medium, ml-auto
│   ├── Title: text-md semibold, color-t1, mt-1.5
│   ├── Reasoning: text-sm regular, color-t2, mt-1, line-clamp-2
│   ├── Meta Row: flex items-center gap-2, mt-2
│   │   ├── Thesis Tag: text-xs mono, color-violet (text only, no bg pill)
│   │   ├── Assigned: text-xs mono, color-t3
│   │   ├── Score: text-xs mono, color-t3, ml-auto
│   │   └── Time: text-xs mono, color-t3
│   └── Actions: flex gap-2, mt-2 (only if status=Proposed)
│       ├── Accept: h-8, rounded-md, green text, green-bg on hover
│       └── Dismiss: h-8, rounded-md, t3 text, neutral bg
```

**Key differences from current:**
- `p-3` not `p-5`
- `rounded-lg` not `rounded-xl`
- `border-l-2` not `border-left: 3px solid`
- Type label as plain text, not a pill badge
- Meta row is single line, not separate date row
- Action buttons are 32px (h-8) not 44px (min-h-[44px]) visually

### Thesis Card (Conviction Visual)

```
Structure:
├── Container: p-3, rounded-lg, bg-surface, border-border
│   ├── Header: flex items-center gap-2
│   │   ├── Name: text-md semibold, color-t1, flex-1
│   │   └── Activity Badge: text-xs mono, flame (only if recentActivity > 0)
│   ├── Conviction Bar: flex gap-px, h-4, mt-2
│   │   └── 6 segments: 2px radius, dynamic height, active=color / inactive=transparent
│   ├── Labels: flex gap-2, mt-1.5
│   │   ├── Conviction Level: text-xs mono medium, colored
│   │   └── Status: text-xs mono, pill with bg
│   ├── Core Thesis: text-sm, color-t2, mt-1.5, line-clamp-2
│   ├── Evidence Bar: mt-2, h-1 (thinner than current h-1.5)
│   ├── Metrics: flex gap-3, text-xs mono, mt-1.5
│   └── Updated: text-xs mono, color-t3, mt-2
```

**Key differences from current:**
- `p-3` not `p-5`
- No colored pill backgrounds on bucket tags (use color-t3 text, no background)
- Evidence bar is 4px (h-1) not 6px (h-1.5)
- Metrics row is tighter

### Navigation (Sidebar + Bottom Nav)

**Sidebar:**
```
Width: 200px (expanded), 52px (collapsed)
Background: var(--color-surface) at 95% opacity, blur(8px)
Border-right: 1px solid var(--color-border)

Nav Item (idle):
  height: 36px
  padding: 0 12px
  color: var(--color-t2)
  icon: 18px, stroke-width 1.5

Nav Item (active):
  color: var(--color-t1)
  background: rgba(255, 255, 255, 0.04)
  left-bar: 2px wide, var(--color-flame)
  icon: 18px, stroke-width 2, filled
```

Note: Active item uses `color-t1` (not flame). The accent color is reserved for the 2px left indicator bar only. This is the Linear pattern: active item is brighter white, not colored.

**Bottom Nav (mobile):**
```
Height: 56px + safe area
Background: var(--color-surface) at 95% opacity, blur(8px)
Border-top: 1px solid var(--color-border)

Item (idle):
  icon: 20px, color-t3
  label: text-xs, color-t3

Item (active):
  icon: 20px, color-t1
  label: text-xs, color-t1
  dot: 3px flame dot below icon (subtle indicator)
```

### Command Palette

```
Position: fixed, centered, top-[12vh]
Width: min(560px, 100vw - 32px)
Background: var(--color-elevated)
Border: 1px solid var(--color-border-medium)
Shadow: var(--shadow-overlay)
Radius: var(--radius-lg) (8px)

Input area:
  height: 48px (from 52px)
  font: var(--font-sans), var(--text-base)
  placeholder-color: var(--color-t3)
  caret-color: var(--color-flame)

Results:
  max-height: 50vh
  item-height: 40px
  item-padding: 8px 12px
  selected: background rgba(255,255,255,0.04)

Group headers:
  font: var(--font-mono), var(--text-xs)
  tracking: var(--tracking-wide)
  color: var(--color-t3)
  padding: 8px 12px

Footer hints:
  height: 32px (from 40px)
  font: var(--font-mono), var(--text-xs)
  kbd: 18px square, radius-sm, border-border, bg transparent
```

### Data Tables (New Pattern)

```
Container: border-border, rounded-lg, overflow-hidden

Header Row:
  height: 32px
  background: var(--color-surface)
  font: var(--font-mono), var(--text-xs), medium, tracking-wide, uppercase
  color: var(--color-t3)
  padding: 0 12px
  border-bottom: 1px solid var(--color-border)

Data Row:
  height: 36px (desktop), 44px (mobile)
  padding: 0 12px
  font: var(--font-sans), var(--text-sm)
  color: var(--color-t1) for primary column, var(--color-t2) for others
  border-bottom: 1px solid var(--color-border) (or alternating bg)

Data Row (hover):
  background: rgba(255, 255, 255, 0.02)

Data Row (selected):
  background: rgba(232, 97, 58, 0.04)
  border-left: 2px solid var(--color-flame)

Numerical Data:
  font: var(--font-mono), var(--text-sm)
  text-align: right
  tabular-nums: true
```

---

## 10. Anti-Patterns — What to STOP Doing

### Stop Immediately

1. **Stop using Instrument Serif for headlines.** It creates a magazine aesthetic, not a tool aesthetic. Replace with Geist/Inter at semibold weight.

2. **Stop using atmospheric gradient backgrounds** (`.bg-intelligence`, `.bg-hero-thesis`, `.bg-hero-action`, `.bg-hero-portfolio`, `.bg-hero-company`, `.bg-hero-network`). Replace with flat `var(--color-base)`.

3. **Stop using rainbow timeline gradients.** Replace `.timeline-line::before` with a single-color line in `var(--color-border)` or `var(--color-t3)` at 30% opacity.

4. **Stop using `text-[9px]` and `text-[10px]`.** The minimum readable size is 11px. Round up everything below 11 to 11.

5. **Stop using accent-colored scrollbar thumbs.** The flame scrollbar is decorative. Use `rgba(255,255,255,0.08)`.

6. **Stop putting colored backgrounds on every badge.** A priority badge can be `P0` in flame-colored text on transparent background. The colored pill background is only needed when the badge is actionable.

7. **Stop glass-morphism on navigation.** Replace `backdrop-filter: blur(16px) saturate(1.2)` with `background: color-mix(in srgb, var(--color-surface) 95%, transparent)`. Simpler, lighter, more professional.

### Phase Out

8. **Reduce from 5 accent colors to 3 primary + 2 reserve.** In any given view, only flame + green + one contextual color should appear as prominent accents. Violet and cyan become subtle text colors only.

9. **Replace `rounded-xl` (12px) with `rounded-lg` (8px)** on all cards. Reserve `rounded-xl` for modals and sheets only.

10. **Remove the `.reveal` animation class.** Content should not animate on scroll. This is a marketing-site pattern. For a tool, instant visibility on scroll is correct.

11. **Remove `.badge-pulse` and `.pulse-dot` animations.** Pulsing elements are distracting in a dense tool UI. If something needs attention, use a static accent color. If it's urgent, use the P0 banner (which already exists).

12. **Remove `.fab-pulse` from the FAB.** A persistently pulsing button is the opposite of calm. Use a static flame-colored button with a subtle shadow.

---

## Implementation Priority

### Phase 1: Foundation (Highest Impact, Lowest Risk)
1. Swap CSS variables to new color system (backgrounds, text tiers, borders)
2. Desaturate accent colors
3. Remove atmospheric gradients
4. Remove Instrument Serif, switch to Geist/Inter
5. Implement the type scale (consolidate font sizes)

### Phase 2: Density
6. Tighten card padding (p-5 to p-3)
7. Reduce border-radius (xl to lg)
8. Tighten page margins and section gaps
9. Implement the spacing system

### Phase 3: Refinement
10. Refine hover states (subtle backgrounds, not border changes)
11. Replace glass-morphism with semi-transparent solids
12. Implement neutral scrollbars
13. Clean up animations (remove reveal, pulse, rainbow)

### Phase 4: New Patterns
14. Add list/table view for entity pages
15. Tighten command palette
16. Implement skeleton loading states
17. Add multi-column breakpoints for wider screens

---

*This document synthesizes design patterns from Linear, Superhuman, Bloomberg Terminal, Arc, Raycast, Notion, and Figma. Every recommendation is grounded in what makes those products feel world-class: restraint, consistency, perceptual precision, and respect for information density.*
