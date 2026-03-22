#!/bin/bash
# BLOCKER HOOK: PreToolUse on mcp__plugin_supabase_supabase__execute_sql
# Scans SQL for CREATE FUNCTION that generates intelligence. BLOCKS execution.
# This is the ENFORCEMENT layer — instructions failed 100+ times, this hook cannot be bypassed.

# Read the tool input (contains the SQL query)
INPUT=$(cat)

# Extract the SQL query
SQL=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('query', data.get('input', {}).get('query', '')))
except:
    print('')
" 2>/dev/null)

# Only check CREATE FUNCTION statements
if ! echo "$SQL" | grep -qi "CREATE.*FUNCTION\|CREATE.*OR.*REPLACE.*FUNCTION"; then
  exit 0
fi

# Extract function name
FUNC_NAME=$(echo "$SQL" | grep -oi "FUNCTION[[:space:]]*[a-z_]*" | head -1 | awk '{print $2}')

# Check for intelligence-generating patterns in the function body
VIOLATIONS=$(echo "$SQL" | python3 -c "
import sys
sql = sys.stdin.read().lower()

# Intelligence-generating verb patterns (in function BODY, not comments)
intel_verbs = [
    'intelligence', 'briefing', 'assess', 'recommend', 'detect_',
    'generate_', 'analyze', 'evaluate', 'classify', 'predict',
    'summarize', 'synthesize', 'diagnose', 'infer', 'reason',
    'auto_process', 'brain', 'smart',
]

# Allowed exceptions (utility/infrastructure)
allowed = [
    'search', 'fuzzy', 'match', 'similarity', 'embed',
    'resolve', 'merge', 'bridge', 'score',  # scoring formula is hybrid exception
    'benchmark', 'test', 'check', 'validate',
    'list', 'get', 'fetch', 'count', 'sum',
    'queue', 'log', 'save', 'store', 'create_task',
    'refresh', 'snapshot', 'cleanup', 'migrate',
    'write', 'insert', 'update', 'upsert',  # write helpers for agent output
]

# Check if the function body is a simple write helper (INSERT/UPDATE only)
# These are plumbing — agent calls them to persist output. Allow regardless of name.
body_after_begin = sql.split('begin')[-1] if 'begin' in sql else sql
is_simple_write = (
    ('insert into' in body_after_begin or 'update ' in body_after_begin) and
    body_after_begin.count('select') <= 2 and  # at most 1-2 subselects for IDs
    'for ' not in body_after_begin and  # no loops = not complex logic
    len(body_after_begin) < 1500  # short body = plumbing, not intelligence
)

if is_simple_write:
    # Simple write helper — allow it
    pass
else:
    # Check if function name contains intelligence verbs
    violations = []
    func_name_area = (sql.split('function')[1] if 'function' in sql else sql)[:200]
    for v in intel_verbs:
        if v in func_name_area:
            is_allowed = any(a in func_name_area for a in allowed)
            if not is_allowed:
                violations.append(v)

# Check function body for complex intelligence patterns (only if not simple write)
if not is_simple_write:
    # Count intelligence indicators in body
    intel_indicators = 0
    for pattern in ['briefing', 'intelligence', 'recommendation', 'assessment', 'analysis', 'report', 'dashboard', 'summary']:
        if pattern in sql:
            intel_indicators += 1

# If function has 3+ intelligence indicators AND builds complex JSON, it's likely generating intelligence
if intel_indicators >= 3:
    violations.append(f'body has {intel_indicators} intelligence indicators')

if violations:
    print('|'.join(violations))
" 2>/dev/null)

if [ -n "$VIOLATIONS" ]; then
  echo "🚫 BLOCKED: SQL function '$FUNC_NAME' appears to generate intelligence."
  echo ""
  echo "   Violations detected: $VIOLATIONS"
  echo ""
  echo "   RULE: SQL functions CANNOT generate briefings, assess risk, detect signals,"
  echo "   recommend actions, summarize relationships, or produce intelligence."
  echo "   That work belongs in a PERSISTENT CLAUDE AGENT SDK AGENT."
  echo ""
  echo "   ALLOWED SQL: search, fuzzy match, embedding similarity, scoring formula"
  echo "   execution, simple CRUD, queue management, data aggregation."
  echo ""
  echo "   If this function is a legitimate utility tool, rename it to avoid"
  echo "   intelligence-generating verb patterns (detect_, assess_, generate_,"
  echo "   intelligence_, briefing_, recommend_, analyze_)."
  echo ""
  echo "   DO NOT PROCEED. Rethink the approach. The agent should reason and write"
  echo "   outputs to a table. This SQL function should NOT exist."

  # Return non-zero to BLOCK the tool use
  exit 2
fi

exit 0
