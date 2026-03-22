# User Feedback Timeline — 2026-03-22

Chronological stream of user reactions during machine loops. Analyzed at pause/sync points and fed into machine loops.

---

## Session Start — 21:30 IST

**User directive:** Resume all machineries. Feedback tracker live at `docs/FEEDBACK-TRACKER-LIVE.md`. User will stream feedback from CC and WebFront. All machines must update tracker as they address items.

**Unaddressed P0s from prior session:**
1. Deep research button dead (reported TWICE — FB-15, FB-21)
2. Founder vs co-investor misclassification (FB-22)
3. `/network/2455` bug (FB-23)
4. 609 thin-content companies (FB-3)
5. Connection noise — only 24.9% evidence-based (FB-4)

---

## Feedback Stream

### M9 QA Audit Findings (internal — not user feedback)

**[~10:00 IST] M9 QA Loop 1 complete.** Full Supabase data audit. System revised DOWN from 6.9/10 to 5.2/10.

Key findings that all machines must absorb:
1. **Data richness is 10x worse than reported.** FB-3 said "609 thin companies." Actual: 4,501 out of 4,567 (98.6%) have <500 chars. Average 170 chars. The "609" number was only counting thin portfolio companies, not the full companies table.
2. **Connection quality is 99.9% noise, not "85.1% meaningful."** 23,701/23,716 connections have evidence_count=1. The "85.1%" metric measured connection strength (above 0.5), not evidence quality. True multi-evidence connections: ~15 out of 23,716.
3. **Intelligence layer is starving.** Only 23 interactions in the interactions table. 715 WhatsApp conversations exist but are NOT in interactions. Cindy has almost nothing to reason over.
4. **Obligation priorities are inflated.** All top 7 obligations have blended_priority=1.0. No differentiation = no signal for the user.
5. **4 "addressed" feedback items (FB-17/18/19/20) have no verified fix.** "Marked as addressed" without code change evidence.
6. **Deadlock still occurring** in rescore_related_actions despite "fixed" claim.
7. **Agent CLAUDE.md quality:** Cindy 4.5/10 (639+ lines of procedural scripts), Content 5.5/10 (half scripts), ENIAC 7/10 (mostly good). These need script-to-objective refactor.

**Pattern:** Machine self-grades are still inflated. "8.3/10 system" and "healed to 8.7" and "85.1% meaningful" all overstate reality when you pull the actual data. Honest score: 5.2/10.

### User Feedback Wave — 04:21-04:47 UTC (11 items, FB-24 to FB-34)

**[04:21] FB-24 — /network/403 Bug.** "Clicking a founder name in portfolio detail page landed on this page. Clearly a bug." → Founder link routing issue, same class as FB-13. M1+M4.

**[04:22] FB-25 — /portfolio/25 Thesis Links.** "Thesis links are poor and one of healthcare is not valid! Needs proper diagnosis and correction." → ILIKE matching is broken, needs semantic matching via embeddings. M4+M1.

**[04:24] FB-26 — /portfolio/25 Similar Companies.** "Similar companies listed are totally off. Needs high match and two sets: (1) similar portfolio companies by founder archetype + domain, (2) similar companies outside portfolio via parallel search, updated every 30 days." → Current matching algorithm is useless. Need embedding-based similarity + external search. M4+M12+M1.

**[04:26] FB-27 — /portfolio/25 AddSignal UX.** Rating 5/5! "The add note button and window are very powerful UX. Should rethink and evolve and make it even better! Also need a way to edit DB data from WebFront with trail/logs and undo." → POSITIVE SIGNAL. Build on this. M1.

**[04:26] FB-28 — /portfolio/25 Key Contacts Dedup.** "Key contacts and Founders & Team look duplicate. Chuck key contacts." → ALREADY FIXED in M1 L2.

**[04:29] FB-29 — /network/403 Interaction History.** "Content, UI, and quality of intelligence all need improvement." → Person page interaction history is skeletal. Needs richer rendering with WhatsApp context, Granola summaries, timeline visualization. M1+M8.

**[04:32] FB-30 — /portfolio/103 Internal Intelligence.** "Deep research is external. I also want richness from internal info: Notion page content with comments, mails, WhatsApp. Intelligence from internal sources is temporal and needs to be on this page." → CRITICAL INSIGHT. Deep research = external. Need internal intelligence panel: Notion comments, WhatsApp mentions, email threads, Granola meeting notes. Temporal, not static. M1+M4+M8.

**[04:38] FB-31 — /comms Surabhi/Soulside.** "Surabhi Bandari — (1) She's now a portfolio founder at Soulside, why doesn't Cindy know? (2) Some MSC Fund thing linked incorrectly, maybe from Granola where another Surabhi is co-founder. Need way better resolution." → Identity resolution failure. Cindy not cross-referencing portfolio DB. M8+M4.

