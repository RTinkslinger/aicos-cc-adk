# Aakash AI CoS — System Vision

## The Problem in One Sentence

Aakash operates as a high-throughput human signal processor — 7-8 meetings/day, consuming content across 5+ surfaces, building thesis through rabbit holes, running IDS on hundreds of people and companies simultaneously — but every transition between capture → connection → action leaks signal, and the entire system runs on fuzzy mental memory with no intelligence layer managing time allocation, follow-up, or dot connection.

## Design Principles (Derived from 11 Sessions of Understanding)

1. **WhatsApp-first, mobile-native.** Aakash lives on his phone and WhatsApp. Any system that requires him to open a desktop app, check a dashboard, or visit a URL as a primary interaction will fail. The AI CoS must meet him where he already is.

2. **Capture must be zero-friction.** The screengrab-as-memory, WhatsApp-self-as-bookmark, and fuzzy-mental-map patterns exist because they're the lowest-friction capture available. The AI CoS must be even lower friction than a screengrab — or it won't get used.

3. **IDS is the core operating methodology.** Everything compounds. A meeting note from November becomes critical context for a BRC in March. The system must treat every signal as a node in an ever-growing intelligence graph, not as a transient event.

4. **Two operating modes, one intelligence layer.** Network-led mode (meeting people, signal gathering, pipeline, decisions) and Thesis-building mode (content consumption, rabbit holes, deep research) feed each other. The AI CoS must bridge them — connecting a USTOL thesis session to a founder who pitches an aviation startup 3 months later.

5. **Judgment stays with Aakash. Everything else is leverage.** The AI CoS never makes investment decisions. It makes Aakash's judgment more effective by ensuring he has the right context at the right time, sees the connections he'd otherwise miss, and spends time on highest-leverage activities.

6. **Gradual trust building.** Start with read-only intelligence (surfacing, connecting, preparing). Earn the right to act (scheduling, messaging, updating) through demonstrated accuracy and value.

---

## TIER 1: COWORK + CLAUDE (10x Leverage)

### What This Tier Can Do

Cowork today has: Notion (full read/write), Gmail (personal), Google Calendar, Granola meeting notes, web search/fetch, Explorium (people + company enrichment), browser automation (Claude in Chrome), Apple Notes, scheduled tasks, and file creation. M365 connector is coming.

The constraint: Cowork is session-based, not always-on. It activates when Aakash opens it or when a scheduled task fires. It cannot live in WhatsApp. It cannot persist memory across sessions without writing to files/Notion. It cannot run continuously in the background.

### Architecture: "The Daily Intelligence Layer"

Despite limitations, Cowork can deliver massive value through three scheduled patterns plus on-demand deep work:

#### 1. Morning Briefing (Scheduled — 7:30 AM daily)

**What it does:** Fires before Aakash's day starts. Reads today's Google Calendar, cross-references every person/company against Notion (Network DB, Companies DB, Portfolio DB), pulls recent Granola meeting notes for any recurring contacts, searches for recent signals (news, funding, social activity via web search + Explorium), and produces a WhatsApp-length intelligence brief.

**Output:** A structured brief saved to a known Notion page (or Apple Note) that Aakash can glance at on his phone. For each meeting:
- Who: name, archetype, last interaction, IDS conviction level
- Context: what was discussed last, any open follow-ups, recent signals
- Prep: what Aakash should know walking in, suggested talking points
- Leverage lens: why this meeting matters right now across his graph of work

**Why it's 10x:** Currently Aakash walks into meetings with whatever he remembers. This gives him total context recall for every interaction, every day, with zero prep effort.

**Cowork implementation:** Scheduled task → reads Google Calendar API → for each attendee, queries Notion Network DB + Companies DB + Granola → runs Explorium enrichment on any new contacts → web searches for recent news → writes output to a fixed Notion page "Daily Brief" or Apple Note.

#### 2. Post-Meeting Processor (On-Demand — triggered after key meetings)

