"""Unit tests for Multi-Object Face Tracker, IoU association, and state machine."""

import numpy as np
import pytest

from src.config import TrackingConfig
from src.detector import Detection
from src.tracker import FaceTracker, TrackState, compute_iou


def create_dummy_detection(bbox, blur=60.0, conf=0.9):
    x1, y1, x2, y2 = bbox
    crop = np.zeros((y2 - y1, x2 - x1, 3), dtype=np.uint8)
    return Detection(
        bbox=bbox,
        confidence=conf,
        crop=crop,
        blur_score=blur,
        is_valid_quality=True,
    )


def test_compute_iou():
    """Verify IoU overlap calculations."""
    boxA = (10, 10, 50, 50)
    boxB = (10, 10, 50, 50)
    assert pytest.approx(compute_iou(boxA, boxB)) == 1.0

    box_disjoint = (100, 100, 150, 150)
    assert compute_iou(boxA, box_disjoint) == 0.0

    # 50% overlap scenario
    # box1: (0, 0, 10, 10) -> area 100
    # box2: (5, 0, 15, 10) -> area 100
    # intersection: (5, 0, 10, 10) -> area 50, union: 150 -> IoU = 50/150 = 0.3333
    box1 = (0, 0, 10, 10)
    box2 = (5, 0, 15, 10)
    assert pytest.approx(compute_iou(box1, box2), rel=1e-3) == 50.0 / 150.0


def test_tracker_confirmation_and_deletion():
    """Verify tentative track confirms after min_hits and deletes after max_lost_frames."""
    config = TrackingConfig(min_hits_to_confirm=3, max_lost_frames=2, iou_threshold=0.3)
    tracker = FaceTracker(config)

    det = create_dummy_detection((50, 50, 150, 150))

    # Frame 1: Tentative
    active, deleted = tracker.update([det], frame_index=1)
    assert len(active) == 0  # not yet confirmed
    assert len(deleted) == 0
    track_id = list(tracker.tracks.keys())[0]
    assert tracker.tracks[track_id].state == TrackState.TENTATIVE

    # Frame 2: Hit 2
    active, deleted = tracker.update([det], frame_index=2)
    assert len(active) == 0

    # Frame 3: Hit 3 -> Transitions to CONFIRMED!
    active, deleted = tracker.update([det], frame_index=3)
    assert len(active) == 1
    assert active[0].track_id == track_id
    assert active[0].state == TrackState.CONFIRMED

    # Frame 4: Missed detection 1 (LOST)
    active, deleted = tracker.update([], frame_index=4)
    assert len(active) == 1  # Still active during grace period
    assert active[0].state == TrackState.LOST

    # Frame 5: Missed detection 2 (LOST)
    active, deleted = tracker.update([], frame_index=5)
    assert len(active) == 1

    # Frame 6: Missed detection 3 (> max_lost_frames of 2) -> DELETED!
    active, deleted = tracker.update([], frame_index=6)
    assert len(active) == 0
    assert len(deleted) == 1
    assert deleted[0].track_id == track_id
    assert deleted[0].state == TrackState.DELETED
