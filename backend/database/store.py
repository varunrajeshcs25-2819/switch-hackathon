
"""SQLite persistence for issues."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


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
                    issue_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -------------------- Writes --------------------

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
            conn.execute(
                "DELETE FROM issues WHERE issue_id = ?",
                (issue_id,),
            )
            conn.commit()

    # -------------------- Reads --------------------

    def load(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Load one issue using its ID."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()

        if row is None:
            return None

        return json.loads(row["payload"])

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load every saved issue."""
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT issue_id, payload FROM issues ORDER BY created_at ASC"
            ).fetchall()

        return {
            row["issue_id"]: json.loads(row["payload"])
            for row in rows
        }

    def list_ids(self) -> List[str]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT issue_id FROM issues ORDER BY created_at ASC"
            ).fetchall()

        return [row["issue_id"] for row in rows]

    def count(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM issues"
            ).fetchone()

        return int(row["n"])
