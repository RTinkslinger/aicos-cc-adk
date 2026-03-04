---
name: parallel-deep-research
description: "Triggers when user says 'research deep and wide', 'deep research', 'exhaustive research', 'comprehensive report', 'thorough investigation', or any variant requesting multi-source parallel research on a topic. Uses the Parallel AI deep research MCP tools to run exhaustive multi-source research with citations. This is for DEEP, time-consuming research — not quick lookups. For quick factual questions, web search is faster. Use this skill aggressively whenever the user signals they want depth, breadth, or exhaustive coverage on any topic — investing, technology, market analysis, historical deep dives, anything."
---

# Parallel Deep Research (Cowork)

This skill runs exhaustive, multi-source research using Parallel AI's deep research engine via the MCP tools already available in Cowork. It's the Cowork equivalent of the `parallel-cli research` command in Claude Code.

## When to Use

ONLY use this skill when the user explicitly requests deep research. Trigger phrases include:
- "research deep and wide"
- "deep research on X"
- "exhaustive research"
- "comprehensive report on X"
- "thorough investigation"
- "research this thoroughly"
- "go deep on X"
- "I want to understand everything about X"

For normal quick lookups, factual questions, or simple research, use web search tools directly — they're 10-100x faster.

## Step 1: Formulate the Research Query

Take the user's topic and craft a detailed, specific research query. Good queries are:
- Specific about what to investigate
- Clear about the angle or lens (market analysis, technical deep dive, competitive landscape, etc.)
- Scoped appropriately (not too broad, not too narrow)

**Example transformation:**
- User says: "research deep and wide on the agentic AI infrastructure space"
- Research query: "Comprehensive analysis of the agentic AI infrastructure market: key companies building orchestration/harness layers (MCP, tool management, agent-to-agent protocols), market structure, competitive dynamics, recent funding, technology architecture patterns, and where durable value is emerging. Include Composio, Smithery.ai, LangChain, CrewAI, and any emerging players."

If the topic is ambiguous, ask the user ONE clarifying question about the angle they want before proceeding.

## Step 2: Choose the Right Processor

| Processor | Expected Time | Use When |
|-----------|--------------|----------|
| `pro-fast` | 30s – 5 min | Default — good depth, fast turnaround |
| `pro` | 2 – 10 min | More thorough, still reasonable wait |
| `ultra-fast` | 1 – 10 min | Deeper analysis, more sources (~2x cost) |
| `ultra` | 5 – 25 min | Maximum depth, only when user says "exhaustive" or "leave no stone unturned" |

Default to `pro` unless the user signals they want maximum depth (then use `ultra`).

## Step 3: Kick Off the Research

Use the `createDeepResearch` MCP tool:

```
Tool: createDeepResearch
input: <your crafted research query>
processor: <chosen processor tier>
```

This returns immediately with a task run ID (`trun_*`) and a monitoring URL.

**Immediately tell the user:**
1. Deep research has been kicked off
2. Expected wait time based on the processor tier
3. The monitoring URL where they can track progress
4. That you'll check on it and deliver results when ready

## Step 4: Poll for Completion

Use the `getStatus` MCP tool to check progress:

```
Tool: getStatus
taskRunOrGroupId: <trun_id>
```

Check every 30-60 seconds. Status will be one of: `pending`, `running`, `completed`, `failed`.

While waiting, you can tell the user what you're doing and offer to help with other things in the meantime.

## Step 5: Retrieve and Deliver Results

Once status is `completed`, use `getResultMarkdown`:

```
Tool: getResultMarkdown
taskRunOrGroupId: <trun_id>
```

This returns the full research report with citations.

**Deliver to the user:**
1. A concise executive summary (3-5 bullet points of the most important findings)
2. Save the full report as a markdown file in the workspace folder
3. Share the file link so they can read the full report

## Step 6: Thesis Connection Check (Investing Context)

After delivering results, check if any findings connect to Aakash's active thesis threads or suggest new ones. Query the Notion Thesis Tracker:

```
Data source: 3c8d1a34-e723-4fb1-be28-727777c22ec6
```

If you find connections to existing thesis threads OR the research suggests a new thesis thread, flag it:

> "This research connects to your [Thesis Thread Name] thesis — specifically [connection]. Want me to update the Thesis Tracker with these new evidence points?"

Or for new threads:

> "This research suggests a potential new thesis thread around [topic]. Want me to add it to your Thesis Tracker?"

**Wait for explicit confirmation before writing to Notion.** Never auto-sync.

## Error Handling

- If `createDeepResearch` fails: Fall back to comprehensive web search using `WebSearch` tool — run 5-8 parallel searches across different angles of the topic, synthesize results manually.
- If polling times out after 15 minutes: Tell the user the research is still running server-side, share the monitoring URL, and offer to check again later.
- If results are thin: Offer to run a follow-up research pass with a more specific query or different angle.

## Output Format

The final deliverable should be:
1. **In-chat**: Executive summary (3-5 key findings)
2. **As file**: Full markdown report saved to workspace folder with `computer://` link
3. **Optional**: Thesis Tracker update (only after user confirms)
