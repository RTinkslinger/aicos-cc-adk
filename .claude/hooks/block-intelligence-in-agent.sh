#!/bin/bash
# BLOCKER HOOK: PreToolUse on Agent
# Scans agent prompts for instructions to BUILD intelligence-generating SQL.
# Catches the violation at the INSTRUCTION level before the agent even starts.

PROMPT=$(cat)

# Check if the agent prompt instructs building intelligence SQL
VIOLATIONS=$(echo "$PROMPT" | python3 -c "
import sys
prompt = sys.stdin.read().lower()

# Patterns that indicate the agent is being told to build intelligence SQL
bad_patterns = [
    'build.*sql.*function.*that.*detect',
    'build.*sql.*function.*that.*assess',
    'build.*sql.*function.*that.*recommend',
    'build.*sql.*function.*that.*generat',
    'build.*sql.*function.*that.*analyz',
    'build.*sql.*function.*that.*summar',
    'build.*sql.*function.*that.*briefing',
    'build.*sql.*function.*that.*intelligence',
    'create.*sql.*that.*reason',
    'sql.*function.*to.*detect.*obligation',
    'sql.*function.*to.*generate.*report',
    'sql.*function.*to.*assess.*risk',
    'sql.*function.*to.*recommend',
    'sql.*function.*to.*produce.*intelligence',
    'auto_process',  # the specific pattern that keeps recurring
]

import re
found = []
for p in bad_patterns:
    if re.search(p, prompt):
        found.append(p)

if found:
    print('|'.join(found[:3]))
" 2>/dev/null)

if [ -n "$VIOLATIONS" ]; then
  echo "🚫 WARNING: Agent prompt contains instructions to build intelligence-generating SQL."
  echo ""
  echo "   Detected patterns: $VIOLATIONS"
  echo ""
  echo "   RULE: Machine loops build AGENT capabilities (CLAUDE.md, skills, tools)."
  echo "   They do NOT build SQL functions that generate intelligence."
  echo "   Intelligence = agent reasoning. SQL = data access tools."
  echo ""
  echo "   If the agent needs to produce briefings/intelligence/assessments:"
  echo "   → Build the agent's CLAUDE.md to define the objective"
  echo "   → Build skills that show patterns of success"
  echo "   → Build simple SQL TOOLS the agent calls for data access"
  echo "   → The agent REASONS and WRITES outputs to DB tables"
  echo ""
  echo "   REWRITE the agent prompt to build agent capabilities, not SQL intelligence."
fi

exit 0
