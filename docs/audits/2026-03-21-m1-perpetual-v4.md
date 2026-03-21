# M1 WebFront Perpetual Loop v4 — 2026-03-21

## Loop: In-Product Feedback System

### What Was Built
In-product feedback widget deployed to every page of digest.wiki. Allows Aakash to rate any page and provide structured feedback that routes to the correct machine source.

### Components Created

| File | Purpose |
|------|---------|
| `src/app/actions/submit-feedback.ts` | Server action — validates input, inserts to Supabase `user_feedback_store` table |
| `src/components/FeedbackWidget.tsx` | Client component — floating button, bottom sheet (mobile) / centered dialog (desktop) |
| `src/app/globals.css` | CSS additions — `.feedback-fab`, `.feedback-sheet`, `.feedback-backdrop` + reduced motion |
| `src/app/layout.tsx` | Integration — `<FeedbackWidget />` added globally next to `<AddSignal />` |

### Feature Details

1. **Floating button** — bottom-left, 40px, unobtrusive ghost style (`rgba(255,255,255,0.06)` background, `MessageSquarePlus` icon). Positioned to not conflict with the AddSignal FAB (bottom-right).

2. **Context-aware** — automatically captures current `pathname` and resolves machine sources via `PAGE_MACHINE_MAP`. Displayed as badges in the sheet header.

3. **Rating** — thumbs up/down toggle buttons (maps to rating 5/1 in the integer column).

4. **Category** — optional pills: UX, Intelligence, Data, Bug. Maps to `feedback_type` column.

5. **Free text** — optional textarea, 2000 char limit.

6. **Page-to-machine mapping**:
   - `/comms` → M8, M1
   - `/strategy` → M7, M1
   - `/actions` → M5, M6, M1
   - `/thesis` → M6, M7, M1
   - `/` → M7, M5, M1
   - `/network` → M12, M4, M1
   - `/portfolio` → M12, M4, M1
   - Prefix matching for sub-pages (e.g., `/actions/123` → M5, M6, M1)

7. **Supabase storage** — inserts to `user_feedback_store` table via server action (no client-side Supabase). Context JSONB includes `machine_sources`, `section`, `url`, `category`, `thumb`.

8. **UX** — Sonner toast "Feedback saved" on success, auto-close. Cmd+Enter submit, Escape close. Body scroll lock on mobile. Reduced motion support.

### Technical Notes
- `getMachineSourcesForPage()` lives in the client component (not the server action file) because Next.js `"use server"` files only export async functions as server actions. Non-async utility functions cannot be imported client-side from `"use server"` modules.
- Reuses existing animation keyframes (`signal-backdrop-in`, `signal-sheet-up`, `signal-dialog-in`) to keep CSS DRY.
- z-index 30 for FAB (below AddSignal at z-40, below modals at z-50).

### Deployment
- Commit: `5f84198` → pushed to `main`
- Vercel deployment: `dpl_NA4YkaRjYU8CoJMBP4NehJ7UWsCb` (building)
- Live at: https://digest.wiki

### Build Verification
- `npm run build` passes clean — all routes compile.
