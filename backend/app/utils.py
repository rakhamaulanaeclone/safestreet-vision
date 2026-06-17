from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def decode_image(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("Uploaded file is empty")

    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a valid image")
    return image


def image_size(image: np.ndarray) -> dict[str, int]:
    height, width = image.shape[:2]
    return {"width": int(width), "height": int(height)}


def ensure_within_upload_limit(image_bytes: bytes, max_upload_mb: int) -> None:
    max_bytes = max_upload_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise ValueError(f"Uploaded file exceeds {max_upload_mb} MB")


def relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)
