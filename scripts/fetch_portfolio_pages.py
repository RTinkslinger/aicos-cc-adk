#!/usr/bin/env python3
"""Fetch Notion page body content for all portfolio companies and save as markdown.
Uses only stdlib (urllib) — no external dependencies required.
Sequential processing with rate limiting to avoid 429s."""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

NOTION_TOKEN = "os.environ.get("NOTION_TOKEN", "")"
NOTION_VERSION = "2022-06-28"
PORTFOLIO_DIR = Path(__file__).parent.parent / "portfolio-pages"
MIN_REQUEST_INTERVAL = 0.4  # seconds between requests (~2.5 req/s, under 3 req/s limit)

last_request_time = 0.0


def rate_limited_get(url: str) -> dict:
    """Make a GET request to Notion API with rate limiting and retry."""
    global last_request_time
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
    }
    for attempt in range(5):
        # Enforce minimum interval
        elapsed = time.time() - last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)

        last_request_time = time.time()
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = float(e.headers.get("Retry-After", "3"))
                print(f"    429 rate limited, waiting {retry_after}s (attempt {attempt+1})")
                time.sleep(retry_after)
                continue
            body = e.read().decode("utf-8", errors="replace")[:200]
            print(f"    HTTP {e.code}: {body}")
            return {}
        except Exception as e:
            print(f"    Request error: {e}")
            if attempt < 4:
                time.sleep(2)
                continue
            return {}
    return {}


def fetch_all_blocks(page_id: str, depth: int = 0) -> list:
    """Fetch all blocks for a page, handling pagination and children."""
    if depth > 3:  # safety limit on recursion
        return []
    all_blocks = []
    cursor = None

    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"

        data = rate_limited_get(url)
        if not data:
            break

        results = data.get("results", [])
        for block in results:
            all_blocks.append(block)
            if block.get("has_children", False):
                btype = block["type"]
                child_blocks = fetch_all_blocks(block["id"], depth + 1)
                if btype == "table":
                    all_blocks.extend(child_blocks)
                elif btype in ("column_list", "column"):
                    all_blocks.extend(child_blocks)
                elif btype == "synced_block":
                    block[btype]["children"] = child_blocks
                elif btype in ("bulleted_list_item", "numbered_list_item", "toggle"):
                    all_blocks.extend(child_blocks)

        if not data.get("has_more", False):
            break
        cursor = data.get("next_cursor")

    return all_blocks


def format_rich_text(rich_text: list) -> str:
    """Format rich_text array with annotations."""
    parts = []
    for rt in rich_text:
        t = rt.get("plain_text", "")
        ann = rt.get("annotations", {})
        href = rt.get("href")
        if ann.get("code"):
            t = f"`{t}`"
        if ann.get("bold"):
            t = f"**{t}**"
        if ann.get("italic"):
            t = f"*{t}*"
        if ann.get("strikethrough"):
            t = f"~~{t}~~"
        if href:
            t = f"[{t}]({href})"
        parts.append(t)
    return "".join(parts)


def blocks_to_markdown(blocks: list) -> str:
    """Convert Notion blocks to markdown text."""
    lines = []
    numbered_counter = 0

    for block in blocks:
        btype = block.get("type", "")
        block_data = block.get(btype, {})
        rich_text = block_data.get("rich_text", [])
        plain = "".join(rt.get("plain_text", "") for rt in rich_text)
        formatted = format_rich_text(rich_text) if rich_text else plain

        if btype == "paragraph":
            lines.append(formatted)
            numbered_counter = 0
        elif btype == "heading_1":
            lines.append(f"# {formatted}")
            numbered_counter = 0
        elif btype == "heading_2":
            lines.append(f"## {formatted}")
            numbered_counter = 0
        elif btype == "heading_3":
            lines.append(f"### {formatted}")
            numbered_counter = 0
        elif btype == "bulleted_list_item":
            lines.append(f"- {formatted}")
        elif btype == "numbered_list_item":
            numbered_counter += 1
            lines.append(f"{numbered_counter}. {formatted}")
        elif btype == "to_do":
            checked = block_data.get("checked", False)
            marker = "[x]" if checked else "[ ]"
            lines.append(f"- {marker} {formatted}")
            numbered_counter = 0
        elif btype == "toggle":
            lines.append(f"<details><summary>{formatted}</summary></details>")
            numbered_counter = 0
        elif btype == "callout":
            icon = block_data.get("icon", {})
            emoji = icon.get("emoji", "") if icon else ""
            prefix = f"{emoji} " if emoji else ""
            lines.append(f"> {prefix}{formatted}")
            numbered_counter = 0
        elif btype == "quote":
            lines.append(f"> {formatted}")
            numbered_counter = 0
        elif btype == "divider":
            lines.append("---")
            numbered_counter = 0
        elif btype == "code":
            lang = block_data.get("language", "")
            lines.append(f"```{lang}")
            lines.append(plain)
            lines.append("```")
            numbered_counter = 0
        elif btype == "image":
            url = ""
            if block_data.get("type") == "file":
                url = block_data.get("file", {}).get("url", "")
            elif block_data.get("type") == "external":
                url = block_data.get("external", {}).get("url", "")
            caption = "".join(rt.get("plain_text", "") for rt in block_data.get("caption", []))
            lines.append(f"![{caption}]({url})")
            numbered_counter = 0
        elif btype == "bookmark":
            url = block_data.get("url", "")
            caption = "".join(rt.get("plain_text", "") for rt in block_data.get("caption", []))
            lines.append(f"[{caption or url}]({url})")
            numbered_counter = 0
        elif btype == "embed":
            url = block_data.get("url", "")
            lines.append(f"[Embed: {url}]({url})")
            numbered_counter = 0
        elif btype == "child_page":
            title = block_data.get("title", "")
            lines.append(f"**[Child Page: {title}]**")
            numbered_counter = 0
        elif btype == "child_database":
            title = block_data.get("title", "")
            lines.append(f"**[Child Database: {title}]**")
            numbered_counter = 0
        elif btype == "synced_block":
            children = block_data.get("children", [])
            if children:
                lines.append(blocks_to_markdown(children))
            numbered_counter = 0
        elif btype in ("column_list", "column"):
            numbered_counter = 0
        elif btype == "table":
            numbered_counter = 0
        elif btype == "table_row":
            cells = block_data.get("cells", [])
            row = " | ".join(
                "".join(rt.get("plain_text", "") for rt in cell)
                for cell in cells
            )
            lines.append(f"| {row} |")
            numbered_counter = 0
        elif btype == "link_preview":
            url = block_data.get("url", "")
            lines.append(f"[Link: {url}]({url})")
            numbered_counter = 0
        elif btype == "equation":
            expr = block_data.get("expression", "")
            lines.append(f"$$\n{expr}\n$$")
            numbered_counter = 0
        elif btype == "link_to_page":
            if block_data.get("type") == "page_id":
                ref_id = block_data.get("page_id", "")
                lines.append(f"[Link to page: {ref_id}]")
            numbered_counter = 0
        else:
            if plain:
                lines.append(f"<!-- {btype}: {plain} -->")
            numbered_counter = 0

    return "\n\n".join(lines)


