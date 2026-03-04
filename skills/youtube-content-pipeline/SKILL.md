---
name: youtube-content-pipeline
description: "Process content queue — analyze YouTube transcripts with deep portfolio context using parallel subagents, generate rich PDF digests, connect to thesis/portfolio/deals, propose intelligent actions. Trigger: 'process my content queue', 'process my YouTube queue', or 'process my videos'"
---

# YouTube Content Pipeline v4 — Cowork Processing Skill

You are processing Aakash Kumar's YouTube content queue. This is Part 2 of the two-part YouTube Content Pipeline for the AI CoS system.

**Core principles:**
1. **AI strategist, not keyword matcher.** Every analysis must be informed by deep portfolio/thesis context.
2. **Content consumption engine.** Aakash may NOT have watched these videos. The digest must be rich enough to (a) decide what to watch, (b) absorb key ideas without watching, and (c) know exactly which sections to watch for nuance.
3. **Rabbit hole discovery machine.** Aakash is a content-consumption-led thinker. Surface net new threads alongside reinforcing/contra signals to existing threads.
4. **Rich delivery, not wall-of-text.** Every video ≥10 min gets a rich PDF digest. The chat experience leads with scannable summaries and PDF links, not raw analysis dumps.
5. **Context-efficient.** Parallel subagents prevent context window bloat. Each video gets its own full-context subagent.

## Architecture Recap
- **Part 1 (Mac):** `youtube_extractor.py` runs on Aakash's Mac, fetches playlist metadata + transcripts, saves JSON to `Aakash AI CoS/queue/`
- **Part 2 (Cowork — THIS):** Orchestrator loads queue + builds shared context → spawns parallel subagents (one per video, each with full context window) → collects results → generates PDF digests → writes to Notion → presents interactive review → accept/dismiss loop

### v4 Architecture: Orchestrator + Subagent Pattern

```
ORCHESTRATOR (this main agent)
├── Step 1: Load queue
├── Step 2: Build shared context (Portfolio, Thesis, Pipeline, Previous Digests)
│   ↓ context package (~5-15KB compressed per video)
├── Step 3: PARALLEL SUBAGENTS (one Task per video)
│   ├── Subagent A: Video 1 analysis (full v3 protocol) → returns JSON
│   ├── Subagent B: Video 2 analysis (full v3 protocol) → returns JSON
│   └── Subagent C: Video 3 analysis (full v3 protocol) → returns JSON
├── Step 4: Collect results + generate PDF digests
├── Step 5: Write to Notion (Content Digest DB + Actions Queue)
├── Step 6: Present interactive review (PDF links + scannable summary + actions)
├── Step 7: Process accept/dismiss → update Notion + Thesis Tracker
└── Step 8: Mark queue processed
```

**Why subagents:** Each video transcript can be 10-50K tokens. Loading 3+ transcripts plus full portfolio context into one agent hits context limits fast. Subagents each get their own full context window with just the transcript + relevant portfolio context — no bleed between videos.

## Step-by-Step Execution

### Step 1: Load the Queue
Read all `youtube_extract_*.json` files from the queue directory under `Aakash AI CoS/queue/`.

If the queue is empty, tell Aakash:
> "No videos in the queue. Run the extractor on your Mac first:
> `cd ~/Documents/Aakash\ AI\ CoS/scripts && python3 youtube_extractor.py <PLAYLIST_URL>`"

### Step 2: Build Company Context Profiles

**This is the intelligence foundation.** Before analyzing any content, build a rich context profile for every Fund Priority portfolio company. This profile is what enables strategist-level analysis.

#### 2a. Pull Portfolio DB Data
Query **Portfolio DB** (data source: `4dba9b7f-e623-41a5-9cb7-2af5976280ee`) for all Fund Priority companies.

For each company, extract ALL available fields:
- **Identity:** Company Name, Sector, Current Stage
- **Investment State:** Health (Green/Yellow/Red), EF/EO classification, HC Priority, Entry Cheque, Money In
- **Decision Context:** Follow-on Decision, Key Questions, IDS Trail notes
- **Relationships:** Key people connected to this company (founders, co-investors, board members)

#### 2b. Load Deep Research Enrichment
For each Fund Priority company, load the corresponding enrichment file from `portfolio-research/[company-slug].md`. These files (11-18KB each) contain competitive landscape, traction, funding history, risks, team, market dynamics, and strategic opportunities.

**File mapping** (company name → slug):
- Confido Health → confido-health
- CodeAnt → codeant-ai
- GameRamp → gameramp
- PowerUp → powerup
- Terractive → terractive
- Unifize → unifize
- Orange Slice → orange-slice
- Dodo Payments → dodo-payments
- Boba Bhai → boba-bhai
- Inspecity → inspecity
- Atica → atica
- Ballisto AgriTech → ballisto-agritech
- Isler → isler
- Legend of Toys → legend-of-toys
- Highperformr AI → highperformr-ai
- Smallest AI → smallest-ai
- Step Security → step-security
- Terafac → terafac
- Cybrilla → cybrilla
- Stance Health → stance-health

