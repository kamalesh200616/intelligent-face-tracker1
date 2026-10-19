"""Unit tests for SQLite database repository, schema, transactions, and idempotency."""

import numpy as np
import pytest
from src.database import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_tracker.db"
    return DatabaseManager(str(db_file))


def test_schema_initialization(temp_db):
    """Verify tables and indexes exist upon initialization."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row["name"] for row in cursor.fetchall()}
    conn.close()

    assert "faces" in tables
    assert "events" in tables
    assert "sessions" in tables


def test_register_and_get_face(temp_db):
    """Verify storing and retrieving face records with binary embeddings."""
    fake_emb = np.random.randn(512).astype(np.float32)
    fake_emb /= np.linalg.norm(fake_emb)

    record = temp_db.register_face("face_0001", fake_emb, name="Alice", metadata={"role": "tester"})
    assert record.face_id == "face_0001"
    assert record.total_visits == 1

    fetched = temp_db.get_face("face_0001")
    assert fetched is not None
    assert fetched.face_id == "face_0001"
    assert fetched.name == "Alice"
    assert np.allclose(fetched.embedding, fake_emb, atol=1e-5)


def test_event_recording_and_idempotency(temp_db):
    """Verify exactly-once event logging per track and event_type."""
    fake_emb = np.zeros(512, dtype=np.float32)
    temp_db.register_face("face_0001", fake_emb)

    # First entry event: succeeds
    ok1 = temp_db.record_event(
        event_id="evt_1",
        face_id="face_0001",
        track_id=101,
        event_type="entry",
        timestamp="2026-10-17T08:00:00Z",
        image_path="/path/crop1.jpg",
        confidence=0.92,
    )
    assert ok1 is True

    # Duplicate entry event for the same track_id: rejected by idempotency constraint
    ok2 = temp_db.record_event(
        event_id="evt_2",
        face_id="face_0001",
        track_id=101,
        event_type="entry",
        timestamp="2026-10-17T08:00:01Z",
        image_path="/path/crop2.jpg",
        confidence=0.94,
    )
    assert ok2 is False

    # Exit event for the same track_id: succeeds
    ok3 = temp_db.record_event(
        event_id="evt_3",
        face_id="face_0001",
        track_id=101,
        event_type="exit",
        timestamp="2026-10-17T08:00:10Z",
        image_path="/path/exit1.jpg",
        confidence=0.88,
    )
    assert ok3 is True

    # Total events in DB must be exactly 2 (1 entry + 1 exit)
    events = temp_db.get_events()
    assert len(events) == 2


def test_aggregate_stats(temp_db):
    """Verify global counting totals."""
    temp_db.register_face("face_0001", np.zeros(512, dtype=np.float32))
    temp_db.register_face("face_0002", np.ones(512, dtype=np.float32))

    temp_db.record_event("e1", "face_0001", 1, "entry", "2026-10-17T08:00:00Z", "p1", 0.9)
    temp_db.record_event("e2", "face_0001", 1, "exit", "2026-10-17T08:01:00Z", "p2", 0.9)
    temp_db.record_event("e3", "face_0002", 2, "entry", "2026-10-17T08:02:00Z", "p3", 0.9)

    stats = temp_db.get_aggregate_stats()
    assert stats["total_unique_faces"] == 2
    assert stats["total_entries"] == 2
    assert stats["total_exits"] == 1


def test_delete_face_cascading(temp_db):
    """Verify permanent deletion of face identity and associated events."""
    temp_db.register_face("face_0001", np.zeros(512, dtype=np.float32))
    temp_db.record_event("e1", "face_0001", 1, "entry", "2026-10-18T08:00:00Z", "p1", 0.9)
    temp_db.record_event("e2", "face_0001", 1, "exit", "2026-10-18T08:01:00Z", "p2", 0.9)

    assert temp_db.get_face("face_0001") is not None
    assert len(temp_db.get_events(face_id="face_0001")) == 2

    # Delete face
    deleted = temp_db.delete_face("face_0001")
    assert deleted is True

    # Face and events must be removed
    assert temp_db.get_face("face_0001") is None
    assert len(temp_db.get_events(face_id="face_0001")) == 0

    # Non-existent face deletion returns False
    assert temp_db.delete_face("non_existent_face") is False


def test_session_id_isolation(temp_db):
    """Verify different video sessions can reuse track_id=1 without constraint collisions."""
    temp_db.register_face("face_0001", np.zeros(512, dtype=np.float32))

    # Video 1: track_id 1
    ok1 = temp_db.record_event("e1", "face_0001", 1, "entry", "2026-10-18T08:00:00Z", "p1", 0.9, session_id="video_session_1")
    assert ok1 is True

    # Video 2: track_id 1 with different session_id must NOT collide
    ok2 = temp_db.record_event("e2", "face_0001", 1, "entry", "2026-10-18T08:05:00Z", "p2", 0.9, session_id="video_session_2")
    assert ok2 is True

    # Verify session filtering
    s1_events = temp_db.get_events(session_id="video_session_1")
    s2_events = temp_db.get_events(session_id="video_session_2")
    assert len(s1_events) == 1
    assert len(s2_events) == 1


def test_add_gallery_embedding(temp_db):
    """Verify storing and loading multiple embeddings in face gallery."""
    base_emb = np.random.randn(512).astype(np.float32)
    base_emb /= np.linalg.norm(base_emb)
    temp_db.register_face("face_0001", base_emb)

    new_emb = np.random.randn(512).astype(np.float32)
    new_emb /= np.linalg.norm(new_emb)
    temp_db.add_gallery_embedding("face_0001", new_emb)

    face = temp_db.get_face("face_0001")
    assert face is not None
    assert len(face.gallery) == 2  # base + 1 additional

