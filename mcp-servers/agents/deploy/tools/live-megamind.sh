#!/bin/bash
# Live megamind agent log — real-time tool calls, thinking, text
trap "exit" INT TERM
touch /opt/agents/megamind/live.log
tail -n20 -f /opt/agents/megamind/live.log