#### 2c. Synthesize Per-Company Context Blocks
For each company, synthesize a context block:

```
COMPANY: [Name]
SECTOR: [sector] | STAGE: [stage] | HEALTH: [health]
MONEY IN: [amount] | HC PRIORITY: [priority]
FOLLOW-ON: [decision status]

KEY QUESTIONS (what would move conviction):
- [from Portfolio DB Key Questions field]
- [from enrichment: identified risks and open questions]

COMPETITIVE DYNAMICS:
- [key competitors from enrichment]
- [moat / differentiation]
- [market position]

CURRENT TRACTION:
- [growth metrics from enrichment]
- [key milestones]

KEY RISKS:
- [from enrichment]
- [from Portfolio DB health indicators]

KEY PEOPLE:
- [founders, key execs from enrichment]
- [co-investors, board members from Portfolio DB relations]

THESIS CONNECTIONS:
- [which of Aakash's thesis threads this company relates to]
```

#### 2d. Pull Thesis Tracker Context
Query **Thesis Tracker** (data source: `3c8d1a34-e723-4fb1-be28-727777c22ec6`):
- All threads with Status = Active or Exploring
- Extract: Thread Name, Core Thesis, Key Companies, Key People, Connected Buckets, Key Question, Conviction Level
- **⚠️ BUILD A THREAD NAME → PAGE ID MAP** — Store each thread's page ID. You'll need this in Step 5b to set the `Thesis` relation on routed actions.

#### 2e. Pull Companies DB Context
Query **Companies DB** (data source: `1edda9cc-df8b-41e1-9c08-22971495aa43`):
- Recent/active pipeline entries
- Extract: Company names, status, sector, stage

#### 2f. Pull Previous Content Digests (Net Newness Baseline)
Query **Content Digest DB** (data source: `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`):
- Last 20-30 entries (or last 2 weeks)
- Extract: Video Title, Key Insights, Thesis Connections, Rabbit Holes
- This gives the "already encountered" baseline for net newness scoring

#### 2g. Context Accumulation (Future-Proofing)
The company context profile is a **layer cake** — each source adds depth:

| Layer | Source | Status | What it adds |
|-------|--------|--------|-------------|
| Base | Portfolio DB (Notion) | ✅ Live | Investment state, decisions, relationships |
| Depth | Deep Research Enrichment (files) | ✅ Available | Competitive landscape, traction, risks, team |
| History | Previous Content Digests | ✅ Live | What Aakash has already consumed, net newness baseline |
| Conviction | Structured Interviews | 🔜 Planned | Investor-specific conviction, key questions, gut feel |
| Real-time | Email/Messaging access | 🔜 Future | Recent founder interactions, support requests |
| Signal | Meeting notes (Granola) | 🔜 Future | What was discussed, commitments made |

---

### Step 3: Dispatch Parallel Subagents (One Per Video)

For each video with a transcript, spawn a **Task subagent** using `subagent_type: "general-purpose"`. Each subagent runs the full v3 analysis protocol independently with its own context window.

**Orchestrator responsibilities:**
1. Build the subagent prompt for each video (template at bottom of this file)
2. Include in each prompt: video metadata + full transcript + relevant company context blocks + thesis threads + previous digest summaries
3. **Launch ALL subagents in parallel** (use multiple Task tool calls in a single message)
4. Collect JSON results from each subagent
5. Do NOT include other videos' transcripts — each subagent only needs its own video

**Context budget per subagent (~15-25KB text):**
- Video transcript: 5-50KB (the big variable)
- Relevant company context blocks: 2-5KB (only companies likely relevant, not all 20)
- Thesis threads summary: 1-2KB
- Previous digest summaries: 1-2KB
- Prompt template + instructions: 3KB

**Selective company loading:** Before dispatching subagents, do a QUICK pre-scan of each transcript for sector keywords, company names, and topic signals. Only include company context blocks for companies that might be relevant (usually 3-8 out of 20). This keeps each subagent's context lean.

**Subagent output:** Each subagent returns a structured JSON object with ALL v3 fields. The orchestrator collects these and proceeds to Step 4.

---

## v3 Analysis Protocol (executed by each subagent)

The following sections (3a through 3k) define what each subagent must produce. The subagent prompt template at the bottom of this file includes all of these as required output sections.

---

#### 3a. Timestamped Topic Map 🆕

Break down the entire transcript into a topic map with timestamps. This is the table of contents for the video.

**How to generate:**
1. Read through the transcript chronologically
2. Identify topic shifts — when the conversation moves to a meaningfully different subject
3. For each topic segment, record: start timestamp, topic title (concise, descriptive), 1-2 sentence description of what's discussed
4. Aim for 8-15 topics for a 60-90 min video (fewer for shorter)

**Output format:**
```
00:00 — Introduction & Context Setting
Brief description of opening framing.

04:30 — [Topic Title]
What's discussed in this segment, key claims made.

12:15 — [Topic Title]
...
```

