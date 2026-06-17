from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "runs" / "safestreet_v1_2" / "weights" / "best.pt"

CLASS_NAMES = [
    "pothole",
    "crack",
    "manhole",
    "speed_bump",
    "vehicle_small",
    "vehicle_large",
    "pedestrian",
    "with_helmet",
    "without_helmet",
]


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _device() -> str:
    value = os.getenv("SAFESTREET_DEVICE", "auto").strip().lower()
    if value == "auto":
        return "0" if torch.cuda.is_available() else "cpu"
    return value


@dataclass(frozen=True)
class Settings:
    app_name: str
    model_path: Path
    device: str
    imgsz: int
    conf: float
    iou: float
    max_upload_mb: int
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_origins = os.getenv("SAFESTREET_CORS_ORIGINS", "*")
    cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    return Settings(
        app_name="SafeStreet Vision API",
        model_path=Path(os.getenv("SAFESTREET_MODEL_PATH", str(DEFAULT_MODEL_PATH))).resolve(),
        device=_device(),
        imgsz=_int_env("SAFESTREET_IMGSZ", 640),
        conf=_float_env("SAFESTREET_CONF", 0.25),
        iou=_float_env("SAFESTREET_IOU", 0.7),
        max_upload_mb=_int_env("SAFESTREET_MAX_UPLOAD_MB", 15),
        cors_origins=cors_origins,
    )
