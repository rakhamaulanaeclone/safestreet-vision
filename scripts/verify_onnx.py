"""
Compare PyTorch and ONNX predictions on the same image.

Run from the project root after ONNX export:
    python scripts/verify_onnx.py --image datasets/merged/images/test/example.jpg
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PT = ROOT / "runs" / "safestreet_v1_2" / "weights" / "best.pt"
DEFAULT_ONNX = ROOT / "runs" / "safestreet_v1_2" / "weights" / "best.onnx"
DEFAULT_TEST_IMAGES = ROOT / "datasets" / "merged" / "images" / "test"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify ONNX inference against PyTorch")
    parser.add_argument("--pt", type=Path, default=DEFAULT_PT, help="Path to PyTorch .pt weights")
    parser.add_argument("--onnx", type=Path, default=DEFAULT_ONNX, help="Path to ONNX model")
    parser.add_argument("--image", type=Path, default=None, help="Image used for comparison")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.7, help="NMS IoU threshold")
    parser.add_argument("--pt-device", default="0", help="Device for PyTorch inference")
    parser.add_argument("--onnx-device", default="cpu", help="Device for ONNX Runtime inference")
    parser.add_argument("--output", type=Path, default=None, help="Output directory")
    return parser.parse_args()


def default_image() -> Path:
    if not DEFAULT_TEST_IMAGES.exists():
        raise FileNotFoundError(f"Test image directory not found: {DEFAULT_TEST_IMAGES}")
    images = sorted(p for p in DEFAULT_TEST_IMAGES.iterdir() if p.suffix.lower() in IMG_EXTS)
    if not images:
        raise FileNotFoundError(f"No test images found in: {DEFAULT_TEST_IMAGES}")
    return images[0]


def predict(model_path: Path, image: Path, args: argparse.Namespace, device: str) -> Any:
    model = YOLO(str(model_path))
    return model.predict(
        str(image),
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=device,
        verbose=False,
    )[0]


def detections(result: Any) -> list[dict[str, Any]]:
    names = result.names
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return []

    rows = []
    for box in boxes:
        cls_id = int(box.cls[0])
        rows.append({
            "class_id": cls_id,
            "class_name": names.get(cls_id, str(cls_id)),
            "confidence": float(box.conf[0]),
            "xyxy": [float(v) for v in box.xyxy[0].tolist()],
        })
    return sorted(rows, key=lambda row: row["confidence"], reverse=True)


def compare(pt_rows: list[dict[str, Any]], onnx_rows: list[dict[str, Any]]) -> dict[str, Any]:
    paired = min(len(pt_rows), len(onnx_rows))
    class_matches = 0
    max_conf_delta = 0.0
    max_box_delta = 0.0

    for i in range(paired):
        pt = pt_rows[i]
        ox = onnx_rows[i]
        if pt["class_id"] == ox["class_id"]:
            class_matches += 1
        max_conf_delta = max(max_conf_delta, abs(pt["confidence"] - ox["confidence"]))
        max_box_delta = max(
            max_box_delta,
            max(abs(a - b) for a, b in zip(pt["xyxy"], ox["xyxy"])),
        )

    return {
        "pt_count": len(pt_rows),
        "onnx_count": len(onnx_rows),
        "paired": paired,
        "top_class_matches": class_matches,
        "max_confidence_delta": max_conf_delta,
        "max_box_pixel_delta": max_box_delta,
        "coarse_match": len(pt_rows) == len(onnx_rows) and class_matches == paired,
    }


def save_plot(result: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plotted = result.plot()
    cv2.imwrite(str(path), plotted)


def main() -> None:
    args = parse_args()
    pt_path = args.pt.resolve()
    onnx_path = args.onnx.resolve()
    image_path = args.image.resolve() if args.image else default_image().resolve()

    for path in [pt_path, onnx_path, image_path]:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output.resolve() if args.output else ROOT / "runs" / f"onnx_verification_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    pt_result = predict(pt_path, image_path, args, args.pt_device)
    onnx_result = predict(onnx_path, image_path, args, args.onnx_device)

    pt_rows = detections(pt_result)
    onnx_rows = detections(onnx_result)
    comparison = compare(pt_rows, onnx_rows)

    save_plot(pt_result, output_dir / "pt_prediction.jpg")
    save_plot(onnx_result, output_dir / "onnx_prediction.jpg")

    report = {
        "image": str(image_path),
        "pt_model": str(pt_path),
        "onnx_model": str(onnx_path),
        "comparison": comparison,
        "pt_detections": pt_rows,
        "onnx_detections": onnx_rows,
    }
    report_path = output_dir / "comparison.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(comparison, indent=2))
    print(f"Saved verification report: {report_path}")


if __name__ == "__main__":
    main()