**Quality bar:** Topic titles should be specific enough that Aakash can scan and immediately know "I need to hear this" or "I know this already." Bad: "AI Discussion." Good: "Why vertical AI agents will beat horizontal platforms in healthcare."

---

#### 3b. Net Newness Assessment 🆕

Score how NEW this content is relative to Aakash's existing knowledge base (thesis threads, previous content digests, portfolio context).

**Net Newness Categories:**
- **Mostly New** — Majority of ideas/frameworks/data are things Aakash hasn't encountered. New rabbit hole territory.
- **Additive** — Builds meaningfully on existing threads with new evidence, angles, or data points. Deepens existing rabbit holes.
- **Reinforcing** — Confirms existing positions with similar arguments. Low marginal info value, but useful as social proof / conviction data.
- **Contra** — Challenges current thesis positions, portfolio assumptions, or commonly held views in Aakash's investment thesis. HIGH value — requires attention.
- **Mixed** — Contains both reinforcing and genuinely new/contra elements (most common for long-form content).

**Assessment method:**
1. Compare video's key themes against active thesis threads in Thesis Tracker
2. Compare against previous Content Digest key insights and rabbit holes
3. Check if the specific data points, frameworks, or perspectives have appeared before
4. Weight toward "new" when in doubt — Aakash prefers to be shown too much than miss something

---

#### 3c. Contra Signals Detection 🆕

Explicitly identify anything in the content that challenges:
1. **Active thesis positions** — "Your agentic AI thesis assumes X, but this speaker presents evidence for Y"
2. **Portfolio company assumptions** — "Content suggests [market trend] that would undermine [company]'s moat"
3. **Investment heuristics** — "Speaker argues against [pattern] that Aakash uses in deal evaluation"
4. **Commonly held VC views** — "Contra to the consensus view that [X], this speaker argues [Y] because [Z]"

**Output format per contra signal:**
```
CONTRA: [What it challenges]
EVIDENCE: [The specific argument/data from the content]
STRENGTH: Strong / Moderate / Weak
IMPLICATION: [What Aakash should think about or investigate]
```

Even if the content is broadly aligned with Aakash's views, actively look for contra signals. If genuinely none exist, say so explicitly — don't leave it blank.

---

#### 3d. Watch These Sections 🆕

Curate the 3-7 most valuable sections of the video for Aakash to watch himself. These are sections where the NUANCE matters — where reading a summary loses essential texture.

**Selection criteria (pick sections where):**
- The speaker makes a counterintuitive argument that needs to be heard in their own words
- Data or frameworks are presented that are better absorbed visually/aurally
- The discussion gets into tactical nuance relevant to a portfolio company
- A debate or disagreement happens between speakers that reveals important tensions
- The speaker describes personal experience that adds conviction beyond the argument itself
- The section relates to an active IDS thread or key question

**Output format:**
```
⭐ [Timestamp range] — [Section title]
WHY WATCH: [1-2 sentences on why Aakash should hear this himself, not just read a summary]
CONNECTS TO: [thesis thread / portfolio company / bucket]
```

**Quality bar:** "Why Watch" must be specific. Bad: "Interesting discussion about AI." Good: "Sebastian argues that Klarna's approach to replacing SaaS with AI agents is fundamentally different from what incumbents can copy — if true, this validates the SaaS death thesis and has direct implications for Unifize's competitive position."

---

#### 3e. Rabbit Holes 🆕

Identify genuinely NET NEW threads that Aakash hasn't explored yet. These are potential new thesis threads, new sectors, new patterns, or new mental models that the content introduces.

**What qualifies as a rabbit hole:**
- A sector or market dynamic not currently in the Thesis Tracker
- A framework or mental model that could change how Aakash evaluates deals
- A person, company, or ecosystem that Aakash should learn more about
- A counter-narrative that's worth investigating independently
- A data point or trend that, if true, would change investment decisions

