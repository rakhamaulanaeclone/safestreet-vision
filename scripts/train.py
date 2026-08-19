"""
train.py — SafeStreet Vision
=============================
Training YOLOv8 untuk deteksi kerusakan jalan + helm motor.

Jalankan dari ROOT proyek:
    python scripts/train.py
"""

from ultralytics import YOLO
from pathlib import Path

def main():
    ROOT  = Path(__file__).parent.parent
    DATA  = ROOT / "datasets" / "merged" / "data.yaml"
    RUNS  = ROOT / "runs"

    model = YOLO("yolov8s.pt")

    model.train(
        data        = str(DATA),
        epochs      = 100,
        imgsz       = 640,
        batch       = 16,
        device      = 0,
        project     = str(RUNS),
        name        = "safestreet_v1_2",
        patience    = 20,
        save        = True,
        save_period = 10,
        val         = True,
        plots       = True,
        workers     = 4,
    )

if __name__ == "__main__":
    main()