#!/bin/bash
# Live cindy agent log — real-time tool calls, thinking, text
trap "exit" INT TERM
touch /opt/agents/cindy/live.log
tail -n20 -f /opt/agents/cindy/live.log
