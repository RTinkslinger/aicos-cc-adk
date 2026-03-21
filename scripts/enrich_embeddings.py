#!/usr/bin/env python3
"""
Enrich company embeddings by extracting page content summaries
and writing them to agent_ids_notes column.

Outputs SQL files in batches of 100 for execution via Supabase MCP.
"""

import json
import os
import re
import sys

COMPANIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "companies-pages")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql")
MAX_CONTENT_LENGTH = 1500  # chars for embedding input
BATCH_SIZE = 10


def extract_meaningful_content(filepath: str) -> str:
    """Extract structured, meaningful content from a company page file.

    Strips:
    - YAML frontmatter
    - Raw transcripts (conversational noise)
    - Template boilerplate (READ ME, scoring tables, etc.)
    - Empty/minimal pages

    Keeps:
    - Deck summaries, problem/solution/market sections
    - AI-generated structured notes (Action Items, summaries)
    - RM reflections and scoring notes
    - Meeting context and key observations
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip YAML frontmatter
    content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Check for empty pages or template-only pages
    if "*No page body content found.*" in content:
        return ""
    if 'content_type: "template_only"' in content:
        return ""
    if content.strip().startswith("## Template Page"):
        return ""

    lines = content.split("\n")

    # Skip pages that are just a title (< 15 meaningful lines)
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    if len(non_empty_lines) < 5:
        return ""

    # Skip pages that are purely template (scoring rubrics with no filled data)
    template_markers = [
        "Here's how you are supposed to use the COMMENTS section",
        "Here's how you are supposed to use the BODY section",
        "Once you have READ THIS",
        "WHEN this company moves from Pipeline to Portfolio",
    ]
    has_template = any(m in content for m in template_markers)

    # Check if there's any substantive content beyond template
    # Look for actual notes: meeting dates, founder info, scoring data filled in
    substantive_markers = [
        "notes:", "traction", "revenue", "product", "founder",
        "raised", "round", "deck", "market", "problem", "solution",
        "Inbound via", "Source:", "reflections", "meeting",
    ]
    has_substance = any(m.lower() in content.lower() for m in substantive_markers)

    if has_template and not has_substance:
        return ""

    # Build sections, keeping structured content and dropping raw transcripts
    sections = []
    current_section = []
    current_header = ""
    in_transcript_block = False
    in_template_block = False

    for line in lines:
        # Detect transcript blocks (raw conversational text)
        if "<!-- transcription block -->" in line:
            in_transcript_block = True
            continue

        # Detect template/boilerplate blocks
        if "READ ME" in line and "template" in content[:500].lower():
            in_template_block = True
            continue
        if "WHEN this company moves from Pipeline" in line:
            in_template_block = True
            continue
        if "Once you have READ THIS" in line:
            in_template_block = False
            continue

        # Headers reset context
        if line.startswith("## ") or line.startswith("### "):
            if current_section and current_header:
                sections.append((current_header, "\n".join(current_section)))
            current_header = line.strip("# ").strip()
            current_section = []
            in_transcript_block = False
            in_template_block = False
            continue

        if in_transcript_block or in_template_block:
            # Still capture AI-structured notes within transcript blocks
            if line.strip().startswith("### ") or line.strip().startswith("- **"):
                current_section.append(line)
            continue

        # Skip scoring table rows
        if line.strip().startswith("|") and ("Score" in line or "---" in line or "Select" in line):
            continue

        # Skip file block markers
        if "<!-- file block -->" in line:
            continue

        current_section.append(line)

    # Don't forget last section
    if current_section and current_header:
        sections.append((current_header, "\n".join(current_section)))

    # Priority order for content extraction:
    # 1. Deck summaries, problem/solution/market
    # 2. AI structured notes (Action Items, backgrounds, etc.)
    # 3. RM reflections
    # 4. Meeting context
    priority_keywords = [
        "deck summary", "problem", "solution", "market", "product",
        "competition", "progress", "roadmap", "use case", "gtm",
        "team", "fundrais", "current", "differentiat",
        "action item", "background", "technology", "strategy",
        "concern", "advisor", "engagement",
        "RM reflect", "RM notes",
    ]

    # Score sections by priority
    scored_sections: list[tuple[int, str, str]] = []
    for header, body in sections:
        score = 0
        header_lower = header.lower()
        body_lower = body.lower()
        combined = header_lower + " " + body_lower

        for kw in priority_keywords:
            if kw.lower() in combined:
                score += 2

        # Penalize sections that look like raw conversation
        conversation_markers = ["yeah", "okay", "uh", "um", "hmm", "like,"]
        conv_count = sum(1 for m in conversation_markers if m in body_lower)
        if conv_count > 5:
            score -= 3

        # Bonus for structured content (bullet points, bold text)
        if body.count("- ") > 3 or body.count("**") > 3:
            score += 2

        scored_sections.append((score, header, body))

    # Sort by score (highest first) and build output
    scored_sections.sort(key=lambda x: x[0], reverse=True)

    result_parts: list[str] = []
    char_count = 0

    for score, header, body in scored_sections:
        if score < 0:
            continue

        # Clean up the body
        body_lines = [l.strip() for l in body.split("\n") if l.strip()]
        cleaned = f"{header}: " + " ".join(body_lines)

        if char_count + len(cleaned) > MAX_CONTENT_LENGTH:
            remaining = MAX_CONTENT_LENGTH - char_count
            if remaining > 100:  # Only add if meaningful amount left
                result_parts.append(cleaned[:remaining] + "...")
            break

        result_parts.append(cleaned)
        char_count += len(cleaned) + 1  # +1 for newline

    return "\n".join(result_parts)


def escape_sql_string(s: str) -> str:
    """Escape a string for safe SQL inclusion."""
    return s.replace("'", "''").replace("\\", "\\\\")


def build_batch_sql(batch: list[tuple[int, str]]) -> str:
    """Build a SQL call to util.batch_update_agent_notes with JSON payload."""
    if not batch:
        return ""

    # Build JSON array
    items = []
    for company_id, content in batch:
        # Escape for JSON inside SQL string
        escaped = content.replace("\\", "\\\\").replace("'", "''").replace('"', '\\"')
        items.append(f'{{"id": "{company_id}", "content": "{escaped}"}}')

    json_array = "[" + ", ".join(items) + "]"

    return f"SELECT util.batch_update_agent_notes('{json_array}'::jsonb);"


def build_batch_json(batch: list[tuple[int, str]]) -> str:
    """Build a JSON file for the batch (used by runner script)."""
    items = [{"id": cid, "content": content} for cid, content in batch]
    return json.dumps(items, ensure_ascii=False)


def build_batch_case_sql(batch: list[tuple[int, str]]) -> str:
    """Build a CASE WHEN UPDATE statement for a batch."""
    if not batch:
        return ""

    case_parts = []
    ids = []
    for company_id, content in batch:
        escaped = escape_sql_string(content)
        case_parts.append(f"    WHEN {company_id} THEN '{escaped}'")
        ids.append(str(company_id))

    case_sql = "\n".join(case_parts)
    id_list = ", ".join(ids)

    return f"""UPDATE companies
