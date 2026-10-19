"""FastAPI REST API Server for Intelligent Face Tracker.

Provides complete web API endpoints for video upload, asynchronous job processing,
visitor statistics, event history, registered identities, sessions, and configuration.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import AppConfig, load_config
from src.database import DatabaseManager
from src.job_manager import JobManager
from src.logging_setup import get_logger, setup_logging
from src.visitor_counter import VisitorCounter

# Initialize logger and config
app_cfg = load_config()
logger = setup_logging(app_cfg.logging, log_file_path=app_cfg.storage.log_file)

app = FastAPI(
    title="Intelligent Face Tracker API",
    description="Web API for Real-time AI Face Tracking, Auto-Registration & Visitor Counting",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload and log directories exist
upload_dir = Path("data/uploads")
upload_dir.mkdir(parents=True, exist_ok=True)
Path(app_cfg.storage.entries_dir).mkdir(parents=True, exist_ok=True)
Path(app_cfg.storage.exits_dir).mkdir(parents=True, exist_ok=True)

# Mount static files safely for video previews and crop thumbnails
app.mount("/static/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
app.mount("/static/logs", StaticFiles(directory="logs"), name="logs")

# Subsystems
db = DatabaseManager(app_cfg.storage.database_path)
counter = VisitorCounter(db)
job_mgr = JobManager()


# -------------------------------------------------------------
# Request & Response Models
# -------------------------------------------------------------

class StartJobRequest(BaseModel):
    source_type: str = Field(default="file", pattern="^(file|rtsp)$")
    file_path: Optional[str] = None
    rtsp_url: Optional[str] = None
    frame_skip: Optional[int] = Field(default=None, ge=0, le=20)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.1, le=0.99)


class ConfigUpdateRequest(BaseModel):
    frame_skip: Optional[int] = Field(default=None, ge=0, le=20)
    confidence_threshold: Optional[float] = Field(default=None, ge=0.1, le=1.0)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.1, le=0.99)
    track_lost_timeout_seconds: Optional[float] = Field(default=None, ge=0.5, le=30.0)
    blur_threshold: Optional[float] = Field(default=None, ge=0.0, le=200.0)


# -------------------------------------------------------------
# Utility Helpers
# -------------------------------------------------------------

def convert_crop_path_to_url(local_path: str) -> Optional[str]:
    """Convert a local file path like 'logs/entries/2026-10-17/face.jpg' to '/static/logs/entries/2026-10-17/face.jpg'."""
    if not local_path:
        return None
    p = Path(local_path)
    if not p.is_file():
        return None
    # Normalize path separators
    clean_parts = p.parts
    try:
        idx = clean_parts.index("logs")
        rel_parts = clean_parts[idx + 1 :]
        return f"/static/logs/{'/'.join(rel_parts)}"
    except ValueError:
        return f"/static/logs/{p.name}"


# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": "Intelligent Face Tracker",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/stats")
def get_dashboard_stats() -> Dict[str, Any]:
    """Aggregate statistics for the dashboard view."""
    stats = db.get_aggregate_stats()
    job_status = job_mgr.get_status()
    current_occupancy = max(0, stats["total_entries"] - stats["total_exits"])

    return {
        "total_unique_visitors": stats["total_unique_faces"],
        "total_entries": stats["total_entries"],
        "total_exits": stats["total_exits"],
        "current_occupancy": current_occupancy,
        "active_job": job_status,
    }


@app.get("/api/events")
def list_events(
    face_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None, pattern="^(entry|exit)$"),
    session_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Retrieve filtered, paginated events with accessible image thumbnail URLs."""
    all_events = db.get_events(face_id=face_id, event_type=event_type, session_id=session_id, limit=1000)

    # In-memory search if provided
    if search:
        search_lower = search.lower()
        all_events = [
            e for e in all_events
            if search_lower in e.face_id.lower() or search_lower in e.event_id.lower() or (e.session_id and search_lower in e.session_id.lower())
        ]

    total_count = len(all_events)
    paginated = all_events[offset : offset + limit]

    results = []
    for evt in paginated:
        thumb_url = convert_crop_path_to_url(evt.image_path)
        results.append({
            "event_id": evt.event_id,
            "session_id": evt.session_id,
            "face_id": evt.face_id,
            "track_id": evt.track_id,
            "event_type": evt.event_type,
            "timestamp": evt.timestamp,
            "confidence": round(evt.confidence, 3),
            "thumbnail_url": thumb_url,
            "has_thumbnail": bool(thumb_url),
        })

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "events": results,
    }