**What it does:** Aakash opens Cowork after a meeting (or batch at end of day). He voice-dumps or types quick notes — raw, unstructured, the way he currently does on WhatsApp or Granola. The AI CoS:
- Parses the raw dump into structured IDS notation (+, ++, ?, ??, etc.)
- Identifies which Notion entities to update (Network DB person, Companies DB company, Portfolio DB entry)
- Drafts the Notion comment/update in Aakash's voice and IDS style
- Identifies follow-up actions (intro to make, document to send, BRC to schedule)
- Detects thesis connections ("this founder's approach reminds me of your USTOL research — the same infrastructure-vs-application question")

**Output:** Draft Notion updates ready for Aakash to approve with one tap. Follow-up tasks queued in Tasks Tracker DB with proper relations to Pipeline and Target Person.

**Why it's 10x:** Currently, meeting insights either go to WhatsApp (get buried), Granola (sometimes appended), or nowhere. This ensures every meeting compounds into IDS with near-zero effort from Aakash.

**Cowork implementation:** Interactive session → Aakash provides raw input → Claude parses using IDS framework knowledge → queries Notion for relevant entities → drafts updates → writes to Notion with Aakash's approval.

#### 3. Weekly Synthesis (Scheduled — Sunday evening)

**What it does:** Reviews all Granola meetings from the past week, all Notion updates made, all Tasks Tracker items, and produces:
- **Network heat map:** Who did Aakash meet? Who hasn't he met that he should have? Where are the gaps?
- **Pipeline movement:** Which companies moved in conviction? Which are stalling? What BRCs are overdue?
- **Thesis threads:** Based on the week's meetings and any research sessions, what thesis threads are active? Any new connections between people and ideas?
- **Follow-up accountability:** What was supposed to happen this week that didn't?
- **Next week optimization:** Given calendar as-is, what's the highest-leverage day? Any meetings that should be deprioritized/rescheduled?

**Why it's 10x:** Currently, the backlog clearing happens mentally on weekends. This makes it systematic and ensures nothing falls through.

#### 4. On-Demand Deep Work Sessions

Beyond scheduled tasks, Cowork excels at on-demand analytical work:

- **Pre-BRC Preparation:** Pull all IDS history on a company, enrich via Explorium, compile scoring framework, draft IDS deck structure
- **Thesis Deep Research:** Replace ChatGPT sessions — Claude has the same deep research capability plus it's connected to Aakash's Notion, so it can automatically link findings to pipeline companies
- **Network Analysis:** "Who in my network has deep experience in pen testing?" → searches Network DB, enriches via Explorium, surfaces unexpected connections
- **Collective Sourcing Support:** When Aakash screengrabs a profile or sends a link, he can paste it into Cowork and get: full enrichment, archetype classification, leverage assessment, recommended approach, and a drafted Notion Network DB entry
- **Portfolio IDS Updates:** Pull latest data on portfolio companies, compare to investor updates, flag discrepancies or concerns

### Tier 1 Limitations (What Cowork Cannot Do)

1. **No WhatsApp presence.** Aakash has to come to Cowork; Cowork can't come to him on WhatsApp. This is the single biggest limitation — the primary interaction surface isn't served.

2. **No persistent background processing.** Between sessions, nothing happens. No real-time signal detection, no proactive alerts, no continuous monitoring.

3. **No M365 integration yet.** Can't read work email threads (where much IDS communication lives) or optimize the work calendar with contextual intelligence.

4. **Session memory limits.** Each Cowork session starts relatively fresh. The iteration logs help, but there's no true persistent memory layer. Long-running IDS compounding requires re-loading context each time.

5. **Browser automation friction on bot-detected platforms.** X and LinkedIn require authenticated sessions and actively block bots. Cowork's browser tools can work but are fragile for these platforms.

6. **No proactive outreach.** Can't send messages, emails, or calendar invites on Aakash's behalf without him being in the session.

### Tier 1 Value Summary

