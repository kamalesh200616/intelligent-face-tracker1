"""Generate high-resolution architecture, sequence, and database ER diagrams for the Word guide."""

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure diagrams directory exists
diagrams_dir = Path("docs/diagrams")
diagrams_dir.mkdir(parents=True, exist_ok=True)


def create_architecture_diagram():
    """Create system architecture diagram."""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Title
    ax.text(5.5, 6.7, "Intelligent Face Tracker — Implemented System Architecture", 
            ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")

    # 1. Frontend Layer
    rect_fe = patches.FancyBboxPatch((0.5, 4.8), 2.8, 1.5, boxstyle="round,pad=0.1", 
                                     facecolor="#eff6ff", edgecolor="#3b82f6", linewidth=1.5)
    ax.add_patch(rect_fe)
    ax.text(1.9, 6.0, "Frontend Single Page App", ha="center", va="center", fontsize=10, fontweight="bold", color="#1e3a8a")
    ax.text(1.9, 5.5, "• React 19 + TypeScript + Vite\n• Tailwind CSS v4 & Lucide Icons\n• 7 Pages (Dashboard, Upload, Live...)", 
            ha="center", va="center", fontsize=8, color="#1e40af")

    # 2. FastAPI Gateway
    rect_api = patches.FancyBboxPatch((4.1, 4.8), 2.8, 1.5, boxstyle="round,pad=0.1", 
                                      facecolor="#f0fdf4", edgecolor="#22c55e", linewidth=1.5)
    ax.add_patch(rect_api)
    ax.text(5.5, 6.0, "Backend REST API (FastAPI)", ha="center", va="center", fontsize=10, fontweight="bold", color="#14532d")
    ax.text(5.5, 5.5, "• Port 8000 (Uvicorn ASGI)\n• CORS & Static Mounts (/static)\n• Endpoints: /api/jobs, /stats, /events", 
            ha="center", va="center", fontsize=8, color="#166534")

    # 3. Job Manager
    rect_job = patches.FancyBboxPatch((7.7, 4.8), 2.8, 1.5, boxstyle="round,pad=0.1", 
                                      facecolor="#fefce8", edgecolor="#eab308", linewidth=1.5)
    ax.add_patch(rect_job)
    ax.text(9.1, 6.0, "Async Job Manager", ha="center", va="center", fontsize=10, fontweight="bold", color="#713f12")
    ax.text(9.1, 5.5, "• Singleton Thread Controller\n• Cooperative Cancel Event\n• Real-time FPS & Metric Polling", 
            ha="center", va="center", fontsize=8, color="#854d0e")

    # 4. Core AI Processing Pipeline (Large Box)
    rect_ai = patches.FancyBboxPatch((0.5, 1.8), 6.4, 2.4, boxstyle="round,pad=0.1", 
                                     facecolor="#faf5ff", edgecolor="#a855f7", linewidth=1.5)
    ax.add_patch(rect_ai)
    ax.text(3.7, 3.9, "Core AI Computer Vision Pipeline (src/)", ha="center", va="center", fontsize=10, fontweight="bold", color="#581c87")

    # Sub-modules inside AI Pipeline
    sub_modules = [
        ("VideoSource", "OpenCV / RTSP\nReconnect Backoff", 1.1, 2.3),
        ("FaceDetector", "YOLOv8-Face\nBlur & Clamping", 2.4, 2.3),
        ("FaceTracker", "ByteTrack / IoU\nMulti-frame Hits", 3.7, 2.3),
        ("ArcFace", "512-D Embedding\nCosine Similarity", 5.0, 2.3),
        ("EventManager", "Entry / Exit FSM\nCrop Archiver", 6.2, 2.3),
    ]
    for title, desc, cx, cy in sub_modules:
        sub_box = patches.FancyBboxPatch((cx - 0.55, cy - 0.4), 1.1, 1.4, boxstyle="round,pad=0.05",
                                        facecolor="#ffffff", edgecolor="#c084fc", linewidth=1.0)
        ax.add_patch(sub_box)
        ax.text(cx, cy + 0.65, title, ha="center", va="center", fontsize=7.5, fontweight="bold", color="#6b21a8")
        ax.text(cx, cy + 0.1, desc, ha="center", va="center", fontsize=6.5, color="#4c1d95")

    # 5. Storage Layer
    rect_st = patches.FancyBboxPatch((7.7, 1.8), 2.8, 2.4, boxstyle="round,pad=0.1", 
                                     facecolor="#f8fafc", edgecolor="#64748b", linewidth=1.5)
    ax.add_patch(rect_st)
    ax.text(9.1, 3.9, "Persistence & Storage Layer", ha="center", va="center", fontsize=10, fontweight="bold", color="#0f172a")
    ax.text(9.1, 2.9, "• SQLite Database (WAL Mode)\n  (faces, events, sessions)\n• Cropped Face Images (logs/)\n• Audit Log (logs/events.log)\n• JSON Config (config.json)", 
            ha="center", va="center", fontsize=8, color="#334155")

    # Connecting Arrows
    arrow_props = dict(arrowstyle="->", color="#475569", lw=1.5, mutation_scale=12)
    # Frontend <-> API
    ax.annotate("", xy=(4.1, 5.55), xytext=(3.3, 5.55), arrowprops=arrow_props)
    ax.annotate("", xy=(3.3, 5.45), xytext=(4.1, 5.45), arrowprops=arrow_props)
    ax.text(3.7, 5.75, "HTTP REST", ha="center", va="center", fontsize=7, color="#64748b")

    # API -> JobManager
    ax.annotate("", xy=(7.7, 5.55), xytext=(6.9, 5.55), arrowprops=arrow_props)
    ax.text(7.3, 5.75, "start / stop", ha="center", va="center", fontsize=7, color="#64748b")

    # JobManager -> AI Pipeline
    ax.annotate("", xy=(5.5, 4.2), xytext=(8.3, 4.8), 
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5, connectionstyle="arc3,rad=-0.15"))
    ax.text(7.2, 4.4, "Spawns Worker Thread", ha="center", va="center", fontsize=7, color="#64748b")

    # AI Pipeline -> Storage
    ax.annotate("", xy=(7.7, 2.9), xytext=(6.9, 2.9), arrowprops=arrow_props)
    ax.text(7.3, 3.1, "Insert / Save", ha="center", va="center", fontsize=7, color="#64748b")

    # Storage -> API
    ax.annotate("", xy=(5.5, 4.8), xytext=(8.0, 4.2), 
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5, connectionstyle="arc3,rad=0.15"))
    ax.text(6.4, 4.4, "Query Stats / Thumbnails", ha="center", va="center", fontsize=7, color="#64748b")

    # Bottom Footer Note
    ax.text(5.5, 0.8, "Decoupled Architecture: React SPA communicates via REST API; Background Thread runs OpenCV/YOLO/ArcFace pipeline with zero UI freeze.", 
            ha="center", va="center", fontsize=8, fontstyle="italic", color="#64748b")

    plt.tight_layout()
    output_path = diagrams_dir / "architecture_diagram.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Generated {output_path}")


