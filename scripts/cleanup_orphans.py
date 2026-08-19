"""
cleanup_orphans.py - SafeStreet Vision
======================================
Remove orphan images from datasets/merged only.

An orphan image is an image file that has no matching YOLO label file after
class remapping. Keeping these images in the training set can teach YOLO that
relevant road-damage scenes are background.

This script intentionally does not delete files from the original source
datasets (RAD, RoadDamage, HelmetMain, HelmetSupp). Source data should stay
intact so the dataset pipeline remains reproducible.

Run from the project root:
    python scripts/cleanup_orphans.py
"""

from pathlib import Path
from collections import Counter


ROOT = Path(__file__).parent.parent
MERGED = ROOT / "datasets" / "merged"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_orphans():
    """Return (split, stem, image_path) for merged images without labels."""
    orphans = []
    for split in ["train", "val", "test"]:
        img_dir = MERGED / "images" / split
        lbl_dir = MERGED / "labels" / split
        if not img_dir.exists():
            continue

        img_stems = {
            f.stem: f
            for f in img_dir.iterdir()
            if f.suffix.lower() in IMG_EXTS
        }
        lbl_stems = {
            f.stem
            for f in lbl_dir.iterdir()
            if f.suffix.lower() == ".txt"
        } if lbl_dir.exists() else set()

        for stem, img_path in img_stems.items():
            if stem not in lbl_stems:
                orphans.append((split, stem, img_path))

    return orphans


def main():
    print("=" * 60)
    print("  CLEANUP ORPHAN IMAGES IN datasets/merged")
    print("=" * 60)

    if not MERGED.exists():
        print(f"\n[ERROR] Merged dataset not found: {MERGED}")
        return

    print("\n[1/3] Searching orphan images in merged dataset...")
    orphans = find_orphans()
    print(f"  Found: {len(orphans)} orphan images")

    if not orphans:
        print("\n  No orphan images found. Dataset is already clean.")
        return

    prefix_count = Counter(stem.split("_")[0] for _, stem, _ in orphans)
    split_count = Counter(split for split, _, _ in orphans)
    print(f"  By prefix: {dict(prefix_count)}")
    print(f"  By split : {dict(split_count)}")

    to_delete = [(img_path, f"merged/{split}/images") for split, _, img_path in orphans]
    print(f"\n[2/3] Files that will be deleted from merged dataset: {len(to_delete)}")
    print("  Source dataset files will not be changed.")

    print("\n  Preview:")
    for path, desc in to_delete[:10]:
        print(f"    [{desc}] {path.name}")
    if len(to_delete) > 10:
        print(f"    ... and {len(to_delete) - 10} more")

    print(f"\n  [WARNING] This will permanently delete {len(to_delete)} merged image files.")
    confirm = input("  Type 'YA' to continue: ").strip()

    if confirm != "YA":
        print("\n  Cancelled.")
        return

    print("\n[3/3] Deleting merged orphan images...")
    deleted = 0
    errors = 0
    for path, _ in to_delete:
        try:
            if path.exists():
                path.unlink()
                deleted += 1
        except Exception as exc:
            print(f"  [ERROR] Failed to delete {path}: {exc}")
            errors += 1

    remaining = find_orphans()

    print("\n" + "=" * 60)
    print("  DONE")
    print("=" * 60)
    print(f"  Deleted          : {deleted:,}")
    print(f"  Errors           : {errors:,}")
    print(f"  Orphans remaining: {len(remaining):,}")

    if remaining:
        print("\n  Remaining examples:")
        for split, stem, _ in remaining[:5]:
            print(f"    {split}: {stem}")

    print("\n  Run validate_dataset.py for the final integrity check.")
    print("=" * 60)


if __name__ == "__main__":
    main()
