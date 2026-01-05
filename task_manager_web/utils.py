"""Utility helpers to read/write tasks to data/tasks.json safely.

Functions:
- `read_tasks()` -> list of tasks (returns empty list on missing/invalid file)
- `write_tasks(tasks)` -> atomically write tasks list to disk
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'tasks.json')


def _ensure_datafile() -> None:
    dirpath = os.path.dirname(DATA_FILE)
    os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)


def read_tasks() -> List[Dict[str, Any]]:
    """Read and return the list of tasks from the JSON file.

    If the file is missing or malformed, returns an empty list.
    """
    _ensure_datafile()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def write_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Atomically write the tasks list to the JSON file.

    Uses a temporary file in the same directory and then replaces the
    original to avoid partial writes.
    """
    _ensure_datafile()
    dirpath = os.path.dirname(DATA_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmpf:
            json.dump(tasks, tmpf, indent=2)
        os.replace(tmp_path, DATA_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# Notifications helpers (stored in data/notifications.json)
NOTIFY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'notifications.json')


def _ensure_notifyfile() -> None:
    dirpath = os.path.dirname(NOTIFY_FILE)
    os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(NOTIFY_FILE):
        with open(NOTIFY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)


def read_notifications() -> List[Dict[str, Any]]:
    """Read persisted notifications from disk. Returns [] on error."""
    _ensure_notifyfile()
    try:
        with open(NOTIFY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def write_notifications(notes: List[Dict[str, Any]]) -> None:
    """Atomically write notifications list to disk."""
    _ensure_notifyfile()
    dirpath = os.path.dirname(NOTIFY_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmpf:
            json.dump(notes, tmpf, indent=2)
        os.replace(tmp_path, NOTIFY_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def add_notification(message: str, kind: str = 'info') -> None:
    """Append a notification dict with timestamp and kind.

    Example notification: {"ts": "2025-12-31T12:00:00", "kind": "info", "message": "Task created: ..."}
    """
    notes = read_notifications()
    notes.append({
        'ts': datetime.utcnow().isoformat(),
        'kind': kind,
        'message': message,
    })
    write_notifications(notes)


def clear_notifications() -> None:
    """Remove all persisted notifications (clear the file)."""
    write_notifications([])
