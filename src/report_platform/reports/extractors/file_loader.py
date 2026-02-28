"""File-based data loading utilities for extractors.

Reads CSV/JSON outputs from toolset directories on disk, avoiding fragile
Python imports of toolset code.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict[str, Any] | list | None:
    """Load a JSON file, returning None if missing or malformed."""
    if not path.exists():
        logger.debug("JSON not found: %s", path)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load JSON %s: %s", path, e)
        return None


def load_csv_records(path: Path, limit: int = 0) -> list[dict[str, str]]:
    """Load a CSV file as a list of dicts (DictReader rows).

    Args:
        path: Path to CSV file.
        limit: Max rows to return (0 = all).

    Returns:
        List of row dicts, or empty list if file missing.
    """
    if not path.exists():
        logger.debug("CSV not found: %s", path)
        return []
    try:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = []
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                rows.append(dict(row))
            return rows
    except (OSError, csv.Error) as e:
        logger.warning("Failed to load CSV %s: %s", path, e)
        return []


def csv_row_count(path: Path) -> int:
    """Count data rows in a CSV file (excluding header)."""
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return sum(1 for _ in f) - 1  # subtract header
    except OSError:
        return 0


def file_exists(path: Path) -> bool:
    """Check if a file exists and is non-empty."""
    return path.exists() and path.stat().st_size > 0


def file_modified(path: Path) -> str:
    """Return last-modified date as ISO string, or 'unknown'."""
    if not path.exists():
        return "unknown"
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
