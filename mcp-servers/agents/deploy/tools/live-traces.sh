#!/bin/bash
# Live traces viewer — follows active traces file
trap "exit" INT TERM
FILE="/opt/agents/$(cat /opt/agents/traces/active.txt 2>/dev/null)"
[ ! -f "$FILE" ] && echo "No active traces file" && exit 1
tail -n10 -f "$FILE"
