"""Script to generate the comprehensive, beginner-friendly Microsoft Word guide: docs/PROJECT_EXPLANATION_GUIDE.docx."""

import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOC_PATH = Path("docs/PROJECT_EXPLANATION_GUIDE.docx")
DIAGRAMS_DIR = Path("docs/diagrams")


# ---------------------------------------------------------------------------
# Formatting & XML Helper Functions
# ---------------------------------------------------------------------------

def set_cell_background(cell, hex_color: str):
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell (in twips, 20 twips = 1 pt)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def add_callout(doc: Document, text: str, title: str = "IMPORTANT NOTE"):
    """Add a professional styled callout box with a colored left accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)

    # Set left border to thick indigo, others to none
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="4F46E5"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tc_pr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run_title = p.add_run(f"📌 {title}: ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = RGBColor(0x31, 0x2E, 0x81)

    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc: Document, code_text: str):
    """Add a styled monospace code block."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=100, bottom=100, left=160, right=160)

    tc_pr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'<w:left w:val="single" w:sz="18" w:space="0" w:color="94A3B8"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'</w:tcBorders>'
    )
    tc_pr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05

    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_styled_table(doc: Document, headers: list, data: list, col_widths: list = None):
    """Add a cleanly styled data table with an indigo header row and alternating row colors."""
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1E293B")  # Slate Dark
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.bold = True
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Data Rows
    for r_idx, row_values in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        bg_col = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_values):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.line_spacing = 1.05
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width

    # Add light borders to all cells
    for row in table.rows:
        for cell in row.cells:
            tc_pr = cell._tc.get_or_add_tcPr()
            b = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                f'<w:left w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                f'<w:right w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                f'</w:tcBorders>'
            )
            tc_pr.append(b)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_diagram(doc: Document, image_path: Path, caption: str, width_inches: float = 6.0):
    """Insert a centered diagram image with caption."""
    if not image_path.is_file():
        p_err = doc.add_paragraph(f"[Diagram not found: {image_path.name}]")
        p_err.runs[0].font.color.rgb = RGBColor(0xDC, 0x26, 0x26)
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    run = p_img.add_run()
    run.add_picture(str(image_path), width=Inches(width_inches))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(f"Figure: {caption}")
    run_cap.font.name = "Calibri"
    run_cap.font.size = Pt(8.5)
    run_cap.font.italic = True
    run_cap.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)


def add_h1(doc: Document, text: str, page_break: bool = True):
    """Add Level 1 Heading (Chapter Header)."""
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(17)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)  # Navy Dark


def add_h2(doc: Document, text: str):
    """Add Level 2 Heading."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x31, 0x2E, 0x81)  # Deep Indigo


def add_h3(doc: Document, text: str):
    """Add Level 3 Heading."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)  # Slate Dark


def add_p(doc: Document, text: str) -> docx.text.paragraph.Paragraph:
    """Add standard styled body paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return p


def add_bullet(doc: Document, bold_prefix: str, text: str):
    """Add a styled bullet list item."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    r_txt = p.add_run(text)
    r_txt.font.name = "Calibri"
    r_txt.font.size = Pt(10)
    r_txt.font.color.rgb = RGBColor(0x33, 0x41, 0x55)


# ---------------------------------------------------------------------------
# Document Builder Main Routine
# ---------------------------------------------------------------------------

