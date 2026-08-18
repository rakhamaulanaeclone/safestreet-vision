# Catatan Perbaikan Kendala Inferensi Model ONNX (GPU)

Dokumen ini berisi rincian perbaikan terkait kendala aplikasi (FastAPI/Uvicorn) yang sebelumnya mengalami *crash* dan *loading* tanpa henti di sisi *frontend* saat mencoba menggunakan model format `.onnx`.

## Deskripsi Kendala
Aplikasi berjalan normal saat menggunakan model PyTorch (`.pt`). Namun, ketika konfigurasi model diubah untuk menggunakan file `best.onnx` (`runs/safestreet_v1_2/weights/best.onnx`) dengan tujuan menghemat penggunaan memori, aplikasi gagal memproses gambar dan server *backend* Uvicorn mengalami *crash*.

Pesan *error* utama yang muncul pada terminal *backend* adalah:
```
RuntimeError: Error when binding input: There's no data transfer registered for copying tensors from Device:[DeviceType:1 MemoryType:0 VendorId:4318 DeviceId:0 Alignment:0] to Device:[DeviceType:0 MemoryType:0 VendorId:0 DeviceId:0 Alignment:0]
```

## Analisis Akar Masalah (Root Cause)
Pesan *error* tersebut mengindikasikan adanya ketidakcocokan perangkat (*device mismatch*) antara *tensor* yang dikirim oleh PyTorch dan *execution provider* yang digunakan oleh ONNX Runtime. 
1. **Konflik Paket ONNX Runtime**: Terdapat dua paket yang terinstal secara bersamaan di dalam *environment* (yaitu `onnxruntime` untuk CPU dan `onnxruntime-gpu` untuk GPU). Hal ini sering menyebabkan konflik di mana versi CPU secara tidak sengaja menimpa eksekusi versi GPU.
2. **Ketidakcocokan Versi CUDA**: Setelah paket dibersihkan dan `onnxruntime-gpu` versi terbaru (1.29.0) diinstal, eksekusi tetap gagal. Hal ini dikarenakan versi terbaru dari `onnxruntime-gpu` membutuhkan lingkungan **CUDA versi 13**, sedangkan PyTorch pada *environment* ini berjalan di atas **CUDA versi 12.1**.
3. Karena CUDA 13 tidak ditemukan, `onnxruntime-gpu` gagal memuat modul `CUDAExecutionProvider` dan secara otomatis (*fallback*) menggunakan CPU. Di saat yang bersamaan, PyTorch tetap mengirimkan data gambar (*tensor*) yang berada di memori GPU (`DeviceType:1`). Akibatnya, ONNX (yang berjalan di CPU) gagal memproses tensor dari GPU tersebut, sehingga memicu *RuntimeError* dan membuat server *crash*.

## Solusi dan Perbaikan yang Telah Dilakukan
1. **Pembersihan Paket**: Mencopot (*uninstall*) kedua paket `onnxruntime` dan `onnxruntime-gpu` secara menyeluruh dari *environment* Python untuk mencegah konflik pustaka.
2. **Downgrade Versi ONNX Runtime GPU**: Menginstal ulang paket `onnxruntime-gpu` secara spesifik ke versi **1.19.2**. Versi ini dipilih karena merupakan versi stabil terakhir yang memberikan dukungan *native* secara penuh terhadap lingkungan **CUDA 12.x** (yang sejalan dengan versi CUDA PyTorch bawaan sistem).
   
   Perintah yang dijalankan:
   ```bash
   pip uninstall -y onnxruntime onnxruntime-gpu
   pip install onnxruntime-gpu==1.19.2
   ```
3. **Pengujian Internal**: Sebuah *script* tes dibuat dan dijalankan di *background* untuk memastikan model dapat dimuat dengan baik menggunakan `CUDAExecutionProvider` (GPU) tanpa melakukan *fallback* ke CPU. Hasilnya sukses dan inferensi berhasil diselesaikan di GPU.

## Kesimpulan
Saat ini, aplikasi sudah stabil dan Anda dapat terus menggunakan model berekstensi `.onnx` (seperti `best.onnx`) di environment Anda dengan dukungan akselerasi GPU penuh. Penggunaan memori seharusnya kini menjadi lebih efisien tanpa mengorbankan fungsionalitas pendeteksian objek.
