#!/usr/bin/env python3
"""Clean JSONL log viewer for Claude Agent SDK sessions."""
import sys
import json

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"
GRAY = "\033[90m"
PURPLE = "\033[1;35m"
RESET = "\033[0m"

for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        t = d.get("type", "?")
        ts = d.get("timestamp", "")
        short_ts = ts[11:19] if len(ts) > 19 else ""

        if t == "user":
            msg = d.get("message", {})
            content = msg.get("content", [])
            if isinstance(content, str):
                print(f"{CYAN}{short_ts} >>> {content[:120]}{RESET}")
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict):
                        ct = c.get("type", "")
                        if ct == "text":
                            print(f"{CYAN}{short_ts} >>> {c['text'][:120]}{RESET}")
                        elif ct == "tool_result":
                            raw = c.get("content", "")
                            if isinstance(raw, str):
                                txt = raw[:150]
                            elif isinstance(raw, list):
                                txt = str(raw[0].get("text", ""))[:150] if raw else ""
                            else:
                                txt = str(raw)[:150]
                            tid = c.get("tool_use_id", "")[-6:]
                            print(f"{YELLOW}{short_ts}   <- [{tid}] {txt}{RESET}")

        elif t == "assistant":
            msg = d.get("message", {})
            content = msg.get("content", [])
            usage = msg.get("usage", {})
            for c in content:
                ct = c.get("type", "")
                if ct == "tool_use":
                    inp = str(c.get("input", ""))[:130]
                    tid = c.get("id", "")[-6:]
                    print(f"{GREEN}{short_ts}   TOOL [{tid}] {c['name']}: {inp}{RESET}")
                elif ct == "text":
                    txt = c.get("text", "")[:180]
                    if txt.strip():
                        print(f"{WHITE}{short_ts}   {txt}{RESET}")
                elif ct == "thinking":
                    think = c.get("thinking", "")[:100]
                    if think.strip():
                        print(f"{GRAY}{short_ts}   (think) {think}{RESET}")
            if usage:
                i = usage.get("input_tokens", 0)
                o = usage.get("output_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)
                cc = usage.get("cache_creation_input_tokens", 0)
                parts = []
                if i:
                    parts.append(f"in={i}")
                if o:
                    parts.append(f"out={o}")
                if cr:
                    parts.append(f"cache_read={cr}")
                if cc:
                    parts.append(f"cache_create={cc}")
                if parts:
                    joined = " ".join(parts)
                    print(f"{GRAY}           [{joined}]{RESET}")

        elif t == "progress":
            sub = d.get("subtype", "")
            cost = d.get("costUsd") or d.get("total_cost_usd") or 0
            turns = d.get("numTurns") or d.get("num_turns") or 0
            dur = d.get("durationMs") or d.get("duration_ms") or 0
            if sub or cost:
                sec = dur / 1000 if dur else 0
                print(f"{PURPLE}{short_ts} === {sub}: ${cost:.4f} | {turns} turns | {sec:.1f}s ==={RESET}")

    except Exception:
        pass
