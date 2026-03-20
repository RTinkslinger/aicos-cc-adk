#!/bin/bash
# Live datum agent log — real-time tool calls, thinking, text
trap "exit" INT TERM
touch /opt/agents/datum/live.log
tail -n20 -f /opt/agents/datum/live.log
