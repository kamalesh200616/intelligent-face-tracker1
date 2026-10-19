"""Main application entry point for Intelligent Face Tracker with Auto-Registration and Visitor Counting.

CLI Usage:
    # 1. Process default video file configured in config.json
    python app.py

    # 2. Process custom video file in headless mode
    python app.py --source data/sample_video.mp4 --headless

    # 3. Process live RTSP stream
    python app.py --source-type rtsp --source rtsp://admin:pass@192.168.1.50:554/h264

    # 4. Display visitor counting summary from SQLite database
    python app.py --summary

    # 5. Inspect specific visitor history
    python app.py --inspect --face-id face_0001
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
import uuid
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

from src.config import AppConfig, load_config
from src.database import DatabaseManager
from src.detector import FaceDetector
from src.event_manager import EventManager
from src.face_recognizer import ArcFaceRecognizer
from src.identity_manager import IdentityManager
from src.logging_setup import get_logger, setup_logging
from src.tracker import FaceTracker, TrackState
from src.video_source import VideoSource
from src.visitor_counter import VisitorCounter

logger = get_logger("app")


class FaceTrackerApp:
    """Orchestrates video ingestion, detection, recognition, tracking, event logging, and counting."""

    def __init__(self, config: AppConfig, headless: bool = False):
        self.config = config
        self.headless = headless
        self._running = False

        # Initialize persistence & core subsystems
        self.db = DatabaseManager(config.storage.database_path)
        self.detector = FaceDetector(config.detection, margin_ratio=config.storage.crop_margin_ratio)
        self.recognizer = ArcFaceRecognizer(config.recognition)
        self.tracker = FaceTracker(config.tracking)
        self.identity_mgr = IdentityManager(self.db, self.recognizer, config.recognition)
        self.event_mgr = EventManager(self.db, config.storage)
        self.counter = VisitorCounter(self.db)

        # Setup graceful shutdown signals
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info("Interrupt signal (%s) received. Shutting down gracefully...", signum)
        self._running = False

    def run(self) -> None:
        """Execute the main video processing pipeline."""
        video_source = VideoSource(self.config.video)
        if not video_source.open():
            logger.error("Failed to initialize video source. Exiting pipeline.")
            return

        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        self.db.start_session(
            session_id=session_id,
            source_type=self.config.video.source_type,
            source_path=str(self.config.video.get_effective_source()),
        )

        logger.info("Beginning video pipeline execution (Session ID: %s)", session_id)
        self._running = True
        frame_idx = 0
        start_time = time.time()
        fps_display = 0.0

        try:
            for f_num, timestamp_iso, frame in video_source.read_frames():
                if not self._running:
                    break

                frame_idx = f_num
                t_frame_start = time.time()

                # 1. Detection Frame Skipping logic
                # Only perform heavy face detection every (frame_skip + 1) frames
                skip_interval = self.config.detection.frame_skip
                should_detect = (skip_interval == 0) or (frame_idx % (skip_interval + 1) == 0)

                detections = []
                if should_detect:
                    detections = self.detector.detect(
                        frame=frame,
                        min_size=self.config.recognition.min_face_size,
                        blur_threshold=self.config.recognition.blur_threshold,
                    )

                # 2. Multi-Object Tracking Association
                active_tracks, deleted_tracks = self.tracker.update(detections, frame_index=frame_idx)

                # 3. Handle newly confirmed tracks -> Auto-registration / Re-identification & Entry Event
                for track in active_tracks:
                    if track.state == TrackState.CONFIRMED:
                        assigned_face_id = self.identity_mgr.process_track(track)
                        if assigned_face_id and not track.entry_event_logged:
                            self.event_mgr.handle_entry(track, timestamp_iso=timestamp_iso)

                # 4. Handle expired tracks (Lost beyond timeout) -> Confirmed Exit Event & Cleanup
                for expired_track in deleted_tracks:
                    if expired_track.entry_event_logged and not expired_track.exit_event_logged:
                        self.event_mgr.handle_exit(expired_track, timestamp_iso=timestamp_iso)
                    self.identity_mgr.release_track(expired_track.track_id)

                # 5. Measure instantaneous processing FPS
                t_frame_end = time.time()
                dt = t_frame_end - t_frame_start
                if dt > 0:
                    fps_display = 0.9 * fps_display + 0.1 * (1.0 / dt)

                # 6. Optional GUI Visualizer
                if not self.headless:
                    annotated_frame = self._render_ui(frame, active_tracks, fps_display, frame_idx)
                    cv2.imshow("Intelligent Face Tracker", annotated_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q") or key == 27:  # 'q' or ESC
                        logger.info("User requested exit via GUI keyboard event.")
                        break

        except KeyboardInterrupt:
            logger.info("Processing aborted by user keyboard interrupt.")
        finally:
            video_source.release()
            if not self.headless:
                cv2.destroyAllWindows()

            # End of session housekeeping
            elapsed = time.time() - start_time
            unique_count = self.counter.get_unique_visitor_count()
            self.db.end_session(session_id, total_frames=frame_idx, unique_faces_count=unique_count)
            logger.info(
                "Pipeline stopped. Processed %d frames in %.2fs (Avg FPS: %.1f). Total Unique Visitors: %d",
                frame_idx,
                elapsed,
                frame_idx / elapsed if elapsed > 0 else 0,
                unique_count,
            )
            print("\n" + self.counter.format_terminal_report())

    def _render_ui(
        self,
        frame: np.ndarray,
        active_tracks: list,
        fps: float,
        frame_idx: int,
    ) -> np.ndarray:
        """Render detection boxes, tracking IDs, persistent face IDs, and status dashboard."""
        out = frame.copy()
        h, w = out.shape[:2]

        # Draw active tracks
        for trk in active_tracks:
            x1, y1, x2, y2 = trk.bbox
            face_label = trk.face_id if trk.face_id else "Identifying..."
            color = (0, 255, 0) if trk.face_id else (0, 200, 255)

            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            caption = f"ID:{face_label} | Trk:{trk.track_id}"
            cv2.putText(out, caption, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        # Header Dashboard Overlay
        stats = self.counter.get_summary()
        overlay = out.copy()
        cv2.rectangle(overlay, (0, 0), (w, 45), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.75, out, 0.25, 0, out)

        info_text = (
            f"Frame: {frame_idx} | FPS: {fps:.1f} | "
            f"Unique Visitors: {stats['total_unique_visitors']} | "
            f"Entries: {stats['total_entry_events']} | "
            f"Exits: {stats['total_exit_events']}"
        )
        cv2.putText(out, info_text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        return out


def main():
    parser = argparse.ArgumentParser(
        description="Intelligent Face Tracker with Auto-Registration and Visitor Counting",
    )
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--source", default=None, help="Override video source file path or RTSP URL")
    parser.add_argument("--source-type", choices=["file", "rtsp", "webcam"], default=None, help="Override source type")
    parser.add_argument("--headless", action="store_true", help="Run without graphical display window")
    parser.add_argument("--summary", action="store_true", help="Print visitor counting report and exit")
    parser.add_argument("--inspect", action="store_true", help="Inspect specific visitor history")
    parser.add_argument("--face-id", default=None, help="Visitor face_id to inspect with --inspect")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Initialize structured logging
    setup_logging(config.logging, log_file_path=config.storage.log_file)

    # Database inspection mode
    if args.summary:
        db = DatabaseManager(config.storage.database_path)
        counter = VisitorCounter(db)
        print(counter.format_terminal_report())
        return

    if args.inspect:
        if not args.face_id:
            print("Error: --inspect requires --face-id <ID>")
            sys.exit(1)
        db = DatabaseManager(config.storage.database_path)
        counter = VisitorCounter(db)
        history = counter.get_visitor_history(args.face_id)
        if not history:
            print(f"No records found for Face ID '{args.face_id}'")
        else:
            import pprint
            pprint.pprint(history)
        return

    # Apply CLI overrides to configuration
    if args.source_type:
        config.video.source_type = args.source_type
    if args.source:
        if config.video.source_type == "rtsp":
            config.video.rtsp_url = args.source
        else:
            config.video.file_path = args.source

    # Launch tracking application
    app = FaceTrackerApp(config=config, headless=args.headless)
    app.run()


if __name__ == "__main__":
    main()
