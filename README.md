# SafeStreet Vision

Real-time detection of **road damage** and **motorcycle helmet usage** using YOLOv8.

## Overview

A single YOLOv8 model that detects 9 classes simultaneously from dashcam or CCTV footage:

| ID | Class | Source |
|----|-------|--------|
| 0 | `pothole` | Road Damage Dataset |
| 1 | `crack` | Road Damage Dataset |
| 2 | `manhole` | Road Damage Dataset |
| 3 | `speed_bump` | RAD India |
| 4 | `vehicle_small` | RAD India |
| 5 | `vehicle_large` | RAD India |
| 6 | `pedestrian` | RAD India |
| 7 | `with_helmet` | Deteksi Helm + helm motor |
| 8 | `without_helmet` | Deteksi Helm + helm motor |

## Dataset Statistics

| Split | Images | Labels |
|-------|--------|--------|
| Train | 9,377 | 9,377 |
| Val | 2,041 | 2,041 |
| Test | 1,705 | 1,705 |
| **Total** | **13,123** | **13,123** |

Total annotations: 35,780 across 9 classes

### Dataset Sources

| Dataset | Source | Images | License |
|---------|--------|--------|---------|
| RAD Road Anomaly Detection | Kaggle (Rohit Suresh15) | 8,394 | MIT |
| Road Damage: Potholes, Cracks, Manholes | Kaggle (Lorenzo Arcioni) | 2,009 | MIT |
| Deteksi Helm | Roboflow Universe | 3,169 | CC BY 4.0 |
| helm motor (ox1de) | Roboflow Universe | 152 | CC BY 4.0 |

Datasets are not included in this repository due to size. Download manually and place in `datasets/` following the structure below.

## Project Structure

```
SafeStreet Vision/
├── datasets/                  (NOT pushed to GitHub)
│   ├── RAD/
│   ├── RoadDamage/
│   ├── HelmetMain/
│   ├── HelmetSupp/
│   └── merged/
│       ├── images/
│       │   ├── train/
│       │   ├── val/
│       │   └── test/
│       ├── labels/
│       │   ├── train/
│       │   ├── val/
│       │   └── test/
│       └── data.yaml
├── scripts/
│   ├── merge_datasets.py
│   ├── merge_helmet.py
│   ├── validate_dataset.py
│   └── clean_orphans.py
├── backend/                   (coming soon)
├── frontend/                  (coming soon)
├── .gitignore
└── README.md
```

## Setup

```bash
git clone https://github.com/username/safestreet-vision.git
cd safestreet-vision

python -m venv .venv
.venv\Scripts\activate

pip install ultralytics pyyaml
```

## Dataset Pipeline

```bash
python scripts/merge_datasets.py    # Step 1: Merge road damage datasets
python scripts/merge_helmet.py      # Step 2: Add helmet datasets
python scripts/validate_dataset.py  # Step 3: Validate
python scripts/clean_orphans.py     # Step 4: Remove orphan images
python scripts/validate_dataset.py  # Step 5: Final validation
```

## Tech Stack

- **ML Model:** YOLOv8 (Ultralytics)
- **Backend:** FastAPI + WebSocket
- **Frontend:** React + Canvas API
- **Training:** Google Colab

## Model Performance

| Metric | Value |
|--------|-------|
| mAP@50 | TBD (after training) |
| mAP@50-95 | TBD |
| Inference CPU | ~100-150ms |
| Inference GPU | ~10-20ms |

## Credits

- RAD Dataset — Rohit Suresh15 (Kaggle)
- Road Damage Dataset — Lorenzo Arcioni (Kaggle)
- Deteksi Helm — Roboflow Universe
- helm motor — ox1de (Roboflow Universe)

## License

Code: MIT
Datasets: see Dataset Sources table (CC BY 4.0 attribution required for Roboflow datasets)