| Capability | Current State | With Cowork | Leverage |
|---|---|---|---|
| Meeting prep | Fuzzy memory | Full context brief | 5-8x |
| Post-meeting capture | WhatsApp dump / nothing | Structured IDS with Notion sync | 8-10x |
| Weekly synthesis | Mental backlog clearing | Systematic review + recommendations | 5x |
| Pre-BRC preparation | Manual Notion diving | Automated compilation + enrichment | 10x |
| Thesis research | ChatGPT (disconnected) | Claude + Notion + pipeline linked | 3-5x |
| Network enrichment | Manual lookups | Explorium + structured profiles | 8x |
| Follow-up tracking | Doesn't exist | Tasks Tracker with accountability | ∞ (from 0) |

**Realistic overall leverage: 5-10x on the activities it touches.** But it only touches ~40% of Aakash's operating surface because it can't be in WhatsApp, can't run persistently, and can't do proactive outreach.

---

## TIER 2: CUSTOM AGENT SDK BUILD (100x+ Leverage)

### The Vision: A Living, Breathing AI Chief of Staff

This isn't a tool Aakash opens. It's an entity that operates alongside him — present in his WhatsApp, monitoring his email, preparing for his meetings, connecting dots across his entire information universe, and acting on his behalf where authorized. It has its own email address, its own cloud infrastructure, and its own persistent memory that compounds over months and years — just like Aakash's own IDS methodology.

### Core Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AAKASH (Human Layer)                   │
│         Primary surfaces: WhatsApp, Phone, In-person     │
└──────────────┬──────────────────────────┬────────────────┘
               │                          │
        ┌──────▼──────┐           ┌───────▼───────┐
        │  WhatsApp    │           │   Voice/SMS    │
        │  Interface   │           │   Interface    │
        └──────┬──────┘           └───────┬───────┘
               │                          │
