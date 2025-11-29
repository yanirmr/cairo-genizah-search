"""SQLite database management for Genizah search.

This module provides database connection and schema management for the Cairo
Genizah search system using SQLite FTS5 full-text search.
"""

import sqlite3
from pathlib import Path
from typing import Optional


class GenizahDatabase:
    """Manages SQLite database connection and schema for Genizah documents."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, db_path: str, enable_wal: bool = True):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
            enable_wal: Enable WAL mode for better concurrency (default: True)
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.enable_wal = enable_wal

    def connect(self) -> sqlite3.Connection:
        """Create or open database connection.

        Returns:
            SQLite connection object

        Raises:
            sqlite3.Error: If connection fails
        """
        if self.conn is None:
            self.conn = sqlite3.connect(
                self.db_path, check_same_thread=False  # For Flask multi-threading
            )
            self.conn.row_factory = sqlite3.Row  # Dict-like access to rows
            # Enable WAL mode for better concurrency (if requested)
            if self.enable_wal:
                self.conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys=ON")
        return self.conn

    def initialize_schema(self):
        """Create tables, indexes, and triggers if they don't exist.

        Creates:
        - documents table (main document storage)
        - documents_fts table (FTS5 virtual table for full-text search)
        - indexes on has_annotations and line_count
        - triggers to keep FTS table in sync with main table
        - index_metadata table for statistics
        """
        if self.conn is None:
            self.connect()

        cursor = self.conn.cursor()

        # Main documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                has_annotations BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Indexes for filtering
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_has_annotations
            ON documents(has_annotations)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_line_count
            ON documents(line_count)
        """
        )

        # FTS5 virtual table for full-text search
        # unicode61 tokenizer with remove_diacritics 0 preserves Hebrew/Arabic diacritics
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(
                doc_id UNINDEXED,
                content,
                content=documents,
                content_rowid=rowid,
                tokenize='unicode61 remove_diacritics 0'
            )
        """
        )

        # Trigger to keep FTS table in sync after INSERT
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_ai
            AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, doc_id, content)
                VALUES (new.rowid, new.doc_id, new.content);
            END
        """
        )

        # Trigger to keep FTS table in sync after DELETE
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_ad
            AFTER DELETE ON documents BEGIN
                DELETE FROM documents_fts WHERE rowid = old.rowid;
            END
        """
        )

        # Trigger to keep FTS table in sync after UPDATE
        # FTS5 with external content requires DELETE+INSERT, not UPDATE
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS documents_au
            AFTER UPDATE ON documents BEGIN
                DELETE FROM documents_fts WHERE rowid = old.rowid;
                INSERT INTO documents_fts(rowid, doc_id, content)
                VALUES (new.rowid, new.doc_id, new.content);
            END
        """
        )

        # Metadata table for statistics and versioning
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS index_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )

        # Initialize metadata
        cursor.execute(
            """
            INSERT OR IGNORE INTO index_metadata (key, value)
            VALUES ('version', ?)
        """,
            (self.SCHEMA_VERSION,),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO index_metadata (key, value)
            VALUES ('created_at', datetime('now'))
        """
        )

        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
