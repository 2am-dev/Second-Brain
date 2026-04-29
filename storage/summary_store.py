import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SummaryStore:
    """
    SQLite-backed store for document summaries, topic maps, and
    daily insights so we don't regenerate them on every run.
    """

    def __init__(self, db_path: str = "./brain_summaries.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
        logger.info(f"SummaryStore connected to '{db_path}'")

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_source  TEXT    NOT NULL,
                summary     TEXT    NOT NULL,
                key_points  TEXT,           -- JSON list
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS insights (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                insight     TEXT    NOT NULL,
                tags        TEXT,           -- JSON list
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topic_maps (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                topic       TEXT    NOT NULL UNIQUE,
                summary     TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id      TEXT    NOT NULL UNIQUE,
                source      TEXT    NOT NULL,
                source_type TEXT    NOT NULL,
                chunk_count INTEGER NOT NULL,
                ingested_at TEXT    NOT NULL,
                extra_meta  TEXT            -- JSON dict
            );
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Document registry
    # ------------------------------------------------------------------

    def register_document(
        self,
        doc_id: str,
        source: str,
        source_type: str,
        chunk_count: int,
        extra_meta: Optional[Dict] = None,
    ):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (doc_id, source, source_type, chunk_count, ingested_at, extra_meta)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                source,
                source_type,
                chunk_count,
                datetime.now().isoformat(),
                json.dumps(extra_meta or {}),
            ),
        )
        self.conn.commit()

    def is_document_ingested(self, doc_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM documents WHERE doc_id = ?", (doc_id,)
        )
        return cur.fetchone() is not None

    def list_documents(self) -> List[Dict]:
        cur = self.conn.execute(
            "SELECT doc_id, source, source_type, chunk_count, ingested_at "
            "FROM documents ORDER BY ingested_at DESC"
        )
        cols = ["doc_id", "source", "source_type", "chunk_count", "ingested_at"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    def save_summary(
        self,
        doc_source: str,
        summary: str,
        key_points: Optional[List[str]] = None,
    ):
        self.conn.execute(
            "INSERT INTO summaries (doc_source, summary, key_points, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                doc_source,
                summary,
                json.dumps(key_points or []),
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def get_summary(self, doc_source: str) -> Optional[Dict]:
        cur = self.conn.execute(
            "SELECT summary, key_points, created_at FROM summaries "
            "WHERE doc_source = ? ORDER BY created_at DESC LIMIT 1",
            (doc_source,),
        )
        row = cur.fetchone()
        if row:
            return {
                "summary": row[0],
                "key_points": json.loads(row[1]),
                "created_at": row[2],
            }
        return None

    # ------------------------------------------------------------------
    # Insights
    # ------------------------------------------------------------------

    def save_insight(self, insight: str, tags: Optional[List[str]] = None):
        self.conn.execute(
            "INSERT INTO insights (insight, tags, created_at) VALUES (?, ?, ?)",
            (insight, json.dumps(tags or []), datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        cur = self.conn.execute(
            "SELECT insight, tags, created_at FROM insights "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [
            {"insight": row[0], "tags": json.loads(row[1]), "created_at": row[2]}
            for row in cur.fetchall()
        ]

    # ------------------------------------------------------------------
    # Topic maps
    # ------------------------------------------------------------------

    def save_topic_map(self, topic: str, summary: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO topic_maps (topic, summary, updated_at) "
            "VALUES (?, ?, ?)",
            (topic, summary, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_topic_map(self, topic: str) -> Optional[str]:
        cur = self.conn.execute(
            "SELECT summary FROM topic_maps WHERE topic = ?", (topic,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()