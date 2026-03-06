"""SyncAgent — orchestrates bidirectional sync between Postgres and Notion.

Runs on cron schedule. Handles:
1. Thesis status sync (Notion → Postgres, human-owned field)
2. Actions bidirectional sync (pull Notion changes, push local creates)
3. Change detection (diff Notion vs Postgres, log to change_events)
4. Sync queue drain (retry failed Notion pushes)

Usage:
    python -m runners.sync_agent          # full sync
    python -m runners.sync_agent thesis   # thesis only
    python -m runners.sync_agent actions  # actions only
    python -m runners.sync_agent retry    # retry queue only
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def sync_thesis() -> dict:
    """Sync thesis threads: pull status from Notion, detect changes."""
    from lib.change_detection import detect_thesis_changes
    from lib.notion_client import fetch_thesis_threads, sync_thesis_status_from_notion

    print("[SyncAgent] Syncing thesis threads...")

    # 1. Pull status from Notion
    status_changes = sync_thesis_status_from_notion()

    # 2. Detect other changes (conviction moved by another surface)
    notion_threads = fetch_thesis_threads()
    field_changes = detect_thesis_changes(notion_threads)

    result = {
        "status_synced": len(status_changes),
        "changes_detected": len(field_changes),
        "changes": field_changes,
    }
    print(f"[SyncAgent] Thesis sync: {result['status_synced']} status synced, {result['changes_detected']} changes detected")
    return result


def sync_actions() -> dict:
    """Bidirectional actions sync: pull Notion changes, push local creates."""
    from lib.actions_db import get_unsynced_actions, set_notion_page_id
    from lib.change_detection import detect_action_changes
    from lib.notion_client import fetch_actions, push_action_to_notion, sync_actions_from_notion

    print("[SyncAgent] Syncing actions queue...")

    # 1. Pull from Notion (picks up status changes, manual actions)
    notion_actions = fetch_actions(limit=100)
    field_changes = detect_action_changes(notion_actions)
    pull_result = sync_actions_from_notion()

    # 2. Push unsynced local actions to Notion
    unsynced = get_unsynced_actions()
    pushed = 0
    push_errors = 0
    for action in unsynced:
        try:
            notion_page_id = push_action_to_notion(action)
            if notion_page_id:
                set_notion_page_id(action["id"], notion_page_id)
                pushed += 1
        except Exception as e:
            push_errors += 1
            print(f"[SyncAgent] Failed to push action '{action['action'][:50]}': {e}")

    result = {
        "pulled_inserted": pull_result["inserted"],
        "pulled_updated": pull_result["updated"],
        "pushed": pushed,
        "push_errors": push_errors,
        "changes_detected": len(field_changes),
        "changes": field_changes,
    }
    print(f"[SyncAgent] Actions sync: pulled {pull_result['inserted']}+{pull_result['updated']}, pushed {pushed}, {len(field_changes)} changes")
    return result


def drain_sync_queue() -> dict:
    """Process pending items in the sync queue (retry failed Notion pushes)."""
    from lib.thesis_db import get_pending_syncs, mark_sync_done, mark_sync_failed

    print("[SyncAgent] Draining sync queue...")
    pending = get_pending_syncs()

    done = 0
    failed = 0
    for item in pending:
        try:
            payload = item["payload"]
            if item["table_name"] == "thesis_threads":
                if item["operation"] == "create":
                    from lib.notion_client import create_thesis_thread
                    from lib.thesis_db import set_notion_page_id

                    result = create_thesis_thread(**payload)
                    set_notion_page_id(item["record_id"], result.get("id", ""))
                elif item["operation"] == "update":
                    from lib.notion_client import update_thesis_tracker
                    from lib.thesis_db import mark_synced

                    update_thesis_tracker(**payload)
                    mark_synced(item["record_id"])

                mark_sync_done(item["id"])
                done += 1
            elif item["table_name"] == "actions_queue":
                from lib.actions_db import set_notion_page_id as set_action_notion_id
                from lib.notion_client import push_action_to_notion

                # For actions, payload is the full row
                notion_id = push_action_to_notion(payload)
                if notion_id:
                    set_action_notion_id(item["record_id"], notion_id)
                mark_sync_done(item["id"])
                done += 1
        except Exception as e:
            mark_sync_failed(item["id"], str(e))
            failed += 1
            print(f"[SyncAgent] Retry failed for {item['table_name']} #{item['record_id']}: {e}")

    result = {"pending": len(pending), "done": done, "failed": failed}
    print(f"[SyncAgent] Queue: {len(pending)} pending, {done} done, {failed} failed")
    return result


def full_sync() -> dict:
    """Run all sync operations."""
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[SyncAgent] Full sync starting at {timestamp}")

    thesis_result = sync_thesis()
    actions_result = sync_actions()
    queue_result = drain_sync_queue()

    result = {
        "timestamp": timestamp,
        "thesis": thesis_result,
        "actions": actions_result,
        "queue": queue_result,
    }
    print(f"[SyncAgent] Full sync complete")
    return result


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "thesis":
        sync_thesis()
    elif mode == "actions":
        sync_actions()
    elif mode == "retry":
        drain_sync_queue()
    else:
        full_sync()
