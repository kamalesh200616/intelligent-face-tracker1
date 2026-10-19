"""Identity Manager bridging transient tracking IDs with persistent database identities.

Responsibilities:
- Auto-registration of newly seen individuals upon first confirmed appearance.
- Cosine-similarity matching against registered identities in the SQLite database.
- Caching database identities in-memory for sub-millisecond vector comparisons.
- Strict mapping between temporary `track_id`s and permanent `face_id`s.
- Preventing duplicate registrations across consecutive frames while a track is alive.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np

from src.config import RecognitionConfig
from src.database import DatabaseManager, FaceRecord
from src.face_recognizer import ArcFaceRecognizer
from src.logging_setup import get_logger
from src.tracker import Track, TrackState

logger = get_logger("identity_manager")


class IdentityManager:
    """Manages face auto-registration, re-identification, and ID lifecycle."""

    def __init__(
        self,
        db: DatabaseManager,
        recognizer: ArcFaceRecognizer,
        config: RecognitionConfig,
    ):
        self.db = db
        self.recognizer = recognizer
        self.config = config

        # In-memory mapping: track_id -> persistent face_id
        self._track_to_face: Dict[int, str] = {}
        # Cached registered faces for fast matching
        self._cached_faces: List[FaceRecord] = []
        self.total_matches: int = 0
        self.total_registrations: int = 0
        self._refresh_face_cache()

    def _refresh_face_cache(self) -> None:
        """Reload registered faces from database into memory."""
        self._cached_faces = self.db.get_all_faces()
        logger.info("Loaded %d registered identities into memory cache", len(self._cached_faces))

    def _generate_next_face_id(self) -> str:
        """Generate human-readable sequential identifier without collision, e.g. face_0001."""
        max_idx = 0
        for face in self._cached_faces:
            if face.face_id.startswith("face_"):
                try:
                    num = int(face.face_id.split("_")[1])
                    if num > max_idx:
                        max_idx = num
                except (IndexError, ValueError):
                    pass
        return f"face_{max_idx + 1:04d}"

    def process_track(self, track: Track) -> Optional[str]:
        """Resolve or assign a persistent face_id for an active track.

        Returns:
            Persistent `face_id` (str) if identified/registered, or None if awaiting confirmation/quality.
        """
        # 1. Fast path: track already has an associated face_id
        if track.track_id in self._track_to_face:
            assigned_face_id = self._track_to_face[track.track_id]
            track.face_id = assigned_face_id
            return assigned_face_id

        # 2. Only register/identify confirmed tracks (filters single-frame detection noise)
        if track.state not in (TrackState.CONFIRMED, TrackState.LOST):
            return None

        # 3. Quality validation on crop
        if track.best_crop is None or track.best_crop.size == 0:
            logger.debug("Track %d has empty crop; deferring identification", track.track_id)
            return None

        crop_h, crop_w = track.best_crop.shape[:2]
        if crop_w < self.config.min_face_size[0] or crop_h < self.config.min_face_size[1]:
            logger.debug("Track %d crop %dx%d below min size; deferring identification", track.track_id, crop_w, crop_h)
            return None

        # 4. Extract 512-D normalized embedding
        embedding = self.recognizer.extract_embedding(track.best_crop)
        logger.info("Generated 512-D ArcFace embedding for Track %d (crop sharpness: %.1f)", track.track_id, track.best_blur_score)

        # 5. Search registered identities
        matched_face_id, similarity = self.recognizer.match_identity(
            embedding,
            self._cached_faces,
            threshold=self.config.similarity_threshold,
        )

        if matched_face_id is not None:
            # Re-identified existing visitor!
            logger.info(
                "RE-IDENTIFIED visitor: Assigned existing %s to Track %d (Cosine Similarity: %.4f >= %.4f)",
                matched_face_id,
                track.track_id,
                similarity,
                self.config.similarity_threshold,
            )
            self._track_to_face[track.track_id] = matched_face_id
            track.face_id = matched_face_id
            self.total_matches += 1
            # Add diverse embedding to gallery in DB and update in-memory cache
            self.db.add_gallery_embedding(matched_face_id, embedding)
            for f in self._cached_faces:
                if f.face_id == matched_face_id:
                    if not hasattr(f, "gallery") or f.gallery is None:
                        f.gallery = [f.embedding]
                    if len(f.gallery) < 5:
                        f.gallery.append(embedding)
                    all_embs = [f.embedding] + f.gallery
                    centroid = np.mean(all_embs, axis=0)
                    c_norm = np.linalg.norm(centroid)
                    if c_norm > 0:
                        f.embedding = (centroid / c_norm).astype(np.float32)
                    break
            return matched_face_id
        else:
            # Auto-register newly seen visitor!
            new_face_id = self._generate_next_face_id()
            self.total_registrations += 1
            logger.info(
                "AUTO-REGISTERING new visitor: Creating %s for Track %d (Max Similarity: %.4f < %.4f)",
                new_face_id,
                track.track_id,
                similarity,
                self.config.similarity_threshold,
            )
            created_record = self.db.register_face(
                face_id=new_face_id,
                embedding=embedding,
                metadata={
                    "initial_track_id": track.track_id,
                    "confidence": float(track.confidence),
                    "blur_score": float(track.best_blur_score),
                },
            )
            self._cached_faces.append(created_record)
            self._track_to_face[track.track_id] = new_face_id
            track.face_id = new_face_id
            return new_face_id

    def delete_identity(self, face_id: str) -> bool:
        """Permanently delete identity from database and in-memory caches."""
        success = self.db.delete_face(face_id)
        if success:
            self._cached_faces = [f for f in self._cached_faces if f.face_id != face_id]
            tracks_to_clear = [tid for tid, fid in self._track_to_face.items() if fid == face_id]
            for tid in tracks_to_clear:
                self._track_to_face.pop(tid, None)
            logger.info("Successfully deleted identity %s from database and active memory", face_id)
        return success

    def reset_tracks(self) -> None:
        """Clear transient track mappings between video jobs while preserving database identities."""
        self._track_to_face.clear()
        self.total_matches = 0
        self.total_registrations = 0
        self._refresh_face_cache()
        logger.info("Reset active track mappings; reloaded %d cached identities", len(self._cached_faces))

    def get_face_id_for_track(self, track_id: int) -> Optional[str]:
        """Look up assigned face_id for a track ID."""
        return self._track_to_face.get(track_id)

    def release_track(self, track_id: int) -> Optional[str]:
        """Clean up in-memory track mapping once track has fully exited."""
        return self._track_to_face.pop(track_id, None)

    @property
    def total_registered_visitors(self) -> int:
        return len(self._cached_faces)