def create_sequence_diagram():
    """Create chronological sequence diagram of video upload and processing."""
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # Title
    ax.text(5.5, 8.1, "Chronological Sequence: Video Upload, Background AI Ingestion & Dashboard Update", 
            ha="center", va="center", fontsize=13, fontweight="bold", color="#0f172a")

    # Actors / Swimlanes
    columns = [
        ("User / Browser", 1.0, "#3b82f6"),
        ("React Frontend", 3.0, "#6366f1"),
        ("FastAPI Server", 5.0, "#22c55e"),
        ("JobManager Worker", 7.2, "#eab308"),
        ("AI Pipeline", 9.0, "#a855f7"),
        ("SQLite DB & Disk", 10.4, "#64748b"),
    ]

    for label, x, col in columns:
        # Header box
        rect = patches.FancyBboxPatch((x - 0.75, 7.3), 1.5, 0.5, boxstyle="round,pad=0.05",
                                      facecolor=col, edgecolor="#1e293b", linewidth=1)
        ax.add_patch(rect)
        ax.text(x, 7.55, label, ha="center", va="center", fontsize=7.5, fontweight="bold", color="#ffffff")
        # Vertical lifeline
        ax.plot([x, x], [0.8, 7.3], color="#cbd5e1", linestyle="--", linewidth=1.0)

    # Sequence Messages
    steps = [
        # (step_num, text, from_col, to_col, y_pos, color)
        ("1", "Selects video & clicks Upload", 1.0, 3.0, 6.8, "#1e3a8a"),
        ("2", "POST /api/upload (multipart video)", 3.0, 5.0, 6.3, "#1e3a8a"),
        ("3", "Saves file to data/uploads/", 5.0, 10.4, 5.8, "#047857"),
        ("4", "POST /api/jobs/start {source_type, file_path}", 3.0, 5.0, 5.3, "#1e3a8a"),
        ("5", "Spawns background thread with Job ID", 5.0, 7.2, 4.8, "#b45309"),
        ("6", "Frame loop: read -> detect -> track", 7.2, 9.0, 4.3, "#7e22ce"),
        ("7", "ArcFace match / auto-register -> Entry/Exit event", 9.0, 10.4, 3.7, "#6b21a8"),
        ("8", "Saves crop to logs/ & inserts into events table", 10.4, 10.4, 3.2, "#334155"),
        ("9", "Polls GET /api/jobs/status (FPS, %, counts)", 3.0, 5.0, 2.6, "#1e3a8a"),
        ("10", "Job completes -> Fetches /api/stats & /api/events", 3.0, 5.0, 2.0, "#1e3a8a"),
        ("11", "Renders updated visitor counts & face thumbnails", 3.0, 1.0, 1.4, "#1e3a8a"),
    ]

    arrow_style = dict(arrowstyle="->", lw=1.2, mutation_scale=10)

    for num, txt, x1, x2, y, col in steps:
        if x1 == x2:  # Self-call
            ax.plot([x1, x1 + 0.3, x1 + 0.3, x1], [y + 0.15, y + 0.15, y - 0.15, y - 0.15], color=col, lw=1.2)
            ax.text(x1 - 0.1, y, f"[{num}] {txt}", ha="right", va="center", fontsize=7, fontweight="semibold", color=col)
        else:
            ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color=col, lw=1.3))
            mid_x = (x1 + x2) / 2
            ax.text(mid_x, y + 0.15, f"[{num}] {txt}", ha="center", va="bottom", fontsize=7, fontweight="semibold", color=col)

    plt.tight_layout()
    output_path = diagrams_dir / "sequence_diagram.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Generated {output_path}")


