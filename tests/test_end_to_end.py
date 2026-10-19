"""End-to-End integration test simulating a multi-frame video sequence with 2 visitors."""

from pathlib import Path
import cv2
import numpy as np
import pytest

from src.config import AppConfig
from src.database import DatabaseManager
from src.detector import Detection
from src.event_manager import EventManager
from src.face_recognizer import ArcFaceRecognizer
from src.identity_manager import IdentityManager
from src.tracker import FaceTracker, TrackState
from src.visitor_counter import VisitorCounter


def test_full_pipeline_multi_visitor_lifecycle(tmp_path):
    """Simulate a complete 20-frame video sequence with 2 distinct visitors entering and exiting."""
    # 1. Setup isolated test environment
    db_path = str(tmp_path / "e2e_tracker.db")
    entries_dir = str(tmp_path / "logs" / "entries")
    exits_dir = str(tmp_path / "logs" / "exits")
    log_file = str(tmp_path / "logs" / "events.log")

    cfg = AppConfig()
    cfg.storage.database_path = db_path
    cfg.storage.entries_dir = entries_dir
    cfg.storage.exits_dir = exits_dir
    cfg.storage.log_file = log_file
    cfg.tracking.min_hits_to_confirm = 2
    cfg.tracking.max_lost_frames = 2
    cfg.recognition.similarity_threshold = 0.70

    db = DatabaseManager(db_path)
    recognizer = ArcFaceRecognizer(cfg.recognition)
    tracker = FaceTracker(cfg.tracking)
    identity_mgr = IdentityManager(db, recognizer, cfg.recognition)
    event_mgr = EventManager(db, cfg.storage)
    counter = VisitorCounter(db)

    # 2. Synthetic faces: Visitor A and Visitor B with distinct spatial/spectral characteristics
    cropA = np.zeros((80, 80, 3), dtype=np.uint8)
    cropA[:, :40, 0] = 255  # Left half blue
    cropA[:, 40:, 1] = 255  # Right half green

    cropB = np.zeros((80, 80, 3), dtype=np.uint8)
    cropB[:40, :, 2] = 255  # Top half red
    cropB[40:, :, 0] = 255  # Bottom half blue

    # Frames 1-4: Visitor A present at (100, 100), Visitor B present at (400, 100)
    for f in range(1, 5):
        detA = Detection(bbox=(100, 100, 180, 180), confidence=0.92, crop=cropA, blur_score=70.0, is_valid_quality=True)
        detB = Detection(bbox=(400, 100, 480, 180), confidence=0.95, crop=cropB, blur_score=85.0, is_valid_quality=True)

        active_tracks, deleted_tracks = tracker.update([detA, detB], frame_index=f)

        for trk in active_tracks:
            if trk.state == TrackState.CONFIRMED:
                assigned_face_id = identity_mgr.process_track(trk)
                if assigned_face_id and not trk.entry_event_logged:
                    event_mgr.handle_entry(trk, f"2026-10-17T08:00:{f:02d}Z")

    # Both tracks must be confirmed and auto-registered
    assert counter.get_unique_visitor_count() == 2
    assert counter.get_total_entries() == 2
    assert counter.get_total_exits() == 0

    # Frames 5-8: Both visitors leave the frame (0 detections)
    for f in range(5, 9):
        active_tracks, deleted_tracks = tracker.update([], frame_index=f)
        for dtrk in deleted_tracks:
            if dtrk.entry_event_logged and not dtrk.exit_event_logged:
                event_mgr.handle_exit(dtrk, f"2026-10-17T08:00:{f:02d}Z")
            identity_mgr.release_track(dtrk.track_id)

    # Both tracks must now have triggered exits
    assert counter.get_unique_visitor_count() == 2
    assert counter.get_total_entries() == 2
    assert counter.get_total_exits() == 2
    assert counter.get_currently_present_count() == 0

    # Check image crops on disk
    entry_images = list(Path(entries_dir).rglob("*.jpg"))
    exit_images = list(Path(exits_dir).rglob("*.jpg"))
    assert len(entry_images) == 2
    assert len(exit_images) == 2
