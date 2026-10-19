"""Event Lifecycle Manager handling Entry and Exit state transitions and crop archiving.

Mandatory Requirements Met:
- Exactly one Entry event emitted upon track confirmation.
- Exactly one Exit event emitted when track is deleted following the lost timeout.
- Saves high-quality cropped face images to dated directory trees:
    logs/entries/YYYY-MM-DD/
    logs/exits/YYYY-MM-DD/
- Enforces database idempotency and updates persistent audit logs (events.log).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

from src.config import StorageConfig
from src.database import DatabaseManager
from src.logging_setup import get_logger
from src.tracker import Track

logger = get_logger("event_manager")


class EventManager:
    """Coordinates entry and exit event emissions, image saving, and database audit logs."""

    def __init__(self, db: DatabaseManager, config: StorageConfig):
        self.db = db
        self.config = config
        self._ensure_storage_dirs()

    def _ensure_storage_dirs(self) -> None:
        """Create root crop directories if needed."""
        Path(self.config.entries_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.exits_dir).mkdir(parents=True, exist_ok=True)

    def _get_dated_subfolder(self, base_dir: str, dt_obj: datetime) -> Path:
        """Return Path object for base_dir/YYYY-MM-DD/ ensuring it exists."""
        dated_path = Path(base_dir) / dt_obj.strftime("%Y-%m-%d")
        dated_path.mkdir(parents=True, exist_ok=True)
        return dated_path

    def handle_entry(
        self,
        track: Track,
        timestamp_iso: Optional[str] = None,
        session_id: str = "session_default",
    ) -> bool:
        """Process confirmed track entry into the camera view.

        Returns True if event was emitted and logged; False if skipped (already logged or unassigned).
        """
        if track.entry_event_logged:
            return False

        if not track.face_id:
            logger.debug("Cannot emit ENTRY for track %d: no face_id assigned", track.track_id)
            return False

        now_dt = datetime.now(timezone.utc)
        ts_iso = timestamp_iso or now_dt.isoformat()
        clean_ts = now_dt.strftime("%H%M%S_%f")[:11]
        event_id = f"evt_entry_{uuid.uuid4().hex[:8]}"

        # 1. Save Cropped Face Image
        crop_path_str = ""
        if self.config.save_crops and track.best_crop is not None and track.best_crop.size > 0:
            target_dir = self._get_dated_subfolder(self.config.entries_dir, now_dt)
            filename = f"{track.face_id}_track{track.track_id}_{clean_ts}.jpg"
            full_crop_path = target_dir / filename
            cv2.imwrite(str(full_crop_path), track.best_crop)
            crop_path_str = str(full_crop_path)

        # 2. Persist in Database
        recorded = self.db.record_event(
            event_id=event_id,
            face_id=track.face_id,
            track_id=track.track_id,
            event_type="entry",
            timestamp=ts_iso,
            image_path=crop_path_str,
            confidence=float(track.confidence),
            session_id=session_id,
        )

        if recorded:
            track.entry_event_logged = True
            logger.info(
                "CONFIRMED ENTRY: Face %s (Session: %s, Track ID: %d, Event ID: %s, Crop: %s)",
                track.face_id,
                session_id,
                track.track_id,
                event_id,
                crop_path_str or "none",
            )
            return True

        return False

    def handle_exit(
        self,
        track: Track,
        timestamp_iso: Optional[str] = None,
        session_id: str = "session_default",
    ) -> bool:
        """Process confirmed track exit after disappearing beyond timeout.

        Returns True if exit was emitted; False if skipped.
        """
        # Enforce lifecycle: only exit if entry was confirmed, and avoid duplicate exits
        if track.exit_event_logged or not track.entry_event_logged:
            return False

        if not track.face_id:
            return False

        now_dt = datetime.now(timezone.utc)
        ts_iso = timestamp_iso or now_dt.isoformat()
        clean_ts = now_dt.strftime("%H%M%S_%f")[:11]
        event_id = f"evt_exit_{uuid.uuid4().hex[:8]}"

        # 1. Save Exit Cropped Image
        crop_path_str = ""
        if self.config.save_crops and track.best_crop is not None and track.best_crop.size > 0:
            target_dir = self._get_dated_subfolder(self.config.exits_dir, now_dt)
            filename = f"{track.face_id}_track{track.track_id}_{clean_ts}.jpg"
            full_crop_path = target_dir / filename
            cv2.imwrite(str(full_crop_path), track.best_crop)
            crop_path_str = str(full_crop_path)

        # 2. Persist in Database
        recorded = self.db.record_event(
            event_id=event_id,
            face_id=track.face_id,
            track_id=track.track_id,
            event_type="exit",
            timestamp=ts_iso,
            image_path=crop_path_str,
            confidence=float(track.confidence),
            session_id=session_id,
        )

        if recorded:
            track.exit_event_logged = True
            logger.info(
                "CONFIRMED EXIT: Face %s (Session: %s, Track ID: %d, Event ID: %s, Crop: %s)",
                track.face_id,
                session_id,
                track.track_id,
                event_id,
                crop_path_str or "none",
            )
            return True

        return False
