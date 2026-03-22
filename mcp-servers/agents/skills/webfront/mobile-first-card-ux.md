# Mobile-First Card UX — WebFront Design Skill
*For M1 WebFront machine agents. User tests on mobile (375px) FIRST.*

---

## ABSOLUTE RULE: Mobile is the primary device.

Aakash uses digest.wiki on his phone. Every design decision starts at 375px and scales UP to desktop. Never the reverse.

---

## Card Design Principles

### Size & Touch
- **Minimum card height: 80px.** No cramped 40px rows. Each card is a tappable surface.
- **Touch targets: 48px minimum.** Buttons, icons, interactive elements — all 48x48px.
- **Padding: 16px minimum** inside cards. 20px preferred. Never 8px.
- **Gap between cards: 12px minimum.** 16px preferred. Cards need breathing room.
- **Font size: 15px base** on mobile. Not 12px. Not 13px. Labels can be 13px. Body text 15px+.

### Information Density — LESS is more on mobile
- **3-5 data points per card MAX.** Not 8. Not 12. Three to five key things.
- **Primary info: 1 line, bold, 17px+.** Person name, company name, action title.
- **Secondary info: 1-2 lines, 14px, muted color.** Role, date, status.
- **Tertiary info: hidden by default.** Show on tap/expand. Don't clutter the card.
- **One CTA per card.** Not three buttons. One primary action. Secondary actions in expanded view or swipe.

### Visual Hierarchy
- **Left-to-right priority.** Most important info on the left. Action on the right.
- **Color signals, not labels.** Red dot for urgent. Green dot for healthy. Don't write "URGENT" when a red dot suffices.
- **Badges over text.** "P0" badge > "Priority: P0" text. Saves space, scans faster.
- **Icons with meaning.** Each icon must map to one concept. Don't decorate — communicate.

### Sections & Grouping
- **Section headers: sticky, 44px, semibold.** Scroll with clear section context.
- **Maximum 2 levels of nesting** on mobile. Card → expanded detail. No card → sub-card → sub-sub-card.
- **Horizontal scroll for categories.** Filter pills, tabs, tags — horizontal scroll, not stacked.
- **Collapsible sections.** Don't show everything. Let user expand what they care about.

---

## Anti-Patterns (NEVER do these on mobile)

| Anti-Pattern | Why It's Bad | Do This Instead |
|-------------|-------------|-----------------|
| `grid-cols-4` without `sm:` prefix | 4 columns at 375px = 80px each = unreadable | `grid-cols-2 sm:grid-cols-4` |
| `text-xs` (12px) for data values | Unreadable on phone | `text-sm` (14px) minimum |
| `p-2` (8px) card padding | Feels cramped, touch targets overlap | `p-4` (16px) minimum |
| `gap-1` (4px) between cards | Cards blur together | `gap-3` (12px) minimum |
| Tables on mobile | Horizontal scroll = unusable | Stack as cards |
| Fixed sidebars | Steals 200px from 375px screen | Bottom nav + sheet overlays |
| Multiple CTAs per card | Decision paralysis, fat-finger taps | One primary CTA, rest in expanded view |
| Long text paragraphs | Won't read on phone | 2 lines max, then "Read more" |
| Modals with form fields | Keyboard covers modal | Full-screen sheets from bottom |
| Nested scroll areas | Scroll confusion, trapped gestures | Single scroll context per view |

---

## Card Templates for AI CoS

### Action Card (triage)
```
┌──────────────────────────────────┐
│ 🔥 Meet Kunal at Hexo AI    P0  │  ← 17px bold + badge
│ Portfolio check-in · 3d overdue  │  ← 14px muted
│                                  │
│ [Accept]  [Defer]  [Skip]        │  ← 48px touch targets
│                         👍 👎    │  ← RL thumbs
└──────────────────────────────────┘
  gap-3 (12px)
```

### Research Proposal Card (ENIAC)
```
┌──────────────────────────────────┐
│ 🔬 Applied AI thesis gap         │  ← 17px bold
│ "Is agent-friendly codebase a    │  ← 15px, 2 lines max
│  real category?"                 │
│                                  │
│ Skip · Scan · [Investigate] · Ultra │  ← depth grade pills
│                         👍 👎    │  ← RL quality
└──────────────────────────────────┘
```

### Obligation Card (Cindy)
```
┌──────────────────────────────────┐
│ Ayush Sharma · AuraML        🔴 │  ← name + company + urgency dot
│ Intro to Schneider investors     │  ← 15px obligation text
│ 5 days overdue                   │  ← 14px muted, urgency color
│                                  │
│ [Handle]              👍 👎     │  ← one CTA + RL
└──────────────────────────────────┘
  → tap "Handle" → expand with contextual options
  → options are dynamic (Cindy decides what to show)
```

### Person Card (compact, in lists)
```
┌──────────────────────────────────┐
│ 👤 Mohit Gupta                   │  ← 16px bold
│ Co-Founder · Levocred · 🟢      │  ← 14px role + company + status
│ 12d ago · WhatsApp + Granola     │  ← 13px channels
│                              ›   │  ← chevron = tappable
└──────────────────────────────────┘
```

---

## Spacing System

| Token | Value | Use For |
|-------|-------|---------|
| `space-xs` | 4px | Icon padding, badge internal |
| `space-sm` | 8px | Within tight groups (label+value) |
| `space-md` | 16px | Card padding, between elements |
| `space-lg` | 24px | Between sections |
| `space-xl` | 32px | Page top/bottom padding |
| `space-2xl` | 48px | Between major page sections |

---

## Typography Scale (mobile)

| Role | Size | Weight | Use For |
|------|------|--------|---------|
| Page title | 22px | 700 | Page headers |
| Section header | 17px | 600 | Section titles (sticky) |
| Card title | 16px | 600 | Primary card info |
| Body | 15px | 400 | Readable text, descriptions |
| Secondary | 14px | 400 | Dates, metadata, labels |
| Caption | 13px | 500 | Badges, tags, subtle labels |
| Micro | 11px | 500 | Monospace IDs, timestamps |

---

## Before Every Deploy Checklist

1. [ ] Test at 375px viewport width
2. [ ] All touch targets ≥ 48px
3. [ ] No `grid-cols-N` without responsive prefix
4. [ ] Card padding ≥ 16px
5. [ ] Card gaps ≥ 12px
6. [ ] No tables — cards or stacked layout
7. [ ] Font sizes: body ≥ 15px, secondary ≥ 14px
8. [ ] Single scroll context (no nested scroll traps)
9. [ ] Bottom nav clearance (pb-20 or pb-24)
10. [ ] Safe area insets for notch/home indicator
