# Aakash AI CoS — System Vision v2
## "Who Should I Meet Next?"

### The Reframe

v1 of this document designed an assistant that automates tasks around Aakash's day — morning briefs, post-meeting capture, weekly reviews. That's plumbing. Useful plumbing, but plumbing.

The actual problem is a **network optimization problem**: Aakash has a finite number of meeting slots and an ever-expanding universe of people he could meet. The highest-leverage thing an AI Chief of Staff can do is answer the question: **"Given everything I know about your world right now — your open IDS threads, your portfolio positions, your pipeline, your thesis, your travel, your Collective gaps — who should occupy your next 50 meeting slots, and why?"**

This isn't scheduling. This is strategic capital allocation, where the capital is Aakash's time and the returns compound through his network.

### The Core Problem: Meeting Slot Optimization

**Inputs:**
- **The Universe:** 400+ people Aakash could potentially meet at any given time — LinkedIn connections, new discoveries from X/content feeds, screengrabs, Collective targets, portfolio founders, existing network, inbound requests
- **The Constraint:** ~50 meeting slots in a given planning window (a week, a trip, a quarter)
- **The Context:** Where Aakash will physically be (Mumbai, SF trip, etc.), what's happening in portfolio, what's active in pipeline, what thesis threads are hot, what Collective gaps exist

