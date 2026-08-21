# SafeStreet Vision

Real-time object detection for road damage and motorcycle helmet usage using YOLOv8.

SafeStreet Vision is an end-to-end machine learning portfolio project. The current version includes dataset engineering, YOLOv8 training/evaluation, ONNX export, and a FastAPI inference backend.

## Classes

A single YOLOv8 model detects 9 classes:

| ID | Class | Source |
|---:|---|---|
| 0 | `pothole` | RoadDamage Italy |
| 1 | `crack` | RoadDamage Italy |
| 2 | `manhole` | RoadDamage Italy |
| 3 | `speed_bump` | RAD India |
| 4 | `vehicle_small` | RAD India |
| 5 | `vehicle_large` | RAD India |
| 6 | `pedestrian` | RAD India |
| 7 | `with_helmet` | HelmetMain + HelmetSupp |
| 8 | `without_helmet` | HelmetMain + HelmetSupp |

## Dataset

Datasets are not included in this repository due to size and licensing. Place them under `datasets/` before running the merge pipeline.

| Split | Images | Labels |
|---|---:|---:|
| Train | 9,377 | 9,377 |
| Val | 2,041 | 2,041 |
| Test | 1,705 | 1,705 |
| Total | 13,123 | 13,123 |

Total annotations: 35,780 across 9 classes.

| Dataset | Source | Images | License |
|---|---|---:|---|
| RAD Road Anomaly Detection | Kaggle, Rohit Suresh15 | 8,394 | MIT |
| Road Damage: Potholes, Cracks, Manholes | Kaggle, Lorenzo Arcioni | 2,009 | MIT |
| Deteksi Helm | Roboflow Universe | 3,169 | CC BY 4.0 |
| helm motor | Roboflow Universe, ox1de | 152 | CC BY 4.0 |

## Project Structure

```text
SafeStreet Vision/
|-- datasets/                  
|   |-- RAD/
|   |-- RoadDamage/
|   |-- HelmetMain/
|   |-- HelmetSupp/
|   `-- merged/
|       |-- images/train, val, test/
|       |-- labels/train, val, test/
|       `-- data.yaml
|-- runs/                      #  YOLO training/evaluation outputs
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- model.py
|   |   |-- schemas.py
|   |   `-- utils.py
|   |-- requirements.txt
|   |-- Dockerfile
|   `-- README.md
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- Dockerfile
|-- docker-compose.yml
|-- scripts/
|   |-- merge_datasets.py
|   |-- merge_helmet.py
|   |-- validate_dataset.py
|   |-- cleanup_orphans.py
|   |-- train.py
|   |-- evaluate.py
|   |-- export_model.py
|   `-- verify_onnx.py
|-- .gitignore
`-- README.md
```

## Setup

```bash
python -m venv .venv311
.venv311\Scripts\activate
pip install ultralytics pyyaml opencv-python
pip install onnx onnxruntime
pip install -r backend/requirements.txt
```

## Dataset Pipeline

```bash
python scripts/merge_datasets.py
python scripts/merge_helmet.py
python scripts/validate_dataset.py
python scripts/cleanup_orphans.py
python scripts/validate_dataset.py
```

`cleanup_orphans.py` only deletes orphan images from `datasets/merged`. It does not delete source dataset files, so the pipeline remains reproducible.

## Training

Training was run locally with:

| Item | Value |
|---|---|
| Model | YOLOv8s |
| Pretrained weights | `yolov8s.pt` |
| Epochs | 100 |
| Batch size | 16 |
| Image size | 640 |
| Hardware | NVIDIA RTX 2060 Super 8GB |
| Python | 3.11.9 |
| PyTorch | 2.5.1+cu121 |
| Ultralytics | 8.4.48 |

```bash
python scripts/train.py
```

Model weights and training outputs are ignored by Git.

## Model Performance

Metrics for `runs/safestreet_v1_2/weights/best.pt`:

| Split | Images | Instances | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 2,041 | 5,587 | 0.773 | 0.774 | 0.802 | 0.463 |
| Test | 1,705 | 4,732 | 0.825 | 0.747 | 0.789 | 0.447 |