┌──────────────▼──────────────────────────▼────────────────┐
│                                                           │
│              🧠  ORCHESTRATOR AGENT                       │
│              "The Chief of Staff Brain"                    │
│                                                           │
│   - Receives all inputs, routes to specialist agents      │
│   - Maintains the "What does Aakash need right now?"      │
│     priority model                                        │
│   - Decides when to proactively surface information       │
│   - Manages inter-agent coordination                      │
│   - Holds the unified context of Aakash's full graph      │
│                                                           │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬─────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│SIGNAL││MEET-││NET- ││THESIS││CALEN││PIPE-││PORT- │
│CATCH-││ING  ││WORK ││TRACK-││DAR  ││LINE ││FOLIO │
│ER   ││INTEL││WEAV-││ER    ││INTEL││MGR  ││WATCH │
│     ││     ││ER   ││      ││     ││     ││ER    │
└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────────────────────────────────────────────────────────┐
│                   SHARED INFRASTRUCTURE                    │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Knowledge │  │ M365     │  │ Notion   │  │ Enrichment│ │
│  │ Graph     │  │ (Mail +  │  │ (DBs +   │  │ (Explorium│ │
│  │ (Memory)  │  │ Calendar)│  │ IDS repo)│  │ + Web)    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Browser   │  │ WhatsApp │  │ Granola  │  │ CoS      │ │
│  │ Sessions  │  │ Bridge   │  │ API      │  │ Mailbox  │ │
│  │ (X, LI)  │  │          │  │          │  │          │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────┘
```

### The Seven Specialist Agents

#### Agent 1: Signal Catcher
**Lives in:** WhatsApp, Email inbox, X/LinkedIn (passive monitoring)
**Purpose:** Catches every signal before it evaporates

**How it works:**
- Monitors Aakash's WhatsApp messages (both what he sends to groups and what comes in). When Aakash sends a screengrab to himself or drops a link in his self-channel, Signal Catcher immediately: extracts the content, enriches the person/company via Explorium, classifies it (Collective target? Thesis trigger? Portfolio signal?), and stores it in the Knowledge Graph with full context of when/why it was captured.
- Monitors incoming email (M365) for signals: founder updates, investor reports, intro requests, meeting requests. Classifies by urgency and type.
- Runs scheduled sweeps of X bookmarks and LinkedIn saves (via authenticated browser sessions) to capture the content behind Aakash's fuzzy bookmarks.

**What changes for Aakash:** Instead of screengrabs disappearing into camera roll and WhatsApp links scrolling into oblivion, every signal gets captured, classified, enriched, and connected — automatically. He keeps doing what he does naturally (screengrab, bookmark, forward to self) and the system handles the rest.

**Key capabilities needed:**
- WhatsApp Business API integration or WhatsApp bridge (e.g., via Baileys/whatsapp-web.js)
- M365 Graph API (mail reading)
- Browser sessions with persistent X/LinkedIn auth
- Explorium API for enrichment
- OCR for screengrab text extraction
- Knowledge Graph write access

#### Agent 2: Meeting Intelligence
**Lives in:** Calendar + Granola + CoS Mailbox
**Purpose:** Makes every meeting maximally productive

**Pre-meeting (automated, proactive):**
- 30 minutes before each meeting, assembles a brief and sends it to Aakash via WhatsApp
- Brief includes: person/company IDS history (pulled from Knowledge Graph + Notion), recent signals (from Signal Catcher), any open follow-ups from last interaction, suggested talking points, leverage assessment
- For new contacts: full Explorium enrichment, mutual connections analysis, archetype classification
- For portfolio: latest metrics vs. last update, any concerns flagged by Portfolio Watcher

**During meeting (passive):**
- Granola captures the transcript

**Post-meeting (semi-automated):**
- Reads Granola transcript when it appears
- Drafts structured IDS notes in Aakash's notation style (+, ++, ?, ??)
- Identifies follow-up commitments (both from Aakash and from the other party)
- Proposes Notion updates (Companies DB conviction changes, Network DB notes, Portfolio DB updates)
- Sends summary to Aakash on WhatsApp: "Just processed your meeting with [X]. Here's what I captured: [summary]. Shall I update Notion and create follow-ups?"
- Aakash replies "yes" or edits → agent executes

**What changes for Aakash:** Walking into every meeting with full context (currently fuzzy recall). Walking out of every meeting with structured IDS capture (currently sporadic Granola appending or nothing). Follow-ups never get lost.

#### Agent 3: Network Weaver
**Lives in:** Knowledge Graph + Notion Network DB
**Purpose:** Maintains and activates the relationship graph

**Continuous functions:**
- Maintains a living network graph connecting every person Aakash knows to: their companies, their capabilities, their archetype, their thesis relevance, their network connections, and Aakash's current relationship temperature
- Detects dormant high-value relationships: "You haven't spoken to [X] in 4 months. They're in [Y] sector which is relevant to [Z] thesis you've been building. They also know [founder] in your pipeline."
- When Aakash meets someone new, Network Weaver maps them into the graph, identifies all connections to existing nodes, and surfaces opportunities: "This person overlaps with your Collective criteria. They know 3 founders in your pipeline."
- Manages the Collective funnel: tracks outreach status, response rates, engagement progression

**Proactive surfacing:** Sends weekly "Network Pulse" to WhatsApp — relationships that need attention, high-leverage connections to make, introductions that would create value.

**What changes for Aakash:** The "dot connection problem" (which he said happens all the time but is hard to recall specifics) gets solved. The network stops being a fuzzy mental map and becomes a living, queryable intelligence layer.

#### Agent 4: Thesis Tracker
**Lives in:** Knowledge Graph + Web + Content platforms
**Purpose:** Captures, compounds, and connects thesis development

**How it works:**
- When Aakash does a deep research session (now on Claude instead of ChatGPT), Thesis Tracker stores the entire session as a thesis node in the Knowledge Graph, tagged with: topic, domain, key entities mentioned, conclusions, and open questions
- Monitors Aakash's content consumption signals (YouTube watch list API, X bookmarks, LinkedIn saves, Substack reads) and maps them to thesis threads
- Detects when multiple signals converge on a thesis: "You've bookmarked 3 articles on agentic infrastructure this week, had a meeting with [founder] in this space, and your research session on Composio vs Smithery is related. Your active thesis threads: [list]"
- When a new company enters the pipeline, automatically checks against all thesis threads: "This company is directly relevant to your harness-layer thesis from June 2025"
- Maintains a living "Thesis Map" — visual or queryable — of Aakash's intellectual landscape

**What changes for Aakash:** The thesis → investment pipeline gap gets bridged. Research sessions stop being isolated conversations and become a compounding knowledge base that automatically connects to deal flow.

#### Agent 5: Calendar Intelligence
**Lives in:** M365 Calendar + Google Calendar
**Purpose:** Injects intelligence into scheduling

**How it works:**
- Receives all scheduling requests (from Sneha, from direct emails, from WhatsApp)
- Before slotting a meeting, evaluates: Who is this person? What's the urgency? What's the leverage? What's the optimal clustering with other meetings? What prep time is needed?
- Proposes scheduling to Aakash (via WhatsApp): "Sneha got a request from [X] for a meeting. They're a [archetype], relevant to your [thesis/pipeline item]. Suggest: [slot] with [prep brief attached]. Approve?"
- Handles rescheduling: when a higher-leverage meeting needs to slot in, identifies what can be moved
- Protects deep work / thesis time: blocks time for research sessions, content consumption, thinking
- Weekly calendar review: "Next week looks like [X]. Your highest-leverage meetings are [Y]. You have no time blocked for thesis work. Suggest moving [Z]?"

**What changes for Aakash:** Sneha currently slots meetings without contextual intelligence. Calendar Intelligence becomes the brain behind scheduling — every meeting placement is optimized for leverage, context, and Aakash's energy/focus patterns.

#### Agent 6: Pipeline Manager
**Lives in:** Notion Companies DB + Tasks Tracker + CoS Mailbox
**Purpose:** Manages deal flow with zero manual overhead

**How it works:**
- Tracks every company in the pipeline across all stages (TOFU → MOFU → BOFU)
- For Collective sourcing: when Signal Catcher identifies a potential Collective target, Pipeline Manager creates the initial Network DB entry, sets up the outreach cadence, and tracks responses
- For deal flow: monitors conviction levels, flags when companies have been in "Maybe" too long, tracks when BRCs are due, ensures IDS deck preparation happens on schedule
- Manages the team: coordinates with DeVC team members (DT, AP, Ashwini etc.) by assigning tasks in Tasks Tracker DB and following up
- Follow-on monitoring: tracks portfolio companies against the follow-on evaluation lens (Founder MPI gate → Traction → TAM), flags when conditions are met for follow-on conversations
- Has its own email address (cos@[domain].com): can send and receive correspondence on Aakash's behalf (with approval). Handles logistics like "Send [founder] the term sheet" or "Request latest metrics from [portfolio company]"

**What changes for Aakash:** Currently, follow-up is the biggest gap. Pipeline Manager ensures nothing stalls, every commitment gets tracked, and the team stays coordinated — all without Aakash manually updating Notion or chasing threads.

#### Agent 7: Portfolio Watcher
**Lives in:** Notion Portfolio DB + Company data sources + Web monitoring
**Purpose:** Continuous IDS on portfolio companies

**How it works:**
- Monitors all portfolio companies for signals: press mentions, competitor movements, hiring patterns (Explorium workforce trends), social activity, web changes
- Reads investor updates when they come in (via M365 email or direct share), extracts key metrics, compares to previous period, flags anomalies
- Runs the portfolio checkin framework automatically: prepares "state of [company]" briefs before checkin calls
- Detects problems early: "Revenue growth decelerated by [X]%, hiring in engineering dropped [Y]%, competitor [Z] just raised $[N]M"
- Detects opportunities: "Portfolio company [A] is working on [X], which connects to portfolio company [B]'s need for [Y]. Introduction opportunity?"
- Surfaces the "founder ranking" question proactively: based on interactions and data, prompts Aakash to reassess conviction

**What changes for Aakash:** Portfolio IDS becomes truly continuous and data-driven instead of meeting-dependent. Problems get caught earlier. Opportunities between portfolio companies get surfaced.

### The Orchestrator: Tying It All Together

The Orchestrator is the most critical piece. It's not another specialist — it's the brain that:

1. **Manages attention:** Aakash gets dozens of signals per day. The Orchestrator decides what rises to his WhatsApp with a proactive message vs. what gets stored silently for later. The filter is: "Does Aakash need to know this NOW, or can it wait?" This requires a sophisticated model of Aakash's current priorities, calendar, and cognitive load.

2. **Routes inputs:** When Aakash sends a message to the AI CoS WhatsApp ("just met [X], really sharp, thinks AI infrastructure will be verticalized"), the Orchestrator parses intent and routes to the right agents: Signal Catcher (capture), Meeting Intelligence (if there was a formal meeting), Network Weaver (classify and connect), Thesis Tracker (the "verticalized AI infrastructure" claim), and Pipeline Manager (if [X] is a founder or Collective target).

3. **Connects dots across agents:** This is the highest-value function. When Thesis Tracker identifies a pattern, Orchestrator checks against Pipeline Manager's deal flow. When Network Weaver surfaces a dormant relationship, Orchestrator checks Calendar Intelligence for optimal timing. When Portfolio Watcher flags a concern, Orchestrator checks Meeting Intelligence for when the founder was last engaged.

4. **Learns Aakash's patterns:** Over time, the Orchestrator builds a model of: what Aakash acts on, what he ignores, what timing works, what format he prefers, what triggers him to say "this is exactly what I needed." This is IDS on Aakash himself.

### Shared Infrastructure

#### Knowledge Graph (The Persistent Memory Layer)

This is the single most important technical component. It's a graph database (Neo4j or similar) that stores:

- **People nodes:** Every person Aakash has interacted with, enriched and continuously updated. Properties: archetype, conviction, relationship temperature, thesis relevance, IDS history.
- **Company nodes:** Every company encountered, with pipeline status, scoring, IDS trail.
- **Thesis nodes:** Every thesis thread, with evidence (research sessions, articles, meetings that contributed), conviction level, and connected entities.
- **Interaction nodes:** Every meeting, email, WhatsApp exchange, tagged with signals extracted.
- **Signal nodes:** Every captured signal (screengrab, bookmark, link, mention), classified and connected.

Edges connect everything: Person → Works at → Company. Company → Relevant to → Thesis. Meeting → Produced signal → Signal → Connects to → Thesis. Person → Introduced by → Person.

The Knowledge Graph IS the AI CoS's memory. It persists across all sessions, compounds over time, and becomes more valuable the longer it runs — exactly like Aakash's own IDS methodology, but externalized and queryable.

#### M365 Integration (Microsoft Graph API)
- Read/write email
- Read/write calendar
- Search across mailboxes
- Monitor incoming mail in real-time via webhooks

#### WhatsApp Bridge
- Send/receive messages as the AI CoS
- Monitor specific groups (DeVC, Z47) for signals
- Handle Aakash's self-channel captures
- Options: WhatsApp Business API (official, limited), or bridge libraries (whatsapp-web.js/Baileys — more capable but requires careful session management)

#### Authenticated Browser Sessions
- Persistent login sessions for X and LinkedIn
- Scheduled content sweeps (bookmarks, saves, watch lists)
- Profile enrichment where Explorium doesn't have data
- Run in headless containers with anti-detection measures

#### CoS Mailbox
- Dedicated email address for the AI CoS
- Can send/receive correspondence on Aakash's behalf
- Handles logistics, data requests, scheduling correspondence
- Always operates under Aakash's authorization model

#### Cloud Infrastructure
- Kubernetes cluster or equivalent running all agent containers
- Message queue (Redis/RabbitMQ) for inter-agent communication
- Vector database (Pinecone/Weaviate) for semantic search across all captured content
- The Knowledge Graph database
- Monitoring and alerting
- Cost management (Claude API calls are the primary ongoing cost)

### The Interaction Model

The key insight: the AI CoS communicates with Aakash primarily through WhatsApp, using a carefully designed interaction language:

**Proactive messages (from AI CoS to Aakash):**
```
🔵 Pre-Meeting Brief
Meeting with [Name] in 30min
Last met: [date] — discussed [topic]
IDS: [current conviction notation]
Key context: [2-3 bullets]
Open follow-ups: [list]
Suggested asks: [2-3 items]
```

```
🟢 Signal Captured
[Person/Company] — [signal type]
[1-line summary]
Connected to: [thesis/pipeline item]
Action needed? [Y/N suggestion]
```

```
🟡 Follow-Up Due
[Task] for [Person/Company]
Originally committed: [date]
Context: [1-line]
[Reply "done", "defer", or "drop"]
```

```
🔴 Alert
[Urgent signal about portfolio company or high-priority item]
[Context]
[Suggested action]
```

**Aakash's inputs (to AI CoS on WhatsApp):**
- Quick voice note after a meeting → transcribed, processed by Meeting Intelligence
- Screenshot of a profile/post → captured and enriched by Signal Catcher
- Forward of a link → captured, classified, connected by Thesis Tracker
- Short text command: "prep me for [meeting/company]" → full brief generated
- Question: "who in my network knows [topic/company]?" → Network Weaver responds
- Approval: "yes" / "approved" / "go ahead" → executes proposed action

The conversation should feel like texting an exceptionally well-prepared, always-available chief of staff.

---

## BRIDGING THE TWO TIERS: A Phased Approach

### Phase 0: Cowork Foundation (Weeks 1-4) — WE ARE HERE
Complete the understanding phase. Build the first Cowork scheduled tasks:
- Morning Briefing (Google Calendar + Notion + Granola → daily brief)
- Post-Meeting Processor (structured IDS capture from raw notes)
- Weekly Synthesis (review and prioritize)
- Thesis Research sessions migrated from ChatGPT to Claude

**Value delivered:** 5-10x on meeting prep, IDS capture, and follow-up tracking.

### Phase 1: Agent SDK Foundation (Weeks 4-8)
Build the core infrastructure:
- Knowledge Graph setup and initial data load (import from Notion)
- M365 integration (email reading + calendar)
- Claude Agent SDK scaffolding — Orchestrator + 2 initial agents
- First agents: Signal Catcher (email monitoring only) + Meeting Intelligence (calendar-triggered briefs)

**Value delivered:** Automated meeting briefs via M365, email signal capture.

### Phase 2: WhatsApp Interface (Weeks 8-12)
The biggest unlock:
- WhatsApp bridge integration
- Signal Catcher expanded to WhatsApp monitoring
- Two-way WhatsApp interaction with AI CoS
- Screengrab processing (OCR + enrichment)
- Meeting Intelligence sends briefs via WhatsApp

**Value delivered:** The AI CoS meets Aakash where he lives. Signal capture becomes zero-friction.

### Phase 3: Full Agent Deployment (Weeks 12-20)
Roll out remaining specialist agents:
- Network Weaver (relationship graph, dormant relationship detection, Collective funnel)
- Calendar Intelligence (scheduling optimization, Sneha augmentation)
- Pipeline Manager (deal flow tracking, team task management)
- Thesis Tracker (content consumption monitoring, thesis-to-pipeline linking)
- Portfolio Watcher (continuous portfolio IDS)

**Value delivered:** The full 100x vision starts operating.

### Phase 4: Compounding Intelligence (Ongoing)
The Knowledge Graph grows. The Orchestrator learns Aakash's patterns. The system gets better at predicting what he needs, when he needs it, and what connections matter. This is where the 100x becomes 1000x over time — the AI CoS develops its own IDS on Aakash's operating patterns and continuously optimizes.

---

## Critical Technical Decisions

### 1. WhatsApp Integration Method
- **WhatsApp Business API (official):** Reliable, sanctioned, but limited (can't monitor personal groups, templates required for outbound, business account needed). Better for CoS → Aakash messaging.
- **WhatsApp Web bridge (whatsapp-web.js / Baileys):** Full capability (read groups, monitor self-channel, no template restrictions), but unofficial, requires active phone session, risk of account ban if not careful.
- **Recommendation:** Start with WhatsApp Business API for CoS outbound messages. Use bridge carefully for inbound signal monitoring from personal account. Hybrid approach.

### 2. Knowledge Graph vs. Vector DB vs. Both
- Knowledge Graph (Neo4j): Best for relationship queries ("who knows who that knows about X"), structured entity relationships, IDS history traversal
- Vector DB (Pinecone/Weaviate): Best for semantic search ("find everything related to agentic infrastructure"), content similarity, fuzzy recall
- **Recommendation:** Both. Knowledge Graph for the structured entity layer. Vector DB for the semantic search layer. They serve different query patterns and both are essential.

### 3. Agent Framework
- Claude Agent SDK provides the foundation for building each specialist agent
- Each agent runs as a persistent process in its own container
- Inter-agent communication via message queue (not direct API calls)
- Orchestrator manages routing, prioritization, and coordination
- All agents share access to Knowledge Graph, but own their specialist domains

### 4. Privacy and Authorization Model
- Tiered authorization: Read (default) → Suggest (propose actions) → Act (execute with approval) → Auto-act (execute without approval, earned over time)
- All outbound communications require explicit approval initially
- Approval can be granted by category ("auto-approve follow-up reminders")
- Full audit trail of every action taken
- Aakash can revoke auto-act permissions at any time

---

## What 100x+ Actually Looks Like

A day in Aakash's life with the full AI CoS:

**7:30 AM:** WhatsApp message from AI CoS: morning brief with all 8 meetings contextualized, top 3 follow-ups due today, one thesis connection surfaced overnight ("The pen testing company from your pipeline had a competitor raise $30M yesterday").

**8:45 AM:** Before first meeting, another WhatsApp: full brief on the founder he's about to meet, including Explorium enrichment, mutual connections, and a note: "This founder's approach to vertical AI connects to your harness-layer thesis."

**9:30 AM:** Meeting ends. Aakash voice-notes to AI CoS: "Good meeting, sharp founder. Strong on product, questions on go-to-market. Follow up on customer references. ++product, ?gtm." AI CoS responds: "Captured. I've drafted a Notion update and created a follow-up task for customer references. The Confido Health approach to channel partners might be relevant here — want me to pull that playbook? Approve Notion update?"

**11:00 AM:** Aakash screengrabs a LinkedIn post from someone with interesting security thesis views. Sends to AI CoS on WhatsApp. AI CoS: "Got it. This is [Name], [Title] at [Company]. Enriched via Explorium: [key details]. They match your Collective criteria — strong cybersecurity evaluator. I've added them to Network DB as EXT Target and flagged for outreach. They also follow [mutual connection]. Want me to draft an approach message?"

**2:00 PM:** AI CoS proactive: "Reminder: BRC for [Company] is scheduled for next week. IC process v1.1 says IDS deck needed 48-72hrs prior. I've compiled a draft based on all IDS history. [Link]. Review when you get a chance."

**5:30 PM:** End of day WhatsApp from AI CoS: "Today's capture: 4 meetings processed, 2 signals enriched, 1 pipeline company moved from Maybe to Maybe+, 3 follow-ups completed, 2 new. Your thesis on [topic] has 3 new data points. Tomorrow: 6 meetings, starting with [X] who's critical for [Y]."

**Sunday evening:** Weekly synthesis arrives. Network heat map, pipeline movement, thesis threads, follow-up accountability, next week optimization. Aakash reviews in 10 minutes instead of spending 2 hours clearing mental backlogs.

**Over months:** The Knowledge Graph has processed 1000+ meetings, 5000+ signals, connected 50+ thesis threads to pipeline companies, caught 3 portfolio problems early, surfaced 10 introductions Aakash wouldn't have thought to make, and saved ~20 hours per week of mental overhead. The system knows Aakash's patterns well enough to anticipate what he needs before he asks.

That's what 100x looks like. Not just doing the same things faster — fundamentally changing the information architecture around how one of the most network-dense operating models in venture capital actually works.
