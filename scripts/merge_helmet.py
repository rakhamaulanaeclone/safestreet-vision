"""
merge_helmet.py  —  SafeStreet Vision
=======================================
Menambahkan dataset helm (HelmetMain + HelmetSupp)
ke dalam dataset merged/ yang sudah ada.
 
Jalankan dari folder ROOT proyek (SafeStreet Vision):
    python scripts/merge_helmet.py
 
Kelas baru yang ditambahkan:
    7: with_helmet
    8: without_helmet
 
Kelas final setelah script ini selesai (9 kelas total):
    0: pothole
    1: crack
    2: manhole
    3: speed_bump
    4: vehicle_small
    5: vehicle_large
    6: pedestrian
    7: with_helmet      <- BARU
    8: without_helmet   <- BARU
"""
 
import shutil
import yaml
from pathlib import Path
from collections import defaultdict
 
# ══════════════════════════════════════════════════
#  PATH
# ══════════════════════════════════════════════════
 
ROOT          = Path(__file__).parent.parent
HELMET_MAIN   = ROOT / "datasets" / "HelmetMain"
HELMET_SUPP   = ROOT / "datasets" / "HelmetSupp"
MERGED        = ROOT / "datasets" / "merged"
 
# ══════════════════════════════════════════════════
#  PEMETAAN KELAS HELM
#
#  HelmetMain data.yaml:
#    0: helm         -> 7: with_helmet
#    1: tanpaHelm    -> 8: without_helmet
#
#  HelmetSupp data.yaml:
#    0: With Helmet  -> 7: with_helmet
#    1: Without Helmet -> 8: without_helmet
# ══════════════════════════════════════════════════
 
HELMET_MAIN_MAP = {
    0: 7,   # helm       -> with_helmet
    1: 8,   # tanpaHelm  -> without_helmet
}
 
HELMET_SUPP_MAP = {
    0: 7,   # With Helmet    -> with_helmet
    1: 8,   # Without Helmet -> without_helmet
}
 
# Kelas final lengkap setelah penggabungan
CLASS_NAMES_FINAL = [
    "pothole",        # 0
    "crack",          # 1
    "manhole",        # 2
    "speed_bump",     # 3
    "vehicle_small",  # 4
    "vehicle_large",  # 5
    "pedestrian",     # 6
    "with_helmet",    # 7  <- BARU
    "without_helmet", # 8  <- BARU
]
 
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
 
# ══════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════
 
def cari_gambar(folder: Path):
    if not folder.exists():
        return []
    return [f for f in folder.iterdir() if f.suffix.lower() in IMG_EXTS]
 
def remap_label(src: Path, dst: Path, class_map: dict) -> int:
    """Baca label, remap class_id, tulis ke dst."""
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
                continue
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
#  KUMPULKAN PASANGAN DARI DATASET HELM
#  Struktur Roboflow: train/images/, train/labels/
#                     valid/images/, valid/labels/
#                     test/images/,  test/labels/
# ══════════════════════════════════════════════════
 
def kumpulkan_helmet(dataset_dir: Path, class_map: dict, prefix: str):
    """
    Baca semua split dari dataset helm Roboflow.
    Kembalikan dict: {"train": [...], "val": [...], "test": [...]}
    """
    hasil = defaultdict(list)
    peta_split = {"train": "train", "valid": "val", "test": "test"}
 
    for folder_rf, nama_split in peta_split.items():
        img_dir = dataset_dir / folder_rf / "images"
        lbl_dir = dataset_dir / folder_rf / "labels"
 
        if not img_dir.exists():
            print(f"  [SKIP] Tidak ditemukan: {img_dir}")
            continue
 
        gambar = cari_gambar(img_dir)
        print(f"  {prefix} {folder_rf:6s} -> {len(gambar):,} gambar")
 
        for g in gambar:
            l = lbl_dir / (g.stem + ".txt")
            hasil[nama_split].append((g, l, class_map, prefix))
 
    return hasil
 
# ══════════════════════════════════════════════════
#  TAMBAHKAN KE MERGED
# ══════════════════════════════════════════════════
 
