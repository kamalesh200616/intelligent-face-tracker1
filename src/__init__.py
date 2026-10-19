"""Intelligent Face Tracker with Auto-Registration and Visitor Counting.

Package containing core modules:
- config: Configuration schema and loader
- video_source: Resilient video capture for files and RTSP streams
- detector: YOLOv8 face detection with coordinate validation
- face_recognizer: SOTA ArcFace/InsightFace embedding extractor and cosine matcher
- tracker: Multi-frame ByteTrack/IoU face tracking
- identity_manager: Auto-registration and track-to-face_id mapper
- event_manager: Entry/Exit event state machine and crop archiver
- database: Thread-safe SQLite repository layer
- visitor_counter: Analytics and unique visitor aggregation
- logging_setup: Structured file and console logging
"""

__version__ = "1.0.0"
