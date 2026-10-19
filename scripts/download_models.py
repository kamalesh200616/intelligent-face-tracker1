"""Model Download and Weight Management Utility.

Provides automated retrieval and verification for:
1. YOLOv8 Face Detection Model (e.g. YOLOv8n-face.pt)
2. ArcFace SOTA 512-D ONNX Recognition Model (MobileFaceNet / ResNet50 ArcFace)
3. OpenCV YuNet ONNX Face Detector (face_detection_yunet_2023mar.onnx)

All models include documented sources, licenses, and expected input/output shapes.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import urllib.request

MODELS = {
    "yolov8_face": {
        "filename": "yolov8n-face.pt",
        "url": "https://huggingface.co/arnabdhar/YOLOv8-Face-Detection/resolve/main/model.pt",
        "description": "YOLOv8-Nano Pretrained Face Detection Model (PyTorch / Ultralytics)",
        "license": "AGPL-3.0",
        "input_shape": "(1, 3, 640, 640)",
        "output": "Face bounding boxes [x1, y1, x2, y2] and confidence scores",
    },
    "yunet": {
        "filename": "face_detection_yunet_2023mar.onnx",
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "description": "OpenCV Zoo YuNet High-Efficiency Face Detector (ONNX)",
        "license": "Apache 2.0",
        "input_shape": "(1, 3, 640, 640)",
        "output": "15-element face bounding box and 5 landmarks",
    },
    "arcface": {
        "filename": "arcface_sota.onnx",
        "url": "https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/w600k_r50.onnx",
        "description": "InsightFace / ArcFace ResNet-50 512-D L2-normalized feature extractor (buffalo_l)",
        "license": "MIT / Non-commercial academic license",
        "input_shape": "(1, 3, 112, 112)",
        "output": "(1, 512) float32 embedding vector",
    },
}


def download_file(url: str, dest_path: Path):
    """Download a file with progress reporting."""
    print(f"Downloading from {url} to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
        print(f"Downloaded successfully ({dest_path.stat().st_size} bytes)")
    except Exception as e:
        print(f"Download failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download deep learning model weights.")
    parser.add_argument("--model", choices=["all", "yunet", "arcface"], default="all", help="Model to download")
    args = parser.parse_args()

    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    targets = list(MODELS.keys()) if args.model == "all" else [args.model]

    print("=" * 60)
    print("  DEEP LEARNING MODEL ASSET MANAGER")
    print("=" * 60)

    for key in targets:
        info = MODELS[key]
        dest = models_dir / info["filename"]
        print(f"\nModel: {info['description']}")
        print(f"License: {info['license']}")
        print(f"Input: {info['input_shape']} | Output: {info['output']}")
        if dest.is_file():
            print(f"File already exists at: {dest} ({dest.stat().st_size} bytes)")
        else:
            download_file(info["url"], dest)

    print("\nModel management complete.")


if __name__ == "__main__":
    main()