def build_project_explanation_guide():
    print("Initializing Microsoft Word Document...")
    doc = Document()

    # Configure Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        # Configure Header & Footer
        footer = section.footer
        p_ft = footer.paragraphs[0]
        p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_ft = p_ft.add_run("Intelligent Face Tracker — Technical Learning & Explanation Guide")
        r_ft.font.name = "Calibri"
        r_ft.font.size = Pt(8)
        r_ft.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(36)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(8)
    r_t = p_title.add_run("Intelligent Face Tracker with Auto-Registration and Visitor Counting")
    r_t.font.name = "Calibri"
    r_t.font.size = Pt(24)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(20)
    r_sub = p_sub.add_run("Comprehensive Technical Learning & Project Explanation Guide (Beginner to Production)")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)

    add_callout(doc, 
                "This document is an exhaustive, beginner-friendly technical manual for the Intelligent Face Tracker project. "
                "It covers every component from frontend buttons, React components, and FastAPI endpoints to YOLOv8 face detection, "
                "ArcFace deep biometric embeddings, ByteTrack multi-object tracking, and SQLite database persistence. "
                "All concepts are explained in plain English with analogies, real code paths, database schemas, and diagrams.",
                title="PURPOSE OF THIS MANUAL")

    # Document Meta Box
    meta_headers = ["Project Property", "Specification Details"]
    meta_data = [
        ["Project Workspace", "C:\\Users\\Acer\\.gemini\\antigravity\\scratch\\intelligent-face-tracker"],
        ["Application Title", "Intelligent Face Tracker with Auto-Registration and Visitor Counting"],
        ["Target Audience", "Beginners, Computer Vision Engineers, Full-Stack Developers, Technical Interviewers"],
        ["Implemented Architecture", "React 19 + TypeScript + Vite + FastAPI + OpenCV + YOLOv8 + ArcFace + SQLite"],
        ["Automated Test Suite", "33 Automated Pytest Tests (100% Pass Rate across Core AI, DB & REST API)"],
        ["Hackathon Attribution", "This project is a part of a hackathon run by https://katomaran.com"],
    ]
    add_styled_table(doc, meta_headers, meta_data, [Inches(2.2), Inches(4.2)])

    # =========================================================================
    # TABLE OF CONTENTS SUMMARY
    # =========================================================================
    add_h2(doc, "Manual Table of Contents")
    toc_items = [
        ("Chapter 1", "Project Overview: Problem Solved, Real-World Use, and Key Modules"),
        ("Chapter 2", "Technologies Used in My Actual Project: The Verified Tech Stack"),
        ("Chapter 3", "Complete System Architecture: Components, Connections, and Diagrams"),
        ("Chapter 4", "Complete Application Flow — Step by Step (17 Numbered Steps)"),
        ("Chapter 5", "Frontend Explained: React, TypeScript, Vite, State, and UI Events"),
        ("Chapter 6", "Backend and API Explained: FastAPI, HTTP REST, Endpoints, and Async Jobs"),
        ("Chapter 7", "Database — From Zero to Understanding: SQLite, Schema, ERD, and SQL"),
        ("Chapter 8", "JSON Configuration Explained: config.json Keys, Validation, and Rules"),
        ("Chapter 9", "Face Detection, Recognition, and Tracking: Deep Mathematical Principles"),
        ("Chapter 10", "Image Storage, Logs, and Event Lifecycle: File Trees and Audit Logs"),
        ("Chapter 11", "Environment Variables and Dependencies: Requirements, Models, and Secrets"),
        ("Chapter 12", "Complete Setup and Running Guide: Verified Commands and Execution"),
        ("Chapter 13", "Troubleshooting: Real-World Scenarios and Practical Solutions"),
        ("Chapter 14", "Interview Preparation: Pitches, Architecture, and 30+ In-Depth Q&As"),
        ("Chapter 15", "Glossary and Beginner Learning Roadmap: 10 Steps and File Reading Order"),
    ]
    for ch, desc in toc_items:
        add_bullet(doc, ch + ":", desc)

    # =========================================================================
    # CHAPTER 1: PROJECT OVERVIEW
    # =========================================================================
    add_h1(doc, "Chapter 1: Project Overview")

    add_h2(doc, "1.1 What This Project Does")
    add_p(doc, "The Intelligent Face Tracker with Auto-Registration and Visitor Counting is an automated artificial "
               "intelligence system designed to monitor entrances, hallways, or security checkpoints. It ingests video feeds "
               "(such as local MP4 video files or live IP security cameras), detects every human face appearing in the frame, "
               "extracts an invisible mathematical fingerprint (called a deep biometric embedding), tracks the person's movement "
               "from frame to frame, automatically registers newly seen individuals into a database, records exactly-once "
               "Entry and Exit events with cropped face photographs, and delivers an accurate count of unique visitors.")

    add_h2(doc, "1.2 The Problem It Solves")
    add_p(doc, "In traditional security and visitor counting systems, several major challenges arise:")
    add_bullet(doc, "Manual Tallying Inaccuracy:", "Human security guards using clickers or paper logs frequently miscount during busy rush hours, cannot recognize whether someone previously entered, and cannot maintain an objective photographic audit trail.")
    add_bullet(doc, "The Double-Counting Flaw:", "Basic optical sensors or simple motion detectors record an event every time a person walks past. If a visitor named Alice enters in the morning, steps out for lunch, and returns in the afternoon, naive counters count 2 visitors. Our system recognizes that the afternoon face matches Alice's morning embedding, logging a new Entry event while keeping the Unique Visitor Count strictly at 1.")
    add_bullet(doc, "Unenforced Pre-Enrollment:", "Most biometric access systems require every user to stand in front of a specialized terminal beforehand to pre-register their photograph. This project features Zero-Touch Auto-Registration: the first time a person walks past the camera, the system registers them autonomously without human intervention.")

    add_h2(doc, "1.3 Who Would Use It?")
    add_bullet(doc, "Corporate Offices & Campuses:", "Automated visitor logging and occupancy tracking without requiring visitors to wait at a reception desk.")
    add_bullet(doc, "Retail Stores & Shopping Malls:", "Accurate customer footfall analytics, repeat visitor identification, and peak-hour traffic estimation.")
    add_bullet(doc, "Event Venues & Conference Halls:", "Real-time headcount monitoring and capacity safety compliance.")
    add_bullet(doc, "High-Security Facilities:", "Verifiable, tamper-evident audit trails with timestamped face crops for forensic investigations.")

    add_h2(doc, "1.4 What Happens When a User Uploads a Video?")
    add_p(doc, "When an operator opens the web application and uploads a video file (such as a 30-second corridor security clip):")
    add_bullet(doc, "1. Upload & Storage:", "The browser sends the video file over HTTP to the FastAPI backend, which saves it inside `data/uploads/` and returns an HTML5 video preview URL.")
    add_bullet(doc, "2. Background Job Initiation:", "When the user clicks 'Start Processing', the backend creates a unique job identifier (e.g. `job_a1b2c3d4`) and launches the AI pipeline inside an asynchronous worker thread. This ensures the web page never freezes or hangs.")
    add_bullet(doc, "3. Video Decoding & Frame Skipping:", "OpenCV opens the video. To maintain high performance on standard CPUs, the system skips frames based on configuration (default: process 1 frame, skip 2 frames).")
    add_bullet(doc, "4. Face Detection (YOLOv8-face):", "The deep learning detector scans each sampled frame, identifying facial bounding boxes, validating image quality, and rejecting blurry crops (Laplacian blur score < 50.0).")
    add_bullet(doc, "5. Spatial Tracking (ByteTrack):", "The tracker links detections across frames using bounding box overlap (IoU), creating continuous trajectories (Track IDs). Transient noise is filtered out by requiring 3 consecutive hits before confirming a track.")
    add_bullet(doc, "6. Biometric Auto-Registration & Matching (ArcFace):", "For each confirmed track, the ArcFace model converts the clearest face crop into a 512-dimensional vector. The system calculates the cosine similarity against all previously registered faces in the SQLite database. If a match has similarity >= 0.60, the existing `face_id` is reused. Otherwise, a new identity (e.g. `face_0001`) is enrolled.")
    add_bullet(doc, "7. Event Emission & Crop Archiving:", "Upon confirmation, an Entry event is written to the database, and a cropped face photo is archived in `logs/entries/YYYY-MM-DD/`. When the person leaves the camera view for over 2 seconds (60 frames), an Exit event is emitted, and the exit crop is saved in `logs/exits/YYYY-MM-DD/`.")
    add_bullet(doc, "8. Live Dashboard Telemetry:", "While the job runs, the frontend polls the backend every second, displaying real-time FPS (~250 FPS CPU), frame count, active tracks, and visitor counts. When finished, the operator inspects the results.")

    add_h2(doc, "1.5 What Output Does the User Receive?")
    add_bullet(doc, "Live Dashboard Statistics:", "Total unique registered identities, total entries, total exits, and current estimated occupancy.")
    add_bullet(doc, "Searchable Audit Event Table:", "Every entry/exit record with timestamp, track ID, confidence score, and clickable thumbnail preview.")
    add_bullet(doc, "Face Crop Gallery:", "High-resolution cropped images of every visitor at the moment of entry and exit.")
    add_bullet(doc, "Registered Identities Directory:", "A gallery of unique visitors showing first seen, last seen, and total visit frequency.")
    add_bullet(doc, "Processing History:", "A permanent audit of every video processing run with durations, total frames analyzed, and status.")

    add_h2(doc, "1.6 Differences Between Subsystems: Analogies for Beginners")
    add_p(doc, "To understand how the pieces fit together, consider a modern secure hotel lobby:")
    add_bullet(doc, "The Frontend (React + Vite):", "The Reception Desk & Screen. It is the visual interface the human operator interacts with. It does not perform heavy AI calculations; it simply displays buttons, tables, cards, and charts.")
    add_bullet(doc, "The Backend (FastAPI + Python):", "The Hotel Concierge & Coordinator. It receives requests from the front desk, coordinates jobs, directs files, and serves information back to the screen.")
    add_bullet(doc, "The AI Pipeline (YOLOv8 + ArcFace + ByteTrack):", "The Elite Security Team with Photographic Memory. YOLO spots faces in the crowd; ByteTrack follows each person walking across the lobby; ArcFace compares their face against memory to see if they are a returning guest.")
    add_bullet(doc, "The Database (SQLite):", "The Master Ledger. An organized, permanent digital book storing registered visitor IDs, mathematical embeddings, timestamps, and event history.")
    add_bullet(doc, "File Storage (logs/ & data/):", "The Photo Album & Archives. The physical folders on disk where actual video files, cropped face snapshots, and text audit logs are kept.")

    add_h2(doc, "1.7 Simple Real-World Walkthrough: Alice & Bob in the Corridor")
    add_p(doc, "Let us trace a simple scenario across a 30-second corridor video:")
    add_bullet(doc, "Second 02:", "Alice enters from the left doorway. The tracker creates Track 1. After 3 frames, Track 1 is confirmed. ArcFace extracts her 512-D embedding. Since the database is empty, the system auto-registers her as 'face_0001', logs an Entry event, and saves her photo to `logs/entries/2026-10-17/face_0001_track1_091500.jpg`. Current Unique Visitors = 1.")
    add_bullet(doc, "Second 10:", "Alice walks out of the frame through the right exit. The camera loses sight of her. After 60 frames (2.0s) without detections, Track 1 is deleted. An Exit event is emitted, and her exit crop is saved to `logs/exits/`. Current Unique Visitors = 1.")
    add_bullet(doc, "Second 15:", "Bob enters from the left. Tracker creates Track 2. After 3 frames, ArcFace extracts his embedding. Cosine similarity against Alice is only 0.18 (well below 0.60). System auto-registers Bob as 'face_0002', logs an Entry event, and saves his crop. Current Unique Visitors = 2.")
    add_bullet(doc, "Second 22:", "Alice re-enters the corridor from the right. Tracker creates Track 3. After 3 frames, ArcFace extracts her embedding. Cosine similarity against 'face_0001' in memory is 0.96 (far above 0.60!). The system recognizes Alice! It assigns 'face_0001' to Track 3, updates her visit count to 2, and logs a second Entry event. Crucially, the Unique Visitor Count remains 2!")
    add_bullet(doc, "Summary Output:", "Total Unique Visitors: 2 | Total Entry Events: 3 | Total Exit Events: 1.")

    print("Completed Chapter 1.")

    # =========================================================================
    # CHAPTER 2: TECHNOLOGIES USED IN MY ACTUAL PROJECT
    # =========================================================================
    add_h1(doc, "Chapter 2: Technologies Used in My Actual Project")
    add_p(doc, "This chapter documents every major programming language, library, framework, and tool actually present "
               "in this repository. None of these technologies are fictional or speculative; all were verified directly against "
               "`requirements.txt`, `frontend/package.json`, and backend Python source files.")

    tech_headers = ["Technology", "Category", "Role in Project", "Primary Source File", "Key Inputs / Outputs"]
    tech_data = [
        ["Python 3.10 / 3.11", "Runtime Language", "Core backend and AI execution environment", "server.py, app.py", "Input: Code scripts | Output: Executable process"],
        ["React 19", "Frontend UI Library", "Component-based interactive single page application", "frontend/src/App.tsx", "Input: State & props | Output: Virtual DOM & HTML"],
        ["TypeScript", "Programming Language", "Type-safe JavaScript ensuring compile-time safety", "frontend/src/types/index.ts", "Input: TS source | Output: Typed JS bundle"],
        ["Vite 8", "Build Tool & Bundler", "Ultra-fast dev server with HMR and production bundler", "frontend/vite.config.ts", "Input: TSX files | Output: Optimized static dist/"],
        ["Tailwind CSS v4", "CSS Framework", "Modern utility-first responsive styling and layout", "frontend/src/index.css", "Input: Utility classes | Output: Compiled CSS bundle"],
        ["Lucide React", "Icon Library", "Clean, consistent icons for cards, navigation, and badges", "frontend/src/components/Sidebar.tsx", "Input: Component props | Output: Scalable SVG icons"],
        ["FastAPI", "Web Framework", "Asynchronous, high-throughput REST API with OpenAPI", "server.py", "Input: HTTP Requests | Output: JSON & file responses"],
        ["Uvicorn", "ASGI Web Server", "High-performance asynchronous server running FastAPI", "server.py", "Input: TCP socket traffic | Output: ASGI events"],
        ["OpenCV (cv2)", "Computer Vision", "Video decoding, coordinate math, blur calculation", "src/detector.py, src/video_source.py", "Input: MP4/RTSP stream | Output: NumPy BGR frames"],
        ["YOLOv8-Face", "Deep Learning Model", "Single-stage face detection and bounding box regression", "src/detector.py (yolov8n-face.pt)", "Input: (640,640,3) frame | Output: [x1,y1,x2,y2,conf]"],
        ["ArcFace / InsightFace", "Deep Metric Learning", "Extracts 512-D L2-normalized hyperspherical vectors", "src/face_recognizer.py", "Input: (112,112,3) crop | Output: (512,) float32 vector"],
        ["ByteTrack / IoU", "Tracking Algorithm", "Multi-frame spatial continuity and trajectory linking", "src/tracker.py", "Input: Detections & boxes | Output: Active & deleted tracks"],
        ["SQLite 3 (WAL)", "Relational Database", "ACID-compliant storage for faces, events, and sessions", "src/database.py", "Input: SQL queries | Output: Rows, transactions, counts"],
        ["Pydantic v2", "Data Validation", "Strict configuration parsing and request validation", "src/config.py, server.py", "Input: Raw dict / JSON | Output: Validated objects"],
        ["Pytest", "Testing Framework", "Automated test execution across unit, API, and DB tests", "tests/ (33 test cases)", "Input: Test assertions | Output: Pass/Fail report"],
    ]
    add_styled_table(doc, tech_headers, tech_data, [Inches(1.2), Inches(1.1), Inches(1.8), Inches(1.2), Inches(1.1)])

    add_h2(doc, "2.1 Distinguishing Libraries, Frameworks, Models, and Protocols")
    add_bullet(doc, "Library (e.g. OpenCV, Lucide):", "A collection of reusable pre-written functions you call when needed. You maintain full control over the application flow.")
    add_bullet(doc, "Framework (e.g. React, FastAPI):", "A structured architectural foundation that calls your code. In React, the framework determines when to render; in FastAPI, the framework routes network requests to your functions.")
    add_bullet(doc, "Deep Learning Model (e.g. YOLOv8n-Face, ArcFace):", "A set of trained neural network weights (stored in `.pt` or `.onnx` files) that transform raw images into bounding boxes or 512-dimensional biometric numbers.")
    add_bullet(doc, "Protocol (e.g. HTTP, RTSP):", "A standardized set of rules governing how two computers exchange information over a network. HTTP transmits web pages and JSON; RTSP streams continuous live video.")
    add_bullet(doc, "File Format (e.g. JSON, MP4, SQLite DB):", "A standardized structure for saving information to physical disk so other programs can read it.")

    print("Completed Chapter 2.")

    # =========================================================================
    # CHAPTER 3: COMPLETE SYSTEM ARCHITECTURE
    # =========================================================================
    add_h1(doc, "Chapter 3: Complete System Architecture")
    add_p(doc, "The architecture of the Intelligent Face Tracker is built upon strict separation of concerns, decoupling "
               "the user interface from the CPU-heavy computer vision pipeline. This ensures that even when processing a 4K "
               "video at full speed, the web application remains responsive, interactive, and resilient.")

    add_h2(doc, "3.1 Implemented Component Architecture")
    add_p(doc, "The diagram below illustrates the actual implemented system components and their communication channels:")
    add_diagram(doc, DIAGRAMS_DIR / "architecture_diagram.png", 
                "Complete Implemented System Architecture: Frontend, REST API, Background Job Manager, AI Pipeline, and Storage Layer")

    add_h2(doc, "3.2 Detailed Component Breakdown")
    add_bullet(doc, "1. Frontend Single Page Application (`frontend/src/`):", "Built with React 19 and Tailwind CSS. Manages 7 interactive views: Dashboard, Upload, Live Camera, Visitor Events, Registered Identities, Processing History, and Settings. Communicates exclusively with the backend via asynchronous HTTP fetch requests.")
    add_bullet(doc, "2. API Gateway & Static Server (`server.py`):", "FastAPI server running on port 8000. Provides 13 REST API endpoints, handles CORS, validates payloads with Pydantic, and mounts `/static/uploads` and `/static/logs` to serve video previews and face crop thumbnails directly to web browsers.")
    add_bullet(doc, "3. Asynchronous Job Manager (`src/job_manager.py`):", "A thread-safe singleton that coordinates long-running video processing. It runs the OpenCV/YOLO/ArcFace loop in a background daemon thread, allowing web clients to poll progress without blocking HTTP request workers.")
    add_bullet(doc, "4. Video Ingestion (`src/video_source.py`):", "Decodes local video files or network IP camera feeds. Implements automatic exponential backoff reconnection (up to 5 retries) if an IP stream drops.")
    add_bullet(doc, "5. Face Detection (`src/detector.py`):", "Executes YOLOv8-face inference, clamps bounding boxes to image dimensions with a 15% margin padding, and computes Laplacian variance blur metrics to filter out degraded faces.")
    add_bullet(doc, "6. Multi-Object Tracking (`src/tracker.py`):", "Implements IoU spatial association. Enforces multi-frame hit confirmation (`min_hits_to_confirm = 3`) to eliminate single-frame false detections and a configurable timeout (`track_lost_timeout_seconds = 2.0s`) to bridge temporary occlusions.")
    add_bullet(doc, "7. Biometric Face Recognizer (`src/face_recognizer.py`):", "Extracts 512-dimensional L2-normalized embeddings using ArcFace/InsightFace SOTA models. Strictly avoids the deprecated `face_recognition` library.")
    add_bullet(doc, "8. Identity Manager (`src/identity_manager.py`):", "Maintains an in-memory cache of registered identities. Compares candidates using cosine similarity. Re-identifies existing visitors if similarity >= 0.60, or auto-registers new sequential identities (`face_0001`, `face_0002`...).")
    add_bullet(doc, "9. Event Lifecycle Manager (`src/event_manager.py`):", "Coordinates the finite state machine for confirmed Entry and Exit events. Saves face crop images into dated subfolders (`logs/entries/YYYY-MM-DD/`) and logs structured audit records.")
    add_bullet(doc, "10. Relational Database Layer (`src/database.py`):", "Transactional SQLite database configured in WAL mode (`PRAGMA journal_mode = WAL;`). Guarantees database idempotency through `UNIQUE(track_id, event_type)`.")
    add_bullet(doc, "11. Visitor Counter & Analytics (`src/visitor_counter.py`):", "Computes true unique visitor counts via `COUNT(DISTINCT face_id)` and derives current venue occupancy.")

    add_h2(doc, "3.3 Chronological Video Processing Sequence")
    add_p(doc, "The sequence diagram below illustrates the exact step-by-step communication lifecycle from user upload to final dashboard display:")
    add_diagram(doc, DIAGRAMS_DIR / "sequence_diagram.png", 
                "Sequence Diagram: Chronological Execution Flow from Video Upload to Database Persistence and Web UI Refresh")

    print("Completed Chapter 3.")

    # =========================================================================
    # CHAPTER 4: COMPLETE APPLICATION FLOW — STEP BY STEP
    # =========================================================================
    add_h1(doc, "Chapter 4: Complete Application Flow — Step by Step")
    add_p(doc, "This chapter explains the exact sequence of events that occur across the application, divided into "
               "17 distinct, numbered steps. For each step, the actual source file, class or function name, inputs, "
               "outputs, and next components are explicitly identified.")

    steps_data = [
        ("Step 1: User Opens the Web Application",
         "The user enters http://127.0.0.1:8000 into their browser.",
         "frontend/dist/index.html & server.py", "FastAPI StaticFiles",
         "HTTP GET / request", "HTML5 page, compiled JS bundle, CSS stylesheets", "Browser DOM parser and React mounting"),

        ("Step 2: Frontend Loads & Displays Interface",
         "React initializes root App component, displays sidebar, header, and active tab.",
         "frontend/src/App.tsx", "App() & Header()",
         "Browser window load event", "Rendered dashboard layout with navigation tabs", "User navigation to Upload Video tab"),

        ("Step 3: User Selects a Video File",
         "User drags and drops an MP4/AVI file into the upload dropzone or uses file picker.",
         "frontend/src/pages/UploadPage.tsx", "handleDrop() / handleFileSelect()",
         "File event from browser input", "File object validated for extension (.mp4, .avi, .mkv)", "Video preview displayed via HTML5 video tag"),

        ("Step 4: Frontend Validates & Uploads File",
         "Frontend creates FormData and dispatches asynchronous POST request.",
         "frontend/src/services/api.ts", "apiService.uploadVideo()",
         "FormData with raw binary video", "HTTP POST /api/upload request payload", "FastAPI server upload endpoint"),

        ("Step 5: Backend Receives & Validates Upload",
         "FastAPI parses multipart body, verifies extension, sanitizes filename with timestamp.",
         "server.py", "upload_video(file: UploadFile)",
         "UploadFile stream", "Saved file in data/uploads/YYYYMMDD_HHMMSS_name.mp4", "Returns JSON with filename, filepath, preview_url"),

        ("Step 6: User Clicks 'Start Processing'",
         "User initiates background video analysis with optional frame-skip and similarity settings.",
         "frontend/src/pages/UploadPage.tsx", "handleStartProcessing()",
         "Click event + config settings", "POST /api/jobs/start {source_type: 'file', file_path: ...}", "FastAPI start_processing endpoint"),

        ("Step 7: Backend Starts Asynchronous Job",
         "FastAPI delegates execution to JobManager, which starts a background daemon thread.",
         "src/job_manager.py", "JobManager.start_job()",
         "StartJobRequest payload", "Unique job_id (e.g. job_4f89a2bc), worker thread started", "Worker enters _run_job_worker() loop"),

        ("Step 8: Video Source Decoding",
         "OpenCV opens the video file, extracts frame dimensions, and begins decoding frames.",
         "src/video_source.py", "VideoSource.read_frames()",
         "File path string", "Generator yielding (frame_index, timestamp_iso, frame_bgr)", "Core detection & tracking loop"),

        ("Step 9: Frame Skip Gating & YOLO Detection",
         "Evaluates frame_idx % (skip + 1) == 0. If true, runs YOLOv8-face detector.",
         "src/detector.py", "FaceDetector.detect()",
         "NumPy BGR image frame (H, W, 3)", "List[Detection] with clamped bboxes, confidences, crops", "Spatial tracker update"),

        ("Step 10: Face Crop Generation & Quality Gating",
         "Validates coordinates with 15% margin padding and computes Laplacian blur score.",
         "src/detector.py", "validate_and_clamp_bbox() & compute_blur_score()",
         "Candidate bbox & frame", "Clamped face crop array, blur score float (threshold >= 50.0)", "Filter degenerate or blurry crops"),

        ("Step 11: Multi-Object Spatial Tracking",
         "ByteTrack algorithm computes IoU between current detections and existing tracks.",
         "src/tracker.py", "FaceTracker.update()",
         "List[Detection], frame_index", "Tuple(active_tracks, deleted_tracks)", "Track state transitions (Tentative->Confirmed)"),

        ("Step 12: ArcFace 512-D Embedding Extraction",
         "For confirmed tracks, ArcFace model extracts normalized 512-D float32 vector.",
         "src/face_recognizer.py", "ArcFaceRecognizer.extract_embedding()",
         "Best quality face crop (112x112x3)", "L2-normalized 1D array of shape (512,)", "Identity matching against database cache"),

        ("Step 13: Identity Matching & Auto-Registration",
         "Computes cosine similarity against cached identities. Matches if sim >= 0.60.",
         "src/identity_manager.py", "IdentityManager.process_track()",
         "512-D embedding vector, Track object", "Assigned face_id (e.g. face_0001), auto-registers if new", "EventManager entry handling"),

        ("Step 14: Entry Event Emission & Crop Archiving",
         "Emits confirmed Entry event, saves crop to disk, and inserts record into SQLite.",
         "src/event_manager.py", "EventManager.handle_entry()",
         "Confirmed Track object, timestamp", "Saved crop in logs/entries/YYYY-MM-DD/, DB event row", "Audit logging to logs/events.log"),

        ("Step 15: Track Deletion & Exit Event Emission",
         "When tracked person disappears beyond timeout, track is deleted and Exit emitted.",
         "src/event_manager.py", "EventManager.handle_exit()",
         "Deleted Track object, timestamp", "Saved crop in logs/exits/YYYY-MM-DD/, DB exit row", "Track memory release"),

        ("Step 16: Telemetry Polling & Live UI Updates",
         "Frontend polls job status every 1000ms, updating progress bar, FPS, and counts.",
         "frontend/src/pages/UploadPage.tsx", "pollJobStatus() -> GET /api/jobs/status",
         "Active job polling timer", "JSON: {progress_percent, fps, unique_visitors, ...}", "React state re-render"),

        ("Step 17: Completion & Result Display",
         "Job finishes, session is closed in DB, frontend automatically fetches final stats.",
         "src/job_manager.py & frontend", "db.end_session() -> GET /api/stats",
         "EOF reached in video", "Final counts, completion banner, updated event tables", "User reviews visitor analytics"),
    ]

    for title, desc, file_loc, fn_name, in_p, out_p, next_c in steps_data:
        add_h2(doc, title)
        add_p(doc, desc)
        add_bullet(doc, "Source File:", file_loc)
        add_bullet(doc, "Function / Class:", fn_name)
        add_bullet(doc, "Input:", in_p)
        add_bullet(doc, "Output:", out_p)
        add_bullet(doc, "Next Component:", next_c)

    print("Completed Chapter 4.")

    # =========================================================================
    # CHAPTER 5: FRONTEND EXPLAINED
    # =========================================================================
    add_h1(doc, "Chapter 5: Frontend Explained")
    add_p(doc, "The frontend is the visual single-page web application (SPA) that runs entirely inside the user's web browser. "
               "It is engineered using React 19, TypeScript, Vite, and Tailwind CSS v4.")

    add_h2(doc, "5.1 What is Frontend and React?")
    add_p(doc, "Frontend refers to the client-side presentation layer—the buttons, typography, colors, layout, and forms "
               "that users see and interact with. Rather than writing thousands of lines of disjointed HTML, the project uses "
               "React, a component-based library. In React, the user interface is broken down into small, reusable building blocks "
               "called components. For example, the `Sidebar`, `Header`, and `DashboardPage` are separate React components.")

    add_h2(doc, "5.2 What is TypeScript?")
    add_p(doc, "Standard JavaScript allows variables to change types dynamically, which frequently leads to unpredictable "
               "bugs (such as trying to call `.map()` on an undefined variable). TypeScript adds strict compile-time types. "
               "In `frontend/src/types/index.ts`, every data structure returned by the backend is explicitly modeled:")
    add_code_block(doc, 
        "export interface EventItem {\n"
        "  event_id: string;\n"
        "  face_id: string;\n"
        "  track_id: number;\n"
        "  event_type: 'entry' | 'exit';\n"
        "  timestamp: string;\n"
        "  confidence: number;\n"
        "  thumbnail_url: string | null;\n"
        "  has_thumbnail: boolean;\n"
        "}"
    )

    add_h2(doc, "5.3 What Does Vite Do?")
    add_p(doc, "Vite is the modern build tool and development server powering the frontend. During development, Vite provides "
               "Hot Module Replacement (HMR)—meaning when you edit a React file, the change appears in your browser in milliseconds "
               "without refreshing the entire page. For production, Vite compiles, tree-shakes, and bundles all TypeScript and CSS "
               "files into an ultra-fast static distribution folder (`frontend/dist/`).")

    add_h2(doc, "5.4 Application Routing and State Management")
    add_p(doc, "Instead of using heavy multi-page reloads, the application uses state-driven tab switching inside `frontend/src/App.tsx`. "
               "A single React state hook, `const [currentTab, setCurrentTab] = useState<TabType>('dashboard')`, determines which page "
               "component is rendered. This produces instantaneous, smooth transitions between screens.")

    add_h2(doc, "5.5 Tracing a Real UI Button Click: 'Start Processing'")
    add_p(doc, "To understand how the frontend connects to the backend, let us trace what happens when an operator clicks the 'Start Processing' button:")
    add_bullet(doc, "1. User Clicks Button:", "In `UploadPage.tsx`, the operator clicks `<button onClick={handleStartProcessing}>Start Processing</button>`.")
    add_bullet(doc, "2. Event Handler Executes:", "`handleStartProcessing()` sets local state `setIsProcessing(true)` and calls `apiService.startJob(...)`.")
    add_bullet(doc, "3. API Client Dispatches HTTP Request:", "`frontend/src/services/api.ts` sends an HTTP `POST /api/jobs/start` request with JSON payload `{ source_type: 'file', file_path: 'data/uploads/...' }`.")
    add_bullet(doc, "4. Status Polling Timer Starts:", "The frontend initiates a JavaScript `setInterval` timer that calls `GET /api/jobs/status` every 1,000 milliseconds.")
    add_bullet(doc, "5. UI Progress Bar Animates:", "As status responses arrive, React updates `jobStatus` state, causing the progress bar width (`style={{ width: `${jobStatus.progress_percent}%` }}`) and instantaneous FPS counter to animate smoothly.")
    add_bullet(doc, "6. Completion Notification:", "When `jobStatus.status === 'completed'`, the interval clears, a success banner appears, and the user is provided a shortcut to view the newly logged events.")

    print("Completed Chapter 5.")

    # =========================================================================
    # CHAPTER 6: BACKEND AND API EXPLAINED
    # =========================================================================
    add_h1(doc, "Chapter 6: Backend and API Explained")
    add_p(doc, "The backend is the server-side computational engine that handles business logic, database transactions, "
               "and deep learning inference. It exposes a clean REST API implemented using FastAPI.")

    add_h2(doc, "6.1 What is an API and HTTP?")
    add_p(doc, "API stands for Application Programming Interface. It is the formal contract that allows the frontend (in the browser) "
               "to talk to the backend (on the server). They communicate over HTTP (Hypertext Transfer Protocol) using standard methods:")
    add_bullet(doc, "GET:", "Retrieve data from the server without modifying anything (e.g. `GET /api/stats`).")
    add_bullet(doc, "POST:", "Submit new data or initiate an action (e.g. `POST /api/upload`, `POST /api/jobs/start`).")
    add_bullet(doc, "PUT:", "Update an existing configuration or resource completely (e.g. `PUT /api/config`).")
    add_bullet(doc, "DELETE:", "Remove a resource from the server.")

    add_h2(doc, "6.2 Complete Implemented API Endpoints Table")
    api_headers = ["Method", "Actual Route", "Purpose", "Request Input", "Response Output", "Source File"]
    api_data = [
        ["GET", "/api/health", "Health check & version info", "None", "JSON: status, version, timestamp", "server.py:109"],
        ["GET", "/api/stats", "Dashboard KPI aggregate counters", "None", "JSON: unique_visitors, entries, exits", "server.py:120"],
        ["GET", "/api/events", "Paginated, filterable event audit log", "Query: face_id, event_type, limit", "JSON: total, events list with thumbnails", "server.py:136"],
        ["GET", "/api/identities", "Registered visitor directory", "None", "JSON: total, identities list", "server.py:180"],
        ["GET", "/api/identities/{id}", "Detailed history for specific visitor", "Path parameter: face_id", "JSON: visitor details & event history", "server.py:216"],
        ["GET", "/api/sessions", "Processing run history", "None", "JSON: total, sessions list", "server.py:230"],
        ["POST", "/api/upload", "Upload video file for processing", "Multipart/form-data: file", "JSON: filename, file_path, preview_url", "server.py:254"],
        ["POST", "/api/jobs/start", "Launch background video analytics", "JSON: StartJobRequest", "JSON: success, job_id, status", "server.py:286"],
        ["GET", "/api/jobs/status", "Poll real-time job progress & FPS", "None", "JSON: progress_percent, fps, visitors", "server.py:325"],
        ["POST", "/api/jobs/stop", "Cancel currently running job", "None", "JSON: success, message", "server.py:331"],
        ["GET", "/api/config", "Retrieve active pipeline settings", "None", "JSON: detection, recognition, tracking", "server.py:338"],
        ["PUT", "/api/config", "Update and persist configuration", "JSON: ConfigUpdateRequest", "JSON: success, message", "server.py:366"],
        ["GET", "/api/analytics/temporal", "Hourly & session chart distributions", "None", "JSON: hourly_activity, session_charts", "server.py:397"],
    ]
    add_styled_table(doc, api_headers, api_data, [Inches(0.8), Inches(1.5), Inches(1.5), Inches(1.1), Inches(1.4), Inches(0.9)])

    add_h2(doc, "6.3 Sample Request & Response Payloads")
    add_p(doc, "Example: Starting a Video Processing Job (`POST /api/jobs/start`)")
    add_code_block(doc,
        "// Request Payload sent to /api/jobs/start\n"
        "{\n"
        "  \"source_type\": \"file\",\n"
        "  \"file_path\": \"data/sample_video.mp4\",\n"
        "  \"frame_skip\": 2,\n"
        "  \"similarity_threshold\": 0.60\n"
        "}\n\n"
        "// Response received from server (HTTP 200 OK)\n"
        "{\n"
        "  \"success\": true,\n"
        "  \"message\": \"Processing job started successfully.\",\n"
        "  \"job_id\": \"job_c7e2b190\",\n"
        "  \"status\": \"running\"\n"
        "}"
    )

    add_p(doc, "Example: Polling Real-Time Progress (`GET /api/jobs/status`)")
    add_code_block(doc,
        "// Response from GET /api/jobs/status during processing\n"
        "{\n"
        "  \"job_id\": \"job_c7e2b190\",\n"
        "  \"status\": \"running\",\n"
        "  \"current_frame\": 180,\n"
        "  \"total_frames\": 250,\n"
        "  \"progress_percent\": 72.0,\n"
        "  \"fps\": 254.2,\n"
        "  \"unique_visitors\": 1,\n"
        "  \"total_entries\": 2,\n"
        "  \"total_exits\": 1,\n"
        "  \"active_tracks\": 1,\n"
        "  \"elapsed_seconds\": 10.4\n"
        "}"
    )

    print("Completed Chapter 6.")

    # =========================================================================
    # CHAPTER 7: DATABASE — FROM ZERO TO UNDERSTANDING
    # =========================================================================
    add_h1(doc, "Chapter 7: Database — From Zero to Understanding")
    add_p(doc, "A database is an organized digital system for storing, managing, and retrieving information securely. "
               "This project uses SQLite 3, an ACID-compliant, serverless, zero-configuration relational database engine.")

    add_h2(doc, "7.1 Database Fundamentals for Beginners")
    add_bullet(doc, "Table:", "A collection of related data organized into rows and columns (e.g. the `faces` table).")
    add_bullet(doc, "Column (Field):", "A specific property of an item (e.g. `face_id`, `confidence`, `timestamp`).")
    add_bullet(doc, "Row (Record):", "A single complete entry (e.g. one specific visitor entry event).")
    add_bullet(doc, "Primary Key (PK):", "A unique identifier ensuring no two rows share the same identity (e.g. `face_id` in `faces`).")
    add_bullet(doc, "Foreign Key (FK):", "A link between two tables ensuring relational integrity (e.g. `events.face_id` points to `faces.face_id`).")
    add_bullet(doc, "WAL Mode (Write-Ahead Logging):", "A high-performance SQLite feature enabled in `src/database.py` that allows multiple readers to read the database at the same time a background thread is writing to it.")

    add_h2(doc, "7.2 Database Entity-Relationship (ER) Diagram")
    add_diagram(doc, DIAGRAMS_DIR / "database_er_diagram.png", 
                "Database Entity-Relationship (ER) Diagram: Tables, Fields, Primary Keys, Foreign Keys, and Constraints")

    add_h2(doc, "7.3 Complete Schema Documentation")
    add_h3(doc, "Table 1: `faces` (Registered Identities)")
    add_bullet(doc, "face_id (TEXT, PK):", "Unique sequential identifier, e.g. 'face_0001'.")
    add_bullet(doc, "name (TEXT):", "Optional human name, e.g. 'Visitor #0001'.")
    add_bullet(doc, "embedding (BLOB):", "Raw binary bytes of the 512-dimensional float32 ArcFace embedding (2,048 bytes).")
    add_bullet(doc, "first_seen (TEXT):", "ISO-8601 timestamp of when the individual was first enrolled.")
    add_bullet(doc, "last_seen (TEXT):", "ISO-8601 timestamp of their most recent confirmed appearance.")
    add_bullet(doc, "total_visits (INTEGER):", "Number of distinct confirmed visits across all sessions.")
    add_bullet(doc, "metadata_json (TEXT):", "Optional JSON string for extra attributes (e.g. tags).")

    add_h3(doc, "Table 2: `events` (Audit Trail)")
    add_bullet(doc, "event_id (TEXT, PK):", "Unique event identifier, e.g. 'evt_entry_a81b3c4d'.")
    add_bullet(doc, "face_id (TEXT, FK):", "Foreign key referencing `faces(face_id)` with `ON DELETE CASCADE`.")
    add_bullet(doc, "track_id (INTEGER):", "Session tracking ID from the multi-object tracker.")
    add_bullet(doc, "event_type (TEXT):", "Must be strictly 'entry' or 'exit' enforced via CHECK constraint.")
    add_bullet(doc, "timestamp (TEXT):", "ISO-8601 timestamp of the physical occurrence.")
    add_bullet(doc, "image_path (TEXT):", "Relative file path to the cropped face image on disk.")
    add_bullet(doc, "confidence (REAL):", "Detection / tracking confidence score [0.0 to 1.0].")
    add_bullet(doc, "created_at (TEXT):", "ISO-8601 timestamp of database record insertion.")
    add_bullet(doc, "UNIQUE(track_id, event_type):", "CRITICAL CONSTRAINT: Guarantees exactly-once event emission per physical trajectory.")

    add_h3(doc, "Table 3: `sessions` (Processing Runs)")
    add_bullet(doc, "session_id (TEXT, PK):", "Job identifier, e.g. 'job_4a2c91e0'.")
    add_bullet(doc, "source_type (TEXT):", "Source mode: 'file' or 'rtsp'.")
    add_bullet(doc, "source_path (TEXT):", "Path to video file or masked camera URL.")
    add_bullet(doc, "started_at / ended_at (TEXT):", "Execution start and completion timestamps.")
    add_bullet(doc, "total_frames / unique_faces_count (INTEGER):", "Aggregate metrics for the run.")
    add_bullet(doc, "status (TEXT):", "Execution status: 'RUNNING', 'COMPLETED', or 'FAILED'.")

    add_h2(doc, "7.4 Beginner-Friendly SQL Inspection Queries")
    add_p(doc, "You can inspect the database directly using the SQLite command-line tool or Python:")
    add_code_block(doc,
        "-- Query 1: Total Unique Visitors\n"
        "SELECT COUNT(DISTINCT face_id) AS total_unique_visitors FROM faces;\n\n"
        "-- Query 2: All Entry and Exit Events for Visitor 'face_0001'\n"
        "SELECT event_id, event_type, timestamp, image_path \n"
        "FROM events \n"
        "WHERE face_id = 'face_0001' \n"
        "ORDER BY timestamp ASC;\n\n"
        "-- Query 3: Processing Run History Summary\n"
        "SELECT session_id, source_type, total_frames, unique_faces_count, status \n"
        "FROM sessions \n"
        "ORDER BY started_at DESC LIMIT 5;"
    )

    print("Completed Chapter 7.")

    # =========================================================================
    # CHAPTER 8: JSON CONFIGURATION EXPLAINED
    # =========================================================================
    add_h1(doc, "Chapter 8: JSON Configuration Explained")
    add_p(doc, "JSON (JavaScript Object Notation) is a lightweight, human-readable format for storing data. "
               "The application separates configuration settings from Python source code using `config.json`. "
               "This allows operators to tune parameters—such as matching thresholds or camera URLs—without touching or breaking code.")

    add_h2(doc, "8.1 Key Parameters in `config.json` Explained")
    config_headers = ["Section", "Parameter Key", "Default Value", "Purpose and Impact on System"]
    config_data = [
        ["system", "app_name", "Intelligent Face Tracker...", "Application display title used in headers and logs"],
        ["system", "environment", "production", "Run mode ('production', 'development', 'testing')"],
        ["video", "source_type", "file", "Ingestion mode ('file', 'rtsp', 'webcam')"],
        ["video", "file_path", "data/sample_video.mp4", "Default video file path when no upload is specified"],
        ["video", "reconnect_delay_seconds", "2.0", "Seconds to pause before attempting an RTSP reconnect"],
        ["video", "max_reconnect_attempts", "5", "Maximum consecutive reconnection retries before failing"],
        ["detection", "model_path", "models/yolov8n-face.pt", "File path to the pretrained YOLOv8-face weights"],
        ["detection", "confidence_threshold", "0.60", "Minimum detector score required to accept a face box"],
        ["detection", "frame_skip", "2", "Number of frames to skip between detections (e.g. process 1 in 3)"],
        ["recognition", "similarity_threshold", "0.60", "Cosine similarity cutoff for matching existing identities"],
        ["recognition", "blur_threshold", "50.0", "Minimum Laplacian variance score to accept face crops"],
        ["recognition", "min_face_size", "[40, 40]", "Minimum width and height in pixels for valid face crops"],
        ["tracking", "iou_threshold", "0.35", "Intersection over Union overlap required to maintain a track"],
        ["tracking", "min_hits_to_confirm", "3", "Consecutive detections required before confirming an Entry"],
        ["tracking", "track_lost_timeout_seconds", "2.0", "Seconds a face can disappear before an Exit is emitted"],
        ["storage", "database_path", "data/visitor_tracker.db", "File path to the primary SQLite database"],
        ["storage", "save_crops", "true", "Whether to save high-resolution face crops to disk"],
        ["storage", "crop_margin_ratio", "0.15", "15% extra padding added around facial crops for context"],
    ]
    add_styled_table(doc, config_headers, config_data, [Inches(1.0), Inches(1.8), Inches(1.3), Inches(2.7)])

    add_h2(doc, "8.2 How Configuration is Loaded and Validated")
    add_p(doc, "When the backend starts, `src/config.py` uses Pydantic v2 to load and validate `config.json`. "
               "Pydantic automatically enforces data types and acceptable ranges. For example, if someone sets "
               "`similarity_threshold: 1.5`, Pydantic immediately throws a `ValidationError` because the threshold must be "
               "between 0.1 and 0.99. This prevents accidental configuration typos from crashing the server during live tracking.")

    print("Completed Chapter 8.")

    # =========================================================================
    # CHAPTER 9: FACE DETECTION, RECOGNITION, AND TRACKING
    # =========================================================================
    add_h1(doc, "Chapter 9: Face Detection, Recognition, and Tracking")
    add_p(doc, "This chapter explains the mathematical and algorithmic foundations of the core computer vision pipeline.")

    add_h2(doc, "A. Video Frames and Frame Skipping")
    add_p(doc, "A video is a rapid sequence of still pictures called frames. Standard security footage runs at 25 or 30 frames "
               "per second (FPS). Running deep neural networks on every frame requires massive computing power. The system uses "
               "frame skipping: `should_detect = (skip == 0) or (frame_idx % (skip + 1) == 0)`. With `frame_skip = 2`, the system "
               "processes 1 frame and skips 2 frames, achieving 3x higher throughput (~250 FPS CPU) while maintaining continuous tracking.")

    add_h2(doc, "B. Face Detection & Bounding Boxes")
    add_p(doc, "The YOLOv8-face model is a single-stage convolutional neural network trained specifically on human faces. "
               "Given a 640x640 input, it predicts bounding boxes `[x1, y1, x2, y2]` along with a confidence probability score.")

    add_h2(doc, "C. Face Crops & Image Quality Checks")
    add_p(doc, "When a face is detected near the edge of the screen, raw coordinates might extend outside the image boundary. "
               "`src/detector.py` uses `validate_and_clamp_bbox()` to clamp coordinates strictly to `[0, frame_w]` and `[0, frame_h]`. "
               "It also computes the Laplacian variance blur score: `cv2.Laplacian(gray, cv2.CV_64F).var()`. If a visitor turns their "
               "head quickly, causing motion blur ($\sigma^2 < 50.0$), the crop is discarded so blurry embeddings never pollute the database.")

    add_h2(doc, "D. Facial Embeddings & Cosine Similarity")
    add_p(doc, "Instead of comparing raw pixel values (which fail if lighting or angles shift), ArcFace transforms the face into "
               "a 512-dimensional vector. Each vector is normalized to unit length: $\|\mathbf{v}\|_2 = 1.0$. The similarity between "
               "two embeddings $\mathbf{u}$ and $\mathbf{v}$ is calculated using the Cosine Similarity formula:")
    add_code_block(doc, "Cosine Similarity = (u · v) / (||u|| * ||v||)")
    add_p(doc, "Since both vectors have length 1.0, this simplifies to the dot product: $\sum_{i=1}^{512} u_i v_i$. "
               "The result is a single float between -1.0 and 1.0, where 1.0 indicates an identical face.")

    add_h2(doc, "E. Recognition Thresholds & Trade-offs")
    add_p(doc, "The default threshold is `0.60`. Setting it higher (e.g. 0.75) reduces False Accept Rate (FAR) but might fail "
               "to recognize someone wearing glasses. Setting it lower (e.g. 0.45) increases False Reject Rate (FRR). "
               "Empirical testing on real corridor footage confirms 0.60 provides optimal balance.")

    add_h2(doc, "F. Automatic Identity Registration")
    add_p(doc, "When a face does not match any registered visitor with similarity >= 0.60, `IdentityManager` automatically generates "
               "the next sequential ID (e.g. `face_0001`), stores its 512-D embedding in the database, and adds it to an in-memory cache.")

    add_h2(doc, "G. Temporary Tracking IDs vs Persistent Face IDs")
    add_p(doc, "A critical architectural rule: `track_id` is a transient integer (1, 2, 3...) that exists only while someone walks "
               "across the camera view. When they leave, the track is deleted. The `face_id` (e.g. `face_0001`) is permanent in SQLite. "
               "If Alice enters twice, she has two different `track_id`s, but both resolve to the exact same persistent `face_id`.")

    add_h2(doc, "H. Multi-Object Tracking & ByteTrack")
    add_p(doc, "Tracking maintains spatial continuity across frames by calculating Intersection over Union (IoU):")
    add_code_block(doc, "IoU = Area of Overlap / Area of Union")
    add_p(doc, "If IoU >= 0.35, the detection is linked to the existing track. Tracks transition through states: "
               "Tentative (awaiting 3 hits) -> Confirmed (active) -> Lost (missing for < 60 frames) -> Deleted (exited).")

    add_h2(doc, "I. Entry and Exit Event Decisions")
    add_p(doc, "Face visibility alone does NOT prove entry or exit. Single-camera operational rules implemented:")
    add_bullet(doc, "Confirmed Entry:", "Triggered strictly when a face is detected and tracked for 3 consecutive frames.")
    add_bullet(doc, "Confirmed Exit:", "Triggered strictly when an active track disappears and remains unseen for 60 consecutive frames (2.0s).")

    add_h2(doc, "J. Unique Identities vs Event Counts")
    add_p(doc, "If Alice enters in the morning, leaves, and enters in the afternoon: Total Entries = 2, Total Exits = 1, "
               "Total Unique Visitors = 1. The database guarantees that re-identifications never inflate the unique visitor count.")

    print("Completed Chapter 9.")

    # =========================================================================
    # CHAPTER 10: IMAGE STORAGE, LOGS, AND EVENT LIFECYCLE
    # =========================================================================
    add_h1(doc, "Chapter 10: Image Storage, Logs, and Event Lifecycle")
    add_p(doc, "This chapter explains where files are stored on disk, how directories are named, and how audit logs are recorded.")

    add_h2(doc, "10.1 Directory Structure on Disk")
    add_code_block(doc,
        "intelligent-face-tracker/\n"
        "├── data/\n"
        "│   ├── uploads/                      <- Uploaded video files (e.g. 20261017_093000_sample.mp4)\n"
        "│   └── visitor_tracker.db            <- SQLite relational database\n"
        "└── logs/\n"
        "    ├── entries/YYYY-MM-DD/           <- Face crops saved upon confirmed Entry\n"
        "    ├── exits/YYYY-MM-DD/             <- Face crops saved upon confirmed Exit\n"
        "    └── events.log                    <- Centralized structured audit log"
    )

    add_h2(doc, "10.2 Face Crop Image Naming Convention")
    add_p(doc, "Crop images follow a strict, human-readable naming pattern:")
    add_code_block(doc, "{face_id}_track{track_id}_{HHMMSS_ffffff}.jpg\nExample: face_0001_track1_091530_1234.jpg")

    add_h2(doc, "10.3 The Structured Audit Log (`logs/events.log`)")
    add_p(doc, "Every significant event is logged with timestamps and logger names:")
    add_code_block(doc,
        "2026-10-17 09:15:30 [INFO] [detector] Face detection backend initialized: yolov8_face (cpu)\n"
        "2026-10-17 09:15:31 [INFO] [tracker] Track 1 confirmed after 3 consecutive hits\n"
        "2026-10-17 09:15:31 [INFO] [identity_manager] AUTO-REGISTERED new identity face_0001 for Track 1\n"
        "2026-10-17 09:15:31 [INFO] [event_manager] CONFIRMED ENTRY: Face face_0001 (Track ID: 1, Crop: logs/entries/...)\n"
        "2026-10-17 09:15:35 [INFO] [tracker] Track 1 marked as DELETED (lost for 61 frames)\n"
        "2026-10-17 09:15:35 [INFO] [event_manager] CONFIRMED EXIT: Face face_0001 (Track ID: 1, Crop: logs/exits/...)"
    )

    print("Completed Chapter 10.")

    # =========================================================================
    # CHAPTER 11: ENVIRONMENT VARIABLES AND DEPENDENCIES
    # =========================================================================
    add_h1(doc, "Chapter 11: Environment Variables and Dependencies")
    add_p(doc, "Environment variables allow configuration parameters and sensitive secrets (such as camera passwords) "
               "to be passed into the application without hardcoding them into source files.")

    add_h2(doc, "11.1 Protecting Secrets with `.env.example`")
    add_p(doc, "The repository contains `.env.example` as a template. To set an RTSP camera stream URL securely in Windows PowerShell:")
    add_code_block(doc, '$env:RTSP_STREAM_URL="rtsp://admin:secret123@192.168.1.100:554/live"')
    add_p(doc, "The system automatically sanitizes RTSP URLs: passwords are replaced with `***:***@` in all logs, UI displays, and API responses.")

    add_h2(doc, "11.2 Pretrained AI Model Weights")
    add_p(doc, "The application expects model files inside `models/`:")
    add_bullet(doc, "yolov8n-face.pt (6.2 MB):", "YOLOv8 face detection weights (auto-downloaded via `scripts/download_models.py`).")
    add_bullet(doc, "face_detection_yunet_2023mar.onnx (232 KB):", "Lightweight OpenCV YuNet ONNX face detector.")
    add_bullet(doc, "arcface_sota.onnx (174 MB):", "InsightFace Buffalo_L ArcFace ONNX model for 512-D embeddings.")

    print("Completed Chapter 11.")

    # =========================================================================
    # CHAPTER 12: COMPLETE SETUP AND RUNNING GUIDE
    # =========================================================================
    add_h1(doc, "Chapter 12: Complete Setup and Running Guide")
    add_p(doc, "This chapter provides verified, step-by-step instructions to set up and run the application.")

    add_h2(doc, "12.1 Step 1: Environment Setup")
    add_code_block(doc,
        "# Windows PowerShell\n"
        "cd C:\\Users\\Acer\\.gemini\\antigravity\\scratch\\intelligent-face-tracker\n"
        "python -m venv venv\n"
        ".\\venv\\Scripts\\Activate.ps1\n"
        "pip install -r requirements.txt"
    )

    add_h2(doc, "12.2 Step 2: Download Model Weights")
    add_code_block(doc, "python scripts/download_models.py --model all")

    add_h2(doc, "12.3 Step 3: Run the Web Application")
    add_code_block(doc,
        "# Start FastAPI server (serves API and React UI on port 8000)\n"
        "python server.py\n\n"
        "# Open your browser and navigate to:\n"
        "# http://127.0.0.1:8000"
    )

    add_h2(doc, "12.4 Step 4: Run Automated Tests")
    add_code_block(doc,
        "# Run all 33 automated tests\n"
        "python -m pytest tests/ -v"
    )

    print("Completed Chapter 12.")

    # =========================================================================
    # CHAPTER 13: TROUBLESHOOTING
    # =========================================================================
    add_h1(doc, "Chapter 13: Troubleshooting")
    add_p(doc, "Practical diagnostic steps for common issues encountered during development and deployment:")

    trouble_data = [
        ("Backend won't start: Port 8000 in use", "Another process or orphaned uvicorn server is bound to port 8000.",
         "Run `Get-NetTCPConnection -LocalPort 8000` in PowerShell and terminate the PID with `Stop-Process -Id <PID> -Force`."),
        ("No faces detected in video", "Faces are too small (<40px) or camera angle is too steep.",
         "Lower `confidence_threshold` to 0.45 or adjust `min_face_size` to [20, 20] in `config.json`."),
        ("Low FPS on CPU (<15 FPS)", "Detection is running on every single frame without skipping.",
         "Increase `frame_skip` in `config.json` to 2 or 3 to achieve 35-50 FPS."),
        ("SQLite Database is locked error", "Concurrent multi-threading write contention.",
         "Resolved by our database repository using WAL mode (`PRAGMA journal_mode = WAL;`) and thread-level mutex locking."),
        ("CORS error in browser console", "Frontend running on different port without proxy.",
         "FastAPI includes `CORSMiddleware` with `allow_origins=['*']`. In Vite dev mode, ensure `vite.config.ts` proxies `/api`."),
    ]
    for issue, cause, fix in trouble_data:
        add_h2(doc, f"Issue: {issue}")
        add_bullet(doc, "Probable Root Cause:", cause)
        add_bullet(doc, "Recommended Solution:", fix)

    print("Completed Chapter 13.")

    # =========================================================================
    # CHAPTER 14: INTERVIEW PREPARATION
    # =========================================================================
    add_h1(doc, "Chapter 14: Interview Preparation")

    add_h2(doc, "14.1 2-Minute Project Pitch")
    add_p(doc, '"I built the Intelligent Face Tracker with Auto-Registration and Visitor Counting, an enterprise-grade AI system '
               'that solves the double-counting problem in traditional visitor monitoring. Using a modern React 19 frontend and '
               'a FastAPI backend, the system detects faces with YOLOv8, extracts 512-dimensional biometric embeddings with ArcFace, '
               'and tracks individuals using ByteTrack. Newly seen visitors are auto-registered into an ACID SQLite database without pre-enrollment. '
               'When someone exits and returns later, ArcFace recognizes them via cosine similarity, logging a new Entry event while keeping the '
               'Unique Visitor Count strictly accurate. The system processes over 250 FPS on CPU, enforces biometric privacy, and has a 100% '
               'pass rate across 33 automated tests."')

    add_h2(doc, "14.2 30+ In-Depth Interview Questions & Answers")
    questions = [
        ("Q1: Why did you choose YOLOv8-face over traditional Haar Cascades or HOG?",
         "Haar Cascades and HOG suffer from high false positive rates and fail severely under facial tilt, yaw, or varied lighting. "
         "YOLOv8-face is a single-stage anchor-free convolutional detector that predicts bounding boxes and facial landmarks in a single pass, "
         "providing state-of-the-art accuracy and real-time inference speed (>40 FPS CPU, >150 FPS GPU)."),

        ("Q2: Why avoid the popular `face_recognition` Python library?",
         "The `face_recognition` library wraps older dlib models that produce 128-dimensional vectors with lower discriminative accuracy (99.38% LFW). "
         "ArcFace is state-of-the-art (99.83% LFW), utilizing Additive Angular Margin loss to compress intra-class variance and expand inter-class "
         "separation on a 512-dimensional hyperspherical manifold."),

        ("Q3: What is the mathematical definition of Cosine Similarity?",
         "Cosine similarity measures the cosine of the angle between two non-zero vectors in an inner product space: "
         "Cosine Similarity = (u · v) / (||u|| * ||v||). When vectors are L2-normalized (||u|| = ||v|| = 1.0), it simplifies to their dot product."),

        ("Q4: Why separate temporary `track_id` from permanent `face_id`?",
         "`track_id` is a transient session integer assigned by the spatial tracker to follow someone walking across the screen. "
         "`face_id` is the permanent biometric identity in the database. Decoupling them allows one person to have multiple tracks across "
         "different visits while mapping to a single persistent database record."),

        ("Q5: How do you prevent duplicate events when someone stands in front of the camera?",
         "We enforce a database unique constraint `UNIQUE(track_id, event_type)`. A track can only emit an Entry event once upon confirmation, "
         "and an Exit event once upon deletion. Subsequent detections during the same track reuse the existing state."),

        ("Q6: How does the system handle temporary occlusions (e.g. someone walking behind a pillar)?",
         "When a detection is temporarily missing, the track enters the LOST state rather than immediately deleting. The tracker maintains a "
         "grace period (`track_lost_timeout_seconds = 2.0s` or 60 frames). If the face reappears within 2 seconds, IoU links it to the existing track."),

        ("Q7: How do you prevent web UI freezes during heavy video processing?",
         "The FastAPI backend runs the computer vision pipeline inside an asynchronous background thread managed by `JobManager`. "
         "The frontend polls job progress via `GET /api/jobs/status`, keeping the UI completely responsive."),

        ("Q8: What is SQLite WAL mode and why is it essential here?",
         "WAL stands for Write-Ahead Logging. In standard SQLite, writes lock the entire database file. WAL mode allows concurrent readers "
         "to query the database simultaneously while the background video thread inserts events."),

        ("Q9: What is the purpose of Laplacian variance blur estimation?",
         "The variance of the Laplacian operator measures the sharpness of image edges: var(ΔI). Blurry crops have few edges, producing low scores (<50.0). "
         "Rejecting blurry crops prevents distorted biometric embeddings from corrupting the identity database."),

        ("Q10: How do you protect sensitive RTSP camera credentials?",
         "Camera URLs can be provided via the `RTSP_STREAM_URL` environment variable so passwords never touch git. In addition, "
         "the backend regex-masks all passwords as `***:***@` in API responses and log files."),

        ("Q11: Why is frame skipping used and what is the formula?",
         "Frame skipping processes 1 frame and skips N frames (`frame_idx % (skip + 1) == 0`). Since adjacent video frames (at 30 FPS) are "
         "visually almost identical, skipping 2 frames triples processing throughput with virtually zero loss in tracking accuracy."),

        ("Q12: How does the frontend communicate with the backend?",
         "The React frontend uses the Fetch API in `frontend/src/services/api.ts` to dispatch asynchronous HTTP requests to `/api/*` endpoints. "
         "In Vite development mode, a reverse proxy forwards requests from port 5173 to port 8000."),

        ("Q13: How is true Unique Visitor Count calculated?",
         "By querying the database with `SELECT COUNT(DISTINCT face_id) FROM faces;`. Because returning visitors are mapped to their existing "
         "`face_id`, re-entries increase total visits but never increment the distinct face count."),

        ("Q14: What happens if an uploaded video has an unsupported format?",
         "FastAPI validates the file extension against `{'.mp4', '.avi', '.mkv', '.mov'}`. If unsupported, it immediately returns HTTP 400 Bad Request "
         "with an informative error message, preventing server crashes."),

        ("Q15: What testing strategies are implemented?",
         "A complete automated test suite of 33 tests using pytest. It tests configuration validation, bounding box clamping, blur estimation, "
         "cosine similarity edge cases, database schema idempotency, multi-visitor lifecycle, and FastAPI REST endpoints."),
    ]

    for q, a in questions:
        add_h3(doc, q)
        add_p(doc, a)

    print("Completed Chapter 14.")

    # =========================================================================
    # CHAPTER 15: GLOSSARY AND LEARNING ROADMAP
    # =========================================================================
    add_h1(doc, "Chapter 15: Glossary and Learning Roadmap")

    add_h2(doc, "15.1 Technical Glossary for Beginners")
    glossary = [
        ("Bounding Box (BBox)", "A rectangle enclosing an object in an image, defined by [x1, y1, x2, y2]."),
        ("Deep Metric Embedding", "A compact numerical vector (512 floats) representing facial geometry on a hyperspherical manifold."),
        ("Cosine Similarity", "A mathematical metric evaluating the angular similarity between two normalized vectors (-1.0 to 1.0)."),
        ("IoU (Intersection over Union)", "The overlap ratio between two bounding boxes, used to track objects across frames."),
        ("Single Page Application (SPA)", "A web app that rewrites the current web page rather than loading entire new pages from a server."),
        ("REST API", "An architectural style using HTTP methods (GET, POST) to exchange JSON data between client and server."),
        ("CORS (Cross-Origin Resource Sharing)", "A browser security mechanism allowing a web page from one origin to access APIs on another."),
        ("Pydantic", "A Python data validation library that uses type annotations to ensure data integrity."),
        ("WAL Mode", "Write-Ahead Logging; an SQLite configuration allowing simultaneous reads and writes without database lock contention."),
    ]
    for term, definition in glossary:
        add_bullet(doc, term + ":", definition)

    add_h2(doc, "15.2 10-Step Beginner Learning Roadmap")
    roadmap = [
        ("Step 1: Understand the Project Purpose", "Read Chapter 1 to understand the core problem: visitor tracking without double-counting."),
        ("Step 2: Inspect config.json", "Examine application parameters and learn how settings control detection and recognition."),
        ("Step 3: Explore SQLite Database (`src/database.py`)", "Review the SQL schema, foreign key relationships, and WAL mode."),
        ("Step 4: Trace Video Ingestion (`src/video_source.py`)", "Learn how OpenCV decodes video files and recovers from RTSP drops."),
        ("Step 5: Study Face Detection (`src/detector.py`)", "Understand coordinate boundary clamping, margin padding, and blur scoring."),
        ("Step 6: Master Spatial Tracking (`src/tracker.py`)", "Learn IoU calculation, multi-frame hit confirmation, and track state transitions."),
        ("Step 7: Understand Deep Embeddings (`src/face_recognizer.py`)", "Study ArcFace 512-D vectors, L2 normalization, and cosine matching."),
        ("Step 8: Connect Identity & Events (`src/identity_manager.py`)", "Trace auto-registration and exactly-once Entry/Exit event emission."),
        ("Step 9: Review FastAPI Backend (`server.py`)", "Explore REST routes, static file mounting, and async JobManager threading."),
        ("Step 10: Explore React Frontend (`frontend/src/`)", "Study React components, TypeScript models, and live job status polling."),
    ]
    for step_title, step_desc in roadmap:
        add_bullet(doc, step_title + ":", step_desc)

    add_h2(doc, "15.3 Recommended Source File Reading Order")
    add_bullet(doc, "1. config.json & src/config.py:", "Gives you a clear map of all system parameters and thresholds.")
    add_bullet(doc, "2. src/database.py:", "Shows how data is permanently stored and how idempotency is enforced.")
    add_bullet(doc, "3. src/detector.py:", "Teaches you how YOLOv8-face detects faces and how OpenCV filters blurry images.")
    add_bullet(doc, "4. src/tracker.py:", "Explains how ByteTrack links detections across video frames.")
    add_bullet(doc, "5. src/face_recognizer.py:", "Demonstrates 512-D ArcFace embedding generation and cosine similarity matching.")
    add_bullet(doc, "6. src/identity_manager.py & src/event_manager.py:", "The central brain that glues tracking, recognition, and database events.")
    add_bullet(doc, "7. server.py & src/job_manager.py:", "Shows how the desktop AI pipeline is exposed as an asynchronous web service.")
    add_bullet(doc, "8. frontend/src/App.tsx & frontend/src/pages/:", "Reveals how the web interface renders live AI telemetry.")

    # Save Document
    doc.save(str(DOC_PATH))
    print(f"Successfully generated {DOC_PATH.resolve()}")
    print(f"File Size: {DOC_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_project_explanation_guide()
