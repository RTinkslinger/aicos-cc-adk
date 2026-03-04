"""
Reusable dedup utility module for tracking processed items across pipeline runs.

Provides DedupTracker class for managing processed IDs with JSON persistence.
Used by content pipelines (YouTube extractor, etc.) to avoid reprocessing items.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Set


class DedupTracker:
    """
    Manages a set of processed item IDs with JSON file persistence.
    
    Usage:
        with DedupTracker(Path('processed_videos.json')) as tracker:
            if not tracker.is_processed('video_id_123'):
                # Process the item
                tracker.mark_processed('video_id_123')
            tracker.commit()  # Auto-saves on __exit__
    """
    
    def __init__(self, filepath: Path):
        """
        Initialize DedupTracker.
        
        Args:
            filepath: Path to JSON file storing processed IDs.
                      File will be created if it doesn't exist.
        """
        self.filepath = Path(filepath)
        self._processed_ids: Set[str] = self.load()
    
    def load(self) -> Set[str]:
        """
        Load processed IDs from JSON file.
        
        Returns:
            Set of processed item IDs. Empty set if file doesn't exist or is corrupt.
        """
        if not self.filepath.exists():
            return set()
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except (json.JSONDecodeError, IOError):
            # Silently return empty set on read errors (corrupt file, etc.)
            return set()
    
    def save(self, ids: Set[str]) -> None:
        """
        Save IDs to JSON file with metadata.
        
        Args:
            ids: Set of IDs to persist.
        """
        data = {
            'processed_ids': sorted(list(ids)),
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'source': 'dedup_utils',
        }
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save dedup file {self.filepath}: {e}")
    
    def is_processed(self, item_id: str) -> bool:
        """
        Check if an item ID has been processed.
        
        Args:
            item_id: ID to check.
            
        Returns:
            True if ID is in processed set, False otherwise.
        """
        return item_id in self._processed_ids
    
    def mark_processed(self, item_id: str) -> None:
        """
        Mark an item ID as processed (add to in-memory set).
        
        Args:
            item_id: ID to mark as processed.
        """
        self._processed_ids.add(item_id)
    
    def commit(self) -> None:
        """Save current in-memory state to disk."""
        self.save(self._processed_ids)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (auto-commit on exit)."""
        self.commit()
        return False


if __name__ == '__main__':
    # Usage example
    tracker_path = Path('example_processed.json')
    
    # Method 1: Using context manager (recommended)
    print("=== Context Manager Example ===")
    with DedupTracker(tracker_path) as tracker:
        # Check and mark items
        for item_id in ['video_001', 'video_002', 'video_003']:
            if tracker.is_processed(item_id):
                print(f"  {item_id}: already processed")
            else:
                print(f"  {item_id}: processing...")
                tracker.mark_processed(item_id)
        # Commits automatically on __exit__
    
    print("\n=== Manual Commit Example ===")
    tracker = DedupTracker(tracker_path)
    tracker.mark_processed('video_004')
    tracker.mark_processed('video_005')
    tracker.commit()
    
    print(f"\nProcessed {len(tracker._processed_ids)} items total")
    print(f"Dedup file saved to: {tracker_path.resolve()}")
    
    # Cleanup
    try:
        if tracker_path.exists():
            tracker_path.unlink()
    except (OSError, PermissionError):
        pass