def process_page(filename: str, page_id: str, company: str, index: int, total: int) -> dict:
    """Fetch and save a single page."""
    filepath = PORTFOLIO_DIR / filename
    blocks = fetch_all_blocks(page_id)
    markdown = blocks_to_markdown(blocks)

    content = f"""---
company: {company}
notion_page_id: {page_id}
source: portfolio_db
fetched: {time.strftime('%Y-%m-%d')}
---

{markdown}
"""
    filepath.write_text(content, encoding="utf-8")

    content_len = len(markdown.strip())
    status = "content" if content_len > 10 else "empty"
    print(f"  [{index}/{total}] {company}: {len(blocks)} blocks, {content_len} chars [{status}]")
    sys.stdout.flush()
    return {
        "filename": filename,
        "company": company,
        "blocks": len(blocks),
        "chars": content_len,
        "status": status,
    }


def main():
    skip_existing = "--skip-done" in sys.argv

    # Collect all pages from the portfolio-pages directory
    pages = []
    for mdfile in sorted(PORTFOLIO_DIR.glob("*.md")):
        if mdfile.name.startswith("_"):
            continue
        text = mdfile.read_text(encoding="utf-8")
        page_id = None
        company = None
        for line in text.split("\n"):
            if line.startswith("notion_page_id:"):
                page_id = line.split(":", 1)[1].strip()
            if line.startswith("company:"):
                company = line.split(":", 1)[1].strip()
        if page_id and company:
            if skip_existing and mdfile.stat().st_size > 500:
                continue
            pages.append((mdfile.name, page_id, company))

    total = len(pages)
    print(f"Pages to fetch: {total}")
    print(f"Output dir: {PORTFOLIO_DIR}")
    print(f"Rate limit: {1/MIN_REQUEST_INTERVAL:.1f} req/s")
    if skip_existing:
        print(f"Skipping files > 500 bytes (already fetched)")
    print()
    sys.stdout.flush()

    results = []
    for i, (fname, pid, co) in enumerate(pages):
        try:
            result = process_page(fname, pid, co, i + 1, total)
            results.append(result)
        except Exception as e:
            print(f"  FAILED: {fname}: {e}")
            sys.stdout.flush()
            results.append({"filename": fname, "company": co, "blocks": 0, "chars": 0, "status": "error"})

    # Summary
    with_content = sum(1 for r in results if r["status"] == "content")
    empty = sum(1 for r in results if r["status"] == "empty")
    errors = sum(1 for r in results if r["status"] == "error")
    total_blocks = sum(r["blocks"] for r in results)
    total_chars = sum(r["chars"] for r in results)

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(results)} pages processed")
    print(f"  With content: {with_content}")
    print(f"  Empty/blank:  {empty}")
    print(f"  Errors:       {errors}")
    print(f"  Total blocks: {total_blocks}")
    print(f"  Total chars:  {total_chars:,}")
    print(f"{'='*60}")

    if empty > 0:
        print(f"\nEmpty pages:")
        for r in sorted(results, key=lambda x: x["filename"]):
            if r["status"] == "empty":
                print(f"  - {r['company']} ({r['filename']})")

    # Write summary JSON
    summary_path = PORTFOLIO_DIR / "_fetch_summary.json"
    summary_path.write_text(json.dumps({
        "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%S'),
        "total": len(results),
        "with_content": with_content,
        "empty": empty,
        "errors": errors,
        "total_blocks": total_blocks,
        "total_chars": total_chars,
        "pages": sorted(results, key=lambda r: r["filename"]),
    }, indent=2), encoding="utf-8")
    print(f"\nSummary written to {summary_path}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
