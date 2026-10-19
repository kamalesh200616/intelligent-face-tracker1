"""Unit tests for Face Detector, coordinate clamping, blur scoring, and crop validation."""

import cv2
import numpy as np
import pytest

from src.config import DetectionConfig
from src.detector import FaceDetector, compute_blur_score, validate_and_clamp_bbox


def test_validate_and_clamp_bbox():
    """Verify out-of-bounds bounding boxes are clamped without error."""
    # Frame size: 640 x 480
    frame_w, frame_h = 640, 480

    # Normal inside box
    clamped = validate_and_clamp_bbox((100, 100, 200, 200), frame_w, frame_h)
    assert clamped == (100, 100, 200, 200)

    # Box partially exceeding right and bottom edges
    clamped_exceed = validate_and_clamp_bbox((600, 450, 700, 550), frame_w, frame_h)
    assert clamped_exceed == (600, 450, 640, 480)

    # Negative coordinates
    clamped_neg = validate_and_clamp_bbox((-50, -20, 80, 90), frame_w, frame_h)
    assert clamped_neg == (0, 0, 80, 90)

    # Inverted or zero area box
    assert validate_and_clamp_bbox((200, 200, 100, 100), frame_w, frame_h) is None
    assert validate_and_clamp_bbox((100, 100, 100, 100), frame_w, frame_h) is None


def test_blur_score_sharp_vs_blurred():
    """Verify Laplacian variance correctly scores sharp image higher than heavily blurred image."""
    # Synthetic checkerboard (sharp edges)
    sharp_img = np.zeros((100, 100, 3), dtype=np.uint8)
    sharp_img[::10, :] = 255
    sharp_img[:, ::10] = 255

    # Blurred version
    blurred_img = cv2.GaussianBlur(sharp_img, (21, 21), 0)

    sharp_score = compute_blur_score(sharp_img)
    blurred_score = compute_blur_score(blurred_img)

    assert sharp_score > blurred_score
    assert blurred_score < 50.0  # Should be flagged as blurred


def test_detector_handles_empty_frame():
    """Verify detector handles empty or zero-sized frames gracefully."""
    config = DetectionConfig()
    detector = FaceDetector(config)

    empty_frame = np.array([], dtype=np.uint8)
    dets = detector.detect(empty_frame)
    assert dets == []

    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets_black = detector.detect(black_frame)
    assert isinstance(dets_black, list)
