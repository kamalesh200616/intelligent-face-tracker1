"""Unit tests for Face Recognizer, ArcFace embeddings, and cosine similarity matching."""

import numpy as np
import pytest

from src.config import RecognitionConfig
from src.database import FaceRecord
from src.face_recognizer import ArcFaceRecognizer, compute_cosine_similarity, normalize_l2


def test_cosine_similarity_edge_cases():
    """Verify cosine similarity properties."""
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert pytest.approx(compute_cosine_similarity(v1, v2)) == 1.0

    v_ortho = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert pytest.approx(compute_cosine_similarity(v1, v_ortho)) == 0.0

    v_opp = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
    assert pytest.approx(compute_cosine_similarity(v1, v_opp)) == -1.0


def test_l2_normalization():
    """Verify normalize_l2 scales vector to unit length."""
    raw = np.array([3.0, 4.0, 0.0], dtype=np.float32)
    normed = normalize_l2(raw)
    assert pytest.approx(np.linalg.norm(normed)) == 1.0
    assert pytest.approx(normed[0]) == 0.6
    assert pytest.approx(normed[1]) == 0.8


def test_identity_matching_threshold():
    """Verify match classification above and below similarity_threshold."""
    config = RecognitionConfig(similarity_threshold=0.70)
    recognizer = ArcFaceRecognizer(config)

    emb_target = np.array([1.0, 0.0, 0.0] + [0.0] * 509, dtype=np.float32)
    emb_target = normalize_l2(emb_target)

    # Registered face in database
    face_alice = FaceRecord(
        face_id="face_0001",
        name="Alice",
        embedding=emb_target,
        first_seen="2026-10-17T08:00:00Z",
        last_seen="2026-10-17T08:00:00Z",
        total_visits=1,
        metadata={},
    )
    registered = [face_alice]

    # Query 1: Close embedding (similarity ~ 0.95 >= 0.70)
    query_close = np.array([0.95, 0.31, 0.0] + [0.0] * 509, dtype=np.float32)
    query_close = normalize_l2(query_close)
    matched_id, score = recognizer.match_identity(query_close, registered)
    assert matched_id == "face_0001"
    assert score >= 0.70

    # Query 2: Distant embedding (similarity ~ 0.20 < 0.70)
    query_far = np.array([0.2, 0.98, 0.0] + [0.0] * 509, dtype=np.float32)
    query_far = normalize_l2(query_far)
    matched_id_none, score_low = recognizer.match_identity(query_far, registered)
    assert matched_id_none is None
    assert score_low < 0.70
