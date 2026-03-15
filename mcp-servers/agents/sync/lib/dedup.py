from __future__ import annotations

"""Dedup tracker — manages processed item IDs with JSON persistence.

Used by extraction and content agent to avoid reprocessing videos.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from shared.logging import get_trace_id


class DedupTracker:
    """Manages a set of processed item IDs with JSON file persistence.

    Usage:
        with DedupTracker(Path('processed_videos.json')) as tracker:
            if not tracker.is_processed('video_id_123'):
                # process it
                tracker.mark_processed('video_id_123')
    """

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self._processed_ids: set[str] = self.load()

    def load(self) -> set[str]:
        if not self.filepath.exists():
            return set()
        try:
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except (json.JSONDecodeError, IOError):
            return set()

    def save(self, ids: set[str] | None = None) -> None:
        ids = ids if ids is not None else self._processed_ids
        data = {
            "processed_ids": sorted(ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": "ai-cos-mcp",
        }
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save dedup file {self.filepath}: {e}")

    def is_processed(self, item_id: str) -> bool:
        return item_id in self._processed_ids

    def mark_processed(self, item_id: str) -> None:
        self._processed_ids.add(item_id)

    def commit(self) -> None:
        self.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        return False
