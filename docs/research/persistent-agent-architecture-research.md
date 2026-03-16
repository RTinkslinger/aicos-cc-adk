# Persistent, Long-Running AI Agent Architecture: Research Report

**Date:** 2026-03-15
**Scope:** How people build persistent, long-running AI agents in production — real-world patterns, not just SDK docs.

---

## Executive Summary

The field of persistent AI agents is maturing rapidly but remains fragmented. There is **no single canonical solution** for running agents that live on servers, do periodic work, maintain context between cycles, and survive crashes. Instead, the community has converged on a handful of composable patterns, each with clear tradeoffs. This report covers what Anthropic officially supports, what the community has built, how competing frameworks handle persistence, and what the RIGHT architecture looks like for your specific requirements.

**Key finding:** The Claude Agent SDK is explicitly designed as a **long-running process** (not stateless API calls). Anthropic's official hosting docs describe persistent daemon containers as a first-class deployment pattern. However, the "glue" between the SDK and recurring scheduling is currently DIY — you need cron, a process supervisor, or a workflow engine to trigger agent runs.

---

## 1. What Anthropic Officially Supports

### 1.1 The Agent SDK as a Long-Running Process

Anthropic's [hosting documentation](https://platform.claude.com/docs/en/agent-sdk/hosting) is explicit:

> "Unlike stateless API calls, the Claude Agent SDK operates as a **long-running process** that: executes commands in a persistent shell environment, manages file operations within a working directory, handles tool execution with context from previous interactions."

The SDK has four official deployment patterns:

| Pattern | Description | Best For |
|---------|-------------|----------|
| **Ephemeral Sessions** | New container per task, destroyed on completion | One-off tasks (bug fixes, invoice processing) |
| **Long-Running Sessions** | Persistent container instances, multiple SDK processes | Email agents, chatbots, site builders |
| **Hybrid Sessions** | Ephemeral containers hydrated with history from DB/session resumption | Project managers, deep research, support agents |
| **Single Containers** | Multiple SDK processes in one container | Agent simulations, tightly collaborating agents |

**Critical detail:** An agent session **will not timeout** on its own. You set `maxTurns` to prevent infinite loops.

**Resource requirements per instance:** 1 GiB RAM, 5 GiB disk, 1 CPU minimum. Cost is roughly $0.05/hour for the container, but tokens dominate total cost.

### 1.2 Session Persistence

