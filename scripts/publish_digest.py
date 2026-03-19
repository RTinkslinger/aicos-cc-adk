#!/usr/bin/env python3
"""
Publish Digest to HTML Site — AI CoS Phase 2
Saves analysis JSON to aicos-digests repo and triggers deploy.

Deploy chain (3 tiers):
  1. Direct git push (Mac terminal / launchd) → GitHub Action → Vercel
  2. osascript MCP → git push on Mac host → GitHub Action → Vercel  [Cowork primary]
  3. npx vercel --prod (local Vercel CLI fallback)

In Cowork: this script commits locally. The Claude agent then calls osascript MCP
to push via Mac host. If publish_digest() returns pushed=False, the caller should
trigger: osascript 'do shell script "cd REPO && git push origin main"'

Usage (from Cowork pipeline or CLI):
    python3 publish_digest.py <analysis.json>
    python3 publish_digest.py <analysis.json> --slug custom-slug

Or as a module:
    from publish_digest import publish_digest
    result = publish_digest(analysis_data)
    if not result['pushed']:
        # Caller triggers osascript MCP: git push on Mac host
        pass
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# ─── Configuration ───────────────────────────────────────
# Works from both Mac and Cowork VM
POSSIBLE_REPO_PATHS = [
    Path.home() / "Claude Projects" / "Aakash AI CoS CC ADK" / "aicos-digests",
]

DATA_DIR = "src/data"


def find_repo() -> Path:
    """Find the aicos-digests repo on whichever machine we're running."""
    for p in POSSIBLE_REPO_PATHS:
        if (p / "package.json").exists():
            return p
    raise FileNotFoundError(
        "Cannot find aicos-digests repo. Checked:\n"
        + "\n".join(f"  - {p}" for p in POSSIBLE_REPO_PATHS)
    )


def _vercel_deploy(repo: Path) -> bool:
    """Fallback: deploy directly via Vercel CLI when git push fails."""
    try:
        # Try npx vercel --prod (works if user has logged in via `npx vercel login`)
        result = subprocess.run(
            ["npx", "vercel", "--prod", "--yes"],
            cwd=repo, capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"✓ Deployed directly via Vercel CLI")
            return True
        else:
            print(f"⚠ Vercel CLI deploy failed: {result.stderr.strip()}")
            print(f"  Manual deploy needed: cd {repo} && npx vercel --prod")
            return False
    except FileNotFoundError:
        print(f"⚠ npx not found — manual deploy needed: cd {repo} && npx vercel --prod")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠ Vercel CLI deploy timed out")
        return False


def publish_digest(data: dict, slug: str | None = None) -> dict:
    """
    Save analysis JSON to aicos-digests/src/data/ and git push.

    Args:
        data: The full analysis dict (must contain 'slug' key, or pass slug param)
        slug: Override slug (default: uses data['slug'])

    Returns:
        dict with 'json_path', 'url', 'pushed' keys
    """
    slug = slug or data.get("slug")
    if not slug:
        # Generate slug from title
        title = data.get("title", "untitled")
        slug = title.lower()
        for ch in "—–:,.!?'\"()[]{}":
            slug = slug.replace(ch, "")
        slug = "-".join(slug.split())[:60]
        data["slug"] = slug

    repo = find_repo()
    data_dir = repo / DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / f"{slug}.json"

    # Write JSON
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON: {json_path}")

    # Git add + commit + push → Vercel auto-deploy via GitHub Action
    # Fallback: direct Vercel CLI deploy if git push fails (e.g. in Cowork sandbox)
    pushed = False
    deployed = False
    try:
        subprocess.run(["git", "add", str(json_path)], cwd=repo, check=True, capture_output=True)

        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo, capture_output=True
        )

        if result.returncode != 0:  # There are staged changes
            subprocess.run(
                ["git", "commit", "-m", f"Add digest: {data.get('title', slug)}"],
                cwd=repo, check=True, capture_output=True
            )

            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo, capture_output=True, text=True, timeout=30
            )

            if push_result.returncode == 0:
                pushed = True
                print(f"✓ Pushed to GitHub → Vercel auto-deploy via GitHub Action (~90s)")
            else:
                print(f"⚠ Git push failed (sandbox — no credentials)")
                print(f"  Commit saved locally. Mac auto_push daemon will pick it up within 2 min.")
                print(f"  Fallback: trying direct Vercel CLI deploy...")
                deployed = _vercel_deploy(repo)
        else:
            print(f"ℹ No changes to commit (JSON unchanged)")
    except FileNotFoundError:
        print(f"⚠ Git not available — trying direct Vercel CLI deploy...")
        deployed = _vercel_deploy(repo)
    except subprocess.TimeoutExpired:
        print(f"⚠ Git push timed out — trying direct Vercel CLI deploy...")
        deployed = _vercel_deploy(repo)
    except Exception as e:
        print(f"⚠ Git error: {e}")
        print(f"  Trying direct Vercel CLI deploy...")
        deployed = _vercel_deploy(repo)

    url = f"https://aicos-digests.vercel.app/d/{slug}"
    print(f"✓ Digest URL: {url}")

    return {
        "json_path": str(json_path),
        "url": url,
        "slug": slug,
        "pushed": pushed,
        "deployed": deployed or pushed,  # True if either path succeeded
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 publish_digest.py <analysis.json> [--slug custom-slug]")
        sys.exit(1)

    json_path = sys.argv[1]
    slug_override = None
    if "--slug" in sys.argv:
        idx = sys.argv.index("--slug")
        if idx + 1 < len(sys.argv):
            slug_override = sys.argv[idx + 1]

    with open(json_path) as f:
        data = json.load(f)

    result = publish_digest(data, slug_override)
    print(f"\nResult: {json.dumps(result, indent=2)}")