@app.get("/api/identities")
def list_identities() -> Dict[str, Any]:
    """Retrieve registered visitor identities with primary thumbnails.

    Protects biometric privacy: raw 512-D vectors are NEVER sent to the client.
    """
    faces = db.get_all_faces()
    identities = []

    for f in faces:
        # Find the most recent entry crop for this face
        recent_events = db.get_events(face_id=f.face_id, limit=5)
        thumb_url = None
        for ev in recent_events:
            url = convert_crop_path_to_url(ev.image_path)
            if url:
                thumb_url = url
                break

        identities.append({
            "face_id": f.face_id,
            "name": f.name or f"Visitor {f.face_id.replace('face_', '#')}",
            "first_seen": f.first_seen,
            "last_seen": f.last_seen,
            "total_visits": f.total_visits,
            "metadata": f.metadata,
            "thumbnail_url": thumb_url,
            "has_thumbnail": bool(thumb_url),
        })

    return {
        "total": len(identities),
        "identities": identities,
    }


@app.get("/api/identities/{face_id}")
def get_identity_detail(face_id: str) -> Dict[str, Any]:
    """Retrieve single identity and chronological visit history."""
    history = counter.get_visitor_history(face_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"Identity '{face_id}' not found.")

    # Enhance event image paths with URLs
    for ev in history.get("events", []):
        ev["thumbnail_url"] = convert_crop_path_to_url(ev.get("image_path", ""))

    return history