def tambahkan_ke_merged(semua: dict):
    statistik = defaultdict(lambda: {"gambar": 0, "anotasi": 0})
 
    for split, pasangan in semua.items():
        print(f"\n  Menulis {split} ({len(pasangan):,} pasangan)...")
 
        out_img = MERGED / "images" / split
        out_lbl = MERGED / "labels" / split
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)
 
        for i, (img, lbl, class_map, prefix) in enumerate(pasangan):
            nama_baru  = f"{prefix}_{img.stem}"
            dst_img    = out_img / (nama_baru + img.suffix)
            dst_lbl    = out_lbl / (nama_baru + ".txt")
 
            salin_gambar(img, dst_img)
            n = remap_label(lbl, dst_lbl, class_map)
 
            statistik[split]["gambar"]   += 1
            statistik[split]["anotasi"]  += n
 
            if (i + 1) % 500 == 0:
                print(f"    {i+1:,}/{len(pasangan):,} selesai...")
 
    return statistik
 
# ══════════════════════════════════════════════════
#  UPDATE data.yaml
# ══════════════════════════════════════════════════
 
def update_yaml():
    yaml_path = MERGED / "data.yaml"
 
    # Baca yaml lama
    with open(yaml_path, "r") as f:
        isi = yaml.safe_load(f)
 
    # Update kelas
    isi["nc"]    = len(CLASS_NAMES_FINAL)
    isi["names"] = CLASS_NAMES_FINAL
 
    # Tulis ulang
    with open(yaml_path, "w") as f:
        yaml.dump(isi, f, default_flow_style=False, allow_unicode=True)
 
    print(f"\n  data.yaml diperbarui: {yaml_path}")
    print(f"  Jumlah kelas sekarang: {len(CLASS_NAMES_FINAL)}")
 
# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
 
def main():
    print("=" * 55)
    print("  TAMBAH DATASET HELM KE MERGED")
    print("=" * 55)
    print(f"\n  ROOT        : {ROOT}")
    print(f"  HelmetMain  : {HELMET_MAIN}")
    print(f"  HelmetSupp  : {HELMET_SUPP}")
    print(f"  Target      : {MERGED}")
 
    # Cek folder input ada
    for folder, nama in [(HELMET_MAIN, "HelmetMain"), (HELMET_SUPP, "HelmetSupp")]:
        if not folder.exists():
            print(f"\n[ERROR] Folder {nama} tidak ditemukan: {folder}")
            print("  Pastikan folder sudah di dalam datasets/")
            return
 
    if not MERGED.exists():
        print(f"\n[ERROR] Folder merged tidak ditemukan: {MERGED}")
        print("  Jalankan merge_datasets.py terlebih dahulu!")
        return
 
    print("\n[1/3] Kumpulkan HelmetMain (backbone helm)...")
    hm = kumpulkan_helmet(HELMET_MAIN, HELMET_MAIN_MAP, "hm")
 
    print("\n[2/3] Kumpulkan HelmetSupp (suplemen helm)...")
    hs = kumpulkan_helmet(HELMET_SUPP, HELMET_SUPP_MAP, "hs")
 
    # Gabungkan kedua dataset helm per split
    gabungan = defaultdict(list)
    for split in ["train", "val", "test"]:
        gabungan[split] = hm.get(split, []) + hs.get(split, [])
        print(f"  {split:6s}: {len(gabungan[split]):,} total pasangan helm")
 
    print("\n[3/3] Tambahkan ke datasets/merged/ ...")
    stats = tambahkan_ke_merged(gabungan)
    update_yaml()
 
    # Ringkasan
    print("\n" + "=" * 55)
    print("  SELESAI!")
    print("=" * 55)
    total_g = total_a = 0
    for split, s in stats.items():
        print(f"  {split:6s}: +{s['gambar']:,} gambar | +{s['anotasi']:,} anotasi")
        total_g += s["gambar"]
        total_a += s["anotasi"]
    print(f"  TOTAL ditambahkan: {total_g:,} gambar | {total_a:,} anotasi helm")
    print(f"\n  Kelas final ({len(CLASS_NAMES_FINAL)}):")
    for i, nama in enumerate(CLASS_NAMES_FINAL):
        status = "<- BARU" if i >= 7 else ""
        print(f"    [{i}] {nama} {status}")
    print(f"\n  Jalankan validate_dataset.py untuk cek hasil!")
    print("=" * 55)
 
 
if __name__ == "__main__":
    main()