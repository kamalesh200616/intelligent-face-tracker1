"""Automated tests for FastAPI web endpoints."""

import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Intelligent Face Tracker" in data["app_name"]


def test_api_stats(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_unique_visitors" in data
    assert "total_entries" in data
    assert "total_exits" in data
    assert "active_job" in data


def test_api_events_paginated(client):
    res = client.get("/api/events?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)


def test_api_identities(client):
    res = client.get("/api/identities")
    assert res.status_code == 200
    data = res.json()
    assert "identities" in data
    # Ensure biometric raw vector is not exposed
    for id_entry in data["identities"]:
        assert "embedding" not in id_entry
        assert "face_id" in id_entry


def test_api_config(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "detection" in data
    assert "recognition" in data
    assert "tracking" in data


def test_api_uploads(client):
    res = client.get("/api/uploads")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "videos" in data
    assert isinstance(data["videos"], list)


def test_api_jobs_reset(client):
    res = client.post("/api/jobs/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True


def test_api_delete_identity(client):
    from server import db
    import numpy as np

    # Register temporary test face
    test_id = "face_test_del_9999"
    emb = np.random.randn(512).astype(np.float32)
    db.register_face(face_id=test_id, embedding=emb)
    db.record_event(
        event_id="evt_test_del_9999",
        face_id=test_id,
        track_id=999,
        event_type="entry",
        timestamp="2026-10-18T12:00:00Z",
        image_path="",
        confidence=0.99,
        session_id="session_test_del",
    )

    # Delete via API
    res = client.delete(f"/api/identities/{test_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Confirm face and events are gone
    assert db.get_face(test_id) is None
    events = db.get_events(face_id=test_id)
    assert len(events) == 0

    # 404 on deleting non-existent face
    res_404 = client.delete(f"/api/identities/{test_id}")
    assert res_404.status_code == 404

