"""
merge_datasets.py  —  RDD & HD PROJECT
========================================
Menggabungkan RAD + RoadDamage menjadi satu dataset YOLO.
 
Jalankan dari folder ROOT proyek (RDD & HD Project):
    python scripts/merge_datasets.py
"""
 
import os
import shutil
import random
import yaml
from pathlib import Path
from collections import defaultdict
 
# ══════════════════════════════════════════════════
#  PATH — sudah disesuaikan dengan struktur foldermu
# ══════════════════════════════════════════════════
#
#  Struktur yang terdeteksi:
#
#  RDD & HD Project/          <- ROOT (tempat kamu jalankan perintah)
#  datasets/
#    RAD/
#      images/
#        train/
#          images/   <- gambar ada di sini
#          labels/   <- label ada di sini
#        valid/
#          images/
#          labels/
#        test/
#          images/
#          labels/
#    RoadDamage/
#      images/       <- gambar ada di sini (LANGSUNG)
#      labels-YOLO/  <- label .txt ada di sini (LANGSUNG)
#  scripts/
#    merge_datasets.py   <- FILE INI
 
# Path root = 1 folder di atas folder scripts/
ROOT = Path(__file__).parent.parent
 
RAD_IMG_ROOT   = ROOT / "datasets" / "RAD" / "images"
ROADDMG_IMG    = ROOT / "datasets" / "RoadDamage" / "images"
ROADDMG_LBL    = ROOT / "datasets" / "RoadDamage" / "labels-YOLO"
OUTPUT         = ROOT / "datasets" / "merged"
 
RANDOM_SEED    = 42
SPLIT_RATIO    = (0.80, 0.10, 0.10)   # train / val / test
 
# ══════════════════════════════════════════════════
#  PEMETAAN KELAS
#
#  RAD data.yaml (kelas asli):
#    0: HMV           (Bus, Truk, Traktor)
#    1: LMV           (Mobil, Motor, Minivan)
#    2: Pedestrian
#    3: RoadDamages   (umum - kita HAPUS, digantikan Dataset 1)
#    4: SpeedBump
#    5: UnsurfacedRoad (kita HAPUS, bukan objek titik)
#
#  RoadDamage labels-YOLO (kelas asli):
#    0: Pothole
#    1: Crack
#    2: Manhole
#
#  KELAS GABUNGAN (output akhir):
#    0: pothole
#    1: crack
#    2: manhole
#    3: speed_bump
#    4: vehicle_small   (LMV: motor, mobil kecil)
#    5: vehicle_large   (HMV: bus, truk)
#    6: pedestrian
# ══════════════════════════════════════════════════
 
RAD_CLASS_MAP = {
    0: 5,     # HMV          -> vehicle_large
    1: 4,     # LMV          -> vehicle_small
    2: 6,     # Pedestrian   -> pedestrian
    3: None,  # RoadDamages  -> HAPUS (digantikan Dataset 1)
    4: 3,     # SpeedBump    -> speed_bump
    5: None,  # UnsurfacedRoad -> HAPUS
}
 
ROADDMG_CLASS_MAP = {
    0: 0,   # Pothole -> pothole
    1: 1,   # Crack   -> crack
    2: 2,   # Manhole -> manhole
}
 
CLASS_NAMES = [
    "pothole",       # 0
    "crack",         # 1
    "manhole",       # 2
    "speed_bump",    # 3
    "vehicle_small", # 4
    "vehicle_large", # 5
    "pedestrian",    # 6
]
 
# ══════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════
 
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
 
def cari_gambar(folder: Path):
    """Cari semua file gambar dalam satu folder."""
    if not folder.exists():
        return []
    return [f for f in folder.iterdir() if f.suffix.lower() in IMG_EXTS]
 
def remap_label(src: Path, dst: Path, class_map: dict) -> int:
    """
    Baca label YOLO, ganti class_id sesuai class_map,
    tulis ke dst. Kembalikan jumlah baris valid.
    """
    if not src.exists():
        return 0
 
    baris_valid = []
    with open(src, "r") as f:
        for baris in f:
            baris = baris.strip()
            if not baris:
                continue
            bagian = baris.split()
            old_id = int(bagian[0])
            new_id = class_map.get(old_id)
            if new_id is None:
                continue   # kelas ini dihapus
            bagian[0] = str(new_id)
            baris_valid.append(" ".join(bagian))
 
    if baris_valid:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w") as f:
            f.write("\n".join(baris_valid) + "\n")
        return len(baris_valid)
    return 0
 
