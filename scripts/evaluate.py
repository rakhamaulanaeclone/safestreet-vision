"""
Evaluate SafeStreet Vision YOLO weights.

Run from the project root:
    python scripts/evaluate.py
    python scripts/evaluate.py --split test
    python scripts/evaluate.py --split all --save-predictions
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import yaml
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = ROOT / "runs" / "safestreet_v1_2" / "weights" / "best.pt"
DEFAULT_DATA = ROOT / "datasets" / "merged" / "data.yaml"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SafeStreet Vision model evaluation")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Path to .pt model")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Path to YOLO data.yaml")
    parser.add_argument(
        "--split",
        choices=["val", "test", "all"],
        default="val",
        help="Dataset split to evaluate",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Validation image size")
    parser.add_argument(
        "--val-conf",
        type=float,
        default=None,
        help="Validation confidence. Leave unset to use Ultralytics mAP default.",
    )
    parser.add_argument("--pred-conf", type=float, default=0.25, help="Confidence for sample images")
    parser.add_argument("--iou", type=float, default=0.7, help="NMS IoU threshold")
    parser.add_argument("--device", default=None, help="Device, for example 0 or cpu")
    parser.add_argument("--output", type=Path, default=None, help="Output directory")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=16,
        help="Number of prediction samples to save per split",
    )
    parser.add_argument(
        "--save-predictions",
        action="store_true",
        help="Save predictions for every image in the evaluated split",
    )
    parser.add_argument("--seed", type=int, default=42, help="Sampling seed")
    return parser.parse_args()


def read_data_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"data.yaml not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid data.yaml: {path}")
    return data


def class_names(data: dict[str, Any]) -> list[str]:
    names = data.get("names")
    if isinstance(names, dict):
        return [str(names[i]) for i in sorted(names)]
    if isinstance(names, list):
        return [str(name) for name in names]
    raise ValueError("data.yaml must define names as a list or dict")


def dataset_root(data_yaml: Path, data: dict[str, Any]) -> Path:
    raw = data.get("path", data_yaml.parent)
    root = Path(raw)
    if root.is_absolute():
        return root

    candidates = [
        (data_yaml.parent / root).resolve(),
        (ROOT / root).resolve(),
        (Path.cwd() / root).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def split_image_dir(data_yaml: Path, data: dict[str, Any], split: str) -> Path:
    value = data.get(split)
    if value is None:
        raise ValueError(f"data.yaml has no '{split}' split")
    if isinstance(value, list):
        raise ValueError(f"Split '{split}' is a list; this script expects one image directory")

    path = Path(str(value))
    if path.is_absolute():
        return path
    return dataset_root(data_yaml, data) / path


def split_label_dir(image_dir: Path, data_yaml: Path, data: dict[str, Any], split: str) -> Path:
    parts = list(image_dir.parts)
    if "images" in parts:
        idx = len(parts) - 1 - parts[::-1].index("images")
        parts[idx] = "labels"
        return Path(*parts)
    return dataset_root(data_yaml, data) / "labels" / split


def image_files(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")
    return sorted(p for p in image_dir.iterdir() if p.suffix.lower() in IMG_EXTS)


def label_stats(label_dir: Path, names: list[str]) -> dict[int, dict[str, int]]:
    stats = {i: {"instances": 0, "images": 0} for i in range(len(names))}
    if not label_dir.exists():
        return stats

    for label_path in sorted(label_dir.glob("*.txt")):
        seen_in_image: set[int] = set()
        with label_path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                try:
                    cls_id = int(parts[0])
                except ValueError:
                    continue
                if cls_id not in stats:
                    continue
                stats[cls_id]["instances"] += 1
                seen_in_image.add(cls_id)

        for cls_id in seen_in_image:
            stats[cls_id]["images"] += 1
    return stats


def metric_array(box_metrics: Any, attr: str) -> list[float]:
    values = getattr(box_metrics, attr, [])
    if values is None:
        return []
    return [float(v) for v in values]


def ap_class_index(box_metrics: Any, size: int) -> list[int]:
    values = getattr(box_metrics, "ap_class_index", None)
    if values is None:
        return list(range(size))
    return [int(v) for v in values]


def extract_metrics(results: Any, names: list[str], stats: dict[int, dict[str, int]]) -> dict[str, Any]:
    box = results.box
    precision = metric_array(box, "p")
    recall = metric_array(box, "r")
    ap50 = metric_array(box, "ap50")
    ap = metric_array(box, "ap")
    indices = ap_class_index(box, len(ap50))

    per_class = {
        i: {
            "class_id": i,
            "class_name": names[i],
            "images": stats[i]["images"],
            "instances": stats[i]["instances"],
            "precision": 0.0,
            "recall": 0.0,
            "map50": 0.0,
            "map50_95": 0.0,
        }
        for i in range(len(names))
    }

    for pos, cls_id in enumerate(indices):
        if cls_id not in per_class:
            continue
        per_class[cls_id]["precision"] = precision[pos] if pos < len(precision) else 0.0
        per_class[cls_id]["recall"] = recall[pos] if pos < len(recall) else 0.0
        per_class[cls_id]["map50"] = ap50[pos] if pos < len(ap50) else 0.0
        per_class[cls_id]["map50_95"] = ap[pos] if pos < len(ap) else 0.0

    return {
        "overall": {
            "precision": float(box.mp),
            "recall": float(box.mr),
            "map50": float(box.map50),
            "map50_95": float(box.map),
        },
        "speed_ms": {k: float(v) for k, v in results.speed.items()},
        "per_class": list(per_class.values()),
    }


def validation_kwargs(args: argparse.Namespace, split: str, output_dir: Path) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "data": str(args.data),
        "split": split,
        "imgsz": args.imgsz,
        "iou": args.iou,
        "plots": True,
        "verbose": True,
        "project": str(output_dir),
        "name": split,
        "exist_ok": True,
    }
    if args.val_conf is not None:
        kwargs["conf"] = args.val_conf
    if args.device is not None:
        kwargs["device"] = args.device
    return kwargs


def save_metrics_files(metrics: dict[str, Any], split_dir: Path, split: str) -> None:
    json_path = split_dir / "metrics.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    csv_path = split_dir / "per_class_metrics.csv"
    rows = metrics["per_class"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = split_dir / "summary.md"
    overall = metrics["overall"]
    lines = [
        f"# SafeStreet Vision Evaluation - {split}",
        "",
        "## Overall",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Precision | {overall['precision']:.4f} |",
        f"| Recall | {overall['recall']:.4f} |",
        f"| mAP@50 | {overall['map50']:.4f} |",
        f"| mAP@50-95 | {overall['map50_95']:.4f} |",
        "",
        "## Per Class",
        "",
        "| Class | Images | Instances | Precision | Recall | mAP@50 | mAP@50-95 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {class_name} | {images} | {instances} | {precision:.4f} | "
            "{recall:.4f} | {map50:.4f} | {map50_95:.4f} |".format(**row)
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_confusion_matrix(results: Any, split_dir: Path, names: list[str]) -> None:
    matrix_obj = getattr(results, "confusion_matrix", None)
    matrix = getattr(matrix_obj, "matrix", None)
    if matrix is None:
        return

    labels = names + ["background"]
    csv_path = split_dir / "confusion_matrix_raw.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["predicted\\true", *labels[: matrix.shape[1]]])
        for idx, row in enumerate(matrix):
            label = labels[idx] if idx < len(labels) else str(idx)
            writer.writerow([label, *[float(v) for v in row]])


def save_prediction_samples(
    model: YOLO,
    args: argparse.Namespace,
    split_dir: Path,
    split: str,
    image_dir: Path,
) -> None:
    files = image_files(image_dir)
    if not files:
        return

    if args.save_predictions:
        selected = files
    else:
        rng = random.Random(args.seed)
        selected = rng.sample(files, min(args.num_samples, len(files)))

    pred_dir = split_dir / "prediction_samples"
    pred_dir.mkdir(parents=True, exist_ok=True)

    predict_kwargs: dict[str, Any] = {
        "imgsz": args.imgsz,
        "conf": args.pred_conf,
        "iou": args.iou,
        "verbose": False,
    }
    if args.device is not None:
        predict_kwargs["device"] = args.device

    index_rows = []
    for image_path in selected:
        result = model.predict(str(image_path), **predict_kwargs)[0]
        plotted = result.plot()
        out_path = pred_dir / image_path.name
        cv2.imwrite(str(out_path), plotted)
        index_rows.append({"source": str(image_path), "prediction": str(out_path)})

    index_path = pred_dir / "index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "prediction"])
        writer.writeheader()
        writer.writerows(index_rows)


def evaluate_split(
    model: YOLO,
    args: argparse.Namespace,
    data: dict[str, Any],
    names: list[str],
    split: str,
    output_dir: Path,
) -> dict[str, Any]:
    split_dir = output_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)

    image_dir = split_image_dir(args.data, data, split)
    label_dir = split_label_dir(image_dir, args.data, data, split)
    stats = label_stats(label_dir, names)

    results = model.val(**validation_kwargs(args, split, output_dir))
    metrics = extract_metrics(results, names, stats)
    metrics["config"] = {
        "model": str(args.model),
        "data": str(args.data),
        "split": split,
        "image_dir": str(image_dir),
        "label_dir": str(label_dir),
        "imgsz": args.imgsz,
        "val_conf": args.val_conf,
        "pred_conf": args.pred_conf,
        "iou": args.iou,
        "device": args.device,
    }

    save_metrics_files(metrics, split_dir, split)
    save_confusion_matrix(results, split_dir, names)
    save_prediction_samples(model, args, split_dir, split, image_dir)
    return metrics


def save_combined_summary(all_metrics: dict[str, dict[str, Any]], output_dir: Path) -> None:
    path = output_dir / "summary.md"
    lines = [
        "# SafeStreet Vision Evaluation Summary",
        "",
        "| Split | Precision | Recall | mAP@50 | mAP@50-95 |",
        "|---|---:|---:|---:|---:|",
    ]
    for split, metrics in all_metrics.items():
        overall = metrics["overall"]
        lines.append(
            f"| {split} | {overall['precision']:.4f} | {overall['recall']:.4f} | "
            f"{overall['map50']:.4f} | {overall['map50_95']:.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.model = args.model.resolve()
    args.data = args.data.resolve()

    if not args.model.exists():
        raise FileNotFoundError(f"Model not found: {args.model}")

    data = read_data_yaml(args.data)
    names = class_names(data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output.resolve() if args.output else ROOT / "runs" / f"evaluation_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Model : {args.model}")
    print(f"Data  : {args.data}")
    print(f"Output: {output_dir}")

    model = YOLO(str(args.model))
    splits = ["val", "test"] if args.split == "all" else [args.split]

    all_metrics: dict[str, dict[str, Any]] = {}
    for split in splits:
        print(f"\nEvaluating split: {split}")
        all_metrics[split] = evaluate_split(model, args, data, names, split, output_dir)

    save_combined_summary(all_metrics, output_dir)
    print(f"\nDone. Reports saved to: {output_dir}")


if __name__ == "__main__":
    main()
