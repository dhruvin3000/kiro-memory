"""
Persistent decision store using JSON (human-readable) + SQLite (queryable).
Handles deduplication and CRUD operations.
"""
import json
import sqlite3
import hashlib
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..extractor.models import DecisionRecord


class DecisionStore:
    """
    Dual-write store: JSON for human readability, SQLite for fast queries.
    """

    def __init__(self, store_path: str):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.json_path = self.store_path / "decisions.json"
        self.db_path = self.store_path / "decisions.db"

        self._init_db()
        self._load_json()

    # ── Init ──────────────────────────────────────────────────────────────

    def _init_db(self):
        """Create SQLite schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    question TEXT,
                    decision TEXT,
                    rationale TEXT,
                    alternatives TEXT,   -- JSON array
                    source_type TEXT,
                    source_path TEXT,
                    source_date TEXT,
                    commit_sha TEXT,
                    author TEXT,
                    tags TEXT,           -- JSON array
                    confidence REAL,
                    raw_excerpt TEXT,
                    content_hash TEXT UNIQUE,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON decisions(tags)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON decisions(source_type)")
            conn.commit()

    def _load_json(self):
        """Load existing decisions from JSON into memory cache."""
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        else:
            self._cache = []

    def _save_json(self):
        """Persist in-memory cache to JSON."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)

    # ── Content hashing for deduplication ────────────────────────────────

    @staticmethod
    def _content_hash(record: DecisionRecord) -> str:
        text = f"{record.question}|{record.decision}|{record.source_path}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    # ── Write ─────────────────────────────────────────────────────────────

    def save(self, record: DecisionRecord) -> bool:
        """
        Save a decision record. Returns True if saved, False if duplicate.
        """
        content_hash = self._content_hash(record)

        with sqlite3.connect(self.db_path) as conn:
            # Check for duplicate
            exists = conn.execute(
                "SELECT id FROM decisions WHERE content_hash = ?", (content_hash,)
            ).fetchone()
            if exists:
                return False

            # Insert into SQLite
            conn.execute("""
                INSERT INTO decisions
                (id, question, decision, rationale, alternatives, source_type,
                 source_path, source_date, commit_sha, author, tags, confidence,
                 raw_excerpt, content_hash, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                record.id,
                record.question,
                record.decision,
                record.rationale,
                json.dumps(record.alternatives_rejected),
                record.source_type,
                record.source_path,
                record.source_date,
                record.commit_sha,
                record.author,
                json.dumps(record.tags),
                record.confidence,
                record.raw_excerpt,
                content_hash,
                datetime.now().isoformat(),
            ))
            conn.commit()

        # Add to JSON cache
        self._cache.append(record.to_dict())
        self._save_json()
        return True

    def save_many(self, records: List[DecisionRecord]) -> int:
        """Save multiple records. Returns count of new records saved."""
        saved = sum(1 for r in records if self.save(r))
        print(f"[store] Saved {saved} new decisions ({len(records) - saved} duplicates skipped)")
        return saved

    # ── Read ──────────────────────────────────────────────────────────────

    def get_all(self) -> List[DecisionRecord]:
        """Return all stored decisions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM decisions ORDER BY source_date DESC"
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get_by_id(self, decision_id: str) -> Optional[DecisionRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = ?", (decision_id,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def search_by_tag(self, tag: str) -> List[DecisionRecord]:
        """Find decisions that have a specific tag."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM decisions WHERE tags LIKE ? ORDER BY source_date DESC",
                (f'%"{tag}"%',),
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def keyword_search(self, query: str) -> List[DecisionRecord]:
        """Simple full-text keyword search across question, decision, rationale."""
        terms = query.lower().split()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            all_rows = conn.execute("SELECT * FROM decisions").fetchall()

        results = []
        for row in all_rows:
            text = f"{row['question']} {row['decision']} {row['rationale']}".lower()
            score = sum(1 for t in terms if t in text)
            if score > 0:
                results.append((score, self._row_to_record(row)))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_record(row) -> DecisionRecord:
        return DecisionRecord(
            id=row["id"],
            question=row["question"] or "",
            decision=row["decision"] or "",
            rationale=row["rationale"] or "",
            alternatives_rejected=json.loads(row["alternatives"] or "[]"),
            source_type=row["source_type"] or "",
            source_path=row["source_path"] or "",
            source_date=row["source_date"],
            commit_sha=row["commit_sha"],
            author=row["author"],
            tags=json.loads(row["tags"] or "[]"),
            confidence=row["confidence"] or 0.0,
            raw_excerpt=row["raw_excerpt"] or "",
        )