**What does NOT qualify:**
- Something Aakash already has a thesis thread on (that's Additive, not a rabbit hole)
- General knowledge or well-known industry trends
- Vague "AI will change everything" type observations

**Output format:**
```
🕳️ [Rabbit Hole Title]
WHAT: [1-2 sentence description of the new thread]
WHY IT MATTERS: [Connection to Aakash's investing, even if indirect]
ENTRY POINT: [Specific thing to read/watch/investigate to go deeper]
NEWNESS: Completely new / Tangentially connected to [existing thread]
```

---

#### 3f. Essence Notes 🆕

Capture the irreducible core of the content — the arguments, frameworks, data points, and quotes that make this content worth having consumed. This is what Aakash should be able to reference months later.

**What to capture:**
- **Core arguments** — The 2-3 central claims, stated precisely (not just "AI will replace SaaS" but the specific mechanism and evidence)
- **Key frameworks** — Any mental models or analytical frameworks introduced
- **Data points** — Specific numbers, metrics, case studies that serve as evidence
- **Memorable quotes** — The 1-2 lines that capture the speaker's key insight in their own words (with timestamps)
- **Predictions / bets** — Specific claims about the future that can be tracked

**Output format:**
```
CORE ARGUMENT: [precise statement of the central thesis]
EVIDENCE: [key supporting data/examples]
FRAMEWORK: [any new mental model introduced]
KEY QUOTE: "[quote]" — [Speaker], [timestamp]
PREDICTION: [specific falsifiable claim about the future]
```

Keep essence notes tight — this should be scannable in 30 seconds and contain the payload of a 60-90 minute video.

---

#### 3g. Content Summary & Extraction (from v2)
- Generate a 3-5 sentence summary focusing on investing/venture relevance
- Extract 3-5 specific, actionable insights (claims, data points, perspectives)
- Classify Content Type: Podcast, Interview, Lecture, Panel, News Analysis, Deep Dive, Other

#### 3h. Semantic Portfolio Matching (from v2 — NOT just name matching)
For each piece of content, check for connections to portfolio companies using BOTH:

1. **Direct mentions:** Company name, founder name, product name explicitly mentioned
2. **Semantic connections:** Content discusses topics, markets, competitors, or dynamics relevant to a portfolio company even if never named

For each matched company, generate a CONTEXTUAL relevance assessment:
- What specific aspect of the content is relevant?
- How does it relate to the company's Key Questions?
- Does it validate or challenge the current thesis on this company?
- Does it reveal competitive dynamics?
- Does it affect follow-on conviction?
- Is there a time-sensitive element?

#### 3i. Thesis Connection Analysis (from v2)
Compare video content against active thesis threads. For each match:
- Name the thesis thread
- Explain the connection (evidence for, evidence against, or new angle)
- Rate strength: Strong / Moderate / Tangential
- Note if the content suggests a NEW thesis thread

#### 3j. Generate Portfolio Actions (from v2)
For each portfolio company connection, generate specific contextual actions using the action generation framework:

1. Does this content answer or inform a Key Question? → Research / Thesis Update
2. Does it reveal competitive intelligence? → Portfolio Check-in / Meeting
3. Does it affect follow-on conviction? → Follow-on Eval
4. Does it suggest a founder should know something? → Meeting/Outreach
5. Does it flag a risk? → Portfolio Check-in
6. Does it validate a thesis connection? → Thesis Update
7. Does it suggest an intro or network action? → Meeting/Outreach

**Priority assignment:**
- **P0 - Act Now:** Time-sensitive competitive intel, direct risk flag, follow-on decision input
- **P1 - This Week:** Key Question answered, founder needs to know something actionable
- **P2 - This Month:** Thesis validation/evolution, general competitive context
- **P3 - Backlog:** Background intelligence, nice-to-have connections

#### 3k. Generate Thesis & Network Actions (from v2)
- Thesis updates and new thesis signals
- Network outreach, pipeline checks, intros

---

### Step 4: Generate PDF Digests

For each video with duration ≥10 minutes, generate a rich PDF digest using `scripts/content_digest_pdf.py`.

**How to generate:**
```python
import sys
sys.path.insert(0, '/path/to/Aakash AI CoS/scripts')
from content_digest_pdf import generate_digest_pdf

# analysis_data is the structured dict returned by the subagent
# (see Subagent Output Format section at bottom)
output_path = f'/path/to/Aakash AI CoS/digests/digest_{safe_title}.pdf'
generate_digest_pdf(analysis_data, output_path)
```

**Directory:** Save PDFs to `Aakash AI CoS/digests/` (create if needed). Also copy to the workspace output folder for immediate user access.

**For videos <10 minutes:** Skip PDF generation. These get a compact inline summary in the chat review only.

**The PDF includes:** Title + At-a-Glance badges → Essence Notes → Summary + Key Insights → Watch These Sections → Topic Map → Contra Signals → Rabbit Holes → Portfolio/Thesis Connections → Proposed Actions by priority → Source URL.

### Step 4b: Publish HTML Digest to Vercel

For each video with duration ≥10 minutes (same threshold as PDF), ALSO publish an HTML digest.

**How to publish:**
```python
import sys
sys.path.insert(0, '/path/to/Aakash AI CoS/scripts')
from publish_digest import publish_digest

# analysis_data is the SAME structured dict used for PDF generation
# It MUST contain a 'slug' field (kebab-case, e.g., "cursor-is-obsolete")
result = publish_digest(analysis_data)
# result = { 'json_path': '...', 'url': 'https://aicos-digests.vercel.app/d/slug', 'pushed': True/False }
```

**What this does:**
1. Saves the analysis JSON to `aicos-digests/src/data/{slug}.json`
2. Git commits + pushes → Vercel auto-deploys in ~30s
3. Returns the live URL for sharing on WhatsApp

**Slug generation:** If the analysis dict doesn't have a `slug` field, add one before calling:
```python
# Generate slug from title
slug = title.lower().replace("—", "").replace(":", "").replace(",", "")
slug = "-".join(slug.split())[:60]
analysis_data["slug"] = slug
```

**After publishing:** Include the Vercel URL in the chat summary for each video:
- `📄 PDF: [link to local PDF]`
- `🌐 HTML: https://aicos-digests.vercel.app/d/{slug}` (shareable on WhatsApp)

**If git push fails (e.g., in Cowork sandbox):** The JSON is still saved locally. Tell the user to run from Mac terminal:
```bash
cd ~/Claude\ Projects/Aakash\ AI\ CoS/aicos-digests && git add -A && git commit -m "Add digests" && git push
```

### Step 5: Write to Notion

#### 5a. Write to Content Digest DB
For each analyzed video, write to the **Content Digest** database:
- Data source ID: `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`

**⚠️ DEDUP CHECK (MANDATORY before creating):**

Before creating a new page, check Content Digest DB for an existing page with the same Video URL.

**Query method (use in this order):**
1. **PRIMARY: `notion-fetch` on `collection://df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`** — returns all pages. Scan results for matching Video URL. This is the most reliable method because it does exact text comparison.
2. **FALLBACK: `notion-search` with the video ID** (the `v=XXXXX` portion only, NOT the full URL) — semantic search is unreliable with full URLs but video IDs are distinctive enough to surface matches. Verify any matches by checking the actual Video URL property.

**URL normalization (apply BEFORE comparing):**
Extract the video ID from any YouTube URL format and compare IDs, not raw URLs:
- `https://www.youtube.com/watch?v=XXXXX` → `XXXXX`
- `https://youtu.be/XXXXX` → `XXXXX`
- `https://youtube.com/watch?v=XXXXX&t=120` → `XXXXX` (strip params after video ID)
- `https://www.youtube.com/embed/XXXXX` → `XXXXX`

Two URLs with the same video ID = same video, regardless of URL format differences.

**Outcomes:**
- If **video ID match found** and the existing page has rich content (non-blank Summary, populated Essence Notes): **SKIP creation**. Log: "Skipping [title] — already exists as [page-id]". Use the existing page ID for Step 5b relations.
- If **video ID match found** but the existing page is a blank/abbreviated duplicate: **UPDATE the existing page** with BOTH content AND properties. Use `notion-update-page` with `replace_content` for body markdown, then a separate `notion-update-page` with `update_properties` for all properties (Summary, Essence Notes, Thesis Connections, etc.). Do NOT skip property updates — the blank duplicate likely has empty/abbreviated properties too.
- If **multiple matches found**: Use the page with the richest content (most non-empty fields). Log a warning: "Multiple matches for video ID [X] — using [page-id], ignoring [other-ids]".
- If **no match found**: Create a new page as normal.

This prevents the duplicate creation bug discovered in Session 029 (pipeline two-pass issue from same batch creating both abbreviated and full versions).

**Properties to fill:**
```
Video Title: [title]
Channel: [channel name]
Video URL: [youtube URL]
Upload Date: [date if available]
Duration: [formatted duration]
Summary: [3-5 sentence summary]
Thesis Connections: [matched thesis threads with explanations]
Portfolio Relevance: [matched portfolio companies with CONTEXTUAL relevance]
Key Insights: [3-5 bullet points]
Proposed Actions: [ALL actions — portfolio, thesis, network — with full reasoning]
Action Status: "Pending"
Connected Buckets: [matched buckets — use JSON array string format: "[\"Bucket1\", \"Bucket2\"]"]
Content Type: [classified type]
Relevance Score: [High/Medium/Low]
Discovery Source: "YouTube Playlist"
Processing Date: [today]
Batch ID: [extraction filename]

--- v3 Fields ---
Topic Map: [Full timestamped topic breakdown from 3a]
Watch These Sections: [Curated sections with timestamps and WHY from 3d]
Net Newness: [Mostly New / Additive / Reinforcing / Contra / Mixed — from 3b]
Contra Signals: [Challenges to current thinking from 3c]
Rabbit Holes: [Net new threads worth exploring from 3e]
Essence Notes: [Irreducible core arguments/frameworks/data from 3f]
```

**Important format notes:**
- Connected Buckets is multi_select — pass as JSON array string: `"[\"Deepen Existing\", \"Thesis Evolution\"]"`
- Net Newness is select — pass as plain string: `"Mixed"`
- Topic Map, Watch These Sections, Contra Signals, Rabbit Holes, Essence Notes are all rich_text — pass as formatted strings

Also add page content (body) with the full analysis in structured markdown.

**⚠️ CAPTURE THE PAGE ID** from the `notion-create-pages` response — you need it in Step 5b to set the `Source Digest` relation on each routed action.

#### 5b. Route Portfolio Actions to Actions Queue
For EACH portfolio action generated in Step 3j, create an entry in the **Actions Queue**:
- Data source ID: `1df4858c-6629-4283-b31d-50c5e7ef885d`

**IMPORTANT: Capture the Content Digest page ID** from the Step 5a creation response. You'll need it for the Source Digest relation below. Also build a thesis name → page ID mapping during Step 2d (query Thesis Tracker, store each thread's page ID).

