"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

type Language = "en" | "id";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations = {
  en: {
    // page.tsx
    "home.title": "SafeStreet Vision",
    "home.subtitle": "Real-time AI object detection for smarter and safer roads. Detecting various types of road damage with high precision.",
    "home.launchApp": "Launch App",
    "home.aboutProject": "About Project",
    "home.feature1.title": "Real-time Inference",
    "home.feature1.desc": "Powered by FastAPI and YOLOv8 for lightning-fast detection on images and video streams.",
    "home.feature2.title": "9-Class Detection",
    "home.feature2.desc": "Identifies potholes, cracks, speed bumps, vehicles, pedestrians, and helmet compliance.",
    "home.feature3.title": "High Precision",
    "home.feature3.desc": "Optimized model achieving robust mAP metrics across diverse road conditions and scenarios.",
    
    // About Section
    "about.section.title": "About This Project",
    "about.dataset.title": "Datasets & Merging",
    "about.dataset.desc": "SafeStreet Vision is built by combining multiple robust datasets to achieve comprehensive 9-class detection. We utilized public datasets from Kaggle including RAD (Road Anomaly Detection) and RoadDamage, and merged them with Roboflow helmet detection datasets to create a unified pipeline.",
    "about.classes.title": "Detection Classes",
    "about.classes.desc": "Our model recognizes the following classes. Note that helmet detection is currently marked as experimental due to a limited amount of training data from the datasets source.",
    "about.model.title": "YOLOv8 & ONNX Optimization",
    "about.model.desc": "The model was trained using YOLOv8 and subsequently exported to ONNX format. This optimization significantly reduces memory consumption and speeds up CPU inference times without sacrificing accuracy. We also enforce a strict Confidence Threshold of 15% (0.15) to ensure high sensitivity to potential road hazards.",

    // Detector.tsx
    "detect.pageTitle": "Object Detection",
    "detect.pageSubtitle": "Upload an image or use your camera to instantly detect road damage and monitor helmet usage using our YOLOv8 model.",
    "detect.back": "Back to Home",
    "detect.title": "SafeStreet Vision Detector",
    "detect.uploadImage": "Upload Image",
    "detect.liveVideo": "Live Video",
    "detect.chooseImage": "Choose an image to detect...",
    "detect.startCamera": "Start Camera",
    "detect.stopCamera": "Stop Camera",
    "detect.processing": "Processing...",
    "detect.downloadImage": "Download Result",
    "detect.inferenceTime": "Inference Time:",
    "detect.objectsDetected": "Objects Detected:",
    "detect.error": "Prediction failed! Please ensure the backend is running.",
    
    // Labels
    "label.pothole": "pothole",
    "label.crack": "crack",
    "label.manhole": "manhole",
    "label.speed_bump": "speed bump",
    "label.vehicle_small": "vehicle (small)",
    "label.vehicle_large": "vehicle (large)",
    "label.pedestrian": "pedestrian",
    "label.with_helmet": "with helmet",
    "label.without_helmet": "without helmet",
  },
  id: {
    // page.tsx
    "home.title": "SafeStreet Vision",
    "home.subtitle": "Deteksi objek AI waktu-nyata untuk jalanan yang lebih pintar dan aman. Mendeteksi kerusakan jalan dan memantau penggunaan helm dengan presisi tinggi.",
    "home.launchApp": "Jalankan Aplikasi",
    "home.aboutProject": "Tentang Proyek",
    "home.feature1.title": "Inferensi Waktu-Nyata",
    "home.feature1.desc": "Ditenagai oleh FastAPI dan YOLOv8 untuk deteksi super cepat pada gambar dan siaran video.",
    "home.feature2.title": "Deteksi 9 Kelas",
    "home.feature2.desc": "Mengenali lubang jalan, retakan, polisi tidur, kendaraan, pejalan kaki, dan kepatuhan helm.",
    "home.feature3.title": "Presisi Tinggi",
    "home.feature3.desc": "Model yang dioptimalkan untuk mencapai akurasi mAP tinggi pada berbagai kondisi jalan.",

    // About Section
    "about.section.title": "Tentang Proyek Ini",
    "about.dataset.title": "Dataset & Penggabungan",
    "about.dataset.desc": "SafeStreet Vision dibangun dengan menggabungkan beberapa dataset andal untuk mencapai deteksi 9-kelas yang komprehensif. Kami menggunakan dataset publik dari Kaggle termasuk RAD (Road Anomaly Detection) dan RoadDamage, lalu menggabungkannya dengan dataset deteksi helm dari Roboflow untuk membuat alur kerja terpadu.",
    "about.classes.title": "Kelas Deteksi",
    "about.classes.desc": "Model kami mengenali kelas-kelas berikut. Perlu diketahui bahwa deteksi helm saat ini berstatus eksperimental karena jumlah data pelatihan yang masih terbatas pada dataset sumber HelmetMain dan HelmetSupp, yang mengakibatkan presisi sedikit lebih rendah.",
    "about.model.title": "Optimasi YOLOv8 & ONNX",
    "about.model.desc": "Model ini dilatih menggunakan YOLOv8 dan kemudian diekspor ke format ONNX. Optimasi ini secara signifikan menghemat konsumsi memori dan mempercepat waktu inferensi CPU tanpa mengorbankan akurasi. Kami juga menerapkan Batas Keyakinan (Confidence Threshold) yang ketat sebesar 15% (0.15) agar sistem sangat peka terhadap potensi bahaya jalan.",

    // Detector.tsx
    "detect.pageTitle": "Deteksi Objek",
    "detect.pageSubtitle": "Unggah gambar atau gunakan kamera Anda untuk langsung mendeteksi kerusakan jalan dan memantau penggunaan helm menggunakan model YOLOv8 kami.",
    "detect.back": "Kembali ke Beranda",
    "detect.title": "Detektor SafeStreet Vision",
    "detect.uploadImage": "Unggah Gambar",
    "detect.liveVideo": "Video Langsung",
    "detect.chooseImage": "Pilih gambar untuk dideteksi...",
    "detect.startCamera": "Mulai Kamera",
    "detect.stopCamera": "Hentikan Kamera",
    "detect.processing": "Memproses...",
    "detect.downloadImage": "Unduh Hasil",
    "detect.inferenceTime": "Waktu Inferensi:",
    "detect.objectsDetected": "Objek Terdeteksi:",
    "detect.error": "Prediksi gagal! Pastikan backend sedang berjalan.",

    // Labels
    "label.pothole": "lubang jalan",
    "label.crack": "retakan",
    "label.manhole": "lubang got",
    "label.speed_bump": "polisi tidur",
    "label.vehicle_small": "kendaraan (kecil)",
    "label.vehicle_large": "kendaraan (besar)",
    "label.pedestrian": "pejalan kaki",
    "label.with_helmet": "memakai helm",
    "label.without_helmet": "tanpa helm",
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  const t = (key: string): string => {
    // @ts-ignore
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
