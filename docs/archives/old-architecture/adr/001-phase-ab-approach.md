# ADR-001: Phase A/B Development Approach

**Status:** Accepted  
**Date:** March 1, 2026  
**Decision Maker:** Aakash Kumar

## Context

Aakash wants to build an AI Chief of Staff that deeply embeds Claude into his work as a VC managing two funds (Z47 + DeVC). The system will touch deal flow, portfolio monitoring, fund operations, content creation, and IC collective management.

There are two approaches:
1. **Spec-first:** Design the full architecture upfront, then build
2. **Iterate-first:** Build a patchy working version, learn, then redesign for production

## Decision

**Iterate-first (Phase A/B).** Build a functional but imperfect system using available tools (Phase A), document all learnings, then use those learnings to inform an enterprise-grade build (Phase B).

## Rationale

- The AI tooling landscape is moving fast (Cowork, MCP connectors, plugins all shipped in Jan-Feb 2026). Locking in architecture too early risks building on unstable foundations.
- VC workflows are complex and personal. What Aakash *thinks* he needs vs. what the AI CoS *actually* needs to do will diverge. Phase A exposes this.
- Attio migration is WIP. Building on a moving CRM creates coupling risk.
- Aakash's operating experience (Hotstar, Housing.com) validates this approach: ship, learn, rebuild.

## Consequences

- Phase A outputs will be imperfect and sometimes manual
- Documentation overhead is high (every session must produce iteration logs)
- Phase B timeline depends on Phase A duration and learning velocity
- Some Phase A code/skills will be thrown away — that's by design

## Related

- Stack Map (Plan v0.2, Section 3)
- Development Philosophy (Plan v0.2, Section 4)
