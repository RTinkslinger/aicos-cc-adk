#!/bin/bash
# Live orchestrator log — real-time tool calls, thinking, text
trap "exit" INT TERM
touch /opt/agents/orchestrator/live.log
tail -n20 -f /opt/agents/orchestrator/live.log
