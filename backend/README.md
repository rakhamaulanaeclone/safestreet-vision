# SafeStreet Vision Backend

FastAPI inference backend for SafeStreet Vision.

## Run Locally

From the project root:

```bash
.venv311\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Model info: `http://127.0.0.1:8000/model/info`

## Configuration

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `SAFESTREET_MODEL_PATH` | `runs/safestreet_v1_2/weights/best.pt` | YOLO weights path |
| `SAFESTREET_DEVICE` | `auto` | `0`, `cpu`, or `auto` |
| `SAFESTREET_IMGSZ` | `640` | YOLO inference image size |
| `SAFESTREET_CONF` | `0.25` | Confidence threshold |
| `SAFESTREET_IOU` | `0.7` | NMS IoU threshold |
| `SAFESTREET_MAX_UPLOAD_MB` | `15` | Upload size limit |
| `SAFESTREET_CORS_ORIGINS` | `*` | Comma-separated CORS origins |

## Endpoints

### `GET /health`

Returns backend health and model availability.

### `GET /model/info`

Loads the model if needed and returns class names, device, thresholds, and model path.

### `POST /predict/image`

Accepts one image file as multipart form field `file`.

PowerShell example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/predict/image" `
  -F "file=@datasets/merged/images/test/rad_51_13-06-2023_mp4-23_jpg.rf.9854b4961e9c2debab4fdee09206f2c9.jpg"
```

Response shape:

```json
{
  "detections": [
    {
      "class_id": 4,
      "class_name": "vehicle_small",
      "confidence": 0.82,
      "box": {"x1": 10.0, "y1": 20.0, "x2": 100.0, "y2": 200.0}
    }
  ],
  "image_size": {"width": 1280, "height": 720},
  "inference_ms": 24.5
}
```

Validated sample response summary:

| Field | Value |
|---|---:|
| Detections | 4 |
| Image width | 1920 |
| Image height | 1080 |
| Inference time | 783.923 ms |
| First class | `vehicle_small` |
| First confidence | 0.8188 |

First detection from the validated sample:

```json
{
  "class_id": 4,
  "class_name": "vehicle_small",
  "confidence": 0.81882244348526,
  "box": {
    "x1": 2.1186904907226562,
    "y1": 604.1807861328125,
    "x2": 162.32000732421875,
    "y2": 847.8758544921875
  }
}
```

### `POST /predict/video-frame`

Same behavior as `/predict/image`, intended for frontend video frame uploads.


• Fase 3 backend FastAPI sudah selesai dan sudah di-commit.

  Commit:
  372b3d8 feat: add FastAPI inference backend

  Yang dibuat:

  - backend/app/main.py
  - backend/app/config.py
  - backend/app/model.py
  - backend/app/schemas.py
  - backend/app/utils.py
  - backend/requirements.txt
  - backend/README.md
  - README root diupdate dengan status backend dan endpoint API

  Endpoint tersedia:

  - GET /health
  - GET /model/info
  - POST /predict/image
  - POST /predict/video-frame

  Validasi yang sudah dijalankan:

  - uvicorn foreground dijalankan; sempat terlihat error bind karena ada proses lama di port 8000, lalu proses lama dihentikan.
  - HTTP biasa via Invoke-RestMethod:
      - /health OK
      - /model/info OK, model best.pt berhasil load, 9 class terbaca

  - HTTP biasa via curl.exe:
      - /predict/image OK
      - sample test menghasilkan 4 deteksi
      - image size 1920x1080
      - first detection vehicle_small, confidence 0.8188

  Cek akhir:

  - compileall backend OK
  - git diff --cached --check OK sebelum commit
  - port 8000 kosong setelah testing
  - working tree bersih
  - branch develop sekarang ahead 1 dari origin/develop, jadi commit backend belum di-push.

  Langkah berikutnya: push commit backend ke GitHub, lalu lanjut Fase 4: React frontend.