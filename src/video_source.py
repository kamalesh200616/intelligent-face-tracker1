"""Resilient video ingestion for local video files, RTSP camera streams, and webcams.

Features:
- Configurable source types ('file', 'rtsp', 'webcam').
- Exponential backoff reconnection for network stream drops.
- Clean resource acquisition and release via context manager.
- Accurate frame index and ISO 8601 timestamp tracking.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional, Tuple, Union
import cv2
import numpy as np

from src.config import VideoConfig
from src.logging_setup import get_logger

logger = get_logger("video_source")


class VideoSource:
    """Manages video capture lifecycle with automatic RTSP stream recovery."""

    def __init__(self, config: VideoConfig):
        self.config = config
        self.source = config.get_effective_source()
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_opened = False
        self._frame_count = 0
        self._fps: float = 30.0

    def open(self) -> bool:
        """Open the video stream or file with verification."""
        logger.info("Opening video source [Type: %s]: %s", self.config.source_type, self._safe_source_repr())

        # If it's a file, verify path existence
        if self.config.source_type == "file":
            file_path = Path(str(self.source))
            if not file_path.is_file():
                logger.error("Video file does not exist: %s", file_path.resolve())
                return False

        # Open cv2 VideoCapture
        if isinstance(self.source, int):
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY)
        else:
            self.cap = cv2.VideoCapture(str(self.source))

        if not self.cap or not self.cap.isOpened():
            logger.error("Failed to open video source: %s", self._safe_source_repr())
            self._is_opened = False
            return False

        self._is_opened = True
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self._fps = fps if fps and fps > 0 else 30.0
        logger.info(
            "Video source successfully opened (FPS: %.1f, Dimensions: %dx%d)",
            self._fps,
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        return True

    def read_frames(self) -> Generator[Tuple[int, str, np.ndarray], None, None]:
        """Yield frames sequentially as (frame_index, iso_timestamp, frame_bgr).

        Automatically attempts reconnection if an RTSP camera stream drops.
        """
        if not self._is_opened:
            if not self.open():
                return

        consecutive_failures = 0
        max_attempts = self.config.max_reconnect_attempts

        while True:
            if not self.cap or not self.cap.isOpened():
                if self.config.source_type == "rtsp":
                    if not self._reconnect():
                        logger.error("Exceeded maximum RTSP reconnection attempts. Terminating video ingestion.")
                        break
                else:
                    break

            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                consecutive_failures += 1
                if self.config.source_type == "rtsp":
                    logger.warning("Stream read failure (%d/%d). Attempting reconnection...", consecutive_failures, max_attempts)
                    if not self._reconnect():
                        logger.error("Unable to restore dropped RTSP stream.")
                        break
                    continue
                else:
                    logger.info("Reached End of File (EOF) or stream complete. Total frames read: %d", self._frame_count)
                    break

            consecutive_failures = 0
            self._frame_count += 1
            now_iso = datetime.now(timezone.utc).isoformat()
            yield self._frame_count, now_iso, frame

    def _reconnect(self) -> bool:
        """Attempt to reconnect to RTSP stream with exponential backoff."""
        self.release()
        delay = self.config.reconnect_delay_seconds

        for attempt in range(1, self.config.max_reconnect_attempts + 1):
            logger.info("Reconnection attempt %d/%d in %.1fs...", attempt, self.config.max_reconnect_attempts, delay)
            time.sleep(delay)
            if self.open():
                logger.info("Successfully reconnected to stream on attempt %d", attempt)
                return True
            delay = min(delay * 1.5, 30.0)

        return False

    def release(self) -> None:
        """Gracefully release the video capture device."""
        if self.cap:
            try:
                self.cap.release()
                logger.info("Released video capture resource for %s", self._safe_source_repr())
            except Exception as e:
                logger.warning("Error releasing video source: %s", e)
            finally:
                self.cap = None
                self._is_opened = False

    def _safe_source_repr(self) -> str:
        """Mask credentials from RTSP URLs for secure logging."""
        s = str(self.source)
        if "@" in s and "://" in s:
            proto, rest = s.split("://", 1)
            creds, host = rest.split("@", 1)
            return f"{proto}://***:***@{host}"
        return s

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def total_frames_processed(self) -> int:
        return self._frame_count

    def __enter__(self) -> VideoSource:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
