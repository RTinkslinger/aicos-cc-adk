#!/bin/bash
# Live content agent log — real-time tool calls, thinking, text
trap "exit" INT TERM
touch /opt/agents/content/live.log
tail -n20 -f /opt/agents/content/live.log
