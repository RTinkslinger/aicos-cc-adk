from __future__ import annotations

"""Publish Digest to digest.wiki — saves JSON to aicos-digests repo and triggers deploy.

Deploy chain: git pull → write JSON → git commit + push → Vercel deploy hook (~30s).
Live at: https://digest.wiki/d/{slug}

Adapted from scripts/publish_digest.py for droplet deployment.
"""

import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

AICOS_DIGESTS_REPO = os.getenv("AICOS_DIGESTS_REPO", "/opt/aicos-digests")
VERCEL_DEPLOY_HOOK = os.getenv(
    "VERCEL_DEPLOY_HOOK",
    "https://api.vercel.com/v1/integrations/deploy/prj_v8o0adOk8rk9WrdoXAjtazwSIH0n/gQ0xBvBfQ3",
)
DATA_DIR = "src/data"


def _generate_slug(title: str) -> str:
    """Generate URL slug from title."""
    slug = title.lower()
    for ch in "—–:,.!?'\"()[]{}":
        slug = slug.replace(ch, "")
    return "-".join(slug.split())[:60]


def publish_digest(
    data: dict[str, Any],
    slug: str | None = None,
    repo_path: str | None = None,
) -> dict[str, Any]:
    """Save analysis JSON to aicos-digests/src/data/ and git push.

    Args:
        data: DigestData dict (must contain 'slug' key, or pass slug param)
        slug: Override slug
        repo_path: Override repo path (default: AICOS_DIGESTS_REPO env var)

    Returns:
        dict with json_path, url, slug, pushed, deployed keys
    """
    slug = slug or data.get("slug")
    if not slug:
        slug = _generate_slug(data.get("title", "untitled"))
        data["slug"] = slug

    repo = Path(repo_path or AICOS_DIGESTS_REPO)
    if not (repo / "package.json").exists():
        raise FileNotFoundError(
            f"aicos-digests repo not found at {repo}. "
            f"Clone it: git clone <repo-url> {repo}"
        )

    # Sync: pull latest before editing (prevents divergence)
    try:
        subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=repo, capture_output=True, text=True, timeout=30,
        )
    except Exception as e:
        print(f"Git pull warning (continuing): {e}")

    data_dir = repo / DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / f"{slug}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON: {json_path}")

    pushed = False
    deployed = False
    try:
        subprocess.run(["git", "add", str(json_path)], cwd=repo, check=True, capture_output=True)

        result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, capture_output=True)
        if result.returncode != 0:
            subprocess.run(
                ["git", "commit", "-m", f"Add digest: {data.get('title', slug)}"],
                cwd=repo, check=True, capture_output=True,
            )
            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo, capture_output=True, text=True, timeout=30,
            )
            if push_result.returncode == 0:
                pushed = True
                print(f"Pushed to GitHub")
                # Trigger Vercel deploy via webhook
                deployed = _trigger_vercel_deploy()
            else:
                print(f"Git push failed: {push_result.stderr.strip()}")
        else:
            print(f"No changes to commit (JSON unchanged)")
    except subprocess.TimeoutExpired:
        print(f"Git push timed out")
    except Exception as e:
        print(f"Git error: {e}")

    url = f"https://digest.wiki/d/{slug}"
    print(f"Digest URL: {url}")

    return {
        "json_path": str(json_path),
        "url": url,
        "slug": slug,
        "pushed": pushed,
        "deployed": deployed,
    }


def _trigger_vercel_deploy() -> bool:
    """Trigger Vercel production deploy via deploy hook."""
    try:
        req = urllib.request.Request(VERCEL_DEPLOY_HOOK, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            job_id = body.get("job", {}).get("id", "unknown")
            print(f"Vercel deploy triggered (job: {job_id}) — live in ~30s")
            return True
    except Exception as e:
        print(f"Vercel deploy hook failed: {e}")
        return False
