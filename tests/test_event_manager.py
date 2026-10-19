"""Unit tests for Event Manager, entry/exit state machine, and crop image archiving."""

from pathlib import Path
import numpy as np
import pytest

from src.config import StorageConfig
from src.database import DatabaseManager
from src.detector import Detection
from src.event_manager import EventManager
from src.tracker import Track, TrackState


@pytest.fixture
def event_setup(tmp_path):
    db_file = tmp_path / "event_test.db"
    db = DatabaseManager(str(db_file))
    storage_cfg = StorageConfig(
        database_path=str(db_file),
        entries_dir=str(tmp_path / "logs" / "entries"),
        exits_dir=str(tmp_path / "logs" / "exits"),
        log_file=str(tmp_path / "logs" / "events.log"),
    )
    # Register face in DB so foreign key constraint passes
    db.register_face("face_0001", np.zeros(512, dtype=np.float32))
    em = EventManager(db, storage_cfg)
    return db, em, storage_cfg, tmp_path


def test_entry_and_exit_lifecycle(event_setup):
    """Verify full Entry -> Exit event lifecycle with crop persistence and idempotency."""
    db, em, storage_cfg, tmp_path = event_setup

    crop = np.full((80, 80, 3), 200, dtype=np.uint8)
    det = Detection(bbox=(10, 10, 90, 90), confidence=0.92, crop=crop, blur_score=70.0, is_valid_quality=True)
    track = Track(track_id=42, initial_detection=det, frame_index=1)
    track.state = TrackState.CONFIRMED
    track.face_id = "face_0001"

    # Step 1: Handle Entry
    ok_entry = em.handle_entry(track)
    assert ok_entry is True
    assert track.entry_event_logged is True

    # Duplicate Entry call: must be rejected
    ok_entry_dup = em.handle_entry(track)
    assert ok_entry_dup is False

    # Verify Entry crop exists on disk
    entry_files = list(Path(storage_cfg.entries_dir).rglob("*.jpg"))
    assert len(entry_files) == 1
    assert "face_0001" in entry_files[0].name

    # Step 2: Handle Exit
    ok_exit = em.handle_exit(track)
    assert ok_exit is True
    assert track.exit_event_logged is True

    # Duplicate Exit call: must be rejected
    ok_exit_dup = em.handle_exit(track)
    assert ok_exit_dup is False

    # Verify Exit crop exists on disk
    exit_files = list(Path(storage_cfg.exits_dir).rglob("*.jpg"))
    assert len(exit_files) == 1
    assert "face_0001" in exit_files[0].name

    # Verify exactly 2 records in database
    events = db.get_events(face_id="face_0001")
    assert len(events) == 2
    types = {e.event_type for e in events}
    assert types == {"entry", "exit"}


def test_cannot_exit_without_entry(event_setup):
    """Verify track cannot trigger exit if entry was never confirmed."""
    db, em, storage_cfg, tmp_path = event_setup

    det = Detection(bbox=(10, 10, 90, 90), confidence=0.92, crop=np.zeros((80, 80, 3), dtype=np.uint8), blur_score=70.0, is_valid_quality=True)
    track = Track(track_id=99, initial_detection=det, frame_index=1)
    track.face_id = "face_0001"

    # Direct exit attempt without entry
    ok_exit = em.handle_exit(track)
    assert ok_exit is False
    assert len(db.get_events()) == 0
