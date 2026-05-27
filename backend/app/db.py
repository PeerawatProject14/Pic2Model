"""Tiny SQLite-backed catalog. No ORM — keep it dependency-free."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import CatalogEntry, CatalogPart


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Catalog:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_image_id TEXT,
                    glb_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    parts_json TEXT NOT NULL DEFAULT '[]',
                    faces INTEGER NOT NULL DEFAULT 0,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    backend TEXT NOT NULL DEFAULT 'mock',
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, entry: CatalogEntry) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT OR REPLACE INTO catalog
                   (id, name, source_image_id, glb_path, thumbnail_path,
                    parts_json, faces, tags_json, backend, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.id,
                    entry.name,
                    entry.source_image_id,
                    entry.glb_path,
                    entry.thumbnail_path,
                    json.dumps([p.model_dump() for p in entry.parts]),
                    entry.faces,
                    json.dumps(entry.tags),
                    entry.backend,
                    entry.created_at.isoformat(),
                ),
            )

    def _row_to_entry(self, row: sqlite3.Row) -> CatalogEntry:
        return CatalogEntry(
            id=row["id"],
            name=row["name"],
            source_image_id=row["source_image_id"],
            glb_path=row["glb_path"],
            thumbnail_path=row["thumbnail_path"],
            parts=[CatalogPart(**p) for p in json.loads(row["parts_json"])],
            faces=row["faces"],
            tags=json.loads(row["tags_json"]),
            backend=row["backend"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def get(self, entry_id: str) -> Optional[CatalogEntry]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM catalog WHERE id = ?", (entry_id,)).fetchone()
            return self._row_to_entry(row) if row else None

    def list(self, query: Optional[str] = None, tag: Optional[str] = None) -> list[CatalogEntry]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM catalog ORDER BY created_at DESC").fetchall()
        entries = [self._row_to_entry(r) for r in rows]
        if query:
            q = query.lower()
            entries = [e for e in entries if q in e.name.lower()]
        if tag:
            entries = [e for e in entries if tag in e.tags]
        return entries

    def delete(self, entry_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM catalog WHERE id = ?", (entry_id,))
            return cur.rowcount > 0