def create_database_er_diagram():
    """Create Database Entity Relationship Diagram."""
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    # Title
    ax.text(5.0, 5.1, "SQLite Database Entity-Relationship (ER) Diagram", 
            ha="center", va="center", fontsize=14, fontweight="bold", color="#0f172a")

    # Table 1: faces
    t1 = patches.FancyBboxPatch((0.5, 1.5), 2.8, 3.2, boxstyle="round,pad=0.08", 
                                facecolor="#f8fafc", edgecolor="#3b82f6", linewidth=1.5)
    ax.add_patch(t1)
    # Header bar
    h1 = patches.Rectangle((0.5, 4.2), 2.8, 0.5, facecolor="#3b82f6")
    ax.add_patch(h1)
    ax.text(1.9, 4.45, "faces (Registered Identities)", ha="center", va="center", fontsize=9, fontweight="bold", color="#ffffff")
    
    fields_t1 = [
        ("face_id", "TEXT (PK)", True),
        ("name", "TEXT (Nullable)", False),
        ("embedding", "BLOB (512x4 B)", False),
        ("first_seen", "TEXT (ISO-8601)", False),
        ("last_seen", "TEXT (ISO-8601)", False),
        ("total_visits", "INTEGER (Default 1)", False),
        ("metadata_json", "TEXT (JSON)", False),
    ]
    y_pos = 3.95
    for fld, tp, is_pk in fields_t1:
        prefix = "[PK] " if is_pk else "     "
        ax.text(0.7, y_pos, f"{prefix}{fld}", ha="left", va="center", fontsize=7.5, fontweight="bold" if is_pk else "normal", color="#0f172a")
        ax.text(3.1, y_pos, tp, ha="right", va="center", fontsize=7, color="#64748b")
        y_pos -= 0.35

    # Table 2: events
    t2 = patches.FancyBboxPatch((4.0, 1.2), 3.0, 3.5, boxstyle="round,pad=0.08", 
                                facecolor="#f8fafc", edgecolor="#8b5cf6", linewidth=1.5)
    ax.add_patch(t2)
    # Header bar
    h2 = patches.Rectangle((4.0, 4.2), 3.0, 0.5, facecolor="#8b5cf6")
    ax.add_patch(h2)
    ax.text(5.5, 4.45, "events (Audit Trail)", ha="center", va="center", fontsize=9, fontweight="bold", color="#ffffff")

    fields_t2 = [
        ("event_id", "TEXT (PK)", True, False),
        ("face_id", "TEXT (FK -> faces)", False, True),
        ("track_id", "INTEGER", False, False),
        ("event_type", "TEXT ('entry'/'exit')", False, False),
        ("timestamp", "TEXT (ISO-8601)", False, False),
        ("image_path", "TEXT (Local File)", False, False),
        ("confidence", "REAL", False, False),
        ("created_at", "TEXT (ISO-8601)", False, False),
    ]
    y_pos = 3.95
    for fld, tp, is_pk, is_fk in fields_t2:
        prefix = "[PK] " if is_pk else ("[FK] " if is_fk else "     ")
        ax.text(4.2, y_pos, f"{prefix}{fld}", ha="left", va="center", fontsize=7.5, fontweight="bold" if (is_pk or is_fk) else "normal", color="#0f172a")
        ax.text(6.8, y_pos, tp, ha="right", va="center", fontsize=7, color="#64748b")
        y_pos -= 0.35

    # Table 3: sessions
    t3 = patches.FancyBboxPatch((7.5, 1.5), 2.1, 3.2, boxstyle="round,pad=0.08", 
                                facecolor="#f8fafc", edgecolor="#10b981", linewidth=1.5)
    ax.add_patch(t3)
    # Header bar
    h3 = patches.Rectangle((7.5, 4.2), 2.1, 0.5, facecolor="#10b981")
    ax.add_patch(h3)
    ax.text(8.55, 4.45, "sessions (Job Runs)", ha="center", va="center", fontsize=9, fontweight="bold", color="#ffffff")

    fields_t3 = [
        ("session_id", "TEXT (PK)", True),
        ("source_type", "TEXT ('file'/'rtsp')", False),
        ("source_path", "TEXT", False),
        ("started_at", "TEXT", False),
        ("ended_at", "TEXT", False),
        ("total_frames", "INTEGER", False),
        ("unique_faces_count", "INTEGER", False),
        ("status", "TEXT", False),
    ]
    y_pos = 3.95
    for fld, tp, is_pk in fields_t3:
        prefix = "[PK] " if is_pk else "     "
        ax.text(7.7, y_pos, f"{prefix}{fld}", ha="left", va="center", fontsize=7.5, fontweight="bold" if is_pk else "normal", color="#0f172a")
        ax.text(9.4, y_pos, tp, ha="right", va="center", fontsize=6.5, color="#64748b")
        y_pos -= 0.35

    # Relationship arrow between faces and events
    arrow_props = dict(arrowstyle="<|-", color="#4338ca", lw=1.8, mutation_scale=12)
    ax.annotate("", xy=(3.3, 3.95), xytext=(4.0, 3.6), arrowprops=arrow_props)
    ax.text(3.65, 3.95, "1", fontsize=9, fontweight="bold", color="#1e40af")
    ax.text(3.8, 3.45, "N", fontsize=9, fontweight="bold", color="#6b21a8")
    ax.text(3.65, 4.15, "1-to-Many\n(ON DELETE CASCADE)", ha="center", va="bottom", fontsize=6.5, color="#4338ca")

    # Constraints Box at bottom
    c_box = patches.FancyBboxPatch((0.5, 0.3), 9.0, 0.7, boxstyle="round,pad=0.05",
                                   facecolor="#fef2f2", edgecolor="#ef4444", linewidth=1.0)
    ax.add_patch(c_box)
    ax.text(0.7, 0.65, "KEY INTEGRITY CONSTRAINTS:", fontsize=8, fontweight="bold", color="#991b1b")
    ax.text(0.7, 0.45, "• UNIQUE(track_id, event_type) enforces exactly-once Entry and Exit events per physical tracking trajectory.", 
            fontsize=7.5, color="#7f1d1d")
    ax.text(0.7, 0.32, "• PRAGMA foreign_keys = ON;  |  PRAGMA journal_mode = WAL; for concurrent, zero-lock multi-thread operations.", 
            fontsize=7.5, color="#7f1d1d")

    plt.tight_layout()
    output_path = diagrams_dir / "database_er_diagram.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Generated {output_path}")


if __name__ == "__main__":
    create_architecture_diagram()
    create_sequence_diagram()
    create_database_er_diagram()
    print("All diagrams generated successfully.")
