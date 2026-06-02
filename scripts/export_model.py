"""
Export SafeStreet Vision YOLO weights to ONNX.

Run from the project root:
    python scripts/export_model.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = ROOT / "runs" / "safestreet_v1_2" / "weights" / "best.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export SafeStreet Vision model")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Path to .pt weights")
    parser.add_argument("--imgsz", type=int, default=640, help="Export image size")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset")
    parser.add_argument("--device", default="0", help="Device for export, for example 0 or cpu")
    parser.add_argument("--dynamic", action="store_true", help="Export with dynamic input shapes")
    parser.add_argument("--simplify", action="store_true", help="Simplify the exported ONNX graph")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model.resolve()

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = YOLO(str(model_path))
    exported = model.export(
        format="onnx",
        imgsz=args.imgsz,
        opset=args.opset,
        device=args.device,
        dynamic=args.dynamic,
        simplify=args.simplify,
    )

    onnx_path = Path(exported).resolve()
    if not onnx_path.exists():
        raise FileNotFoundError(f"ONNX export did not create expected file: {onnx_path}")

    print(f"Exported ONNX: {onnx_path}")


if __name__ == "__main__":
    main()