@app.delete("/api/identities/{face_id}")
def delete_identity(face_id: str) -> Dict[str, Any]:
    """Permanently delete a registered visitor identity and all related events."""
    existing = db.get_face(face_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Identity '{face_id}' not found.")

    success = db.delete_face(face_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete identity '{face_id}'.")

    logger.info("Deleted identity %s via API request", face_id)
    return {
        "success": True,
        "message": f"Visitor identity '{face_id}' deleted successfully.",
        "face_id": face_id,
    }


@app.get("/api/sessions")
def list_sessions() -> Dict[str, Any]:
    """Retrieve history of processing runs."""
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT * FROM sessions ORDER BY started_at DESC LIMIT 50;").fetchall()
        sessions = [
            {
                "session_id": r["session_id"],
                "source_type": r["source_type"],
                "source_path": Path(r["source_path"]).name if r["source_type"] == "file" else r["source_path"],
                "started_at": r["started_at"],
                "ended_at": r["ended_at"],
                "total_frames": r["total_frames"],
                "unique_faces_count": r["unique_faces_count"],
                "status": r["status"],
            }
            for r in rows
        ]
        return {"total": len(sessions), "sessions": sessions}
    finally:
        conn.close()


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a video file for processing and browser preview."""
    allowed_exts = {".mp4", ".avi", ".mkv", ".mov"}
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{suffix}'. Allowed: {', '.join(allowed_exts)}",
        )

    # Sanitize filename
    clean_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    target_path = upload_dir / clean_name

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded video file.")

    file_size = target_path.stat().st_size
    return {
        "success": True,
        "filename": clean_name,
        "file_path": str(target_path.resolve()),
        "preview_url": f"/static/uploads/{clean_name}",
        "size_bytes": file_size,
    }


@app.get("/api/uploads")
def list_uploaded_videos() -> Dict[str, Any]:
    """List available video files in data/uploads for direct selection."""
    allowed_exts = {".mp4", ".avi", ".mkv", ".mov"}
    videos = []
    if upload_dir.exists():
        for p in sorted(upload_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file() and p.suffix.lower() in allowed_exts:
                st = p.stat()
                videos.append({
                    "filename": p.name,
                    "file_path": str(p.resolve()),
                    "preview_url": f"/static/uploads/{p.name}",
                    "size_bytes": st.st_size,
                    "size_mb": round(st.st_size / (1024 * 1024), 2),
                    "modified_iso": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                })
    return {"total": len(videos), "videos": videos}


@app.post("/api/jobs/reset")
def reset_job_state() -> Dict[str, Any]:
    """Reset processing job status and session counts to idle."""
    job_mgr.reset_status()
    return {"success": True, "message": "Job status successfully reset to idle."}


@app.post("/api/jobs/start")
def start_processing(req: StartJobRequest) -> Dict[str, Any]:
    """Launch background video processing on an uploaded file or RTSP stream."""
    cfg = load_config()

    # Apply temporary tuning if supplied
    if req.frame_skip is not None:
        cfg.detection.frame_skip = req.frame_skip
    if req.similarity_threshold is not None:
        cfg.recognition.similarity_threshold = req.similarity_threshold

    source_path = ""
    if req.source_type == "file":
        if not req.file_path:
            # Default to sample video if none provided
            source_path = "data/sample_video.mp4"
        else:
            source_path = req.file_path

        if not Path(source_path).is_file():
            raise HTTPException(status_code=400, detail=f"Target video file not found: {source_path}")

    elif req.source_type == "rtsp":
        if not req.rtsp_url:
            raise HTTPException(status_code=400, detail="RTSP stream URL is required for live camera mode.")
        source_path = req.rtsp_url

    res = job_mgr.start_job(
        source_type=req.source_type,
        source_path=source_path,
        rtsp_url=req.rtsp_url if req.source_type == "rtsp" else None,
        config=cfg,
    )
    if not res.get("success"):
        raise HTTPException(status_code=409, detail=res.get("message"))

    return res


@app.get("/api/jobs/status")
def get_job_status() -> Dict[str, Any]:
    """Retrieve real-time processing metrics and progress."""
    return job_mgr.get_status()


@app.post("/api/jobs/stop")
def stop_processing() -> Dict[str, Any]:
    """Stop active video processing."""
    res = job_mgr.stop_job()
    return res


@app.get("/api/config")
def get_configuration() -> Dict[str, Any]:
    """Retrieve safe, editable configuration settings."""
    cfg = load_config()
    return {
        "detection": {
            "model_type": cfg.detection.model_type,
            "confidence_threshold": cfg.detection.confidence_threshold,
            "nms_threshold": cfg.detection.nms_threshold,
            "frame_skip": cfg.detection.frame_skip,
            "device": cfg.detection.device,
        },
        "recognition": {
            "model_type": cfg.recognition.model_type,
            "similarity_threshold": cfg.recognition.similarity_threshold,
            "blur_threshold": cfg.recognition.blur_threshold,
            "min_face_size": list(cfg.recognition.min_face_size),
        },
        "tracking": {
            "tracker_type": cfg.tracking.tracker_type,
            "iou_threshold": cfg.tracking.iou_threshold,
            "min_hits_to_confirm": cfg.tracking.min_hits_to_confirm,
            "track_lost_timeout_seconds": cfg.tracking.track_lost_timeout_seconds,
            "max_lost_frames": cfg.tracking.max_lost_frames,
        },
    }


@app.put("/api/config")
def update_configuration(req: ConfigUpdateRequest) -> Dict[str, Any]:
    """Update and persist configuration changes."""
    cfg_path = Path("config.json")
    if not cfg_path.is_file():
        raise HTTPException(status_code=404, detail="config.json not found.")

    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if req.frame_skip is not None:
        data.setdefault("detection", {})["frame_skip"] = req.frame_skip
    if req.confidence_threshold is not None:
        data.setdefault("detection", {})["confidence_threshold"] = req.confidence_threshold
    if req.similarity_threshold is not None:
        data.setdefault("recognition", {})["similarity_threshold"] = req.similarity_threshold
    if req.blur_threshold is not None:
        data.setdefault("recognition", {})["blur_threshold"] = req.blur_threshold
    if req.track_lost_timeout_seconds is not None:
        data.setdefault("tracking", {})["track_lost_timeout_seconds"] = req.track_lost_timeout_seconds
        # Also adjust max_lost_frames at 30 fps
        data.setdefault("tracking", {})["max_lost_frames"] = int(req.track_lost_timeout_seconds * 30)

    # Save to disk
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info("Configuration updated via Web API: %s", req.model_dump(exclude_none=True))
    return {"success": True, "message": "Configuration updated successfully."}


@app.get("/api/analytics/temporal")
def get_temporal_analytics() -> Dict[str, Any]:
    """Return event count distribution across hours and recent sessions for charts."""
    conn = db.get_connection()
    try:
        # 1. Hourly distribution
        rows = conn.execute("""
            SELECT substr(timestamp, 12, 2) AS hour_str, event_type, COUNT(*) as cnt
            FROM events
            GROUP BY hour_str, event_type
            ORDER BY hour_str;
        """).fetchall()

        hourly_map: Dict[str, Dict[str, int]] = {}
        for r in rows:
            hr = f"{r['hour_str']}:00"
            if hr not in hourly_map:
                hourly_map[hr] = {"entries": 0, "exits": 0}
            if r["event_type"] == "entry":
                hourly_map[hr]["entries"] = r["cnt"]
            else:
                hourly_map[hr]["exits"] = r["cnt"]

        timeline = [
            {"hour": hr, "entries": vals["entries"], "exits": vals["exits"]}
            for hr, vals in sorted(hourly_map.items())
        ]

        # 2. Session comparison
        sess_rows = conn.execute("""
            SELECT session_id, unique_faces_count, total_frames, status, started_at
            FROM sessions
            ORDER BY started_at DESC LIMIT 7;
        """).fetchall()

        sessions_chart = [
            {
                "session": r["session_id"][:10],
                "visitors": r["unique_faces_count"],
                "frames": r["total_frames"],
            }
            for r in reversed(sess_rows)
        ]

        return {
            "hourly_activity": timeline,
            "session_comparison": sessions_chart,
        }
    finally:
        conn.close()


# Mount built React single-page frontend if distribution directory exists
frontend_dist = Path("frontend/dist")
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


def main():
    """Start uvicorn server directly."""
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False, log_level="info")


if __name__ == "__main__":
    main()

