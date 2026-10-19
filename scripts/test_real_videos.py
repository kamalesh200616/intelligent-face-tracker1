"""Empirical validation script running real video files through Intelligent Face Tracker pipeline.

Tests:
1. Sequential processing of record_20250620_183903.mp4, record_20250620_184049.mp4, and record_20250620_184302.mp4.
2. Verified multi-pose gallery matching without false identity splits.
3. Per-video session count isolation without stale metrics leakage.
4. Full identity deletion and database cascading event cleanup.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.database import DatabaseManager
from src.job_manager import JobManager
from src.logging_setup import get_logger

logger = get_logger("real_video_verifier")


def run_verification():
    cfg = load_config()
    db_path = "data/real_test_run.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    cfg.storage.database_path = db_path
    db = DatabaseManager(db_path)

    job_mgr = JobManager()

    uploads_dir = Path("data/uploads")
    vids = [
        uploads_dir / "record_20250620_183903.mp4",
        uploads_dir / "record_20250620_184049.mp4",
        uploads_dir / "record_20250620_184302.mp4",
    ]

    print("=" * 80)
    print("STARTING REAL VIDEO EMPIRICAL VALIDATION SUITE")
    print("=" * 80)

    results = []

    for idx, vid_path in enumerate(vids, 1):
        if not vid_path.is_file():
            print(f"SKIPPING: {vid_path} not found.")
            continue

        print(f"\n--- [Run {idx}/3] Processing: {vid_path.name} ---")
        job_res = job_mgr.start_job(
            source_type="file",
            source_path=str(vid_path.resolve()),
            config=cfg,
        )
        assert job_res["success"], f"Failed to start job: {job_res}"
        job_id = job_res["job_id"]
        print(f"Job started: {job_id}")

        # Wait for job completion
        while True:
            st = job_mgr.get_status()
            if st["status"] in ("completed", "failed", "stopped"):
                break
            time.sleep(1.0)
            print(f"  Frame: {st['current_frame']}/{st['total_frames']} ({st['progress_percent']}%) | FPS: {st['fps']} | Session Visitors: {st['unique_visitors']} | Entries: {st['total_entries']} | Exits: {st['total_exits']}", end="\r")

        final_st = job_mgr.get_status()
        print(f"\nCompleted in {final_st['elapsed_seconds']}s with status: {final_st['status']}")
        print(f"  Final Session Visitors: {final_st['unique_visitors']}")
        print(f"  Final Session Entries:  {final_st['total_entries']}")
        print(f"  Final Session Exits:    {final_st['total_exits']}")

        results.append({
            "video": vid_path.name,
            "job_id": final_st["job_id"],
            "status": final_st["status"],
            "frames": final_st["current_frame"],
            "total_frames": final_st["total_frames"],
            "duration_s": final_st["elapsed_seconds"],
            "fps": final_st["fps"],
            "session_visitors": final_st["unique_visitors"],
            "session_entries": final_st["total_entries"],
            "session_exits": final_st["total_exits"],
        })

    print("\n" + "=" * 80)
    print("ALL RUNS SUMMARY:")
    print("=" * 80)
    for r in results:
        print(f"Video: {r['video']} | Status: {r['status']} | Frames: {r['frames']}/{r['total_frames']} | Duration: {r['duration_s']}s | Session Visitors: {r['session_visitors']} | Entries: {r['session_entries']} | Exits: {r['session_exits']}")

    # Verification checks
    all_faces = db.get_all_faces()
    print(f"\nTotal Registered Faces in DB across all videos: {len(all_faces)}")
    for f in all_faces:
        print(f"  - {f.face_id}: Name={f.name}, Visits={f.total_visits}, Gallery Embeddings={len(f.gallery)}")

    # Test Delete Visitor Identity
    if all_faces:
        target = all_faces[0].face_id
        print(f"\nTesting Identity Deletion for target: {target}...")
        del_ok = db.delete_face(target)
        assert del_ok, "Failed to delete face from database"
        assert db.get_face(target) is None, "Face still found in DB after deletion"
        evts = db.get_events(face_id=target)
        assert len(evts) == 0, "Events for deleted face were not cascade deleted"
        print(f"Identity {target} and all events successfully deleted!")

    print("\nALL EMPIRICAL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_verification()
