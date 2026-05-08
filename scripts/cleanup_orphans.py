"""
cleanup_orphans.py — SafeStreet Vision
=======================================
Menghapus gambar orphan (tanpa label) dari:
  1. datasets/merged/
  2. Dataset sumber (RAD, RoadDamage)

Alasan penghapusan:
  - 509 gambar RAD yang SEMUA anotasinya kelas RoadDamages/UnsurfacedRoad
    (dihapus saat remap) → gambar berisi kerusakan jalan tapi tanpa anotasi
    → YOLO menganggap "tidak ada objek" → menurunkan recall
  - 91 gambar RAD yang memang kosong di source
  - 1 gambar RoadDamage (rd_vlcsnap-00058) dgn degenerate bbox (h=0)

Jalankan dari ROOT proyek:
    python scripts/cleanup_orphans.py
"""

import os
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
MERGED = ROOT / "datasets" / "merged"
RAD_ROOT = ROOT / "datasets" / "RAD" / "images"
RD_IMG = ROOT / "datasets" / "RoadDamage" / "images"
RD_LBL = ROOT / "datasets" / "RoadDamage" / "labels-YOLO"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Mapping split name: merged -> RAD source
MERGED_TO_RAD_SPLIT = {"train": "train", "val": "valid", "test": "test"}


def find_orphans():
    """Cari semua gambar di merged yang tidak punya label."""
    orphans = []
    for split in ["train", "val", "test"]:
        img_dir = MERGED / "images" / split
        lbl_dir = MERGED / "labels" / split
        if not img_dir.exists():
            continue

        img_stems = {f.stem: f for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXTS}
        lbl_stems = {f.stem for f in lbl_dir.iterdir() if f.suffix.lower() == ".txt"} if lbl_dir.exists() else set()

        for stem, img_path in img_stems.items():
            if stem not in lbl_stems:
                orphans.append((split, stem, img_path))

    return orphans


def trace_source(split, stem):
    """
    Dari nama file di merged, cari file sumber asli.
    Return: (source_img_path, source_lbl_path) atau (None, None)
    """
    if stem.startswith("rad_"):
        original_stem = stem[4:]  # hapus prefix "rad_"
        src_split = MERGED_TO_RAD_SPLIT.get(split, split)
        src_img_dir = RAD_ROOT / src_split / "images"
        src_lbl_dir = RAD_ROOT / src_split / "labels"

        # Cari gambar dengan stem yang cocok (ekstensi bisa berbeda)
        src_img = None
        if src_img_dir.exists():
            for f in src_img_dir.iterdir():
                if f.stem == original_stem and f.suffix.lower() in IMG_EXTS:
                    src_img = f
                    break

        src_lbl = src_lbl_dir / (original_stem + ".txt")
        if not src_lbl.exists():
            src_lbl = None

        return src_img, src_lbl

    elif stem.startswith("rd_"):
        original_stem = stem[3:]  # hapus prefix "rd_"

        src_img = None
        if RD_IMG.exists():
            for f in RD_IMG.iterdir():
                if f.stem == original_stem and f.suffix.lower() in IMG_EXTS:
                    src_img = f
                    break

        src_lbl = RD_LBL / (original_stem + ".txt")
        if not src_lbl.exists():
            src_lbl = None

        return src_img, src_lbl

    return None, None


def main():
    print("=" * 60)
    print("  CLEANUP ORPHAN IMAGES")
    print("=" * 60)

    # 1. Cari orphans
    print("\n[1/3] Mencari gambar orphan di merged/...")
    orphans = find_orphans()
    print(f"  Ditemukan: {len(orphans)} gambar orphan")

    if not orphans:
        print("\n  Tidak ada orphan! Dataset sudah bersih. ✓")
        return

    # Breakdown per prefix
    prefix_count = Counter()
    for _, stem, _ in orphans:
        prefix = stem.split("_")[0]
        prefix_count[prefix] += 1
    print(f"  Per prefix: {dict(prefix_count)}")

    # Breakdown per split
    split_count = Counter()
    for split, _, _ in orphans:
        split_count[split] += 1
    print(f"  Per split : {dict(split_count)}")

    # 2. Trace ke source dan kumpulkan file yang akan dihapus
    print("\n[2/3] Menelusuri file sumber...")
    to_delete = []  # list of (path, description)

    for split, stem, merged_img in orphans:
        # File merged (gambar)
        to_delete.append((merged_img, f"merged/{split}/images"))

        # File sumber
        src_img, src_lbl = trace_source(split, stem)
        if src_img and src_img.exists():
            to_delete.append((src_img, f"source image"))
        if src_lbl and src_lbl.exists():
            to_delete.append((src_lbl, f"source label"))

    print(f"  Total file yang akan dihapus: {len(to_delete)}")

    # Breakdown
    merged_count = sum(1 for _, desc in to_delete if "merged" in desc)
    src_img_count = sum(1 for _, desc in to_delete if desc == "source image")
    src_lbl_count = sum(1 for _, desc in to_delete if desc == "source label")
    print(f"    - Merged images : {merged_count}")
    print(f"    - Source images : {src_img_count}")
    print(f"    - Source labels : {src_lbl_count}")

    # 3. Preview beberapa file
    print("\n  Preview (5 contoh pertama):")
    shown = set()
    count = 0
    for path, desc in to_delete:
        if count >= 5:
            break
        parent_key = path.parent.name
        if parent_key not in shown:
            print(f"    [{desc}] {path.name}")
            shown.add(parent_key)
            count += 1

    # Konfirmasi
    print(f"\n  [WARNING] Akan menghapus {len(to_delete)} file secara permanen!")
    confirm = input("  Ketik 'YA' untuk melanjutkan: ").strip()

    if confirm != "YA":
        print("\n  Dibatalkan.")
        return

    # 4. Hapus!
    print("\n[3/3] Menghapus file...")
    deleted = 0
    errors = 0
    for path, desc in to_delete:
        try:
            if path.exists():
                path.unlink()
                deleted += 1
        except Exception as e:
            print(f"  [ERROR] Gagal hapus {path}: {e}")
            errors += 1

    # Ringkasan akhir
    print("\n" + "=" * 60)
    print("  SELESAI!")
    print("=" * 60)
    print(f"  File dihapus  : {deleted:,}")
    print(f"  Error         : {errors}")

    # Verifikasi ulang
    print("\n  Verifikasi ulang...")
    remaining = find_orphans()
    print(f"  Orphan tersisa: {len(remaining)}")

    if not remaining:
        print("  [OK] Dataset bersih! Tidak ada gambar tanpa label.")
    else:
        print("  [WARNING] Masih ada orphan. Periksa manual.")
        for split, stem, path in remaining[:5]:
            print(f"    {split}: {stem}")

    print(f"\n  Jalankan validate_dataset.py untuk verifikasi lengkap.")
    print("=" * 60)


if __name__ == "__main__":
    main()