def salin_gambar(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
 
# ══════════════════════════════════════════════════
#  KUMPULKAN PASANGAN DARI RAD
# ══════════════════════════════════════════════════
 
def kumpulkan_rad():
    hasil = defaultdict(list)
    peta_split = {"train": "train", "valid": "val", "test": "test"}
 
    for folder_rad, nama_split in peta_split.items():
        img_dir = RAD_IMG_ROOT / folder_rad / "images"
        lbl_dir = RAD_IMG_ROOT / folder_rad / "labels"
 
        if not img_dir.exists():
            print(f"  [SKIP] Tidak ditemukan: {img_dir}")
            continue
 
        gambar = cari_gambar(img_dir)
        print(f"  RAD {folder_rad:6s} -> {len(gambar):,} gambar")
 
        for g in gambar:
            l = lbl_dir / (g.stem + ".txt")
            hasil[nama_split].append((g, l, RAD_CLASS_MAP, "rad"))
 
    return hasil
 
# ══════════════════════════════════════════════════
#  KUMPULKAN PASANGAN DARI ROADDAMAGE
# ══════════════════════════════════════════════════
 
def kumpulkan_roaddmg():
    if not ROADDMG_IMG.exists():
        print(f"  [SKIP] Tidak ditemukan: {ROADDMG_IMG}")
        return defaultdict(list)
 
    semua_gambar = cari_gambar(ROADDMG_IMG)
    print(f"  RoadDamage total -> {len(semua_gambar):,} gambar")
 
    random.seed(RANDOM_SEED)
    random.shuffle(semua_gambar)
 
    n       = len(semua_gambar)
    n_train = int(n * SPLIT_RATIO[0])
    n_val   = int(n * SPLIT_RATIO[1])
 
    pembagian = {
        "train": semua_gambar[:n_train],
        "val":   semua_gambar[n_train : n_train + n_val],
        "test":  semua_gambar[n_train + n_val :],
    }
 
    hasil = defaultdict(list)
    for nama_split, gambar_list in pembagian.items():
        for g in gambar_list:
            l = ROADDMG_LBL / (g.stem + ".txt")
            hasil[nama_split].append((g, l, ROADDMG_CLASS_MAP, "rd"))
        print(f"  RoadDamage {nama_split:6s} -> {len(gambar_list):,} gambar")
 
    return hasil
 
# ══════════════════════════════════════════════════
#  TULIS DATASET GABUNGAN
# ══════════════════════════════════════════════════
 
def tulis_merged(semua: dict):
    statistik = defaultdict(lambda: {"gambar": 0, "anotasi": 0})
 
    for split, pasangan in semua.items():
        print(f"\n  Menulis {split} ({len(pasangan):,} pasangan)...")
 
        out_img = OUTPUT / "images" / split
        out_lbl = OUTPUT / "labels" / split
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)
 
        for i, (img, lbl, class_map, prefix) in enumerate(pasangan):
            nama_baru = f"{prefix}_{img.stem}"
            dst_img = out_img / (nama_baru + img.suffix)
            dst_lbl = out_lbl / (nama_baru + ".txt")
 
            salin_gambar(img, dst_img)
            n = remap_label(lbl, dst_lbl, class_map)
 
            statistik[split]["gambar"]   += 1
            statistik[split]["anotasi"]  += n
 
            if (i + 1) % 500 == 0:
                print(f"    {i+1:,}/{len(pasangan):,} selesai...")
 
    return statistik
 
# ══════════════════════════════════════════════════
#  BUAT data.yaml
# ══════════════════════════════════════════════════
 
def buat_yaml():
    isi = {
        "path":  "datasets/merged",
        "train": "images/train",
        "val":   "images/val",
        "test":  "images/test",
        "nc":    len(CLASS_NAMES),
        "names": CLASS_NAMES,
    }
    out = OUTPUT / "data.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.dump(isi, f, default_flow_style=False, allow_unicode=True)
    print(f"\n  data.yaml dibuat: {out}")
 
# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
 
def main():
    print("=" * 55)
    print("  MERGE DATASET: RAD + RoadDamage")
    print("=" * 55)
    print(f"\n  ROOT   : {ROOT}")
    print(f"  RAD    : {RAD_IMG_ROOT}")
    print(f"  RoadDmg: {ROADDMG_IMG}")
    print(f"  Output : {OUTPUT}")
 
    # Cek folder input ada
    if not RAD_IMG_ROOT.exists():
        print(f"\n[ERROR] Folder RAD tidak ditemukan: {RAD_IMG_ROOT}")
        print("  Pastikan kamu menjalankan dari folder: RDD & HD Project")
        return
    if not ROADDMG_IMG.exists():
        print(f"\n[ERROR] Folder RoadDamage tidak ditemukan: {ROADDMG_IMG}")
        return
 
    print("\n[1/4] Kumpulkan data RAD...")
    rad   = kumpulkan_rad()
 
    print("\n[2/4] Kumpulkan data RoadDamage...")
    rd    = kumpulkan_roaddmg()
 
    print("\n[3/4] Gabungkan & acak...")
    gabungan = defaultdict(list)
    for split in ["train", "val", "test"]:
        gabungan[split] = rad.get(split, []) + rd.get(split, [])
        random.seed(RANDOM_SEED)
        random.shuffle(gabungan[split])
        print(f"  {split:6s}: {len(gabungan[split]):,} total pasangan")
 
    print("\n[4/4] Tulis ke datasets/merged/ ...")
    stats = tulis_merged(gabungan)
    buat_yaml()
 
    print("\n" + "=" * 55)
    print("  SELESAI!")
    print("=" * 55)
    total_g = total_a = 0
    for split, s in stats.items():
        print(f"  {split:6s}: {s['gambar']:,} gambar | {s['anotasi']:,} anotasi")
        total_g += s["gambar"]
        total_a += s["anotasi"]
    print(f"  TOTAL : {total_g:,} gambar | {total_a:,} anotasi")
    print(f"\n  Kelas : {', '.join(CLASS_NAMES)}")
    print(f"  Output: datasets/merged/")
    print("=" * 55)
 
if __name__ == "__main__":
    main()
