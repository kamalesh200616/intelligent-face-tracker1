"""Visitor Counter and Analytics engine.

Key Responsibilities:
- Aggregates true unique visitor count (distinct registered identities).
- Guarantees re-identifications of previously registered visitors do NOT increment unique visitor count.
- Computes real-time occupancy (confirmed entries - confirmed exits).
- Provides detailed per-identity audit histories and reporting utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.database import DatabaseManager, FaceRecord, EventRecord
from src.logging_setup import get_logger

logger = get_logger("visitor_counter")


class VisitorCounter:
    """Computes and formats visitor metrics from database transactions."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_unique_visitor_count(self) -> int:
        """Return the number of unique registered face identities in the database."""
        stats = self.db.get_aggregate_stats()
        return stats["total_unique_faces"]

    def get_total_entries(self) -> int:
        """Return total confirmed entry events across all sessions."""
        stats = self.db.get_aggregate_stats()
        return stats["total_entries"]

    def get_total_exits(self) -> int:
        """Return total confirmed exit events across all sessions."""
        stats = self.db.get_aggregate_stats()
        return stats["total_exits"]

    def get_currently_present_count(self) -> int:
        """Return estimated individuals currently in the venue (entries - exits)."""
        stats = self.db.get_aggregate_stats()
        current = stats["total_entries"] - stats["total_exits"]
        return max(0, current)

    def get_summary(self) -> Dict[str, Any]:
        """Return a structured summary of all system visitor metrics."""
        stats = self.db.get_aggregate_stats()
        faces = self.db.get_all_faces()
        return {
            "total_unique_visitors": stats["total_unique_faces"],
            "total_entry_events": stats["total_entries"],
            "total_exit_events": stats["total_exits"],
            "currently_present_estimate": max(0, stats["total_entries"] - stats["total_exits"]),
            "registered_visitor_ids": [f.face_id for f in faces],
        }

    def get_visitor_history(self, face_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full chronological event history for a specific visitor ID."""
        face = self.db.get_face(face_id)
        if not face:
            return None

        events = self.db.get_events(face_id=face_id, limit=200)
        return {
            "face_id": face.face_id,
            "name": face.name,
            "first_seen": face.first_seen,
            "last_seen": face.last_seen,
            "total_visits": face.total_visits,
            "event_count": len(events),
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "image_path": e.image_path,
                    "confidence": e.confidence,
                }
                for e in events
            ],
        }

    def format_terminal_report(self) -> str:
        """Format an ASCII report for CLI inspection."""
        summary = self.get_summary()
        lines = [
            "============================================================",
            "         INTELLIGENT FACE TRACKER - VISITOR AUDIT REPORT     ",
            "============================================================",
            f"  Total Unique Registered Visitors : {summary['total_unique_visitors']}",
            f"  Total Entry Events Logged        : {summary['total_entry_events']}",
            f"  Total Exit Events Logged         : {summary['total_exit_events']}",
            f"  Current Present In-Camera (Est.) : {summary['currently_present_estimate']}",
            "------------------------------------------------------------",
            "  Registered Visitor IDs:",
        ]
        if summary["registered_visitor_ids"]:
            for vid in summary["registered_visitor_ids"][:20]:
                lines.append(f"    - {vid}")
            if len(summary["registered_visitor_ids"]) > 20:
                lines.append(f"    ... and {len(summary['registered_visitor_ids']) - 20} more")
        else:
            lines.append("    (None registered yet)")
        lines.append("============================================================")
        return "\n".join(lines)
