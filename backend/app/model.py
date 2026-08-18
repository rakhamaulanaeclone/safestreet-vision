from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from .config import CLASS_NAMES, PROJECT_ROOT, Settings
from .schemas import Box, Detection, ImageSize, ModelInfoResponse, PredictionResponse
from .utils import image_size, relative_to_project


class SafeStreetDetector:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: YOLO | None = None
        self._names: list[str] = CLASS_NAMES

    @property
    def model_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_exists(self) -> bool:
        return self.settings.model_path.exists()

    def load(self) -> YOLO:
        if self._model is not None:
            return self._model

        if not self.model_exists:
            raise FileNotFoundError(f"Model weights not found: {self.settings.model_path}")

        self._model = YOLO(str(self.settings.model_path))
        names = self._model.names
        if isinstance(names, dict):
            self._names = [str(names[i]) for i in sorted(names)]
        elif isinstance(names, list):
            self._names = [str(name) for name in names]
        return self._model

    def model_info(self) -> ModelInfoResponse:
        if self.model_exists and not self.model_loaded:
            self.load()

        return ModelInfoResponse(
            model_path=relative_to_project(Path(self.settings.model_path), PROJECT_ROOT),
            model_exists=self.model_exists,
            model_loaded=self.model_loaded,
            device=self.settings.device,
            imgsz=self.settings.imgsz,
            conf=self.settings.conf,
            iou=self.settings.iou,
            class_count=len(self._names),
            class_names=self._names,
        )

    def predict(self, image: np.ndarray) -> PredictionResponse:
        model = self.load()
        started = time.perf_counter()
        result = model.predict(
            source=image,
            imgsz=self.settings.imgsz,
            conf=self.settings.conf,
            iou=self.settings.iou,
            device=self.settings.device,
            verbose=False,
        )[0]
        inference_ms = (time.perf_counter() - started) * 1000

        detections: list[Detection] = []
        if result.boxes is not None:
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence < self.settings.conf:
                    continue
                    
                class_id = int(box.cls[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                detections.append(
                    Detection(
                        class_id=class_id,
                        class_name=self._class_name(class_id),
                        confidence=confidence,
                        box=Box(x1=x1, y1=y1, x2=x2, y2=y2),
                    )
                )

        size = image_size(image)
        return PredictionResponse(
            detections=detections,
            image_size=ImageSize(**size),
            inference_ms=round(inference_ms, 3),
        )

    def _class_name(self, class_id: int) -> str:
        if 0 <= class_id < len(self._names):
            return self._names[class_id]
        return str(class_id)
