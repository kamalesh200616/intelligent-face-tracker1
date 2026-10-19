"""Test persistence and identity preservation across application restarts."""

import numpy as np
import pytest

from src.config import RecognitionConfig
from src.database import DatabaseManager
from src.detector import Detection
from src.face_recognizer import ArcFaceRecognizer
from src.identity_manager import IdentityManager
from src.tracker import Track, TrackState
from src.visitor_counter import VisitorCounter


def test_identity_preservation_after_app_restart(tmp_path):
    """Verify that restarting the application loads previously registered identities from SQLite."""
    db_file = tmp_path / "restart_test.db"
    cfg = RecognitionConfig(similarity_threshold=0.60)

    # -------------------------------------------------------------
    # Session 1: Run application, register visitor 1
    # -------------------------------------------------------------
    db1 = DatabaseManager(str(db_file))
    rec1 = ArcFaceRecognizer(cfg)
    mgr1 = IdentityManager(db1, rec1, cfg)

    crop = np.zeros((80, 80, 3), dtype=np.uint8)
    crop[:, :40, 0] = 255
    crop[:, 40:, 1] = 255

    det = Detection(bbox=(50, 50, 130, 130), confidence=0.95, crop=crop, blur_score=80.0, is_valid_quality=True)
    track1 = Track(track_id=1, initial_detection=det, frame_index=1)
    track1.state = TrackState.CONFIRMED

    fid1 = mgr1.process_track(track1)
    assert fid1 == "face_0001"
    assert mgr1.total_registered_visitors == 1

    # Simulate application termination
    del mgr1
    del rec1
    del db1

    # -------------------------------------------------------------
    # Session 2: Application starts afresh with same database file
    # -------------------------------------------------------------
    db2 = DatabaseManager(str(db_file))
    rec2 = ArcFaceRecognizer(cfg)
    mgr2 = IdentityManager(db2, rec2, cfg)

    # Should have loaded the 1 existing visitor into cache on startup
    assert mgr2.total_registered_visitors == 1

    # Same person arrives in session 2
    track_new = Track(track_id=10, initial_detection=det, frame_index=1)
    track_new.state = TrackState.CONFIRMED

    fid_reopened = mgr2.process_track(track_new)
    # Must preserve identity: recognized as face_0001!
    assert fid_reopened == "face_0001"
    assert mgr2.total_registered_visitors == 1

    vc = VisitorCounter(db2)
    assert vc.get_unique_visitor_count() == 1