Per-class mAP summary:

| Class | Val instances | Val mAP@50 | Val mAP@50-95 | Test instances | Test mAP@50 | Test mAP@50-95 |
|---|---:|---:|---:|---:|---:|---:|
| pothole | 134 | 0.539 | 0.206 | 129 | 0.460 | 0.187 |
| crack | 286 | 0.317 | 0.119 | 272 | 0.363 | 0.117 |
| manhole | 95 | 0.697 | 0.341 | 92 | 0.724 | 0.302 |
| speed_bump | 83 | 0.940 | 0.479 | 70 | 0.829 | 0.398 |
| vehicle_small | 2,201 | 0.960 | 0.624 | 2,158 | 0.957 | 0.617 |
| vehicle_large | 672 | 0.974 | 0.729 | 647 | 0.983 | 0.728 |
| pedestrian | 549 | 0.915 | 0.486 | 561 | 0.915 | 0.488 |
| with_helmet | 1,278 | 0.938 | 0.577 | 653 | 0.929 | 0.575 |
| without_helmet | 289 | 0.941 | 0.605 | 150 | 0.940 | 0.611 |

The weakest classes are still `crack` and `pothole`, especially under stricter mAP@50-95. This is expected from thin/low-contrast crack geometry, small validation/test support for road-damage classes, and domain variation across source datasets.

## Evaluation

Run validation or test evaluation from the project root:

```bash
python scripts/evaluate.py --split val --device 0
python scripts/evaluate.py --split test --device 0
python scripts/evaluate.py --split all --device 0
```

The evaluation script saves metrics, per-class CSV, Markdown summaries, confusion matrix CSV, Ultralytics plots, and prediction samples under `runs/evaluation_*`.

## ONNX Export

Export `best.pt` to ONNX:

```bash
python scripts/export_model.py --device 0
```

The exported ONNX model is saved as `runs/safestreet_v1_2/weights/best.onnx`. This file is ignored by Git.

Verify ONNX inference against the PyTorch model on the same image:

```bash
python scripts/verify_onnx.py --image datasets/merged/images/test/rad_51_13-06-2023_mp4-23_jpg.rf.9854b4961e9c2debab4fdee09206f2c9.jpg --pt-device 0 --onnx-device cpu
```

Latest verification result:

| Check | Result |
|---|---:|
| PyTorch detections | 4 |
| ONNX detections | 4 |
| Matched top classes | 4 / 4 |
| Max confidence delta | 0.0056 |
| Max box coordinate delta | 1.49 px |
| Coarse match | true |


Available endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health and model availability |
| GET | `/model/info` | Model path, class names, thresholds, and device |
| POST | `/predict/image` | Image upload inference |
| POST | `/predict/video-frame` | Same inference path for frontend video frames |

Validated HTTP sample for `/predict/image` using a test image:

| Check | Result |
|---|---:|
| Detections | 4 |
| Image size | 1920 x 1080 |
| First class | `vehicle_small` |
| First confidence | 0.8188 |

## Deployment

The complete application (FastAPI backend + Next.js frontend) is containerized and orchestrated using Docker Compose. The backend automatically mounts the localized YOLOv8 ONNX model from the `runs/` directory.


- **Frontend:** https://safestreet-vision.vercel.app
- **Backend API:** https://safestreet-vision-production.up.railway.app

Features included in the frontend:
- **Real-time Inference:** Access your webcam directly from the browser.
- **Bilingual Support (EN/ID):** Toggle interface language and localized bounding box labels dynamically.
- **Image Export:** Download the annotated image with predictions straight to your device.

## Roadmap

- Phase 0: Dataset pipeline 
- Phase 1: YOLOv8 training 
- Phase 2: Evaluation and export 
- Phase 3: FastAPI backend 
- Phase 4: React frontend
- Phase 5: Docker Compose and integration 
- Phase 6: Deployment 

## License

Code: MIT

Datasets: see the Dataset table. Roboflow datasets require CC BY 4.0 attribution.
