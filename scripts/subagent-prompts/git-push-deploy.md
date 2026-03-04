# Template: Git Commit + Deploy (aicos-digests)
# Use for: Committing changes to aicos-digests and triggering deploy
# Fill in {{PLACEHOLDERS}} before sending to subagent

## SUBAGENT CONSTRAINTS (MANDATORY — DO NOT VIOLATE)

You are a Bash subagent running in a Linux VM sandbox. You have:
- ✅ Bash, Read, Edit, Write, Glob, Grep tools
- ❌ NO MCP tools (no osascript, no present_files, no Notion, no web access)
- ❌ NO outbound network — git push WILL FAIL from sandbox
- ❌ NO ability to run osascript

CRITICAL RULES:
- Git operations ONLY inside aicos-digests/ (the actual git repo)
- NEVER run git commands in the parent /mnt/Aakash AI CoS/ folder
- You CAN: git add, git commit (these are local operations)
- You CANNOT: git push (requires network) — output HAND-OFF instead
- Validate JSON before committing to src/data/ (invalid JSON breaks Next.js SSG)

## WORKING DIRECTORY
/sessions/practical-cool-hopper/mnt/Aakash AI CoS/aicos-digests

## ALLOWED FILES
{{FILE_ALLOWLIST}}

## STEPS

1. Verify working directory is correct:
```bash
cd /sessions/practical-cool-hopper/mnt/Aakash\ AI\ CoS/aicos-digests && git status
```

2. Make file changes as needed (Read → Edit pattern)

3. If any JSON files modified, validate:
```bash
python3 -c "import json; json.load(open('{{JSON_FILE_PATH}}'))" 2>&1
```

4. Stage and commit:
```bash
cd /sessions/practical-cool-hopper/mnt/Aakash\ AI\ CoS/aicos-digests
git add {{FILES_TO_STAGE}}
git commit -m "{{COMMIT_MESSAGE}}"
```

5. Output HAND-OFF for push:
```
HAND-OFF: Main session must run osascript for git push:
osascript MCP: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"
```

## HAND-OFF TO MAIN SESSION
After subagent completes, main session runs:
```
mcp__Control_your_Mac__osascript:
do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"
```
Then wait ~90s for GitHub Action → Vercel deploy.

## DEPLOY ARCHITECTURE (single path)
Cowork: git commit locally → osascript MCP: git push origin main (Mac host) → GitHub Action → Vercel prod (~90s)
