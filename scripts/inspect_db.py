import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import DatabaseManager
from src.visitor_counter import VisitorCounter


def main():
    parser = argparse.ArgumentParser(description="Inspect visitor tracker database.")
    parser.add_argument("--db", default="data/visitor_tracker.db", help="Path to database")
    parser.add_argument("--faces", action="store_true", help="List all registered face identities")
    parser.add_argument("--events", action="store_true", help="List recent entry/exit events")
    parser.add_argument("--sessions", action="store_true", help="List processing sessions")
    args = parser.parse_args()

    db = DatabaseManager(args.db)
    vc = VisitorCounter(db)

    print(vc.format_terminal_report())

    if args.faces:
        print("\nRegistered Faces:")
        faces = db.get_all_faces()
        for f in faces:
            print(f"  [{f.face_id}] Name: {f.name or 'Unknown'} | Visits: {f.total_visits} | First Seen: {f.first_seen} | Last Seen: {f.last_seen}")

    if args.events:
        print("\nRecent Events (Latest 20):")
        events = db.get_events(limit=20)
        for e in events:
            print(f"  [{e.timestamp}] {e.event_type.upper():<5} | Face: {e.face_id} | Track: {e.track_id:<3} | Crop: {e.image_path}")

    if args.sessions:
        print("\nSessions:")
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM sessions ORDER BY started_at DESC LIMIT 10;").fetchall()
        for r in rows:
            print(f"  [{r['session_id']}] Type: {r['source_type']} | Path: {r['source_path']} | Frames: {r['total_frames']} | Status: {r['status']}")
        conn.close()


if __name__ == "__main__":
    main()
