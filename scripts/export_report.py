import argparse
import csv
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import DatabaseManager
from src.visitor_counter import VisitorCounter


def main():
    parser = argparse.ArgumentParser(description="Export visitor audit logs.")
    parser.add_argument("--db", default="data/visitor_tracker.db", help="Path to database")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    parser.add_argument("--output", default="data/visitor_audit_report", help="Output file base path")
    args = parser.parse_args()

    db = DatabaseManager(args.db)
    vc = VisitorCounter(db)
    summary = vc.get_summary()
    events = db.get_events(limit=1000)

    if args.format == "json":
        out_file = Path(f"{args.output}.json")
        data = {
            "summary": summary,
            "events": [
                {
                    "event_id": e.event_id,
                    "face_id": e.face_id,
                    "track_id": e.track_id,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "confidence": e.confidence,
                    "image_path": e.image_path,
                }
                for e in events
            ],
        }
        out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Exported JSON report to {out_file.resolve()}")

    elif args.format == "csv":
        out_file = Path(f"{args.output}.csv")
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Event ID", "Face ID", "Track ID", "Event Type", "Timestamp", "Confidence", "Image Path"])
            for e in events:
                writer.writerow([e.event_id, e.face_id, e.track_id, e.event_type, e.timestamp, e.confidence, e.image_path])
        print(f"Exported CSV report to {out_file.resolve()}")


if __name__ == "__main__":
    main()