Properties to fill:
```
Action: [concise, specific action description — NOT generic templates]
Company: [relation to Portfolio DB company page — use Page IDs from table below]
Thesis: [relation to Thesis Tracker page — use page ID from Step 2d mapping. Format: "[\"https://www.notion.so/{page-id}\"]"]
Source Digest: [relation to Content Digest DB page created in Step 5a — Format: "[\"https://www.notion.so/{digest-page-id}\"]"]
Action Type: [mapped from action generation framework]
Priority: [P0/P1/P2/P3 — assigned based on context]
Status: "Proposed"
Source: "Content Pipeline"
Created By: "Cowork"
Assigned To: "Aakash" (or "Agent" for system-executable, or "Sneha" for scheduling)
Reasoning: [FULL reasoning — what context informed this, why it matters]
Thesis Connection: [specific thesis thread + evidence direction (LEGACY text field — keep populated for backward compat)]
Source Content: [video title, channel, specific timestamp if available]
Relevance Score: [1-10 numeric score]
```

**Relation wiring notes:**
- `Source Digest` enables back-propagation: when this action reaches Done, the Content Digest entry moves to "Actions Taken"
- `Thesis` enables thesis-level action tracking without polluting the Thesis Tracker with action items
- `Company` remains optional — thesis/network actions may not have a company
- All three relations use Notion URL format: `"[\"https://www.notion.so/{page-id-no-dashes}\"]"`

