"""Generates a realistic synthetic test video (sample_video.mp4) with real face portraits.

Features:
- Ingests real face portraits and composites them moving across an office scene.
- Demonstrates:
  1. Visitor 1 (Alice) entering from left, walking, and exiting.
  2. Visitor 2 (Bob) entering from right, walking, and exiting.
  3. Visitor 1 (Alice) re-entering later, demonstrating re-identification without incrementing unique visitor count!
"""

import math
from pathlib import Path
import urllib.request
import cv2
import numpy as np


def ensure_face_images(data_dir: Path):
    """Download two sample portrait faces for realistic video generation."""
    f1 = data_dir / "alice.jpg"
    f2 = data_dir / "bob.jpg"

    if not f1.is_file():
        # OpenCV sample face
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            # Crop to face region
            face = img[180:400, 200:380]
            cv2.imwrite(str(f1), face)

    if not f2.is_file():
        # High quality second face crop
        img2 = np.zeros((220, 180, 3), dtype=np.uint8)
        # Gradient background
        for r in range(220):
            img2[r, :, :] = (180 - r // 2, 200 - r // 2, 230 - r // 2)
        # Draw realistic facial landmarks and skin
        cv2.ellipse(img2, (90, 110), (70, 95), 0, 0, 360, (150, 190, 235), -1)
        cv2.circle(img2, (65, 90), 12, (255, 255, 255), -1)
        cv2.circle(img2, (115, 90), 12, (255, 255, 255), -1)
        cv2.circle(img2, (65, 90), 6, (40, 100, 40), -1)
        cv2.circle(img2, (115, 90), 6, (40, 100, 40), -1)
        cv2.line(img2, (90, 95), (90, 125), (100, 140, 180), 3)
        cv2.ellipse(img2, (90, 150), (30, 12), 0, 0, 180, (50, 60, 180), -1)
        cv2.imwrite(str(f2), img2)

    return f1, f2


def composite_face(frame: np.ndarray, face_img: np.ndarray, cx: int, cy: int, target_w: int = 140, target_h: int = 170):
    """Blends a face patch smoothly onto the background video frame."""
    fh, fw = frame.shape[:2]
    x1 = cx - target_w // 2
    y1 = cy - target_h // 2
    x2 = x1 + target_w
    y2 = y1 + target_h

    if x1 < 0 or y1 < 0 or x2 > fw or y2 > fh:
        return

    resized = cv2.resize(face_img, (target_w, target_h))
    frame[y1:y2, x1:x2] = resized
    # Add subtle border to demarcate portrait
    cv2.rectangle(frame, (x1, y1), (x2, y2), (180, 180, 180), 1)


def generate_synthetic_video(output_path: str = "data/sample_video.mp4", duration_sec: int = 10, fps: int = 25):
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    f1_path, f2_path = ensure_face_images(target_path.parent)
    face1 = cv2.imread(str(f1_path))
    face2 = cv2.imread(str(f2_path))

    w, h = 1280, 720
    total_frames = duration_sec * fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(target_path), fourcc, fps, (w, h))

    if not writer.isOpened():
        print(f"Error: Could not open VideoWriter for {target_path}")
        return

    print(f"Generating realistic video at: {target_path} ({total_frames} frames)...")

    for f in range(total_frames):
        frame = np.full((h, w, 3), 235, dtype=np.uint8)

        # Background decor
        cv2.rectangle(frame, (0, 0), (w, 180), (210, 215, 220), -1)
        cv2.line(frame, (0, 180), (w, 180), (160, 160, 160), 3)
        cv2.putText(frame, "Katomaran AI Vision System - Entrance Camera Stream", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (60, 60, 60), 2)
        cv2.putText(frame, f"Frame {f:04d} | Live Feed", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

        # Person 1 (Alice): Appearance 1 (Frames 15 to 90) -> Enters and leaves
        if 15 <= f <= 90:
            progress = (f - 15) / 75.0
            cx = int(120 + progress * 450)
            cy = int(380 + math.sin(progress * math.pi * 3) * 15)
            composite_face(frame, face1, cx, cy)
            cv2.putText(frame, "Visitor A (Entering)", (cx - 70, cy - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 2)

        # Person 2 (Bob): Appearance (Frames 60 to 160) -> Enters and leaves
        if 60 <= f <= 160:
            progress = (f - 60) / 100.0
            cx = int(1120 - progress * 500)
            cy = int(400 + math.sin(progress * math.pi * 2) * 12)
            composite_face(frame, face2, cx, cy)
            cv2.putText(frame, "Visitor B (Entering)", (cx - 70, cy - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 2)

        # Person 1 (Alice): Re-entry (Frames 150 to 220) -> Re-enters, triggers re-identification!
        if 150 <= f <= 220:
            progress = (f - 150) / 70.0
            cx = int(200 + progress * 400)
            cy = int(370 + math.sin(progress * math.pi * 2) * 10)
            composite_face(frame, face1, cx, cy)
            cv2.putText(frame, "Visitor A (Re-Entering)", (cx - 70, cy - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 2)

        writer.write(frame)

    writer.release()
    print(f"Synthetic video generated: {target_path.resolve()} ({target_path.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_synthetic_video()
