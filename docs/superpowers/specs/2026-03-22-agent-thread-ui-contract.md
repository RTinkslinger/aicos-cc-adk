# Agent Thread UI Contract Spec
*2026-03-22 — Defines the contract between agent machines (M4/M7/M8) and M1 WebFront*

## Architecture

Agent machines build SQL RPCs that return typed thread messages. M1 builds a universal thread renderer.

## Message Type Registry

Each agent thread message has: `{sender, type, content, created_at}`

| Type | When Agent Needs | UI Component |
|------|-----------------|--------------|
| `text` | Plain communication | TextMessage |
| `company_picker` | Company disambiguation | Tappable company cards with match confidence |
| `person_picker` | Person identity resolution | Candidate cards with photos/roles |
| `diff_view` | Confirm a data change | Before/after diff with approve/reject |
| `candidate_cards` | Multiple options to choose from | Card grid with selection |
| `confirmation` | Yes/no approval | Confirm/deny with context summary |
| `status_update` | Task progress | Progress indicator with details |
| `field_edit` | Edit a specific field | Inline editor with current/proposed values |
| `multi_select` | Select multiple items | Checkbox list with descriptions |
| `priority_rank` | Rank items by priority | Draggable list |

## SQL Contract (each agent implements)

```sql
-- Create a task from user input
agent_task_create(user_input text, context jsonb) → task_id

-- Get task list for the tab
agent_task_list(status text DEFAULT 'all') → tasks[]

-- Get thread messages for a task
agent_task_thread(task_id int) → messages[]

-- User responds to a thread message
agent_task_respond(task_id int, message_id int, response jsonb) → next_message

-- Agent posts a contextual question (called by agent, not user)
agent_task_post_message(task_id int, type text, content jsonb) → message_id
```

## Data Model

```sql
CREATE TABLE agent_tasks (
  id serial PRIMARY KEY,
  agent text NOT NULL, -- 'datum', 'cindy', 'megamind'
  user_input text NOT NULL,
  status text DEFAULT 'pending', -- pending, processing, needs_input, done, failed
  context jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  resolved_at timestamptz
);

CREATE TABLE agent_task_messages (
  id serial PRIMARY KEY,
  task_id int REFERENCES agent_tasks(id),
  sender text NOT NULL, -- 'user' or agent name
  type text NOT NULL, -- from message type registry
  content jsonb NOT NULL,
  response jsonb, -- user's response (filled when user responds)
  created_at timestamptz DEFAULT now()
);
```

## Tab Routes

- `/datum` — Datum task interface
- `/cindy` — Cindy communication interface (replaces /comms eventually)
- `/megamind` — Megamind strategic interface

All use the same universal thread renderer with agent-specific styling/branding.