**The Four Priority Buckets (with Aakash's stated weighting):**

| Priority | Objective | Weight | When |
|----------|-----------|--------|------|
| 1 | **New cap tables** — Expand network to be on more amazing companies' cap tables | Highest | Always |
| 2 | **Deepen existing cap tables** — Continuous IDS on portfolio to make ownership increase decisions | High | Always |
| 3 | **New founders/companies** — Meet potential backable founders via DeVC Collective pipeline | High | Always |
| 4 | **Thesis evolution** — Meet interesting people who keep thesis lines evolving | Lower when conflicted with 1-3, but **highest when capacity exists** — "I'd want to do this more than anything else" | Fill remaining capacity, but never zero |

**The Solve:** For each person in the universe, score them against:
- **Leverage:** How much does meeting this person move the needle on one of the four objectives?
- **Urgency:** Is there a time-sensitive reason to meet now (funding round closing, portfolio company inflection point, person visiting same city, hot IDS thread)?
- **Information gain:** What will Aakash learn that he can't learn otherwise? (A meeting with a portfolio founder post-investor-update has less info gain than a meeting pre-launch.)
- **Network multiplier:** Does this person connect Aakash to other high-value nodes? (Someone who knows 5 potential portfolio companies > someone who knows 1)
- **Thesis density:** Is this person at an intersection of multiple thesis threads?
- **Relationship trajectory:** Is this a new relationship that needs investment to unlock, or an established one that needs maintenance?

Then optimize the slot allocation across buckets, accounting for geographic constraints, energy management (not 8 hard meetings back-to-back), and ensuring minimum allocation to bucket 4 even when 1-3 are demanding.

---

## THE INTELLIGENCE ENGINE (What Actually Matters)

### The People Scoring Model

This is the heart of the AI CoS. Not automation — intelligence.

For every person in Aakash's universe, the system maintains a living score:

```
Person Score = f(
    bucket_relevance,      — which of the 4 objectives does meeting this person serve?
    current_ids_state,     — where are they in the IDS journey? what's the open question?
    time_sensitivity,      — is there a reason to meet NOW vs later?
    info_gain_potential,   — what will Aakash learn that he doesn't know?
    network_multiplier,    — who else does this person connect to?
    thesis_intersection,   — does this person sit at a thesis convergence point?
    relationship_temp,     — warm/cold? last interaction? trend?
    geographic_overlap,    — will they be in the same city?
    opportunity_cost       — what does Aakash miss by NOT meeting them now?
)
```

This scoring model is continuously updated as new signals come in — a portfolio company's metrics change (bucket 2 urgency rises), a new founder appears on X (bucket 3 candidate emerges), a thesis thread gets a new data point (bucket 4 person becomes more relevant), someone Aakash wants to meet is visiting Mumbai next week (geographic overlap spikes).

### The Decision Layer

The scoring model feeds a decision layer that produces concrete outputs:

**1. "Who should I meet this week?" (Routine planning)**
Given current calendar availability, produce a ranked list of 10-15 highest-leverage meetings to schedule. For each: who, why now, what bucket, what to discuss, expected outcome.

**2. "Who should I meet on my SF trip?" (Trip optimization)**
Given a travel window (e.g., 5 days in SF), produce an optimized meeting plan. Filter universe to SF-based or SF-visiting people, score and rank, suggest clustering by geography within the city, protect thesis-time blocks. Output: a trip plan that maximizes the ROI of every day.

**3. "I have one open slot tomorrow — who?" (Real-time slot filling)**
When a meeting cancels or an hour opens up, the system already knows the next-best person to slot in. It's pre-computed and ready.

**4. "Here's a new person I discovered — where do they rank?" (Signal integration)**
When Aakash screengrabs a LinkedIn profile or bookmarks an X post, the system instantly scores the person against the current universe and tells Aakash: "This person ranks #7 in your current SF trip planning because [reasons]. Want to add them?"

### What Makes This Different From a CRM

CRMs track interactions. They don't think. The AI CoS thinks:

- **It understands IDS context.** It knows that meeting [Founder X] right now is high-leverage because their Series A is coming up, Aakash's IDS conviction is at "Strong Maybe," and the open question is GTM validation — which means the meeting should be structured around customer reference calls, not product demos.

- **It connects across buckets.** [Person Y] is primarily a bucket 4 thesis contact (deep in agentic AI infrastructure), but they also know [Founder Z] who's in the pipeline (bucket 3), and they sit on the board of [Portfolio Company W] where Aakash has an open IDS question about competitive positioning (bucket 2). One meeting serves three buckets.

- **It sees what Aakash can't see.** Aakash's fuzzy mental map works brilliantly for first-degree connections. But the second and third-degree connections — "your portfolio founder [A] just hired someone from [Company B], where [Person C] who you met last month used to work, and [Company B] is in the exact space your pen testing thesis covers" — that's where the AI's graph traversal ability exceeds human memory.

- **It learns Aakash's revealed preferences.** Over time, the system observes which recommended meetings Aakash takes and which he skips. It learns: Aakash consistently overweights "spiky founders" even when the scoring model says to prioritize portfolio check-ins. The model adjusts.

---

## TIER 1: COWORK + CLAUDE (10x Leverage) — Redesigned

### The Core Cowork Capability: The Network Strategist

Instead of building a morning brief scheduler, the first thing to build is a **strategic meeting advisor** that Aakash can consult interactively.

#### Capability 1: "Optimize My Week" Session

Aakash opens Cowork and says: "I'm planning next week. I'll be in Mumbai Mon-Wed, flying to SF Thursday, there until next Wednesday. Optimize my slots."

Claude then:
1. Pulls the full Notion universe — Network DB (all people + archetypes + IDS state), Companies DB (all pipeline companies + conviction levels + open questions), Portfolio DB (all portfolio companies + current concerns)
2. Enriches via Explorium anyone who needs updating
3. Filters to geographically relevant people (Mumbai universe + SF universe)
4. Scores every person against the four-bucket model using full IDS context
5. Produces a ranked meeting plan:
   - **Mumbai (Mon-Wed):** Top 12-15 meetings ranked, with: who, which bucket(s), why now, what to discuss, expected outcome, IDS open question to resolve
   - **SF (Thu-Wed):** Top 20-25 meetings ranked, same structure
   - **Mix analysis:** "Your SF plan is heavy on bucket 3 (new founders). You have 2 portfolio companies with open concerns that could use face time — consider replacing [lower-ranked meeting] with [portfolio founder]."
   - **Thesis block:** "Based on your active thesis threads (agentic infrastructure, pen testing evolution, USTOL/aviation), here are 3 people in SF who would advance your thinking and aren't in any other bucket."

This is not automation. This is Claude doing deep analytical work on Aakash's network graph, in dialogue with him. Aakash can push back: "I don't need to see [X], move them down. Who else is in SF that's in the drone/logistics space?" and Claude re-optimizes in real time.

#### Capability 2: "Process My Discoveries" Session

Aakash comes back from a week of scrolling LinkedIn, X, attending events. He has 30 screengrabs, 50 bookmarks, and 15 new LinkedIn connections. He dumps them all into Cowork.

Claude then:
1. OCRs all screengrabs, extracts people/companies/thesis signals
2. Enriches every new person via Explorium
3. Classifies each person against Aakash's archetypes and the four buckets
4. Cross-references against existing Notion data — anyone already in the system? any connections to pipeline/portfolio?
5. Produces a ranked list: "From your 95 new captures, here are the top 20 people to pursue, ranked by leverage score. 8 are Collective targets, 5 are thesis contacts, 4 are direct founder leads, 3 are potential co-investors."
6. For each: drafted outreach approach, optimal channel (LinkedIn DM, email, mutual intro via [X]), and where they'd slot in next trip planning.

Then Aakash says "Update Network DB with the top 20 and queue outreach for the top 10" and Claude executes.

#### Capability 3: "Who Am I Underweighting?" Analysis

Periodically (or on demand), Claude runs a gap analysis:
- **Portfolio blind spots:** Which portfolio companies have the longest gap since last IDS interaction? Where is conviction stale?
- **Collective funnel leaks:** Who entered the Collective funnel 3+ months ago and hasn't progressed? What's blocking?
- **Thesis drift:** Are Aakash's thesis threads getting stale? Which threads have the most unresolved questions and fewest recent data points?
- **Network decay:** Which high-value relationships are cooling off? Who should Aakash reconnect with?
- **Geographic opportunity cost:** "You've been to SF 3 times in the last 6 months but haven't met [these 5 high-score people] despite them being SF-based. They keep ranking high — here's why."

#### Capability 4: "Live IDS Feed"

Instead of a morning brief (reactive), build a living feed that Claude updates throughout the day:
- When Aakash is about to meet someone, Claude proactively generates the IDS context — not as a scheduled task but because it's monitoring the calendar in real time (once M365 is connected)
- When a signal comes in (portfolio company news, pipeline company funding, Collective target posts something on LinkedIn), Claude scores it against current priorities and surfaces it IF AND ONLY IF it changes a meeting recommendation or reveals a time-sensitive opportunity
- This is less "daily digest" and more "intelligent interruption based on network relevance"

#### What Cowork Can Actually Do Now for This

Let me be honest about what's immediately buildable vs. what needs M365/WhatsApp:

**Immediately buildable (this week):**
- The "Optimize My Week" session as an interactive Cowork conversation — all Notion data is accessible, Explorium enrichment works, Claude can score and rank
- The "Process My Discoveries" session — Aakash dumps screengrabs and links, Claude enriches and ranks
- The "Who Am I Underweighting?" analysis — purely based on Notion + Explorium data
- Pre-meeting IDS context on demand ("prep me for [person]")

**Needs M365 connection (coming soon):**
- Calendar-triggered intelligence (proactive pre-meeting prep)
- Email signal monitoring
- Scheduling optimization (working with Sneha's calendar management)

**Needs WhatsApp or custom agent (Tier 2):**
- Real-time signal integration as Aakash captures things throughout the day
- Proactive alerts sent to Aakash's phone
- Voice-note processing

### Cowork Tier 1 — Revised Value Assessment

| Capability | What It Solves | Leverage |
|---|---|---|
| Optimize My Week/Trip | Aakash walks into every planning window with an AI-optimized meeting slate instead of fuzzy intuition | **10-15x** on time allocation |
| Process My Discoveries | 95 captures become 20 ranked targets in 15 minutes instead of scattered across surfaces | **8-10x** on signal-to-action |
| Who Am I Underweighting? | Blind spots in portfolio IDS, stale theses, decaying relationships get surfaced | **∞** (currently invisible) |
| Pre-meeting IDS context | Full conviction history + open questions + enrichment before every key meeting | **5-8x** on meeting quality |

**The shift:** v1 was "automate the admin around your day." v2 is "make every meeting-slot decision smarter."

---

## TIER 2: CUSTOM AGENT SDK (100x+ Leverage) — Redesigned

### The Core: An Always-On Network Optimization Engine

The custom agent build isn't about 7 specialist agents doing 7 automated tasks. It's about an **always-on intelligence engine** that continuously:

1. **Ingests signals** from every surface Aakash touches (WhatsApp, LinkedIn, X, email, meetings, content feeds)
2. **Maintains a living score** for every person in Aakash's universe across the four priority buckets
3. **Proactively recommends** meeting allocations based on current priorities, geography, and time sensitivity
4. **Learns and compounds** — every meeting taken, every meeting skipped, every IDS outcome improves the scoring model

### The Three Core Agents (Not Seven)

The v1 design had too many agents doing fragmented work. The redesign has three agents that map to Aakash's actual operating model:

#### Agent 1: The Network Intelligence Engine (The Brain)

This is the single most important agent. It maintains the People Scoring Model and makes all meeting recommendations.

**What it continuously does:**
- Scores every person in Aakash's universe against the four-bucket model
- Re-scores when signals change (new data about a person, portfolio event, thesis development)
- Produces ranked meeting lists on demand (for trip planning, weekly planning, slot-filling)
- Runs optimization: given N available slots and M priority constraints, what's the optimal allocation?
- Detects cross-bucket opportunities: "Meeting [X] serves buckets 1, 2, and 4 simultaneously"
- Identifies time-sensitive windows: "[Founder Y]'s round is closing in 3 weeks — if you want to build conviction, you need 2 meetings before then"
- Tracks meeting outcomes and adjusts scoring model: "Meetings Aakash rates highly tend to have [these characteristics]"

**The scoring model in more detail:**

For each person, the engine computes:

**Bucket 1 Score (New Cap Tables):**
- Is this person associated with a company Aakash could invest in?
- What's the company's stage, sector, thesis-fit?
- What's Aakash's current conviction level? Where is the IDS gap?
- Is there a competitive dynamic (other investors circling)?
- What's the expected return profile?

**Bucket 2 Score (Deepen Existing):**
- Is this a portfolio founder or key person at a portfolio company?
- When was the last IDS interaction?
- Are there open concerns flagged by recent data (metrics, market shifts, competitive moves)?
- Is a follow-on decision approaching?
- What would Aakash learn from this meeting that he can't learn from data?

**Bucket 3 Score (New Founders via Collective):**
- Does this person fit the Collective archetype criteria?
- What's their leverage potential (coverage, evaluation, underwriting)?
- How deep is their domain expertise?
- How connected are they to founder networks Aakash doesn't currently access?
- Are they active in a sector where Aakash has thesis conviction?

**Bucket 4 Score (Thesis Evolution):**
- Does this person have deep expertise in an active thesis thread?
- Can they provide contrarian or non-obvious perspectives?
- Are they practitioners (builders) vs. commentators?
- How does their knowledge connect to investment opportunities?
- Would a conversation with them change Aakash's conviction on any thesis?

**Composite Score = weighted_sum(bucket_scores) × urgency_multiplier × geographic_overlap × relationship_trajectory**

The weights are Aakash's priorities: bucket 1 & 2 dominate when slots are scarce, bucket 4 fills capacity when it exists.

#### Agent 2: The Signal Processor (The Eyes and Ears)

This agent doesn't make decisions — it feeds the Intelligence Engine with continuously updated information.

**Surfaces it monitors:**

- **LinkedIn feed:** New connections Aakash makes, posts that catch his eye (detected via interaction patterns or explicit saves), profile views, people who engage with Aakash's content. For each signal: extract person, enrich, classify, update score in Intelligence Engine.

- **X feed:** Bookmarked tweets, profiles viewed, content saved. Same flow: extract, enrich, classify, update.

- **WhatsApp:** Messages to self-channel, screengrabs in camera roll, links forwarded. Each capture gets: OCR (if image), entity extraction, enrichment, classification, scored.

- **Email (M365):** Inbound intro requests, founder updates, investor reports, meeting requests. Each email gets: entity extraction, intent classification (is this a meeting request? a signal? an FYI?), scored.

- **Content feeds (YouTube, podcasts, Substack):** Watch/listen/read activity tracked (via API where available, browser session where not). Thesis signals extracted: topics getting more attention, new domains being explored.

- **Granola:** Post-meeting transcripts when they appear. Meeting outcomes extracted, IDS signals identified, person scores updated.

- **Market signals (passive web monitoring):** Funding announcements, executive changes, product launches, press mentions for companies in pipeline or portfolio. Via web monitoring or Explorium webhooks.

The Signal Processor's job is to ensure the Intelligence Engine always has the freshest possible view of every person in Aakash's universe. It doesn't decide what to do with signals — it just makes sure they get captured, enriched, and scored.

#### Agent 3: The Operating Interface (The Voice)

This is how Aakash interacts with the system. It lives primarily in WhatsApp.

**Interaction patterns:**

**Aakash asks, system answers:**
- "Who should I meet in SF next week?" → Intelligence Engine produces ranked list, Operating Interface formats for WhatsApp and sends
- "Tell me about [person]" → Full IDS history, current score, bucket relevance, recommended discussion points
- "I just met [person], strong founder, questions on defensibility. ++product ?moat" → Signal Processor captures, Intelligence Engine re-scores, Operating Interface confirms and asks "Want me to update Notion and schedule a follow-up meeting in 2 weeks?"
- "What's happening with my portfolio?" → Intelligence Engine ranks portfolio companies by concern level, Operating Interface sends a prioritized list

**System proactively reaches Aakash:**
- "[Person X] just announced they're visiting Mumbai next week. They rank #3 on your current meeting priority list because [reasons]. Want me to reach out?" → This is the system being a Chief of Staff, not an assistant
- "Your portfolio company [Y]'s competitor just raised $50M. You haven't spoken with [Y]'s founder in 6 weeks. Recommend scheduling a call." → Time-sensitive IDS trigger
- "[New person Z] appeared in your LinkedIn connections. They're ex-[Company] and deeply in the pen testing space. Thesis relevance: high. Collective fit: strong. They're SF-based and you're there in 2 weeks. Add to trip plan?" → Signal → Score → Recommendation in one flow

**The key principle:** The Operating Interface is NOT a chatbot that waits for commands. It's a proactive strategic advisor that surfaces the right information at the right time, always framed around: "Who should Aakash meet, and why?"

### The Data Layer

#### The Network Graph (replaces "Knowledge Graph" from v1)

The central data structure is a **weighted, scored graph** of people and their relationships to Aakash's world:

```
Person Node:
  - identity: name, company, role, location, archetype
  - enrichment: Explorium data, LinkedIn profile, X profile
  - ids_state: conviction level, open questions, last interaction, IDS history
  - bucket_scores: [B1, B2, B3, B4] — continuously updated
  - composite_score: current overall priority
  - geographic: home base, upcoming travel (if known)
  - relationship: temperature, trajectory (warming/cooling/stable)
  - connections: edges to other people, companies, thesis threads

Company Node:
  - pipeline_state: TOFU/MOFU/BOFU, conviction level, deal status
  - portfolio_state: investment amount, current metrics, concerns, follow-on status
  - ids_trail: all notes, all meetings, all signals
  - connections: founders, team, investors, customers, competitors

Thesis Node:
  - topic, domain, conviction level, open questions
  - evidence: research sessions, meetings, articles, content consumed
  - connections: people who've contributed, companies that are relevant
```

Every signal the Signal Processor captures updates this graph. Every recommendation the Intelligence Engine makes reads from this graph. The graph IS the AI CoS's understanding of Aakash's world — it compounds over time exactly like Aakash's own IDS methodology, but externalized, queryable, and never forgets.

### What 100x Actually Looks Like (Revised)

The difference isn't "doing things faster." It's "making fundamentally better decisions about where to spend time."

**Without AI CoS:** Aakash's meeting slate is determined by: who happens to reach out, what Sneha slots in, who he remembers to contact, what his fuzzy mental map surfaces. Maybe 30-40% of his meetings are optimally allocated.

**With AI CoS:** Every meeting slot is allocated based on a scored, ranked, contextual analysis of his entire universe. The system catches opportunities he'd miss (the second-degree connection, the dormant relationship that's suddenly relevant, the thesis contact who also knows a pipeline founder). Maybe 70-80% of meetings are optimally allocated.

If each meeting is worth some amount of expected value, going from 40% to 80% optimal allocation is a 2x on meeting value. Across 7-8 meetings/day, 250+ working days/year, that's a massive compounding effect on network quality, deal flow quality, and investment decision quality.

The 100x comes from the compound effect: better meetings → better IDS → better decisions → better outcomes → better network → even better meetings. The flywheel accelerates because the AI CoS keeps the graph updated and the optimization running continuously.

**A concrete example:**

Aakash is planning a 5-day SF trip. Without AI CoS, he reaches out to people he remembers, Sneha schedules who responds, and the trip is a mix of intentional and opportunistic.

With AI CoS:
- 3 weeks before: "Your SF trip is coming up. I've scored 87 SF-based people in your network. Here are the top 25 meetings, ranked. Your mix: 8 portfolio/pipeline (bucket 1-2), 10 new founders from Collective funnel (bucket 3), 4 thesis contacts (bucket 4), 3 high-value reconnections. The 8 portfolio/pipeline meetings are time-sensitive because [specific reasons for each]. The thesis contacts are clustered around your agentic infrastructure thread, which has the most open questions right now."
- Aakash reviews, adjusts: "Add [X], drop [Y], I also want to meet [Z] who I found on LinkedIn last week."
- AI CoS re-optimizes, handles outreach logistics (or instructs Sneha with context for each), and produces the final slate.
- During trip: real-time adjustments as meetings get confirmed/cancelled, new signals come in, or Aakash discovers someone at an event.
- After trip: all meetings captured, IDS updated, follow-ups tracked, scores adjusted based on outcomes.

That's not 10x better scheduling. That's a fundamentally different way of operating where every trip is a strategically optimized capital deployment.

---

## THE GAP: What Needs to Be True

### For Cowork Tier (10x):
- **Notion data quality:** Network DB, Companies DB, Portfolio DB need to be reasonably up-to-date. The AI can only optimize on what it can see.
- **Interactive sessions:** Aakash needs to be willing to spend 20-30 minutes with Cowork doing "Optimize My Week" sessions. The value is in the dialogue, not a passive brief.
- **Screengrab/bookmark dumps:** Aakash batches his captures and dumps them into Cowork periodically for processing.

### For Custom Agent Tier (100x+):
- **WhatsApp integration:** The single biggest unlock. Aakash interacts via WhatsApp; the system lives there.
- **LinkedIn API or browser access:** To monitor connections, profile views, content engagement. LinkedIn's API is restrictive; browser sessions with Aakash's auth are the realistic path.
- **M365 integration:** Calendar for scheduling intelligence, email for signal monitoring.
- **Persistent compute:** Cloud containers running 24/7 for the Signal Processor and Intelligence Engine.
- **The scoring model needs calibration:** Initial weights come from what we know (the four buckets, Aakash's stated priorities). Over time it needs to learn from Aakash's revealed preferences — which meetings he takes, which he skips, which he rates highly afterward.
- **Aakash's trust in the system:** Starting with recommendations only, earning the right to act (schedule, outreach, update) over time.

---

## WHAT TO BUILD FIRST

### Cowork: The "Optimize My Trip" MVP

The single highest-value Cowork session we can build right now:

1. Aakash says: "I'm going to SF from [date] to [date]. Optimize my meetings."
2. Claude pulls all people from Network DB + Companies DB with SF geography
3. Enriches via Explorium anyone who needs updating
4. Scores every person against the four-bucket model using:
   - Open IDS threads from Companies DB
   - Portfolio positions from Portfolio DB
   - Conviction levels and open questions from all IDS history
   - Thesis relevance from what Claude has learned across 11 sessions
5. Produces a ranked, bucketed meeting plan
6. Aakash iterates in dialogue
7. Final output: optimized slate + Notion updates + outreach drafts

This is buildable TODAY with existing Cowork capabilities. No M365 needed, no WhatsApp needed. Just Claude + Notion + Explorium + deep understanding of Aakash's operating model.

### Custom Agent SDK: The Intelligence Engine MVP

The first agent to build isn't a WhatsApp bot or a signal processor. It's the scoring engine itself — the model that takes Aakash's entire network graph and produces ranked meeting recommendations. Build this as a Claude agent with:
- Notion API access (read all DBs)
- Explorium API (enrichment)
- A persistent data store (the scored network graph)
- An optimization algorithm that allocates N meeting slots across the four buckets

Once the scoring engine works and Aakash trusts its recommendations, THEN wrap it in WhatsApp interface, add the Signal Processor, add the proactive surfacing. The intelligence comes first, the interface second.
