# LEARNINGS.md

Trial-and-error patterns discovered during Claude Code sessions.
Patterns confirmed 2+ times graduate to CLAUDE.md during milestone compaction.

## Active Patterns

### 2026-03-06 - Sprint 2
- Tried: Build Roadmap `notion-create-pages` with plain text select values ("Planned", "Sequential", "Core Product", "XS (<1hr)")
  Works: Must use emoji-prefixed values matching exact Notion options: "🎯 Planned", "🔴 Sequential", "🟢 Safe", "XS (< 1hr)" (note space before 1hr)
  Context: Build Roadmap DB select fields all have emoji prefixes and exact spacing. Always query the DB schema first or use known exact values.
  Confirmed: 1x (4 consecutive failures in one call sequence)

- Tried: Using CLAUDE.md Build Roadmap "Creating items" recipe with generic Epic values ("Core Product", "Data & Schema", etc.)
  Works: Actual Epic options are project-specific: "Content Pipeline v5", "Action Frontend", "Knowledge Store", "Multi-Surface", "Meeting Optimizer", "Always-On", "Infrastructure"
  Context: The Build System Protocol template in CLAUDE.md has generic placeholder Epic values. Must use actual DB options. Update CLAUDE.md recipe if this recurs.
  Confirmed: 1x
