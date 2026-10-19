"""Database access layer and repository pattern for Intelligent Face Tracker.

Provides thread-safe, transactional SQLite storage with foreign key constraints,
WAL mode, indexing, and an interface easily extensible to PostgreSQL.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.logging_setup import get_logger

logger = get_logger("database")


@dataclass
class FaceRecord:
    face_id: str
    name: Optional[str]
    embedding: np.ndarray
    first_seen: str
    last_seen: str
    total_visits: int
    metadata: Dict[str, Any]
    gallery: List[np.ndarray] = field(default_factory=list)


@dataclass
class EventRecord:
    event_id: str
    session_id: str
    face_id: str
    track_id: int
    event_type: str  # "entry" or "exit"
    timestamp: str   # ISO-8601
    image_path: str
    confidence: float
    created_at: str


@dataclass
class SessionRecord:
    session_id: str
    source_type: str
    source_path: str
    started_at: str
    ended_at: Optional[str]
    total_frames: int
    unique_faces_count: int
    status: str


class DatabaseManager:
    """Manages SQLite connection lifecycle, schema initialization, and transactional operations."""

    def __init__(self, db_path: str = "data/visitor_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create a configured SQLite connection with foreign keys and WAL enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode by default, explicit BEGIN for transactions
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def init_db(self) -> None:
        """Create schema, tables, indexes, and constraints if they do not exist."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN;")

                # Table 1: Registered Faces
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS faces (
                    face_id TEXT PRIMARY KEY,
                    name TEXT,
                    embedding BLOB NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    total_visits INTEGER NOT NULL DEFAULT 1,
                    metadata_json TEXT
                );
                """)

                # Table 2: Entry and Exit Events (Scoped to session_id for multi-video idempotency)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL DEFAULT 'session_default',
                    face_id TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL CHECK(event_type IN ('entry', 'exit')),
                    timestamp TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (face_id) REFERENCES faces(face_id) ON DELETE CASCADE,
                    UNIQUE(session_id, track_id, event_type)  -- Enforces idempotency per physical tracking session
                );
                """)

                # Check and perform migration if events table was created with old schema lacking session_id
                col_names = [col[1] for col in cursor.execute("PRAGMA table_info(events);").fetchall()]
                if "session_id" not in col_names:
                    logger.info("Migrating events table to add session_id and update unique constraints...")
                    cursor.execute("""
                    CREATE TABLE events_migrated (
                        event_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL DEFAULT 'session_default',
                        face_id TEXT NOT NULL,
                        track_id INTEGER NOT NULL,
                        event_type TEXT NOT NULL CHECK(event_type IN ('entry', 'exit')),
                        timestamp TEXT NOT NULL,
                        image_path TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (face_id) REFERENCES faces(face_id) ON DELETE CASCADE,
                        UNIQUE(session_id, track_id, event_type)
                    );
                    """)
                    cursor.execute("""
                    INSERT INTO events_migrated (event_id, session_id, face_id, track_id, event_type, timestamp, image_path, confidence, created_at)
                    SELECT event_id, 'session_default', face_id, track_id, event_type, timestamp, image_path, confidence, created_at FROM events;
                    """)
                    cursor.execute("DROP TABLE events;")
                    cursor.execute("ALTER TABLE events_migrated RENAME TO events;")
                    logger.info("Events table migration completed successfully.")

                # Table 3: Processing Sessions
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_frames INTEGER NOT NULL DEFAULT 0,
                    unique_faces_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'RUNNING'
                );
                """)

                # Indexes for fast querying
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_face_id ON events(face_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_faces_last_seen ON faces(last_seen);")

                cursor.execute("COMMIT;")
                logger.info("Database schema initialized successfully at: %s", self.db_path.resolve())
            except Exception as e:
                conn.execute("ROLLBACK;")
                logger.error("Failed to initialize database: %s", e)
                raise
            finally:
                conn.close()

    # ---------------------------------------------------------
    # Face Identity Operations
    # ---------------------------------------------------------

    def register_face(
        self,
        face_id: str,
        embedding: np.ndarray,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FaceRecord:
        """Register a new persistent face identity.

        Args:
            face_id: Unique string identifier (e.g. 'face_0001').
            embedding: 1D numpy array of float32 embeddings.
            name: Optional human-readable name or label.
            metadata: Optional dictionary of additional metadata.

        Returns:
            The created FaceRecord.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        emb_bytes = embedding.astype(np.float32).tobytes()
        meta_json = json.dumps(metadata or {})

        with self._lock:
            conn = self.get_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO faces (face_id, name, embedding, first_seen, last_seen, total_visits, metadata_json)
                    VALUES (?, ?, ?, ?, ?, 1, ?);
                    """,
                    (face_id, name, emb_bytes, now_iso, now_iso, meta_json),
                )
                logger.info("Registered new identity in database: %s", face_id)
                return FaceRecord(
                    face_id=face_id,
                    name=name,
                    embedding=embedding,
                    first_seen=now_iso,
                    last_seen=now_iso,
                    total_visits=1,
                    metadata=metadata or {},
                )
            finally:
                conn.close()

    def update_face_appearance(
        self,
        face_id: str,
        updated_embedding: Optional[np.ndarray] = None,
        increment_visits: bool = False,
    ) -> None:
        """Update last seen timestamp, optionally increment visit count and average embedding."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self.get_connection()
            try:
                if updated_embedding is not None:
                    emb_bytes = updated_embedding.astype(np.float32).tobytes()
                    if increment_visits:
                        conn.execute(
                            """
                            UPDATE faces
                            SET last_seen = ?, total_visits = total_visits + 1, embedding = ?
                            WHERE face_id = ?;
                            """,
                            (now_iso, emb_bytes, face_id),
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE faces
                            SET last_seen = ?, embedding = ?
                            WHERE face_id = ?;
                            """,
                            (now_iso, emb_bytes, face_id),
                        )
                else:
                    if increment_visits:
                        conn.execute(
                            "UPDATE faces SET last_seen = ?, total_visits = total_visits + 1 WHERE face_id = ?;",
                            (now_iso, face_id),
                        )
                    else:
                        conn.execute(
                            "UPDATE faces SET last_seen = ? WHERE face_id = ?;",
                            (now_iso, face_id),
                        )
            finally:
                conn.close()

    def get_face(self, face_id: str) -> Optional[FaceRecord]:
        """Fetch a single face record by ID with gallery support."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT face_id, name, embedding, first_seen, last_seen, total_visits, metadata_json FROM faces WHERE face_id = ?;",
                    (face_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                emb = np.frombuffer(row["embedding"], dtype=np.float32)
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                gallery = [emb]
                if "gallery" in meta and isinstance(meta["gallery"], list):
                    for g_hex in meta["gallery"]:
                        try:
                            g_arr = np.frombuffer(bytes.fromhex(g_hex), dtype=np.float32)
                            if g_arr.shape == emb.shape:
                                gallery.append(g_arr)
                        except Exception:
                            pass
                return FaceRecord(
                    face_id=row["face_id"],
                    name=row["name"],
                    embedding=emb,
                    first_seen=row["first_seen"],
                    last_seen=row["last_seen"],
                    total_visits=row["total_visits"],
                    metadata=meta,
                    gallery=gallery,
                )
            finally:
                conn.close()

    def get_all_faces(self) -> List[FaceRecord]:
        """Load all registered faces and their embeddings for matching."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT face_id, name, embedding, first_seen, last_seen, total_visits, metadata_json FROM faces;")
                records: List[FaceRecord] = []
                for row in cursor.fetchall():
                    emb = np.frombuffer(row["embedding"], dtype=np.float32)
                    meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                    gallery = [emb]
                    if "gallery" in meta and isinstance(meta["gallery"], list):
                        for g_hex in meta["gallery"]:
                            try:
                                g_arr = np.frombuffer(bytes.fromhex(g_hex), dtype=np.float32)
                                if g_arr.shape == emb.shape:
                                    gallery.append(g_arr)
                            except Exception:
                                pass
                    records.append(
                        FaceRecord(
                            face_id=row["face_id"],
                            name=row["name"],
                            embedding=emb,
                            first_seen=row["first_seen"],
                            last_seen=row["last_seen"],
                            total_visits=row["total_visits"],
                            metadata=meta,
                            gallery=gallery,
                        )
                    )
                return records
            finally:
                conn.close()

    def add_gallery_embedding(self, face_id: str, new_embedding: np.ndarray, max_gallery: int = 5) -> None:
        """Add an additional diverse embedding to the face's gallery and recompute centroid."""
        if new_embedding is None or new_embedding.size == 0:
            return
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT embedding, metadata_json FROM faces WHERE face_id = ?;", (face_id,))
                row = cursor.fetchone()
                if not row:
                    return
                base_emb = np.frombuffer(row["embedding"], dtype=np.float32)
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                gallery_hex = meta.get("gallery", [])
                
                new_norm = np.linalg.norm(new_embedding)
                new_emb_norm = (new_embedding / new_norm).astype(np.float32) if new_norm > 0 else new_embedding
                
                if len(gallery_hex) < max_gallery:
                    gallery_hex.append(new_emb_norm.tobytes().hex())
                    meta["gallery"] = gallery_hex
                    
                    all_embs = [base_emb]
                    for gh in gallery_hex:
                        try:
                            all_embs.append(np.frombuffer(bytes.fromhex(gh), dtype=np.float32))
                        except Exception:
                            pass
                    centroid = np.mean(all_embs, axis=0)
                    c_norm = np.linalg.norm(centroid)
                    if c_norm > 0:
                        centroid = (centroid / c_norm).astype(np.float32)
                    
                    now_iso = datetime.now(timezone.utc).isoformat()
                    conn.execute(
                        "UPDATE faces SET embedding = ?, metadata_json = ?, last_seen = ? WHERE face_id = ?;",
                        (centroid.tobytes(), json.dumps(meta), now_iso, face_id),
                    )
                    logger.debug("Added new embedding to face %s gallery (total gallery: %d)", face_id, len(gallery_hex))
            except Exception as e:
                logger.error("Failed to add gallery embedding for %s: %s", face_id, e)
            finally:
                conn.close()

    def delete_face(self, face_id: str) -> bool:
        """Permanently delete a registered visitor identity and its associated events."""
        with self._lock:
            conn = self.get_connection()
            try:
                conn.execute("BEGIN;")
                conn.execute("DELETE FROM events WHERE face_id = ?;", (face_id,))
                cursor = conn.execute("DELETE FROM faces WHERE face_id = ?;", (face_id,))
                conn.execute("COMMIT;")
                changes = cursor.rowcount
                logger.info("Deleted face %s from database (deleted rowcount: %d)", face_id, changes)
                return changes > 0
            except Exception as e:
                conn.execute("ROLLBACK;")
                logger.error("Failed to delete face %s: %s", face_id, e)
                return False
            finally:
                conn.close()

    # ---------------------------------------------------------
    # Event Logging Operations (Entry / Exit)
    # ---------------------------------------------------------

    def record_event(
        self,
        event_id: str,
        face_id: str,
        track_id: int,
        event_type: str,
        timestamp: str,
        image_path: str,
        confidence: float,
        session_id: str = "session_default",
    ) -> bool:
        """Insert a confirmed entry or exit event with idempotency guarantees.

        Returns True if the event was inserted, False if already recorded (idempotent duplicate).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self.get_connection()
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO events
                    (event_id, session_id, face_id, track_id, event_type, timestamp, image_path, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (event_id, session_id, face_id, track_id, event_type, timestamp, image_path, float(confidence), now_iso),
                )
                changes = conn.total_changes
                if changes > 0:
                    logger.info("DB Recorded %s event for %s (session %s, track %d, event_id=%s)", event_type.upper(), face_id, session_id, track_id, event_id)
                    return True
                else:
                    logger.debug("Idempotent ignore: event (%s, session=%s, track=%d) already persisted", event_type, session_id, track_id)
                    return False
            except Exception as e:
                logger.error("Failed to record event %s for face %s: %s", event_id, face_id, e)
                return False
            finally:
                conn.close()

    def get_events(
        self,
        face_id: Optional[str] = None,
        event_type: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[EventRecord]:
        """Query events with optional filtering."""
        query = "SELECT event_id, session_id, face_id, track_id, event_type, timestamp, image_path, confidence, created_at FROM events WHERE 1=1"
        params: List[Any] = []
        if face_id:
            query += " AND face_id = ?"
            params.append(face_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        query += " ORDER BY timestamp DESC LIMIT ?;"
        params.append(limit)

        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [
                    EventRecord(
                        event_id=row["event_id"],
                        session_id=row["session_id"] if "session_id" in row.keys() else "session_default",
                        face_id=row["face_id"],
                        track_id=row["track_id"],
                        event_type=row["event_type"],
                        timestamp=row["timestamp"],
                        image_path=row["image_path"],
                        confidence=row["confidence"],
                        created_at=row["created_at"],
                    )
                    for row in cursor.fetchall()
                ]
            finally:
                conn.close()

    # ---------------------------------------------------------
    # Sessions & Aggregation Queries
    # ---------------------------------------------------------

    def start_session(self, session_id: str, source_type: str, source_path: str) -> None:
        """Create a new processing session row."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self.get_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, source_type, source_path, started_at, status)
                    VALUES (?, ?, ?, ?, 'RUNNING');
                    """,
                    (session_id, source_type, str(source_path), now_iso),
                )
            finally:
                conn.close()

    def end_session(self, session_id: str, total_frames: int, unique_faces_count: int, status: str = "COMPLETED") -> None:
        """Finalize a processing session."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self.get_connection()
            try:
                conn.execute(
                    """
                    UPDATE sessions
                    SET ended_at = ?, total_frames = ?, unique_faces_count = ?, status = ?
                    WHERE session_id = ?;
                    """,
                    (now_iso, total_frames, unique_faces_count, status, session_id),
                )
            finally:
                conn.close()

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Return global totals: unique registered faces, total entry events, total exit events."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS total_faces FROM faces;")
                total_faces = cursor.fetchone()["total_faces"]

                cursor.execute("SELECT COUNT(*) AS total_entries FROM events WHERE event_type = 'entry';")
                total_entries = cursor.fetchone()["total_entries"]

                cursor.execute("SELECT COUNT(*) AS total_exits FROM events WHERE event_type = 'exit';")
                total_exits = cursor.fetchone()["total_exits"]

                cursor.execute("SELECT COUNT(DISTINCT face_id) AS distinct_visitors_seen FROM events;")
                distinct_visitors_seen = cursor.fetchone()["distinct_visitors_seen"]

                return {
                    "total_unique_faces": total_faces,
                    "distinct_visitors_logged": distinct_visitors_seen,
                    "total_entries": total_entries,
                    "total_exits": total_exits,
                }
            finally:
                conn.close()
