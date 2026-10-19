"""Multi-object Face Tracker implementing IoU and ByteTrack association principles.

Key Requirements:
- Strictly maintains session-local `track_id`s separate from database `face_id`s.
- Handles track state transitions: Tentative -> Confirmed -> Lost -> Deleted.
- Enforces multi-frame hit confirmation (`min_hits_to_confirm`) to filter false positives.
- Configurable track-lost timeout (`max_lost_frames`) to withstand temporary occlusions.
- Preserves highest quality face crop across frames for audit image saving.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.config import TrackingConfig
from src.detector import Detection
from src.logging_setup import get_logger

logger = get_logger("tracker")


class TrackState(str, Enum):
    TENTATIVE = "tentative"    # Newly seen, awaiting hit confirmation
    CONFIRMED = "confirmed"    # Actively tracked and confirmed across frames
    LOST = "lost"              # Missing in current frame, within timeout grace period
    DELETED = "deleted"        # Exceeded timeout; track has ended (person exited)


def compute_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Compute Intersection over Union (IoU) between two bounding boxes (x1, y1, x2, y2)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter_area = inter_w * inter_h

    if inter_area <= 0:
        return 0.0

    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union_area = float(boxA_area + boxB_area - inter_area)

    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


def compute_spatial_similarity(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Compute spatial association score combining IoU overlap and normalized center proximity."""
    iou = compute_iou(boxA, boxB)
    if iou >= 0.35:
        return iou

    # Calculate center distance relative to scale for fast-moving faces across sampled frames
    wA, hA = boxA[2] - boxA[0], boxA[3] - boxA[1]
    wB, hB = boxB[2] - boxB[0], boxB[3] - boxB[1]
    if wA <= 0 or hA <= 0 or wB <= 0 or hB <= 0:
        return iou

    cxA, cyA = (boxA[0] + boxA[2]) / 2.0, (boxA[1] + boxA[3]) / 2.0
    cxB, cyB = (boxB[0] + boxB[2]) / 2.0, (boxB[1] + boxB[3]) / 2.0

    dist_sq = (cxA - cxB) ** 2 + (cyA - cyB) ** 2
    avg_diag = np.sqrt(((wA + wB) / 2.0) ** 2 + ((hA + hB) / 2.0) ** 2)

    if avg_diag <= 0:
        return iou

    norm_dist = np.sqrt(dist_sq) / avg_diag
    scale_ratio = max(wA, wB) / max(1.0, min(wA, wB))
    if norm_dist < 1.0 and scale_ratio < 2.5:
        proximity_score = max(0.0, 0.45 * (1.0 - norm_dist))
        return max(iou, proximity_score)

    return iou


class Track:
    """Represents a single continuous face trajectory across frames."""

    def __init__(self, track_id: int, initial_detection: Detection, frame_index: int):
        self.track_id: int = track_id
        self.bbox: Tuple[int, int, int, int] = initial_detection.bbox
        self.confidence: float = initial_detection.confidence
        self.hits: int = 1
        self.time_since_update: int = 0
        self.state: TrackState = TrackState.TENTATIVE
        self.first_frame: int = frame_index
        self.last_frame: int = frame_index

        # Persistent identity association
        self.face_id: Optional[str] = None
        self.entry_event_logged: bool = False
        self.exit_event_logged: bool = False

        # Store best quality crop for event archiving
        self.best_crop: np.ndarray = initial_detection.crop.copy()
        self.best_blur_score: float = initial_detection.blur_score

    def update(self, detection: Detection, frame_index: int, min_hits: int) -> None:
        """Update track with a newly matched detection."""
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.hits += 1
        self.time_since_update = 0
        self.last_frame = frame_index

        # Update best crop if candidate is sharper
        if detection.blur_score > self.best_blur_score and detection.crop.size > 0:
            self.best_crop = detection.crop.copy()
            self.best_blur_score = detection.blur_score

        # Transition tentative -> confirmed
        if self.state == TrackState.TENTATIVE and self.hits >= min_hits:
            self.state = TrackState.CONFIRMED
            logger.info("Track %d confirmed after %d consecutive hits", self.track_id, self.hits)
        elif self.state == TrackState.LOST:
            self.state = TrackState.CONFIRMED
            logger.info("Track %d recovered from LOST state", self.track_id)

    def mark_missed(self, max_lost_frames: int) -> None:
        """Increment lost counter and transition to LOST or DELETED."""
        self.time_since_update += 1
        if self.state == TrackState.CONFIRMED:
            self.state = TrackState.LOST
        if self.time_since_update > max_lost_frames:
            self.state = TrackState.DELETED
            logger.info("Track %d marked as DELETED (lost for %d frames)", self.track_id, self.time_since_update)


