"""Unit tests for VideoSource, file handling, missing sources, and RTSP failures."""

import pytest
from pathlib import Path

from src.config import VideoConfig
from src.video_source import VideoSource


def test_missing_video_file_fails_cleanly(tmp_path):
    """Verify missing video file returns False on open() without throwing uncaught exceptions."""
    cfg = VideoConfig(
        source_type="file",
        file_path=str(tmp_path / "non_existent_video.mp4"),
    )
    vs = VideoSource(cfg)
    assert vs.open() is False
    assert vs.total_frames_processed == 0

    # Generator should yield nothing
    frames = list(vs.read_frames())
    assert len(frames) == 0


def test_release_idempotent():
    """Verify release() can be called safely multiple times."""
    cfg = VideoConfig(source_type="file", file_path="dummy.mp4")
    vs = VideoSource(cfg)
    vs.release()
    vs.release()
    assert vs.cap is None


def test_safe_source_repr_masks_credentials():
    """Verify RTSP passwords are masked from logs."""
    cfg = VideoConfig(
        source_type="rtsp",
        rtsp_url="rtsp://admin:supersecret123@192.168.1.50:554/live",
    )
    vs = VideoSource(cfg)
    safe = vs._safe_source_repr()
    assert "supersecret123" not in safe
    assert "***:***@" in safe