SET agent_ids_notes = CASE id
{case_sql}
    ELSE agent_ids_notes
END
WHERE id IN ({id_list})
  AND (agent_ids_notes IS NULL OR agent_ids_notes = '');"""


def main():
    # Load the company-to-file mapping from stdin or a JSON file
    mapping_file = os.path.join(OUTPUT_DIR, "company_mapping.json")

    if not os.path.exists(mapping_file):
        print(f"ERROR: {mapping_file} not found. Create it first with the company ID -> file path mapping.")
        sys.exit(1)

    with open(mapping_file, "r") as f:
        mapping = json.load(f)  # list of {id, page_content_path}

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process each company
    enriched: list[tuple[int, str]] = []
    skipped_empty = 0
    skipped_missing = 0

    for entry in mapping:
        company_id = entry["id"]
        page_path = entry["page_content_path"]
        filepath = os.path.join(os.path.dirname(COMPANIES_DIR), page_path)

        if not os.path.exists(filepath):
            skipped_missing += 1
            continue

        content = extract_meaningful_content(filepath)
        if not content:
            skipped_empty += 1
            continue

        enriched.append((company_id, content))

    print(f"Total companies with page_content_path: {len(mapping)}")
    print(f"Companies with extractable content: {len(enriched)}")
    print(f"Skipped (empty/minimal): {skipped_empty}")
    print(f"Skipped (file missing): {skipped_missing}")

    # Write batched SQL files (CASE WHEN style) and JSON files
    batch_count = 0
    for i in range(0, len(enriched), BATCH_SIZE):
        batch = enriched[i:i + BATCH_SIZE]

        # Write CASE WHEN SQL
        sql = build_batch_case_sql(batch)
        batch_file = os.path.join(OUTPUT_DIR, f"batch_{batch_count:03d}.sql")
        with open(batch_file, "w") as f:
            f.write(sql)

        # Write JSON for the stored procedure approach
        json_data = build_batch_json(batch)
        json_file = os.path.join(OUTPUT_DIR, f"batch_{batch_count:03d}.json")
        with open(json_file, "w") as f:
            f.write(json_data)

        batch_count += 1
        print(f"  Wrote batch_{batch_count - 1:03d} ({len(batch)} companies)")

    # Write a summary
    summary = {
        "total_mapping": len(mapping),
        "enriched": len(enriched),
        "skipped_empty": skipped_empty,
        "skipped_missing": skipped_missing,
        "batch_count": batch_count,
        "batch_size": BATCH_SIZE,
    }
    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nTotal batches: {batch_count}")
    print(f"Run each batch via Supabase MCP execute_sql")


if __name__ == "__main__":
    main()
