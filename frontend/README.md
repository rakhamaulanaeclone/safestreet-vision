# 🖥️ SafeStreet Vision - Frontend

Ini adalah repositori antarmuka pengguna (Frontend) untuk **SafeStreet Vision**, dibangun menggunakan **Next.js 15 (App Router)**, **TypeScript**, dan **Tailwind CSS**.

Frontend ini bertugas sebagai klien interaktif yang mengirimkan gambar atau *frame* video ke *backend* FastAPI (YOLOv8), lalu merender hasil deteksi berupa kotak pembatas (*bounding box*) secara presisi di layar pengguna.

## 🚀 Fitur yang Sudah Diselesaikan (Progress Saat Ini)

### 1. 🏗️ Pondasi UI & Arsitektur
- [x] Inisialisasi proyek dengan **Next.js 15**, **TypeScript**, dan **Tailwind CSS**.
- [x] Konfigurasi *Dark Mode* eksklusif bergaya *Glassmorphism* modern.
- [x] Optimasi performa *rendering*: Mengganti efek CSS Blur berat menjadi *radial-gradient* agar tidak *freeze* di perangkat *mobile* (HP).
- [x] Desain responsif 100% untuk Desktop, Tablet, maupun Mobile.

### 2. 📸 Fitur Deteksi Gambar (Image Upload)
- [x] Komponen unggah gambar interaktif (*drag & drop* atau klik).
- [x] Dukungan kamera asli (native) HP untuk langsung memotret gambar (`capture="environment"`).
- [x] Algoritma konversi titik koordinat (Piksel Absolut ➔ Persentase Dinamis) agar *Bounding Box* tetap menempel presisi meski ukuran gambar/layar berubah-ubah.
- [x] Panel Metrik UI untuk melihat: Waktu Inferensi (*Inference ms*), Jumlah Objek, dan Daftar Kelas beserta Persentase Akurasi (*Confidence*).

### 3. 🎥 Fitur Live Video Detection (Kamera WebRTC)
- [x] Implementasi **Sistem Tab Navigasi** elegan untuk beralih antara Mode Gambar & Mode Live Kamera.
- [x] Menggunakan WebRTC API (`navigator.mediaDevices.getUserMedia`) untuk menyalakan kamera depan/belakang secara dinamis (Tombol *Flip*).
- [x] **Teknik Frame Sampling (Anti-Lag):** Menggunakan pola *Recursive Async Loop* untuk mengirim *frame* ke *backend* hanya saat *request* sebelumnya selesai. Mencegah jaringan kebanjiran data dan browser *crash/freeze*.
- [x] Fitur **📸 Snap (Snapshot)** untuk memotret dari video langsung ke mode gambar statis.
- [x] Tombol **▶ Start Live** cerdas: Kamera tidak akan menyedot baterai/izin sebelum tombol ditekan.

### 4. ✨ "Efek Pelumas" (Frontend Object Tracking)
- [x] Menambahkan algoritma pencocokan *ID* objek antar-frame menggunakan perhitungan Jarak Euclidean (*Euclidean Distance*).
- [x] Menghubungkan *Tracker ID* ke *React Keys* dan CSS Transition (`transition-all`).
- [x] **Hasil:** Kotak deteksi pada Live Video kini meluncur *(gliding)* dengan sangat mulus mengikuti objek, menghilangkan efek berkedip (*flickering*) parah yang disebabkan oleh *motion blur* atau tangan yang bergetar.

---

## 🛠️ Cara Menjalankan Secara Lokal

Pastikan *backend* FastAPI sudah menyala di port `8000` terlebih dahulu.

1. Buka terminal, masuk ke folder `frontend`.
2. Instal dependensi (jika belum):
   ```bash
   npm install
   ```
3. Jalankan *development server*:
   ```bash
   npm run dev
   ```
4. Buka di browser: `http://localhost:3000`

> **Catatan Penting untuk Pengujian di HP:**
> Fitur Kamera WebRTC (`getUserMedia`) mewajibkan koneksi aman. Jika Anda mengaksesnya dari HP via jaringan lokal (misal: `http://192.168.x.x:3000`), browser HP mungkin akan memblokir kamera. Gunakan HTTPS (layanan port-forwarding seperti ngrok/VSCode) atau jalankan di *localhost* HP secara langsung.