**Action Type Mapping:**
- Key Question answered, competitive intel → Research
- Founder needs to know, intro suggestion → Meeting/Outreach
- Risk flag, health check trigger → Portfolio Check-in
- Follow-on conviction change → Follow-on Eval
- Thesis evidence → Thesis Update
- Deal pipeline signal → Pipeline Action
- General content follow-up → Content Follow-up

**Quality bar:** Every action should pass the "would a great chief of staff suggest this?" test. Not "check in with founder" but "Ask Chetan Reddy about [competitor X]'s new EHR integration — content suggests they're attacking Confido's write-back moat from the billing side."

#### 5c. Route Thesis Actions to Thesis Tracker
For EACH thesis-related action (from Step 3k) that involves thesis thread updates:
- If updating an existing thread: fetch the Thesis Tracker page, update Evidence For/Against, Investment Implications, Key Companies/People as appropriate
- If creating a new thesis thread: create a new page in Thesis Tracker with Discovery Source = "Content Pipeline"
- This sync is AUTOMATIC — do not wait for accept/dismiss. Thesis context should always be current.

### Step 6: Present Interactive Review ⚠️ MANDATORY — DO NOT SKIP

After processing all videos, you MUST present Aakash with an interactive review. This is NOT optional.

**v4 UX Design — Lead with PDFs, not walls of text:**

```
## 📺 Content Digest — [Date]
Processed X videos • Y portfolio connections • Z actions proposed

---

### 📄 Your Digests (read these on mobile)
[For each video ≥10 min, one line with PDF link:]
1. 📄 **[Video Title]** — [Channel] ([Duration])
   [Net Newness emoji] [category] • Relevance: [High/Med/Low] • [X] watch sections • [Y] rabbit holes
   [View digest](computer:///path/to/digest.pdf)

[For videos <10 min, inline mini-summary:]
2. ⚡ **[Video Title]** — [Channel] ([Duration])
   [2-sentence essence]

---

### ⭐ Top Sections to Watch (across all videos)
[Aggregated, max 5-7, sorted by strategic relevance]
1. **[Video Title]** [timestamp] — [section title]
   → [1-line WHY — specific, not generic]
2. ...

---

### 🕳️ New Rabbit Holes
[Aggregated, max 3-5]
1. **[Title]** — [1-line] — Start: [entry point]
2. ...

---

### Proposed Actions (accept/dismiss)

🔴 **P0 — Act Now**
1. **[Company]:** [Action] — from "[Video]"
   [1-line context] → Accept / Dismiss?

🟠 **P1 — This Week**
[same format]

🟡 **P2 — This Month**
[same format]

📋 **P3 — Backlog**
[same format — can batch-accept these]

---

### ⚡ Contra Signals
[Only strong/moderate — 1-2 sentences each max]

### Thesis Tracker Updates (auto-synced)
[Brief note on what was updated — NOT asking for approval, just informing]
```

**UX principles:**
- **PDFs are the consumption medium.** The chat summary is a navigation layer, not a replacement.
- **Scannable in 30 seconds.** Aakash should be able to scan the entire review on his phone and know what matters.
- **Actions are the decision point.** PDFs = consumption, actions = decisions. Keep them separate.
- **Thesis sync is automatic.** Don't add decision fatigue for thesis updates — just inform.

**After Aakash responds with accept/dismiss decisions:**
- **Accepted actions** → Update status to "Accepted" in Actions Queue
- **Dismissed actions** → Update status to "Dismissed" with Outcome note
- **Accepted thesis/research actions** → Also update Thesis Tracker's Investment Implications field
- **Meeting/Outreach accepted** → Flag for Sneha handoff or calendar scheduling

**If Aakash says "accept all":**
- Move ALL actions to "Accepted"
- Flag any P0 actions as needing explicit attention

