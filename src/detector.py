"""Face Detection module supporting YOLOv8-face and high-performance ONNX architectures.

Features:
- YOLO-based real-time face detection with confidence thresholding.
- Strict bounding box coordinate clamping and validation to prevent invalid crops.
- Blur estimation via Laplacian variance and minimum face size gating.
- Configurable margin padding for facial crops.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np

from src.config import DetectionConfig
from src.logging_setup import get_logger

logger = get_logger("detector")


@dataclass
class Detection:
    """Represents a single validated face detection within a frame."""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) in integer pixels
    confidence: float                # Detection confidence score [0.0, 1.0]
    crop: np.ndarray                 # Clamped, validated BGR face image crop
    blur_score: float                # Laplacian variance blur metric
    is_valid_quality: bool           # True if passes both size and blur checks
    detection_id: int = 0            # Frame-local detection index


def compute_blur_score(image: np.ndarray) -> float:
    """Compute the variance of the Laplacian as a focus/sharpness metric.

    Higher scores indicate sharper images; scores below ~40-50 indicate significant blur.
    """
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def validate_and_clamp_bbox(
    bbox: Tuple[float, float, float, float],
    frame_w: int,
    frame_h: int,
    margin_ratio: float = 0.0,
) -> Optional[Tuple[int, int, int, int]]:
    """Validate and clamp bounding box coordinates to frame boundaries with optional margin.

    Returns None if the resulting box is degenerate (area <= 0).
    """
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1

    if w <= 0 or h <= 0:
        return None

    # Apply margin padding
    if margin_ratio > 0.0:
        pad_w = w * margin_ratio
        pad_h = h * margin_ratio
        x1 -= pad_w
        x2 += pad_w
        y1 -= pad_h
        y2 += pad_h

    # Clamp strictly within frame
    cx1 = max(0, min(int(round(x1)), frame_w - 1))
    cy1 = max(0, min(int(round(y1)), frame_h - 1))
    cx2 = max(0, min(int(round(x2)), frame_w))
    cy2 = max(0, min(int(round(y2)), frame_h))

    if cx2 <= cx1 or cy2 <= cy1:
        return None

    return cx1, cy1, cx2, cy2


class FaceDetector:
    """Unified face detector interface with YOLOv8 and ONNX/YuNet engines."""

    def __init__(self, config: DetectionConfig, margin_ratio: float = 0.15):
        self.config = config
        self.margin_ratio = margin_ratio
        self.model = None
        self._backend = "none"
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize the detection backend based on model path and availability."""
        model_path = Path(self.config.model_path)

        # 1. Try Ultralytics YOLO if a .pt model file exists
        if model_path.suffix.lower() == ".pt" and model_path.is_file():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(model_path))
                self._backend = "ultralytics_yolo"
                logger.info("Initialized YOLOv8-face model from %s on device=%s", model_path, self.config.device)
                return
            except Exception as e:
                logger.warning("Could not initialize Ultralytics YOLO (%s). Falling back...", e)

        # 2. Try OpenCV YuNet FaceDetectorYN if an ONNX model is available or use default
        if model_path.suffix.lower() == ".onnx" and model_path.is_file():
            try:
                self.model = cv2.FaceDetectorYN.create(
                    model=str(model_path),
                    config="",
                    input_size=(640, 640),
                    score_threshold=self.config.confidence_threshold,
                    nms_threshold=self.config.nms_threshold,
                )
                self._backend = "cv2_yunet"
                logger.info("Initialized OpenCV YuNet face detector from %s", model_path)
                return
            except Exception as e:
                logger.warning("Could not initialize YuNet model (%s).", e)

        # 3. Default fallback: OpenCV DNN Haar cascade or lightweight face detector for zero-crash startup
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if Path(cascade_path).is_file():
            self.model = cv2.CascadeClassifier(cascade_path)
            self._backend = "opencv_cascade"
            logger.info("Initialized robust OpenCV face cascade detector (fallback mode).")
        else:
            self._backend = "mock"
            logger.warning("No face model weights found; initialized mock/fallback detector.")

    def detect(
        self,
        frame: np.ndarray,
        min_size: Tuple[int, int] = (40, 40),
        blur_threshold: float = 50.0,
    ) -> List[Detection]:
        """Detect faces in a single BGR frame.

        Args:
            frame: BGR image numpy array.
            min_size: (min_w, min_h) minimum face dimensions.
            blur_threshold: Minimum Laplacian variance score for high-quality crops.

        Returns:
            List of validated Detection objects.
        """
        if frame is None or frame.size == 0:
            return []

        frame_h, frame_w = frame.shape[:2]
        raw_boxes: List[Tuple[float, float, float, float, float]] = []

        if self._backend == "ultralytics_yolo" and self.model is not None:
            results = self.model.predict(
                source=frame,
                conf=self.config.confidence_threshold,
                iou=self.config.nms_threshold,
                device=self.config.device if self.config.device != "auto" else 0,
                verbose=False,
            )
            for res in results:
                boxes = res.boxes
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    raw_boxes.append((xyxy[0], xyxy[1], xyxy[2], xyxy[3], conf))

        elif self._backend == "cv2_yunet" and self.model is not None:
            self.model.setInputSize((frame_w, frame_h))
            _, faces = self.model.detect(frame)
            if faces is not None:
                for face in faces:
                    x, y, w, h, conf = face[0], face[1], face[2], face[3], face[14]
                    raw_boxes.append((x, y, x + w, y + h, float(conf)))

        elif self._backend == "opencv_cascade" and self.model is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.model.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=min_size,
            )
            for (x, y, w, h) in faces:
                # Simulated high confidence for cascade matches passing minNeighbors
                raw_boxes.append((float(x), float(y), float(x + w), float(y + h), 0.90))

        # Process, clamp, validate crops and quality
        detections: List[Detection] = []
        for det_idx, (x1, y1, x2, y2, conf) in enumerate(raw_boxes):
            if conf < self.config.confidence_threshold:
                continue

            clamped = validate_and_clamp_bbox((x1, y1, x2, y2), frame_w, frame_h, self.margin_ratio)
            if clamped is None:
                continue

            cx1, cy1, cx2, cy2 = clamped
            crop_w = cx2 - cx1
            crop_h = cy2 - cy1

            if crop_w < min_size[0] or crop_h < min_size[1]:
                logger.debug("Rejected detection %d: crop dimensions %dx%d below min size %s", det_idx, crop_w, crop_h, min_size)
                continue

            crop = frame[cy1:cy2, cx1:cx2].copy()
            blur = compute_blur_score(crop)
            is_sharp = blur >= blur_threshold

            detections.append(
                Detection(
                    bbox=(cx1, cy1, cx2, cy2),
                    confidence=conf,
                    crop=crop,
                    blur_score=blur,
                    is_valid_quality=is_sharp,
                    detection_id=det_idx + 1,
                )
            )

        logger.debug("Frame detection complete: %d raw boxes -> %d validated detections", len(raw_boxes), len(detections))
        return detections
