"""SQLite persistence for issues.

The MVP keeps a hot dict in memory for request handling, and mirrors every
mutation here so issues survive a server restart. Uses the stdlib `sqlite3`
module (no ORM dependency).

Design notes
------------
* One row per issue, payload stored as JSON. PatchPilot issues are read/written
  whole, so a document store keeps the code small and avoids migrations while
  the schema is still moving.
* `payload` is produced by `serialize_issue()` in the API layer, which converts
  Pydantic models and datetimes into JSON-safe primitives.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List


class IssueStore:
    """Thread-safe JSON-document store backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    issue_id   TEXT PRIMARY KEY,
                    payload    TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # --------------------------------------------------------------- writes
    def save(self, issue_id: str, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload)
        created = str(payload.get("created_at") or "")
        updated = str(payload.get("updated_at") or created)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO issues (issue_id, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(issue_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (issue_id, body, created, updated),
            )
            conn.commit()

    def delete(self, issue_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM issues WHERE issue_id = ?", (issue_id,))
            conn.commit()

    # ---------------------------------------------------------------- reads
    def load_all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT issue_id, payload FROM issues ORDER BY created_at ASC"
            ).fetchall()
        return {row["issue_id"]: json.loads(row["payload"]) for row in rows}

    def list_ids(self) -> List[str]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT issue_id FROM issues ORDER BY created_at ASC"
            ).fetchall()
        return [row["issue_id"] for row in rows]

    def count(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM issues").fetchone()
        return int(row["n"])