### Step 7: Mark Queue as Processed
After writing all entries to Notion, move the extraction JSON files to `queue/processed/` to avoid reprocessing.

---

## Key Database IDs (Quick Reference)
- Content Digest data source: `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
- Thesis Tracker data source: `3c8d1a34-e723-4fb1-be28-727777c22ec6`
- Companies DB data source: `1edda9cc-df8b-41e1-9c08-22971495aa43`
- Portfolio DB: `edbc9d0c-fa16-436d-a3d5-f317a86a4d1e` (data source: `4dba9b7f-e623-41a5-9cb7-2af5976280ee`)
- Actions Queue data source: `1df4858c-6629-4283-b31d-50c5e7ef885d`
- Tasks Tracker: `1b829bcc-b6fc-80fc-9da8-000b4927455b`

## Portfolio Company Page IDs (for Relations)
| Company | Page ID |
|---------|---------|
| Confido Health | 12329bccb6fc8059a08fed398744fd5e |
| CodeAnt | 20f33412988040d88d8c3c1e73626e1a |
| GameRamp | 1b429bccb6fc8095b88dfacdb50f9e19 |
| PowerUp | 1b429bccb6fc8090a383cb8ce332bf3b |
| Terractive | 11829bccb6fc8062a9a1f3617a31bc8a |
| Unifize | 5c26ae03837c4c5c9bc964b523a1297f |
| Orange Slice | 28729bccb6fc81abb87de67f7a900e2f |
| Dodo Payments | 25329bccb6fc817d853df54bcd7d28c5 |
| Boba Bhai | c5505a574c7f466796dcfae38e46d11a |
| Inspecity | c1b1f6e69aeb4230945f590d610084a3 |
| Atica | 4a47b00b278948458c88dfcd3b19374d |
| Ballisto AgriTech | f89bbf3ce64046f8a5700bd4545b1f3a |
| Isler | 12d29bccb6fc80f09a2adb7648159b8b |
| Legend of Toys | 12d29bccb6fc80388be2f2757a0c2694 |
| Highperformr AI | 12329bccb6fc800388a2cf00e7931b3a |
| Smallest AI | 1ce29bccb6fc8044bad7f008e35d19eb |
| Step Security | 4630d9eac0534f12a596f3063c317195 |
| Terafac | 12729bccb6fc80d98230db2a1f3fb419 |
| Cybrilla | f6d9910585d64cc38eb2442754ee540d |
| Stance Health | ab1fb93c99cb4742af4fffe1ca175d59 |

## Handling Videos Without Transcripts
If a video has no transcript (auto-captions unavailable), still create a Content Digest entry using just the title, channel, and any metadata. Mark it with a note that analysis is based on metadata only. Topic Map, Watch These Sections, and Essence Notes will be empty — flag this so Aakash knows to watch the full video.

## Error Handling
- If Notion API fails, save the analysis locally and retry
- If a transcript is too long (>50k words), summarize in chunks
- If no thesis connections found, still log it — it might represent an emerging area
- If enrichment file not found for a company, use Portfolio DB data only (reduced context)
- If Portfolio DB query fails, fall back to name-matching only but flag degraded analysis quality
- If previous Content Digests can't be fetched (net newness baseline), note "newness assessment may overweight — no baseline available" and err toward "Mostly New"

## Context Window Management (v4 — Subagent Architecture)

**Problem:** Full enrichment files for 20 companies total ~300KB. A single video transcript can be 10-50KB. Processing 3+ videos in one agent context = guaranteed context limit hit.

**Solution: Orchestrator + Subagent pattern**

### Orchestrator Context Budget
The orchestrator (main agent) handles:
- Queue loading (~1KB)
- Shared context building (~10-20KB for Notion queries + thesis threads)
- Pre-scan for company relevance (~2KB per video, just keywords)
- Subagent dispatch (prompts are built but sent to separate contexts)
- Result collection (subagents return structured JSON ~3-5KB each)
- PDF generation (uses scripts, not context-heavy)
- Notion writes (API calls, not context-heavy)
- Interactive review presentation (~2KB)

**Orchestrator stays lean: ~30-40KB total** regardless of how many videos.

### Subagent Context Budget (per video)
Each subagent gets:
- Prompt template + instructions: ~3KB
- Video transcript: 5-50KB (the variable)
- Relevant company context blocks: 2-8KB (3-8 companies, not all 20)
- Thesis threads summary: 1-2KB
- Previous digest key themes: 1KB

**Subagent total: ~15-65KB** — well within a single context window even for long videos.

### Pre-Scan Strategy (Orchestrator Step 2.5)
Before dispatching subagents, the orchestrator does a FAST keyword scan of each transcript:
1. Check for direct company name mentions (case-insensitive)
2. Check for sector keywords: fintech, healthtech, devtools, cybersecurity, SaaS, etc.
3. Check for competitor names from enrichment files
4. Match against thesis thread topic keywords
5. Result: a relevance map of which companies to include in each subagent's context

This keeps subagent contexts targeted instead of dumping all 20 company profiles into each one.

### Parallel Dispatch
Use the Task tool to launch ALL subagents in a SINGLE message (multiple tool calls). This runs them in parallel, dramatically reducing wall-clock time. Don't wait for one to finish before starting the next.

---

## Subagent Prompt Template

When spawning Task subagents for individual video analysis, use this prompt. The subagent_type should be `"general-purpose"`.

```
You are analyzing a YouTube video for Aakash Kumar's AI Chief of Staff content pipeline.

