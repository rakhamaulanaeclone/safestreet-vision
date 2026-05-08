import os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "datasets" / "merged"

CLASS_NAMES = [
    "pothole",       # 0
    "crack",         # 1
    "manhole",       # 2
    "speed_bump",    # 3
    "vehicle_small", # 4
    "vehicle_large", # 5
    "pedestrian",    # 6
    "with_helmet",    # 7
    "without_helmet", # 8
]

def check_bbox_validity(parts, line_idx):
    if len(parts) != 5:
        return f"Line {line_idx+1}: Does not have 5 elements."
    try:
        x_c, y_c, w, h = map(float, parts[1:5])
        if not (0 <= x_c <= 1 and 0 <= y_c <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
            return f"Line {line_idx+1}: Coordinates out of [0, 1] range. (x_c={x_c}, y_c={y_c}, w={w}, h={h})"
        if w == 0 or h == 0:
            return f"Line {line_idx+1}: Width or height is zero."
    except ValueError:
        return f"Line {line_idx+1}: Cannot parse coordinates to float."
    return None

def validate_dataset():
    if not OUTPUT.exists():
        print(f"[ERROR] Folder merged dataset tidak ditemukan: {OUTPUT}")
        print("Pastikan merge_datasets.py sudah dijalankan.")
        return

    splits = ["train", "val", "test"]
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    total_images = 0
    total_labels = 0
    missing_labels = []
    missing_images = []
    invalid_bboxes = []
    class_distribution = {split: defaultdict(int) for split in splits}
    overall_class_distribution = defaultdict(int)

    for split in splits:
        img_dir = OUTPUT / "images" / split
        lbl_dir = OUTPUT / "labels" / split

        if not img_dir.exists() or not lbl_dir.exists():
            print(f"[WARNING] Folder split '{split}' tidak lengkap atau tidak ada.")
            continue

        images = [f for f in img_dir.iterdir() if f.suffix.lower() in img_exts]
        labels = [f for f in lbl_dir.iterdir() if f.suffix.lower() == ".txt"]
        
        img_stems = {f.stem: f for f in images}
        lbl_stems = {f.stem: f for f in labels}

        # 1. Gambar tanpa label
        for stem, img_path in img_stems.items():
            if stem not in lbl_stems:
                missing_labels.append(img_path)

        # 2. Label tanpa gambar
        for stem, lbl_path in lbl_stems.items():
            if stem not in img_stems:
                missing_images.append(lbl_path)

        total_images += len(images)
        total_labels += len(labels)

        # 3. Validasi isi label & hitung distribusi kelas
        for lbl_path in labels:
            with open(lbl_path, "r") as f:
                for idx, line in enumerate(f):
                    parts = line.strip().split()
                    if not parts:
                        continue
                    
                    try:
                        cls_id = int(parts[0])
                        if 0 <= cls_id < len(CLASS_NAMES):
                            class_distribution[split][cls_id] += 1
                            overall_class_distribution[cls_id] += 1
                        else:
                            invalid_bboxes.append((lbl_path, f"Line {idx+1}: ID Kelas tidak valid '{cls_id}'"))
                        
                        # Cek bounding box
                        err = check_bbox_validity(parts, idx)
                        if err:
                            invalid_bboxes.append((lbl_path, err))
                    except ValueError:
                        invalid_bboxes.append((lbl_path, f"Line {idx+1}: Format kelas tidak valid '{parts[0]}'"))

    # Output Laporan
    print("=" * 60)
    print(" " * 15 + "DATASET VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Gambar dianalisis : {total_images:,}")
    print(f"Total Label dianalisis  : {total_labels:,}")
    
    print("\n--- Distribusi Kelas (Keseluruhan) ---")
    for cls_id in range(len(CLASS_NAMES)):
        name = CLASS_NAMES[cls_id]
        count = overall_class_distribution.get(cls_id, 0)
        print(f"  [{cls_id}] {name.ljust(15)}: {count:,} anotasi")

    print("\n--- Distribusi Kelas per Split ---")
    for split in splits:
        print(f"  Split: {split}")
        for cls_id in range(len(CLASS_NAMES)):
            count = class_distribution[split].get(cls_id, 0)
            if count > 0:
                print(f"    [{cls_id}] {CLASS_NAMES[cls_id].ljust(15)}: {count:,}")
        if sum(class_distribution[split].values()) == 0:
            print("    (Tidak ada anotasi)")
    
    print("\n--- Integrity Checks ---")
    # Gambar tanpa label
    print(f"Gambar tanpa label : {len(missing_labels)}")
    if missing_labels:
        print("  Contoh:", [f.name for f in missing_labels[:5]])
        
    # Label tanpa gambar
    print(f"Label tanpa gambar : {len(missing_images)}")
    if missing_images:
        print("  Contoh:", [f.name for f in missing_images[:5]])
        
    # Bounding Box invalid
    print(f"Bounding Box invalid: {len(invalid_bboxes)}")
    if invalid_bboxes:
        for lbl_path, err in invalid_bboxes[:10]:
            print(f"  {lbl_path.name} -> {err}")
        if len(invalid_bboxes) > 10:
            print(f"  ... dan {len(invalid_bboxes) - 10} lainnya.")

    print("\n" + "=" * 60)
    if not missing_labels and not missing_images and not invalid_bboxes:
        print("Dataset VALID dan SIAP digunakan untuk training!")
    else:
        print("Dataset memiliki ISU. Harap periksa error di atas.")
    print("=" * 60)

if __name__ == "__main__":
    validate_dataset()