class FaceTracker:
    """Associates detections across consecutive frames using IoU overlap."""

    def __init__(self, config: TrackingConfig):
        self.config = config
        self.tracks: Dict[int, Track] = {}
        self._next_track_id: int = 1

    def update(
        self,
        detections: List[Detection],
        frame_index: int,
    ) -> Tuple[List[Track], List[Track]]:
        """Update active tracks with current frame detections.

        Returns:
            Tuple of:
            - active_tracks: List of currently confirmed/active tracks
            - deleted_tracks: List of tracks that just expired in this frame (exit candidates)
        """
        # Step 1: Compute IoU cost matrix between existing non-deleted tracks and detections
        track_ids = [tid for tid, trk in self.tracks.items() if trk.state != TrackState.DELETED]
        matched_pairs: List[Tuple[int, int]] = []
        unmatched_dets = set(range(len(detections)))
        unmatched_tracks = set(track_ids)

        if track_ids and detections:
            # Build IoU matrix
            iou_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)
            for i, tid in enumerate(track_ids):
                for j, det in enumerate(detections):
                    iou_matrix[i, j] = compute_iou(self.tracks[tid].bbox, det.bbox)

            # Greedy matching in descending order of IoU
            indices = np.unravel_index(np.argsort(-iou_matrix, axis=None), iou_matrix.shape)
            used_tracks = set()
            used_dets = set()

            for r, c in zip(indices[0], indices[1]):
                if r in used_tracks or c in used_dets:
                    continue
                if iou_matrix[r, c] >= self.config.iou_threshold:
                    matched_tid = track_ids[r]
                    matched_pairs.append((matched_tid, c))
                    used_tracks.add(r)
                    used_dets.add(c)
                    unmatched_tracks.discard(matched_tid)
                    unmatched_dets.discard(c)

        # Step 2: Update matched tracks
        for tid, det_idx in matched_pairs:
            self.tracks[tid].update(detections[det_idx], frame_index, self.config.min_hits_to_confirm)

        # Step 3: Handle unmatched tracks (mark missed / check timeout)
        deleted_tracks: List[Track] = []
        for tid in unmatched_tracks:
            trk = self.tracks[tid]
            trk.mark_missed(self.config.max_lost_frames)
            if trk.state == TrackState.DELETED:
                deleted_tracks.append(trk)

        # Step 4: Handle unmatched detections (create new tentative tracks)
        for det_idx in unmatched_dets:
            new_trk = Track(
                track_id=self._next_track_id,
                initial_detection=detections[det_idx],
                frame_index=frame_index,
            )
            # If min_hits is 1, immediately confirm
            if self.config.min_hits_to_confirm <= 1:
                new_trk.state = TrackState.CONFIRMED

            self.tracks[self._next_track_id] = new_trk
            logger.debug("Spawned new tentative Track %d at frame %d", self._next_track_id, frame_index)
            self._next_track_id += 1

        # Remove deleted tracks from internal tracking pool after reporting
        for dtrk in deleted_tracks:
            del self.tracks[dtrk.track_id]

        active_tracks = [trk for trk in self.tracks.values() if trk.state in (TrackState.CONFIRMED, TrackState.LOST)]
        return active_tracks, deleted_tracks