Aakash is MD at Z47 ($550M fund) and DeVC ($60M fund). He uses content consumption to build investment theses, discover new sectors, and generate portfolio actions. Your job is to produce a RICH analysis that lets him (a) decide what to watch, (b) absorb key ideas without watching, and (c) know which sections need his direct attention.

## VIDEO
Title: [title]
Channel: [channel]
Duration: [duration]
URL: [url]

## TRANSCRIPT
[full transcript text]

## PORTFOLIO CONTEXT (companies to cross-reference)
[Only the relevant company context blocks — see Step 2c format]

## ACTIVE THESIS THREADS
[Thread name | Status | Core Thesis | Key Question | Conviction — for each active thread]

## PREVIOUS CONTENT THEMES (for net newness baseline)
[Summary of recent digests: titles, key insights, rabbit holes already identified]

---

## REQUIRED OUTPUT — Return as valid JSON with these exact keys:

{
  "title": "video title",
  "channel": "channel name",
  "url": "youtube url",
  "duration": "formatted duration",
  "content_type": "Podcast|Interview|Lecture|Panel|News Analysis|Deep Dive|Other",
  "relevance_score": "High|Medium|Low",
  "connected_buckets": ["bucket1", "bucket2"],

  "summary": "3-5 sentence summary, venture-relevance focus",
  "key_insights": ["insight 1", "insight 2", ...],

  "topic_map": [
    {"timestamp": "00:00", "title": "Topic Title", "description": "What's discussed"},
    ...
  ],

  "net_newness": {
    "category": "Mostly New|Additive|Reinforcing|Contra|Mixed",
    "reasoning": "Why this assessment"
  },

  "contra_signals": [
    {"what": "What it challenges", "evidence": "The argument/data", "strength": "Strong|Moderate|Weak", "implication": "What to think about"},
    ...
  ],

  "watch_sections": [
    {"timestamp_range": "12:30-18:45", "title": "Section title", "why_watch": "Specific reason", "connects_to": "thesis/company/bucket"},
    ...
  ],

  "rabbit_holes": [
    {"title": "Rabbit hole name", "what": "Description", "why_matters": "Connection to investing", "entry_point": "What to investigate", "newness": "Completely new|Tangentially connected to [thread]"},
    ...
  ],

  "essence_notes": {
    "core_arguments": ["precise statement 1", ...],
    "frameworks": ["framework description 1", ...],
    "data_points": ["specific data 1", ...],
    "key_quotes": [{"text": "quote text", "speaker": "name", "timestamp": "00:00"}],
    "predictions": ["falsifiable claim 1", ...]
  },

  "portfolio_connections": [
    {"company": "Company Name", "relevance": "What's relevant and why", "key_question": "How it relates to open questions", "conviction_impact": "validate|challenge|neutral", "actions": []},
    ...
  ],

  "thesis_connections": [
    {"thread": "Thread", "connection": "How it connects", "evidence_direction": "for|against|mixed", "strength": "Strong|Moderate|Weak"},
    ...
  ],

  "proposed_actions": [
    {
      "action": "Specific action description",
      "priority": "P0|P1|P2|P3",
      "type": "Research|Meeting|Portfolio Action|Portfolio Review|Thesis Update|Network|Signal Monitoring",
      "assigned_to": "Cash|AI CoS|Sneha",
      "company": "Company Name (empty string for thesis/network actions)",
      "thesis_connection": "Thread name"
    },
    ...
  ]
}

IMPORTANT QUALITY BARS:
- Topic Map titles must be specific enough to scan and decide relevance. Bad: "AI Discussion." Good: "Why vertical AI agents beat horizontal platforms in healthcare."
- Watch sections need specific WHY. Bad: "Interesting AI discussion." Good: "Sebastian argues Klarna's AI agent approach can't be copied by incumbents — validates SaaS death thesis, implications for Unifize."
- Actions must pass the "great chief of staff" test. Not "check in with founder" but "Ask Chetan about competitor X's new EHR integration."
- Rabbit holes must be genuinely NEW — not existing thesis threads repackaged.
- Contra signals: actively look for them even in aligned content. If none exist, say so explicitly.

Return ONLY the JSON object, no markdown wrapping.
```

## Subagent Output → PDF Data Format

The subagent JSON output maps directly to the `generate_digest_pdf(data, output_path)` function in `scripts/content_digest_pdf.py`. The orchestrator may need to do minor key mapping (the PDF generator expects slightly different key names in some cases — check the docstring in `content_digest_pdf.py` for the exact expected format).