**[04:40] FB-32 — /comms Action Dismissal UX.** "Clicked 'not needed' on Abhishek Anita card, got system backend toast, then options came back. Should show 'resolved/got it' confirmation. That's how an intelligent EA behaves." → Action dismissal UX needs proper confirmation flow. M1+M8.

**[04:42] FB-33 — /comms Contextual Actions + RL.** "Options Cindy surfaces should NOT be fixed — they should be contextual to the action and person. Selecting something should log as message history between Cindy and me. So Cindy remembers what happened for past actions. This is perpetual context, not just RL." → VISION: Cindy-user conversation history per action. Actions are contextual, responses are logged, Cindy builds memory. M8+M1.

**[04:47] FB-34 — /actions Text Input Box.** "What is that box below? I thought it could be for me to tell the AI CoS system something in text. That would be 10x UX. Example: 'give me draft of a mail message' → system drafts it → lies in my email drafts → Cindy tracks it and asks 'should I send it?'" → VISION: Free-text command input on actions page. System interprets intent, takes action, Cindy tracks follow-through. Email draft → send confirmation loop. M1+M8+M6.

---

### Patterns from this feedback wave

16. **Internal intelligence ≠ external research.** Deep research is external (web, reports). Internal intelligence = Notion comments + WhatsApp + email + Granola. Both need to be on portfolio pages, separately.

17. **Cindy-user conversation history.** Actions aren't one-shot. User responds → Cindy logs it → builds contextual memory per person/action. This is how an EA works — remembering what was discussed.

18. **AddSignal UX is a winner.** Rating 5/5. Double down on this interaction pattern.

19. **Free-text command input is 10x.** User types intent → system interprets → acts → tracks. This is the natural evolution toward conversational UX without chat.

20. **Identity resolution is still failing.** Surabhi/Soulside mislink. Portfolio DB data not reaching Cindy. Cross-DB resolution needs to be bulletproof.

### User Feedback Wave 2 — 05:04-05:06 UTC (3 items, FB-35 to FB-37)

**[05:04] FB-35 — /comms Portfolio Founders at Risk.** "I love the portfolio founders at risk section! Though naming is off. Should be intelligent — capture priorities, list accordingly (unless I-owe/they-owe takes precedence). Better UI with > arrow opening intelligent view of what I could do about flagged staleness. Current click opens page with good info but lacks suggestive intelligence." → POSITIVE on concept, needs: (1) rename section, (2) priority ordering, (3) expandable with suggested actions. M1+M8.

**[05:04] FB-36 — /comms Interaction History.** Rating 1/5. "Needs product work. Right now it's just dumb dump." → Interaction history rendering is raw data, not intelligence. Needs summarization, timeline visualization, key moments extraction. M1+M8.

**[05:06] FB-37 — /comms Detail Overlay UX Bug.** "The UX flow of this detail page has buggy behaviour. The overlay page scrolls AND background page too. The X on top right to close sometimes gets hidden behind top nav." → CSS/scroll-lock bug on the slide-out panel. M1.

---

### Pattern from Wave 2

21. **"Lacks suggestive intelligence"** is the recurring theme. Good data exists but the UI dumps it raw instead of reasoning about what to DO with it. Every detail view should suggest actions.

### VISION: Datum Tab — Intelligent Task Interface (FB-38, from CC)

**[~05:30 UTC] User vision for Datum tab on digest.wiki:**

The user wants a Datum tab that is NOT a chat interface and NOT a simple form. It's an **intelligent task communication interface** with:

1. **Task submission** — user sends something to Datum (e.g., "update Bidso's funding to Series A, $12M")
2. **Task tracking** — Datum tracks tasks, shows status (pending/working/done/needs-input)
3. **Thread detail pages** — each task becomes a thread where Datum can ask clarifying questions
4. **Dynamic contextual UI** — the UI elements in threads are NOT fixed. They're contextual to what Datum needs:
   - If Datum needs a company selection → show company picker
   - If Datum needs confirmation of a merge → show diff view
   - If Datum needs a person identity → show candidate cards with match confidence
   - Generic text response field always available
5. **Async by default** — Datum processes in background, user checks back
6. **Optional sync mode** — real-time interaction, but STILL using smart UI elements, not a plain chat window
7. **"Smart chat with power of UI"** — the key phrase. Not chat-only, not form-only. Contextual UI that FEELS like communicating.

**This is the same pattern as FB-33 (Cindy conversation history) and FB-34 (text input = 10x UX) applied to Datum. The user wants every agent to have an intelligent, contextual communication channel — not raw chat, not static forms.**

22. **Agents need communication channels, not chat windows.** Each agent (Datum, Cindy, Megamind) should have a tab where the user communicates via contextual UI. Smart forms, candidate cards, diff views, confirmation flows — not just text. Async with optional sync. This is the "conversational UX without chat" vision applied per-agent.

