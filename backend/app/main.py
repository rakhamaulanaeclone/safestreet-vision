from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .model import SafeStreetDetector
from .schemas import HealthResponse, ModelInfoResponse, PredictionResponse
from .utils import decode_image, ensure_within_upload_limit


settings = get_settings()
detector = SafeStreetDetector(settings)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="FastAPI inference backend for SafeStreet Vision.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "model_info": "/model/info",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=detector.model_loaded,
        model_exists=detector.model_exists,
        device=settings.device,
    )


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    try:
        return detector.model_info()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.post("/predict/image", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)) -> PredictionResponse:
    return await _predict_upload(file)


@app.post("/predict/video-frame", response_model=PredictionResponse)
async def predict_video_frame(file: UploadFile = File(...)) -> PredictionResponse:
    return await _predict_upload(file)


async def _predict_upload(file: UploadFile) -> PredictionResponse:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type: {file.content_type}",
        )

    try:
        image_bytes = await file.read()
        ensure_within_upload_limit(image_bytes, settings.max_upload_mb)
        image = decode_image(image_bytes)
        return detector.predict(image)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
