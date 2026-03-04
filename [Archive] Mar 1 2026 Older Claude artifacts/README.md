# Aakash AI CoS — AI Chief of Staff

## What is this?

An AI-powered Chief of Staff system for **Aakash Kumar**, Managing Director at **Z47** ($550M) and **DeVC** ($60M). The goal: Claude becomes a deeply embedded operating partner across deal flow, portfolio monitoring, fund operations, content creation, and IC collective management.

## Principal

- **Aakash Kumar** — 2x founder, ex-CSO Housing.com, ex-Growth lead Disney+ Hotstar, angel investor (100+ cos)
- Sectors: Enterprise AI, Fintech, Consumer, Manufacturing, Robotics, Space Tech
- Based: Bengaluru, India
- Builder: codes daily with Claude Code, deep understanding of AI/ML/RL

## Funds

| | Z47 | DeVC |
|---|---|---|
| AUM | $550M | $60M |
| Stage | Seed → Series B | Pre-seed → Seed |
| Check | $2M–$30M | $50K–$500K |
| Portfolio/cycle | ~45 cos | 140–150 cos |
| Model | Classic VC | Collaborative (IC Collective) |
| Follow-on | 50% reserves; defend & accrete | Accrete to 5%+ in 1-in-7 |

## Development Philosophy

**Phase A (Now):** Patchy but functional. Use available tools, learn, document everything.  
**Phase B (Later):** Enterprise-grade build. Spec-driven, informed by Phase A learnings.

## Current Stack

| Layer | Tool | Notes |
|---|---|---|
| AI | Claude Max (Cowork + Code + Chat) | via hi@aacash.me |
| Email/Cal | Microsoft 365 | Z47 + DeVC fund accounts |
| CRM (target) | Attio | Migration from Notion WIP |
| CRM (DeVC legacy) | Notion | Network DB + Companies DB |
| Meeting Notes | Granola | Mac only (iOS gap) |
| Messaging | WhatsApp | No direct AI integration |
| Personal Dev | Google Workspace + Supabase | Prototyping base |

## Workstreams

1. **WS1: Deal Flow Intelligence** — sourcing, screening, pipeline
2. **WS2: Portfolio Monitoring & Lines Over Dots** — founder tracking, follow-on signals
3. **WS3: Investment Decision Intelligence** — RL model on 250+ historical decisions
4. **WS4: LP & Fund Operations** — reporting, compliance, analytics
5. **WS5: Platform & Founder Enablement** — research, hiring, GTM for portcos
6. **WS6: Personal Productivity & Content** — email, calendar, content pipeline
7. **WS7: IC Collective Management** — deal sharing, co-evaluation, relationship mgmt

## File Structure

```
~/aakash-ai-cos/
├── README.md
├── PLAN.md
├── docs/
│   ├── plan-versions/
│   ├── adr/
│   ├── iteration-logs/
│   ├── stack-discoveries/
│   └── research/
├── skills/
│   ├── deal-memo/SKILL.md
│   ├── founder-profile/SKILL.md
│   ├── meeting-prep/SKILL.md
│   ├── portfolio-review/SKILL.md
│   ├── lp-report/SKILL.md
│   ├── ic-comm/SKILL.md
│   └── content-pipeline/SKILL.md
├── plugins/
│   └── vc-cos/
├── mcp-servers/
│   ├── attio-mcp/
│   └── whatsapp-bridge/
├── data/
│   ├── deal-history/
│   ├── founder-observations/
│   ├── portfolio-kpis/
│   └── social-analysis/
├── models/
│   ├── deal-scorer/
│   └── followon-signal/
└── templates/
    ├── deal-memo-template.md
    ├── founder-brief-template.md
    ├── lp-update-template.md
    └── ic-deal-share-template.md
```

## Quick Start (Cowork)

1. Open Claude Desktop → Cowork tab
2. Point to `~/aakash-ai-cos/` folder
3. "Read README.md and PLAN.md to understand the project context"
4. Start with any workstream

## Quick Start (Claude Code)

```bash
cd ~/aakash-ai-cos
claude "Read PLAN.md and help me build the meeting-prep skill"
```

## Version

- **v0.2** — March 1, 2026 (Planning Interview Phase)
- See `docs/plan-versions/` for history