The [sessions documentation](https://platform.claude.com/docs/en/agent-sdk/sessions) reveals a mature persistence model:

- **Sessions are written to disk automatically** as `.jsonl` files under `~/.claude/projects/<encoded-cwd>/`
- **`continue`** resumes the most recent session in the working directory — no ID tracking needed
- **`resume`** takes a specific session ID — required for multi-user apps or non-linear conversation flows
- **`fork`** creates a branch of conversation history — try alternative approaches without losing the original
- **Cross-host resume** requires moving the session file to the same path on the new host, or reconstructing state in a fresh prompt

**Python example — multi-turn with automatic session management:**
```python
async with ClaudeSDKClient(options=options) as client:
    # First query: client captures the session ID internally
    await client.query("Analyze the auth module")
    async for message in client.receive_response():
        print_response(message)

    # Second query: automatically continues the same session
    await client.query("Now refactor it to use JWT")
    async for message in client.receive_response():
        print_response(message)
```

**TypeScript example — resume by ID:**
```typescript
for await (const message of query({
  prompt: "Continue with the JWT approach",
  options: { resume: sessionId }
})) {
  // Full context from the original session is available
}
```

### 1.3 Claude Code Scheduled Tasks (`/loop`)

As of Claude Code v2.1.72, there is a built-in `/loop` command for recurring prompts:

```
/loop 5m check if the deployment finished and tell me what happened
```

**However, this is session-scoped:**
- Tasks only fire while Claude Code is running and idle
- No catch-up for missed fires
- No persistence across restarts
- Recurring tasks auto-expire after 3 days
- Maximum 50 scheduled tasks per session

**This is useful for interactive development but explicitly NOT for server-side daemon agents.** The docs say: "For cron-driven automation that needs to run unattended, use a GitHub Actions workflow with a `schedule` trigger."

### 1.4 Secure Deployment Architecture

Anthropic's [secure deployment guide](https://platform.claude.com/docs/en/agent-sdk/secure-deployment) recommends:

- **Container isolation** with `--network none` + Unix socket proxy
- **Credential injection via proxy** — agent never sees API keys
- **gVisor** for kernel-level isolation (adds 2x overhead on syscalls)
- **Firecracker microVMs** for strongest isolation (125ms boot, <5MiB overhead)

Recommended sandbox providers: Modal, Cloudflare Sandboxes, E2B, Fly Machines, Daytona, Vercel Sandbox.

---

## 2. Community Patterns for Persistent Claude Agents

### 2.1 Murmur — Cron Daemon for Claude Code

[Murmur](https://github.com/t0dorakis/murmur) (`brew install t0dorakis/murmur/murmur`) is the most complete community solution for scheduled Claude Code sessions. It runs as a background daemon that triggers Claude Code runs on a schedule.

**Architecture:**
- `HEARTBEAT.md` files define both the schedule (cron/interval) and the prompt
- Daemon ticks regularly, checks which heartbeats are due, executes fresh CLI invocations
- Results append to `~/.murmur/heartbeats.jsonl` as structured JSON lines
- Supports multiple agent harnesses: Claude Code, Pi, Codex

**HEARTBEAT.md format:**
```yaml
---
name: competitor watch
cron: 0 9 * * MON
agent: claude-code
model: sonnet
timeout: 10m
---

fetch https://competitor.com/changelog .
compare against ~/tracking/competitor-last.md for new entries.
for each new feature, check our issue tracker.
only if it genuinely adds value: open an issue with reasoning.
update competitor-last.md. if nothing new, HEARTBEAT_OK.
```

**Key design decisions:**
- Each execution is a **fresh CLI invocation**, not a persistent process. Murmur handles timing; Claude handles logic.
- Missed runs during sleep are collapsed into a single catch-up execution
- `HEARTBEAT_OK` = silent completion, `ATTENTION: <summary>` = surfaces alerts in the TUI

**Limitation:** No session continuity between runs. Each heartbeat starts fresh.

### 2.2 Claude Daemon (macOS User Isolation)

[Jonathan Chang's approach](https://jonathanc.net/blog/claude-daemon) runs Claude Code as a dedicated macOS user (`claude`) with filesystem-level ACL isolation:

```bash
sudo -u claude -i bash -lc "cd '$(pwd)' && claude --dangerously-skip-permissions"
```

This follows the Unix daemon pattern (like `postgres`, `sshd`) — isolate the service's filesystem access rather than relying on software-level permission checks. A helper script manages permissions:
```bash
claude-access add .    # grant access to current directory
claude-access remove . # revoke access
```

### 2.3 Feature Request: Native Daemon Mode

[GitHub Issue #28229](https://github.com/anthropics/claude-code/issues/28229) on the Claude Code repo is the canonical feature request for native scheduling/daemon mode. It documents the full gap:

- No native way to run an agent on a schedule
- No way to keep an agent alive between sessions (daemon mode)
- No resource watching with agent wake
- No fire-and-forget for long-running tasks
- No post-session continuation scheduling

The issue documents a **production workaround** requiring hundreds of lines of infrastructure: cron-based polling, swarm messaging layer, tmux-based session invocation, state deduplication — all to achieve "check GitHub and react."

**Status as of March 2026:** `/loop` partially addresses scheduling within active sessions. The broader daemon mode, resource watching, and event-driven wake primitives remain unimplemented.

### 2.4 The Reddit Consensus on Cost

The [r/ClaudeAI discussion](https://www.reddit.com/r/ClaudeAI/comments/1qyzolz/running_claude_as_a_persistent_agent_changed_how/) on persistent agents surfaces a key concern: **API costs for long-running agents are extremely high**. The consensus is that flat-fee subscriptions (Claude Code with Max plan) are more economical than per-token API billing for persistent agents.

---

## 3. Seven Hosting Patterns (Community Taxonomy)

James Carr's [Seven Hosting Patterns for AI Agents](https://james-carr.org/posts/2026-03-01-agent-hosting-patterns/) is the best community taxonomy. Here's the relevant subset for your use case:

### 3.1 Scheduled Agent (Cron)

**Simplest pattern.** Agent runs on timer, does work, writes results, exits. Stateless between runs.

```python
# scheduled_agent.py — runs via cron, e.g. "0 */6 * * *"
def check_recent_incidents():
    incidents = fetch_incidents(since=datetime.now() - timedelta(hours=6))
    if not incidents:
        return
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        messages=[{"role": "user", "content": f"Summarize: {json.dumps(incidents)}"}]
    )
    post_to_slack("", response.content[0].text)
```

**When to use:** Periodic checks, reports, summaries. Content pipeline runs. Inbox checks.

### 3.2 Event-Driven Agent (Reactive)

Agent activates in response to webhooks, queue messages, or DB changes. Processes event, takes action, exits.

**When to use:** Customer submits ticket, PR opens, payment fails, new email arrives.

### 3.3 Persistent Long-Running Agent (Daemon)

Process stays alive, maintains in-memory state (conversation history, user preferences), serves requests continuously.

```python
class ConversationAgent:
    def __init__(self):
        self.conversations = defaultdict(list)
        self.user_preferences = {}

    def chat(self, user_id, message):
        self.conversations[user_id].append({"role": "user", "content": message})
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            system=f"User preferences: {self.user_preferences.get(user_id)}",
            messages=self.conversations[user_id][-20:]  # sliding window
        )
        return response.content[0].text

# Expose via FastAPI
agent = ConversationAgent()
app = FastAPI()

@app.post("/chat")
async def chat(user_id: str, message: str):
    return {"response": agent.chat(user_id, message)}
```

**When to use:** Fast response with maintained context. Chat services.
**Risk:** State loss on restart is the key failure mode.

### 3.4 Self-Scheduling Agent (Adaptive)

Agent determines its own next execution time based on results. Quiet period? Check in an hour. Something interesting? Check in 5 minutes.

```python
TOOLS = [{
    "name": "schedule_next_run",
    "input_schema": {
        "properties": {
            "delay_minutes": {"type": "integer"},
            "reason": {"type": "string"}
        }
    }
}]
```

**When to use:** Variable-rate monitoring, research where the rate of change varies.

### 3.5 Workflow-Orchestrated Agent (Pipeline)

Multi-step workflows with checkpointing, retries, and audit trails. Uses Temporal, Restate, or similar.

**When to use:** Failure mid-way is expensive (token costs, side effects). Operations spanning minutes to hours.

### 3.6 Pattern Selection Heuristic

| Pattern | Best When | Avoid When |
|---------|-----------|------------|
| Scheduled (Cron) | Periodic checks, reports | Need real-time response |
| Event-Driven | Reacting to triggers | Events infrequent, batch is fine |
| Persistent Daemon | Fast response + maintained context | State loss on restart unacceptable |
| Workflow-Orchestrated | Multi-step, failure-prone ops | Task is simple enough for a script |
| Self-Scheduling | Variable-rate monitoring | Can't set good guardrails |

**Most production systems combine 2-3 patterns.** An event-driven agent that kicks off a workflow pipeline is common. An API that delegates to a self-scheduling background agent is natural.

---

## 4. Framework Comparison: How Others Handle Persistence

### 4.1 LangGraph — Checkpointing-First Design

LangGraph is purpose-built for stateful, long-running agents. Its core innovation is **graph-based state management with pluggable checkpointers**.

**Core primitives:**
- **Interrupt/Resume**: `interrupt()` suspends graph execution mid-node, serializes state to a database, and resumes days later when the user returns
- **Checkpointers**: Every state transition is saved. Options: InMemorySaver (dev), PostgresSaver, DynamoDBSaver (production)
- **Time Travel**: Replay from any checkpoint, fork from any state, inspect full history

**Production pattern from a real deployment:**
```python
# Compile with checkpointer — this is what makes interrupt() work
checkpointer = AsyncPostgresSaver.from_conn_string("postgresql://...")
await checkpointer.setup()  # creates checkpoint tables (idempotent)
graph = builder.compile(checkpointer=checkpointer)

# Same thread_id = same conversation = resume from last checkpoint
config = {"configurable": {"thread_id": THREAD_ID}}
graph.invoke({"messages": ["I need help"]}, config)  # Day 1
graph.invoke({"messages": ["Here's my account"]}, config)  # Day 2
graph.invoke({"action": "resolve"}, config)  # Day 3
```

**Key insight from practitioners:** "The checkpointer is not optional. It's tempting to think of persistence as a nice-to-have. It's not. Without `interrupt()` + checkpointer, you simply cannot build multi-turn conversational agents."

**Community deployment reality (from Reddit):**
- State management is the hard part, not agent logic
- FastAPI + Docker on Cloud Run with Redis checkpoints is common
- Cloud Run's request timeout kills long-running agents — need async task dispatch + polling
- "For persistent state: fly.io + postgres for checkpoints works well"

### 4.2 Letta (MemGPT) — Memory-First Stateful Agents

[Letta](https://www.letta.com/) (formerly MemGPT, $10M raised) is purpose-built for **persistent, stateful agents that learn over time**. Its key insight: agents need tiered memory management, not just conversation history.

**Memory architecture:**
1. **Core Memory (Memory Blocks)**: Always in-context. User preferences, agent config, persistent facts. Editable by the agent via tools.
2. **Recall Memory**: Full interaction history searchable via embedding similarity.
3. **Archival Memory**: Large-scale persistent storage (documents, knowledge bases) — like archival storage the agent can query.
4. **Inner Thoughts**: Private reasoning not visible to users — enables multi-step autonomous execution.

**Critical design pattern — Heartbeat Mechanism:**
Agents request follow-up execution using a `request_heartbeat` flag, enabling:
- Multi-step workflows without human input
- Recursive reasoning
- Background state updates
- Task decomposition

**All state persists in a database (SQLite default, Postgres for production):**
- Survives script restarts
- Maintains identity over time
- Enables long-running agents
- Queryable via REST API

**Letta vs Claude Agent SDK:** Letta manages its own memory hierarchy and context window compilation. The Claude Agent SDK delegates context management to the model (with session files for persistence). Letta gives you more control over what the agent remembers; the Claude SDK gives you more powerful tool execution.

### 4.3 CrewAI — Flow-Based Production Architecture

[CrewAI](https://docs.crewai.com/en/concepts/production-architecture) recommends a **Flow-first design** for production:

- **Flows** = event-driven pipelines with precise execution paths (loops, conditionals, branching)
- **Crews** = autonomous agent teams delegated to from Flows
- **`@persist` decorator** saves Flow state to database for crash recovery
- **`kickoff_async`** for non-blocking long-running tasks

CrewAI is higher-level than LangGraph — less control over state transitions but faster to build.

### 4.4 Temporal — Durable Execution (The Infrastructure Layer)

[Temporal](https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai) is not an agent framework — it's a **workflow execution engine** that provides durability guarantees for any code, including agent code.

**What Temporal provides that other frameworks don't:**
- **Implicit checkpointing**: You never write checkpoint code. Temporal's event sourcing records every activity call and its result. If the process crashes, it replays the history and resumes.
- **Worker architecture**: Long-running processes handled naturally. Workers poll for tasks, execute them, report results. Process can die and restart.
- **Human-in-the-loop** via Signals & Updates: External events can inject data into a running workflow at any point.

**The pitch:** "Developer codes the happy path, Temporal handles the errors."

```typescript
// Tool calls become durable Activities
// LLM calls are automatically wrapped via temporalProvider
export async function dailyBriefingWorkflow(topics: string[]) {
  const searchResults = await Promise.all(
    topics.map(topic => searchTopic(topic))  // retried on failure
  );
  const summary = await generateText({
    model: temporalProvider.languageModel('gpt-4o-mini'),
    prompt: `Summarize: ${JSON.stringify(searchResults)}`
  });
  return summary;
}
```

**Production users:** Netflix, Uber, OpenAI, Replit, Lovable, Hebbia.

**Tradeoff:** Requires operating a multi-service cluster or adopting Temporal Cloud. LLM payloads can cause workflow history saturation.

### 4.5 Framework Comparison Summary

| Feature | Claude Agent SDK | LangGraph | Letta (MemGPT) | CrewAI | Temporal |
|---------|-----------------|-----------|-----------------|--------|----------|
| **State Persistence** | Session files (.jsonl) | Pluggable checkpointers (Postgres, DynamoDB) | Tiered memory (core/recall/archival) in DB | Flow state with @persist | Event sourcing (implicit) |
| **Session Resume** | `continue`/`resume`/`fork` | Thread ID + checkpoint | Always-on (DB-backed) | Flow state restoration | Automatic (event replay) |
| **Scheduling** | `/loop` (session-scoped only) | External (cron/queue) | External (cron/queue) | `kickoff_async` + external | Built-in cron schedules |
| **Crash Recovery** | Manual (resume by session ID) | Checkpoint replay | Automatic (DB-backed) | @persist decorator | Automatic (durable execution) |
| **Tool Execution** | Bash, MCP, file ops (strongest) | LangChain tools | Tool-based with heartbeat | CrewAI tools + MCP | Activities (retried) |
| **Best For** | Code tasks, complex tool use | Stateful workflows | Personalized long-term agents | Multi-agent teams | Mission-critical durability |
| **Weakness** | No built-in scheduling/daemon | No native scheduling | No native tool execution power | Less granular control | Operational complexity |

---

## 5. Recommended Architecture for Your Use Case

Your requirements:
1. Lives on a server (no terminal, no human)
2. Periodic work (check inbox every minute, content pipeline every 5 min)
3. Maintain context between cycles
4. Has access to tools (Bash, MCP servers, skills)
5. Resilient (restart on crash, resume sessions)

### 5.1 Recommended: Hybrid Cron + Session Resume (Pragmatic)

This is the pattern that matches your existing infrastructure (droplet, systemd, cron) with minimal new complexity.

```
┌─────────────────────────────────────────────┐
│  systemd service (process supervisor)       │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Python orchestrator (daemon)       │    │
│  │                                     │    │
│  │  ┌──────────┐   ┌──────────────┐   │    │
│  │  │ Scheduler │   │ State Store  │   │    │
│  │  │ (APScheduler│  │ (Postgres)   │   │    │
│  │  │  or cron) │   │              │   │    │
│  │  └─────┬─────┘   └──────┬───────┘   │    │
│  │        │                │           │    │
│  │        ▼                ▼           │    │
│  │  ┌──────────────────────────────┐   │    │
│  │  │  Agent Runner                │   │    │
│  │  │  - Claude Agent SDK (Python) │   │    │
│  │  │  - Session resume by ID      │   │    │
│  │  │  - MCP tool connections      │   │    │
│  │  │  - Result → State Store      │   │    │
│  │  └──────────────────────────────┘   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Restart=always                             │
│  WatchdogSec=300                            │
└─────────────────────────────────────────────┘
```

**Implementation sketch:**

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

class AgentRunner:
    def __init__(self, db):
        self.db = db
        self.scheduler = AsyncIOScheduler()

    async def run_agent(self, agent_name: str, prompt: str):
        """Run an agent cycle, resuming from last session if available."""
        session_id = self.db.get_last_session(agent_name)
        state = self.db.get_agent_state(agent_name)

        # Build context-aware prompt
        full_prompt = f"""
        Previous state: {state}
        Current task: {prompt}
        """

        options = ClaudeAgentOptions(
            allowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep"],
            mcp_servers={
                "ai-cos": {"url": "https://mcp.3niac.com/mcp"}
            },
            max_turns=20,
        )

        # Resume if we have a session, otherwise start fresh
        if session_id:
            options.resume = session_id

        new_session_id = None
        async for message in query(prompt=full_prompt, options=options):
            if isinstance(message, ResultMessage):
                new_session_id = message.session_id
                if message.subtype == "success":
                    self.db.save_agent_state(agent_name, message.result)
                elif message.subtype.startswith("error"):
                    self.db.log_error(agent_name, message.subtype)

        if new_session_id:
            self.db.save_session_id(agent_name, new_session_id)

    def start(self):
        # Content pipeline: every 5 minutes
        self.scheduler.add_job(
            self.run_agent, 'interval', minutes=5,
            args=['content_agent', 'Check content queue and process new items'],
            id='content_pipeline',
            max_instances=1,  # prevent overlapping runs
        )

        # Inbox check: every minute
        self.scheduler.add_job(
            self.run_agent, 'interval', minutes=1,
            args=['sync_agent', 'Check for new changes and sync'],
            id='sync_check',
            max_instances=1,
        )

        self.scheduler.start()
        asyncio.get_event_loop().run_forever()
```

**Why this pattern:**
- Uses your existing infrastructure (droplet, systemd, Postgres)
- Session resume provides context continuity
- APScheduler handles timing with overlap prevention
- systemd handles crash recovery (`Restart=always`)
- State stored in Postgres survives everything
- Each agent run has full tool access via the Agent SDK

### 5.2 Alternative: Temporal for Mission-Critical Durability

If you need **guaranteed completion** (no lost work, automatic retry, audit trail), wrap the agent in Temporal:

```python
# Temporal workflow — agent runs as an Activity
@activity.defn
async def run_content_pipeline(state: dict) -> dict:
    """Each agent call is a Temporal Activity with automatic checkpointing."""
    async for message in query(
        prompt=f"Process content queue. Previous state: {state}",
        options=ClaudeAgentOptions(max_turns=20),
    ):
        if isinstance(message, ResultMessage):
            return {"session_id": message.session_id, "result": message.result}

@workflow.defn
class ContentPipelineWorkflow:
    @workflow.run
    async def run(self):
        while True:
            state = workflow.info().search_attributes.get("state", {})
            result = await workflow.execute_activity(
                run_content_pipeline,
                state,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            # Temporal automatically persists this state
            await asyncio.sleep(300)  # 5 minutes
```

**When to use Temporal over cron:** When a single failed agent run has costly consequences (lost pipeline data, missed critical actions). Temporal guarantees the workflow completes even across crashes and deploys.

### 5.3 Context Continuity Strategy

The hardest problem is not scheduling — it's **maintaining meaningful context between cycles**. Here are the options in increasing sophistication:

**Level 1 — Stateless with DB context (your current architecture):**
Each run reads state from Postgres, does work, writes results back. No session continuity. Simple, robust.

**Level 2 — Session resume with state injection:**
Save session IDs. Resume previous session on each cycle. Agent has full conversation history from prior runs. Risk: conversation grows unbounded, eventually hitting context limits.

**Level 3 — Hybrid state + summary:**
Every N cycles, run a "compaction" step: summarize recent history into a state document. Start fresh sessions with the compacted state as context. This is the CLAUDE.md/TRACES.md pattern but automated.

**Level 4 — Letta-style tiered memory:**
Core memory (always in context) + recall memory (searchable history) + archival memory (large-scale persistent store). Most sophisticated, most complex to implement.

**Recommendation for your system: Level 2 transitioning to Level 3.** Start with session resume for context continuity. Add automated compaction when conversations get too long (the Agent SDK's session files are `.jsonl` — you can measure their size and trigger compaction).

### 5.4 Resilience Checklist

| Concern | Solution |
|---------|----------|
| Process crash | systemd `Restart=always` + `WatchdogSec` |
| Overlapping runs | APScheduler `max_instances=1` or `fcntl` lockfile |
| Stuck agent | `max_turns` limit on Agent SDK + scheduler timeout |
| State loss | Postgres for all durable state, session files for conversation |
| Token cost explosion | Budget limits per run (`max_budget_usd` on Agent SDK) |
| Context window overflow | Session compaction every N cycles |
| Network failure | Retry with exponential backoff in the orchestrator |
| MCP server down | Agent SDK handles MCP reconnection; log and skip if persistent |

---

## 6. What to Watch

1. **Claude Code native daemon mode** (Issue #28229) — If Anthropic ships this, it replaces the orchestrator layer entirely. The proposed `claude agent schedule monitor --every 5m` would be exactly what you need.

2. **Murmur maturation** — Already installable via Homebrew. If it adds session continuity between runs, it becomes a strong option.

3. **Agent SDK V2 Sessions** — The `unstable_v2_*` API in the demos repo (`createSession()` with `send`/`stream`) is closer to a true persistent connection model.

4. **Temporal AI SDK integration** — Now has integrations for OpenAI Agents SDK and Vercel AI SDK. A Claude Agent SDK integration would be the production-grade answer.

5. **Google A2A Protocol** — For multi-agent coordination. Over 150 organizations adopted. Complementary to MCP (MCP = agent-to-tools, A2A = agent-to-agent).

---

## Sources

### Official Anthropic Documentation
- [Hosting the Agent SDK](https://platform.claude.com/docs/en/agent-sdk/hosting)
- [Securely Deploying AI Agents](https://platform.claude.com/docs/en/agent-sdk/secure-deployment)
- [Agent SDK Sessions](https://platform.claude.com/docs/en/agent-sdk/sessions)
- [Run Claude Code Programmatically](https://code.claude.com/docs/en/headless)
- [Run Prompts on a Schedule](https://code.claude.com/docs/en/scheduled-tasks)
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic's canonical guide

### Community Projects & Discussions
- [Murmur — Cron Daemon for Claude Code](https://github.com/t0dorakis/murmur) — Open-source scheduler with HEARTBEAT.md pattern
- [Claude Daemon — macOS User Isolation](https://jonathanc.net/blog/claude-daemon) — Jonathan Chang's guide
- [Feature Request: Native Daemon Mode](https://github.com/anthropics/claude-code/issues/28229) — Most detailed community proposal
- [Running Claude as a Persistent Agent (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1qyzolz/running_claude_as_a_persistent_agent_changed_how/) — Cost and pattern discussion
- [Claude Agent SDK Demos](https://github.com/anthropics/claude-agent-sdk-demos) — Official demo repo including email agent

### Architecture & Patterns
- [Seven Hosting Patterns for AI Agents](https://james-carr.org/posts/2026-03-01-agent-hosting-patterns/) — James Carr's taxonomy (best single resource)
- [How to Run Claude Agents in Production](https://medium.com/@hugolu87/how-to-run-claude-agents-in-production-using-the-claude-sdk-756f9d3c93d8) — Hugo Lu / Orchestra
- [Claude Agent SDK Workshop](https://www.youtube.com/watch?v=TqC1qOfiVcQ) — Thariq Shihipar / Anthropic (1h52m)
- [Inside the Claude Agents SDK — ML6](https://www.ml6.eu/en/blog/inside-the-claude-agents-sdk-lessons-from-the-ai-engineer-summit) — AI Engineer Summit recap

### Framework-Specific
- [LangGraph: Durable Execution](https://docs.langchain.com/oss/python/langgraph/overview) — Official docs
- [LangGraph + Postgres Checkpointing](https://dev.to/irubtsov/building-conversational-ai-agents-that-remember-langgraph-postgres-checkpointing-and-the-future-gdl) — Production pattern deep dive
- [LangGraph + DynamoDB](https://aws.amazon.com/blogs/database/build-durable-ai-agents-with-langgraph-and-amazon-dynamodb/) — AWS production deployment
- [Deploying LangGraph to Production (Reddit)](https://www.reddit.com/r/AI_Agents/comments/1ricz9m/how_are_you_deploying_langchainlanggraph_agents/) — Community practices
- [Letta — Stateful Agents](https://www.letta.com/blog/stateful-agents) — Memory architecture
- [Letta Agent Loop Architecture](https://www.letta.com/blog/letta-v1-agent) — ReAct, MemGPT, and Claude Code comparison
- [CrewAI Production Architecture](https://docs.crewai.com/en/concepts/production-architecture) — Flow-based patterns
- [Temporal — Durable Execution for AI](https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai) — Canonical article
- [Temporal + Vercel AI SDK](https://temporal.io/blog/building-durable-agents-with-temporal-and-ai-sdk-by-vercel) — Integration pattern

### Infrastructure & State
- [Persistent Memory for Claude Code](https://agentnativedev.medium.com/persistent-memory-for-claude-code-never-lose-context-setup-guide-2cb6c7f92c58) — Memory infrastructure landscape
- [Every AI Agent Has Amnesia](https://pub.towardsai.net/every-ai-agent-has-amnesia-heres-the-infrastructure-that-fixes-it-289dc6ba28a5) — Durable Objects / infrastructure bottleneck analysis
- [State of Autonomous Agents 2026](https://dev.to/rook_damon/the-state-of-autonomous-agents-in-2026-1efa) — Market overview
- [Headless Mode Cheatsheet — SFEIR](https://institute.sfeir.com/en/claude-code/claude-code-headless-mode-and-ci-cd/cheatsheet/) — CI/CD integration patterns
