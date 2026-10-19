"""Unit tests for Identity Manager, auto-registration, re-identification, and deduplication."""

import numpy as np
import pytest

from src.config import RecognitionConfig
from src.database import DatabaseManager
from src.detector import Detection
from src.face_recognizer import ArcFaceRecognizer, normalize_l2
from src.identity_manager import IdentityManager
from src.tracker import Track, TrackState


@pytest.fixture
def identity_setup(tmp_path):
    db_file = tmp_path / "id_test.db"
    db = DatabaseManager(str(db_file))
    config = RecognitionConfig(similarity_threshold=0.60)
    recognizer = ArcFaceRecognizer(config)
    mgr = IdentityManager(db, recognizer, config)
    return db, recognizer, mgr, config


def test_auto_registration_new_face(identity_setup):
    """Verify new face is auto-registered and assigned face_0001."""
    db, recognizer, mgr, config = identity_setup

    crop = np.full((100, 100, 3), 120, dtype=np.uint8)
    det = Detection(bbox=(10, 10, 110, 110), confidence=0.95, crop=crop, blur_score=75.0, is_valid_quality=True)
    track = Track(track_id=1, initial_detection=det, frame_index=1)
    track.state = TrackState.CONFIRMED

    # First call: registers face_0001
    face_id = mgr.process_track(track)
    assert face_id == "face_0001"
    assert mgr.total_registered_visitors == 1

    # Second call for the SAME track: returns existing face_0001 without duplicate registration
    face_id_again = mgr.process_track(track)
    assert face_id_again == "face_0001"
    assert mgr.total_registered_visitors == 1


def test_reidentification_existing_face(identity_setup):
    """Verify returning visitor is re-identified instead of registering a duplicate ID."""
    db, recognizer, mgr, config = identity_setup

    crop1 = np.full((100, 100, 3), 150, dtype=np.uint8)
    det1 = Detection(bbox=(10, 10, 110, 110), confidence=0.95, crop=crop1, blur_score=80.0, is_valid_quality=True)
    track1 = Track(track_id=1, initial_detection=det1, frame_index=1)
    track1.state = TrackState.CONFIRMED

    # Register visitor 1
    fid1 = mgr.process_track(track1)
    assert fid1 == "face_0001"

    # Track 1 exits and is released
    mgr.release_track(track1.track_id)

    # Later, visitor 1 returns in Track 2 with identical visual features
    track2 = Track(track_id=2, initial_detection=det1, frame_index=100)
    track2.state = TrackState.CONFIRMED

    fid2 = mgr.process_track(track2)
    # Must match existing face_0001!
    assert fid2 == "face_0001"
    assert mgr.total_registered_visitors == 1  # Unique visitor count unchanged!
