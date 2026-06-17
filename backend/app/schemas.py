from __future__ import annotations

from pydantic import BaseModel, Field


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    box: Box


class ImageSize(BaseModel):
    width: int
    height: int


class PredictionResponse(BaseModel):
    detections: list[Detection]
    image_size: ImageSize
    inference_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_exists: bool
    device: str


class ModelInfoResponse(BaseModel):
    model_path: str
    model_exists: bool
    model_loaded: bool
    device: str
    imgsz: int
    conf: float
    iou: float
    class_count: int
    class_names: list[str]


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Invalid image upload"])
