"""Configuration management for Intelligent Face Tracker.

Provides strongly typed configuration models using Pydantic, validates
ranges and values, checks paths, and supports environment variable overrides.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


class SystemConfig(BaseModel):
    app_name: str = "Intelligent Face Tracker with Auto-Registration and Visitor Counting"
    version: str = "1.0.0"
    environment: Literal["development", "production", "testing"] = "production"


class VideoConfig(BaseModel):
    source_type: Literal["file", "rtsp", "webcam"] = "file"
    file_path: str = "data/sample_video.mp4"
    rtsp_url: str = ""
    rtsp_env_var: str = "RTSP_STREAM_URL"
    reconnect_delay_seconds: float = Field(default=2.0, ge=0.1, le=60.0)
    max_reconnect_attempts: int = Field(default=5, ge=1, le=100)
    target_width: int = Field(default=1280, ge=320, le=3840)
    target_height: int = Field(default=720, ge=240, le=2160)

    def get_effective_source(self) -> str | int:
        """Resolve the effective video source path, RTSP URL, or device index."""
        if self.source_type == "rtsp":
            env_url = os.environ.get(self.rtsp_env_var, "").strip()
            if env_url:
                return env_url
            if self.rtsp_url.strip():
                return self.rtsp_url.strip()
            raise ValueError(
                f"RTSP source selected but neither '{self.rtsp_env_var}' environment variable "
                f"nor 'rtsp_url' in config is populated."
            )
        elif self.source_type == "webcam":
            try:
                return int(self.file_path)
            except ValueError:
                return 0
        else:
            return self.file_path


class DetectionConfig(BaseModel):
    model_type: Literal["yolov8_face", "onnx_face"] = "yolov8_face"
    model_path: str = "models/yolov8n-face.pt"
    confidence_threshold: float = Field(default=0.60, ge=0.1, le=1.0)
    nms_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    frame_skip: int = Field(default=2, ge=0, le=30)
    device: Literal["cpu", "cuda", "auto"] = "cpu"


class RecognitionConfig(BaseModel):
    model_type: Literal["arcface", "insightface"] = "arcface"
    model_path: str = "models/arcface_sota.onnx"
    embedding_dim: int = Field(default=512, ge=128, le=1024)
    similarity_threshold: float = Field(default=0.60, ge=0.1, le=0.99)
    min_face_size: Tuple[int, int] = (40, 40)
    blur_threshold: float = Field(default=50.0, ge=0.0)
    l2_normalize: bool = True

    @field_validator("min_face_size")
    def validate_min_size(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        if v[0] < 10 or v[1] < 10:
            raise ValueError("Minimum face dimensions must be at least 10x10 pixels.")
        return v


class TrackingConfig(BaseModel):
    tracker_type: Literal["bytetrack", "iou"] = "bytetrack"
    iou_threshold: float = Field(default=0.35, ge=0.05, le=0.95)
    min_hits_to_confirm: int = Field(default=3, ge=1, le=30)
    track_lost_timeout_seconds: float = Field(default=2.0, ge=0.1, le=60.0)
    max_lost_frames: int = Field(default=60, ge=1, le=300)


class StorageConfig(BaseModel):
    database_path: str = "data/visitor_tracker.db"
    entries_dir: str = "logs/entries"
    exits_dir: str = "logs/exits"
    log_file: str = "logs/events.log"
    save_crops: bool = True
    crop_margin_ratio: float = Field(default=0.15, ge=0.0, le=0.5)


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    console_output: bool = True
    file_output: bool = True
    log_format: str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


class AppConfig(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    recognition: RecognitionConfig = Field(default_factory=RecognitionConfig)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def ensure_directories(self) -> None:
        """Create necessary project runtime directories."""
        dirs_to_create = [
            Path(self.storage.database_path).parent,
            Path(self.storage.entries_dir),
            Path(self.storage.exits_dir),
            Path(self.storage.log_file).parent,
            Path("models"),
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)


def load_config(config_path: str | Path = "config.json") -> AppConfig:
    """Load and validate application configuration from JSON.

    Args:
        config_path: Path to config.json. If missing, default AppConfig is returned.

    Returns:
        Validated AppConfig instance.

    Raises:
        ValueError: If JSON is invalid or fields fail validation.
    """
    path = Path(config_path)
    if not path.is_file():
        cfg = AppConfig()
        cfg.ensure_directories()
        return cfg

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON configuration file '{path}': {err}") from err

    # Apply environment variable overrides if present
    if "SIMILARITY_THRESHOLD" in os.environ:
        try:
            raw_data.setdefault("recognition", {})["similarity_threshold"] = float(os.environ["SIMILARITY_THRESHOLD"])
        except ValueError:
            pass

    if "FRAME_SKIP_INTERVAL" in os.environ:
        try:
            raw_data.setdefault("detection", {})["frame_skip"] = int(os.environ["FRAME_SKIP_INTERVAL"])
        except ValueError:
            pass

    if "TRACK_LOST_TIMEOUT_SECONDS" in os.environ:
        try:
            raw_data.setdefault("tracking", {})["track_lost_timeout_seconds"] = float(os.environ["TRACK_LOST_TIMEOUT_SECONDS"])
        except ValueError:
            pass

    config = AppConfig.model_validate(raw_data)
    config.ensure_directories()
    return config
