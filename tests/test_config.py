"""Unit tests for configuration validation and loading."""

import json
import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.config import AppConfig, VideoConfig, DetectionConfig, RecognitionConfig, load_config


def test_default_config_valid():
    """Verify default AppConfig passes all validations."""
    config = AppConfig()
    assert config.system.app_name.startswith("Intelligent Face Tracker")
    assert config.detection.confidence_threshold == 0.60
    assert config.recognition.similarity_threshold == 0.60
    assert config.tracking.track_lost_timeout_seconds == 2.0


def test_invalid_similarity_threshold():
    """Verify out-of-range similarity thresholds trigger ValidationError."""
    with pytest.raises(ValidationError):
        RecognitionConfig(similarity_threshold=1.5)  # Must be <= 0.99

    with pytest.raises(ValidationError):
        RecognitionConfig(similarity_threshold=-0.1)  # Must be >= 0.1


def test_invalid_face_dimensions():
    """Verify face dimensions < 10x10 trigger validation error."""
    with pytest.raises(ValidationError):
        RecognitionConfig(min_face_size=(5, 5))


def test_env_var_override(monkeypatch, tmp_path):
    """Verify environment variables correctly override config settings."""
    cfg_file = tmp_path / "test_config.json"
    cfg_file.write_text(json.dumps({"recognition": {"similarity_threshold": 0.50}}), encoding="utf-8")

    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.75")
    monkeypatch.setenv("FRAME_SKIP_INTERVAL", "4")

    loaded = load_config(cfg_file)
    assert loaded.recognition.similarity_threshold == 0.75
    assert loaded.detection.frame_skip == 4


def test_rtsp_effective_source_error(monkeypatch):
    """Verify VideoConfig raises helpful error if RTSP selected with no URL."""
    monkeypatch.delenv("RTSP_STREAM_URL", raising=False)
    vid_cfg = VideoConfig(source_type="rtsp", rtsp_url="")
    with pytest.raises(ValueError, match="RTSP source selected"):
        vid_cfg.get_effective_source()
