"""Unit tests for Visitor Counter analytics and reporting."""

import numpy as np
import pytest

from src.database import DatabaseManager
from src.visitor_counter import VisitorCounter


@pytest.fixture
def counter_setup(tmp_path):
    db_file = tmp_path / "counter_test.db"
    db = DatabaseManager(str(db_file))
    vc = VisitorCounter(db)
    return db, vc


def test_unique_visitor_counting_across_repeated_visits(counter_setup):
    """Verify returning visitor increments entry count but NOT unique visitor count."""
    db, vc = counter_setup

    # Register 2 unique people
    db.register_face("face_0001", np.zeros(512, dtype=np.float32), name="Bob")
    db.register_face("face_0002", np.ones(512, dtype=np.float32), name="Carol")

    # Visit 1: Bob enters & exits (track 1)
    db.record_event("e1", "face_0001", 1, "entry", "2026-10-17T09:00:00Z", "p1", 0.9)
    db.record_event("e2", "face_0001", 1, "exit", "2026-10-17T09:10:00Z", "p2", 0.9)

    # Visit 2: Carol enters (track 2)
    db.record_event("e3", "face_0002", 2, "entry", "2026-10-17T09:15:00Z", "p3", 0.9)

    # Visit 3: Bob enters again later in the day (track 3)
    db.record_event("e4", "face_0001", 3, "entry", "2026-10-17T11:00:00Z", "p4", 0.9)

    # Validate analytics
    assert vc.get_unique_visitor_count() == 2
    assert vc.get_total_entries() == 3
    assert vc.get_total_exits() == 1
    assert vc.get_currently_present_count() == 2  # Carol + Bob's 2nd visit


def test_visitor_history_retrieval(counter_setup):
    """Verify per-visitor event history retrieval."""
    db, vc = counter_setup

    db.register_face("face_0001", np.zeros(512, dtype=np.float32), name="Alice")
    db.record_event("e1", "face_0001", 1, "entry", "2026-10-17T08:00:00Z", "p1", 0.95)
    db.record_event("e2", "face_0001", 1, "exit", "2026-10-17T08:05:00Z", "p2", 0.95)

    history = vc.get_visitor_history("face_0001")
    assert history is not None
    assert history["face_id"] == "face_0001"
    assert history["name"] == "Alice"
    assert history["event_count"] == 2
    assert history["events"][0]["event_type"] == "exit"  # ordered DESC by timestamp
