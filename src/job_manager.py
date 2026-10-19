"""Background Job Manager for asynchronous video processing.

Executes the AI Face Tracking pipeline in a non-blocking background thread,
allowing web clients to poll progress, view real-time metrics, and cancel jobs.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import cv2

from src.config import AppConfig, VideoConfig, load_config
from src.database import DatabaseManager
from src.detector import FaceDetector
from src.event_manager import EventManager
from src.face_recognizer import ArcFaceRecognizer
from src.identity_manager import IdentityManager
from src.logging_setup import get_logger
from src.tracker import FaceTracker, TrackState
from src.video_source import VideoSource
from src.visitor_counter import VisitorCounter

logger = get_logger("job_manager")


class JobManager:
    """Singleton manager executing video analytics jobs asynchronously."""

    _instance: Optional[JobManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> JobManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._status_lock = threading.Lock()

        # Job state tracking
        self.job_id: Optional[str] = None
        self.status: str = "idle"  # idle, running, completed, failed, stopped
        self.source_type: str = "none"
        self.source_path: str = ""
        self.current_frame: int = 0
        self.total_frames: int = 0
        self.progress_percent: float = 0.0
        self.fps: float = 0.0
        self.unique_visitors: int = 0
        self.total_entries: int = 0
        self.total_exits: int = 0
        self.active_tracks: int = 0
        self.error_message: Optional[str] = None
        self.start_time_iso: Optional[str] = None
        self.end_time_iso: Optional[str] = None
        self.elapsed_seconds: float = 0.0

    def start_job(
        self,
        source_type: str,
        source_path: str,
        rtsp_url: Optional[str] = None,
        config: Optional[AppConfig] = None,
    ) -> Dict[str, Any]:
        """Initiate asynchronous video processing."""
        with self._status_lock:
            if self.status == "running":
                return {
                    "success": False,
                    "message": f"Job {self.job_id} is already in progress.",
                    "job_id": self.job_id,
                }

            self.job_id = f"job_{uuid.uuid4().hex[:8]}"
            self.status = "running"
            self.source_type = source_type
            self.source_path = source_path
            self.current_frame = 0
            self.total_frames = 0
            self.progress_percent = 0.0
            self.fps = 0.0
            self.unique_visitors = 0
            self.total_entries = 0
            self.total_exits = 0
            self.active_tracks = 0
            self.error_message = None
            self.start_time_iso = datetime.now(timezone.utc).isoformat()
            self.end_time_iso = None
            self.elapsed_seconds = 0.0
            self._stop_event.clear()

        app_config = config or load_config()

        self._thread = threading.Thread(
            target=self._run_job_worker,
            args=(self.job_id, source_type, source_path, rtsp_url, app_config),
            daemon=True,
        )
        self._thread.start()
        logger.info("Spawned background processing thread for Job %s", self.job_id)

        return {
            "success": True,
            "message": "Processing job started successfully.",
            "job_id": self.job_id,
            "status": "running",
        }

    def stop_job(self) -> Dict[str, Any]:
        """Request cooperative cancellation of currently running job."""
        with self._status_lock:
            if self.status != "running":
                return {"success": False, "message": "No active job is currently running."}
            self._stop_event.set()
            logger.info("Cancellation requested for Job %s", self.job_id)
            return {"success": True, "message": f"Cancellation signal sent to job {self.job_id}."}

    def reset_status(self) -> None:
        """Reset job status to idle and clear metrics."""
        with self._status_lock:
            if self.status != "running":
                self.job_id = None
                self.status = "idle"
                self.source_type = "none"
                self.source_path = ""
                self.current_frame = 0
                self.total_frames = 0
                self.progress_percent = 0.0
                self.fps = 0.0
                self.unique_visitors = 0
                self.total_entries = 0
                self.total_exits = 0
                self.active_tracks = 0
                self.error_message = None
                self.start_time_iso = None
                self.end_time_iso = None
                self.elapsed_seconds = 0.0

    def get_status(self) -> Dict[str, Any]:
        """Return snapshot of job progress and metrics."""
        with self._status_lock:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "source_type": self.source_type,
                "source_path": self.source_path,
                "current_frame": self.current_frame,
                "total_frames": self.total_frames,
                "progress_percent": round(self.progress_percent, 1),
                "fps": round(self.fps, 1),
                "unique_visitors": self.unique_visitors,
                "total_entries": self.total_entries,
                "total_exits": self.total_exits,
                "active_tracks": self.active_tracks,
                "error_message": self.error_message,
                "start_time": self.start_time_iso,
                "end_time": self.end_time_iso,
                "elapsed_seconds": round(self.elapsed_seconds, 1),
            }

    def _run_job_worker(
        self,
        job_id: str,
        source_type: str,
        source_path: str,
        rtsp_url: Optional[str],
        config: AppConfig,
    ) -> None:
        """Internal processing loop executed inside background worker thread."""
        logger.info("Job %s worker started for %s (%s)", job_id, source_type, source_path)
        start_ts = time.time()

        # Clone and configure video source
        vid_cfg = VideoConfig(
            source_type=source_type,
            file_path=source_path,
            rtsp_url=rtsp_url or "",
            reconnect_delay_seconds=config.video.reconnect_delay_seconds,
            max_reconnect_attempts=config.video.max_reconnect_attempts,
        )

        db = DatabaseManager(config.storage.database_path)
        detector = FaceDetector(config.detection, margin_ratio=config.storage.crop_margin_ratio)
        recognizer = ArcFaceRecognizer(config.recognition)
        tracker = FaceTracker(config.tracking)
        identity_mgr = IdentityManager(db, recognizer, config.recognition)
        identity_mgr.reset_tracks()
        event_mgr = EventManager(db, config.storage)

        # Estimate total frames if file
        total_frames = 0
        if source_type == "file" and Path(source_path).is_file():
            try:
                cap_temp = cv2.VideoCapture(source_path)
                total_frames = int(cap_temp.get(cv2.CAP_PROP_FRAME_COUNT))
                cap_temp.release()
            except Exception:
                total_frames = 0

        with self._status_lock:
            self.total_frames = total_frames

        # Start DB session
        db.start_session(session_id=job_id, source_type=source_type, source_path=source_path)

        video_source = VideoSource(vid_cfg)
        if not video_source.open():
            err = f"Failed to open video source: {source_path}"
            logger.error(err)
            with self._status_lock:
                self.status = "failed"
                self.error_message = err
                self.end_time_iso = datetime.now(timezone.utc).isoformat()
            db.end_session(job_id, total_frames=0, unique_faces_count=0, status="FAILED")
            return

        frame_idx = 0
        fps_smooth = 0.0
        session_faces: set = set()
        session_entries: int = 0
        session_exits: int = 0
        total_detections: int = 0

        try:
            for f_num, timestamp_iso, frame in video_source.read_frames():
                if self._stop_event.is_set():
                    logger.info("Job %s interrupted via user cancellation.", job_id)
                    with self._status_lock:
                        self.status = "stopped"
                    break

                t_start = time.time()
                frame_idx = f_num

                # Frame skipping logic
                skip_interval = config.detection.frame_skip
                should_detect = (skip_interval == 0) or (frame_idx % (skip_interval + 1) == 0)

                detections = []
                if should_detect:
                    detections = detector.detect(
                        frame=frame,
                        min_size=config.recognition.min_face_size,
                        blur_threshold=config.recognition.blur_threshold,
                    )
                    total_detections += len(detections)
                    active_tracks, deleted_tracks = tracker.update(detections, frame_index=frame_idx)
                else:
                    active_tracks = [trk for trk in tracker.tracks.values() if trk.state in (TrackState.CONFIRMED, TrackState.LOST)]
                    deleted_tracks = []

                # Handle newly confirmed tracks -> Auto-registration & Entry Event
                for trk in active_tracks:
                    if trk.state == TrackState.CONFIRMED:
                        assigned_face_id = identity_mgr.process_track(trk)
                        if assigned_face_id:
                            session_faces.add(assigned_face_id)
                            if not trk.entry_event_logged:
                                if event_mgr.handle_entry(trk, timestamp_iso=timestamp_iso, session_id=job_id):
                                    session_entries += 1

                # Handle deleted tracks -> Exit Event & release
                for dtrk in deleted_tracks:
                    if dtrk.entry_event_logged and not dtrk.exit_event_logged:
                        if event_mgr.handle_exit(dtrk, timestamp_iso=timestamp_iso, session_id=job_id):
                            session_exits += 1
                    identity_mgr.release_track(dtrk.track_id)

                dt = time.time() - t_start
                if dt > 0:
                    fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / dt)

                # Update live snapshot every 5 frames or on final frame
                if frame_idx % 5 == 0 or frame_idx == total_frames:
                    elapsed = time.time() - start_ts
                    pct = (frame_idx / total_frames * 100.0) if total_frames > 0 else 0.0

                    with self._status_lock:
                        self.current_frame = frame_idx
                        self.progress_percent = min(100.0, pct)
                        self.fps = fps_smooth
                        self.unique_visitors = len(session_faces)
                        self.total_entries = session_entries
                        self.total_exits = session_exits
                        self.active_tracks = len(active_tracks)
                        self.elapsed_seconds = elapsed

            # Video finished reading: Flush any remaining active tracks for exit events
            video_source.release()
            final_iso = datetime.now(timezone.utc).isoformat()
            for trk in list(tracker.tracks.values()):
                if trk.entry_event_logged and not trk.exit_event_logged:
                    if event_mgr.handle_exit(trk, timestamp_iso=final_iso, session_id=job_id):
                        session_exits += 1
                identity_mgr.release_track(trk.track_id)

            elapsed_total = time.time() - start_ts

            with self._status_lock:
                if self.status != "stopped":
                    self.status = "completed"
                    self.progress_percent = 100.0
                self.end_time_iso = datetime.now(timezone.utc).isoformat()
                self.elapsed_seconds = elapsed_total
                self.unique_visitors = len(session_faces)
                self.total_entries = session_entries
                self.total_exits = session_exits
                self.active_tracks = 0

            db.end_session(
                job_id,
                total_frames=frame_idx,
                unique_faces_count=len(session_faces),
                status=self.status.upper(),
            )

            # Diagnostic summary log
            logger.info(
                "DIAGNOSTIC SUMMARY: Job %s completed | File: %s (%s) | Frames: %d/%d | Duration: %.2fs (%.1f FPS) | Detections: %d | Matches: %d | New Registrations: %d | Session Unique Visitors: %d | Entries: %d | Exits: %d",
                job_id,
                source_path,
                source_type,
                frame_idx,
                total_frames,
                elapsed_total,
                (frame_idx / elapsed_total if elapsed_total > 0 else 0),
                total_detections,
                identity_mgr.total_matches,
                identity_mgr.total_registrations,
                len(session_faces),
                session_entries,
                session_exits,
            )

        except Exception as e:
            logger.exception("Job %s encountered unexpected failure: %s", job_id, e)
            video_source.release()
            with self._status_lock:
                self.status = "failed"
                self.error_message = str(e)
                self.end_time_iso = datetime.now(timezone.utc).isoformat()
            db.end_session(job_id, total_frames=frame_idx, unique_faces_count=0, status="FAILED")

