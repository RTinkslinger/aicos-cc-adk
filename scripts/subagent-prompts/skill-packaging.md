# Template: Skill Packaging
# Use for: Step 6 of close checklist — package ai-cos skill as .skill ZIP
# Fill in {{PLACEHOLDERS}} before sending to subagent

## SUBAGENT CONSTRAINTS (MANDATORY — DO NOT VIOLATE)

You are a Bash subagent running in a Linux VM sandbox. You have:
- ✅ Bash, Read, Edit, Write, Glob, Grep tools
- ❌ NO MCP tools (no osascript, no present_files, no Notion, no web access)
- ❌ NO ability to delete files on mounted folders (rm fails silently or errors)
- ❌ NO outbound network (no curl, wget, git push)

CRITICAL RULES:
- .skill files MUST be ZIP archives containing {skill-name}/SKILL.md directory structure
- .skill frontmatter MUST include `version` field matching the target version
- .skill description MUST be ≤1024 characters
- Package to the MOUNTED path so main session can present_files on it
- Do NOT attempt to deliver the file to the user — output "HAND-OFF: present_files" instead

## WORKING DIRECTORY
/sessions/practical-cool-hopper/mnt/Aakash AI CoS

## ALLOWED FILES
1. `/tmp/pkg/{{SKILL_NAME}}/SKILL.md` — CREATE (temp staging)
2. `{{OUTPUT_PATH}}` — CREATE (final .skill ZIP)

## PACKAGING STEPS

1. Verify source skill exists and check frontmatter version:
```bash
head -10 "{{SOURCE_SKILL_PATH}}"
```

2. Check frontmatter version matches target:
- Expected: `version: {{TARGET_VERSION}}`
- If mismatched, Edit the source to fix BEFORE packaging

3. Check description length:
```bash
grep -A1 "^description:" "{{SOURCE_SKILL_PATH}}" | wc -c
```
- Must be ≤1024 chars. If over, trim trigger words.

4. Package:
```bash
mkdir -p /tmp/pkg/{{SKILL_NAME}}
cp "{{SOURCE_SKILL_PATH}}" /tmp/pkg/{{SKILL_NAME}}/SKILL.md
cd /tmp/pkg
zip -r "{{OUTPUT_PATH}}" {{SKILL_NAME}}/
```

5. Verify:
```bash
unzip -l "{{OUTPUT_PATH}}"
```

## HAND-OFF TO MAIN SESSION
After completion, main session MUST:
```
present_files([{"file_path": "{{OUTPUT_PATH}}"}])
```
User double-clicks to install in Cowork.

## TYPICAL VALUES
- SKILL_NAME: ai-cos
- SOURCE_SKILL_PATH: skills/ai-cos-v6-skill.md
- TARGET_VERSION: {{NEW_VERSION}}
- OUTPUT_PATH: /sessions/practical-cool-hopper/mnt/Aakash AI CoS/ai-cos-{{NEW_VERSION}}.skill
