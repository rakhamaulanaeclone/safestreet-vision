"use client";

import { useState, useRef, ChangeEvent, useEffect } from "react";
import { useLanguage } from "@/context/LanguageContext";

// Types
type Box = { x1: number; y1: number; x2: number; y2: number };
type Detection = { class_id: number; class_name: string; confidence: number; box: Box };
type ImageSize = { width: number; height: number };
type PredictionResponse = { detections: Detection[]; image_size: ImageSize; inference_ms: number };
type TrackedDetection = Detection & { id: string };

const CLASS_COLORS: Record<string, string> = {
  pothole: "#ef4444",
  crack: "#f97316",
  manhole: "#eab308",
  speed_bump: "#3b82f6",
  vehicle_small: "#a855f7",
  vehicle_large: "#d946ef",
  pedestrian: "#14b8a6",
  with_helmet: "#22c55e",
  without_helmet: "#ef4444",
};

// Algoritma Pelacak Sederhana (Simple ID Matching via Distance)
const matchDetections = (
  newDetections: Detection[],
  oldTracks: TrackedDetection[],
  imgWidth: number,
  imgHeight: number
): TrackedDetection[] => {
  const newTracks: TrackedDetection[] = [];
  const usedOldIndices = new Set<number>();

  newDetections.forEach((newDet) => {
    const newCx = (newDet.box.x1 + newDet.box.x2) / 2 / imgWidth;
    const newCy = (newDet.box.y1 + newDet.box.y2) / 2 / imgHeight;

    let bestMatchIdx = -1;
    let minDistance = 0.25; // Ambang batas maksimal jarak pergerakan antar frame

    oldTracks.forEach((oldDet, i) => {
      if (usedOldIndices.has(i)) return;
      if (oldDet.class_name !== newDet.class_name) return;

      const oldCx = (oldDet.box.x1 + oldDet.box.x2) / 2 / imgWidth;
      const oldCy = (oldDet.box.y1 + oldDet.box.y2) / 2 / imgHeight;

      const dist = Math.hypot(newCx - oldCx, newCy - oldCy);
      if (dist < minDistance) {
        minDistance = dist;
        bestMatchIdx = i;
      }
    });

    if (bestMatchIdx !== -1) {
      // Cocok dengan objek lama, pertahankan ID-nya untuk animasi mulus
      newTracks.push({ ...newDet, id: oldTracks[bestMatchIdx].id });
      usedOldIndices.add(bestMatchIdx);
    } else {
      // Objek baru
      newTracks.push({ ...newDet, id: `obj_${Math.random().toString(36).substr(2, 9)}` });
    }
  });

  return newTracks;
};

export default function Detector() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<"image" | "camera">("image");

  // Image Upload State
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Camera State
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const trackedDetectionsRef = useRef<TrackedDetection[]>([]); // Menyimpan riwayat pelacakan frame
  const [isStreamReady, setIsStreamReady] = useState(false);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const [isLive, setIsLive] = useState(false);
  const [liveResult, setLiveResult] = useState<PredictionResponse | null>(null);

  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      stopCamera();
    };
  }, []);

  useEffect(() => {
    if (activeTab === "image") {
      stopCamera();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    // Jika kamera sedang menyala dan facingMode diubah, restart kamera
    if (activeTab === "camera" && streamRef.current) {
      startCamera();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facingMode]);

  const startCamera = async () => {
    // Jangan panggil stopCamera() secara penuh di sini agar isLive tidak keriset ke false
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setError(null);
    setIsStreamReady(false);
    
    try {
      const newStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      if (!isMounted.current) {
        newStream.getTracks().forEach(t => t.stop());
        return;
      }
      streamRef.current = newStream;
      setIsStreamReady(true);
      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }
    } catch (err: any) {
      if (isMounted.current) {
        setError(t("detect.error") + " " + err.message);
        setIsLive(false);
      }
    }
  };

  const stopCamera = () => {
    if (isMounted.current) setIsLive(false);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (isMounted.current) setIsStreamReady(false);
    }
    trackedDetectionsRef.current = []; // Reset tracker on camera stop
  };

  const toggleLive = async () => {
    if (isLive) {
      stopCamera();
    } else {
      setIsLive(true); // Set true di awal agar animasi UI "Requesting..." muncul
      await startCamera();
    }
  };

  const toggleCameraFacingMode = () => {
    setFacingMode((prev) => (prev === "environment" ? "user" : "environment"));
  };

  // Safe Live Detection Loop
  useEffect(() => {
    let active = true;

    const processFrame = async () => {
      if (!isLive || !videoRef.current || !canvasRef.current) return;
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      if (video.videoWidth === 0 || video.videoHeight === 0) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      try {
        const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.7));
        if (!blob || !active) return;
        
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        const RAW_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const API_URL = RAW_URL.replace(/\/$/, "");
        const response = await fetch(`${API_URL}/predict/video-frame`, {
          method: "POST",
          body: formData,
        });
        
        if (response.ok && active) {
          const data = await response.json();
          setLiveResult(data);
        }
      } catch (e) {
        console.error("Live detection error", e);
      }
    };

    const loop = async () => {
      while (active && isLive) {
        await processFrame();
        await new Promise(resolve => setTimeout(resolve, 150));
      }
    };

    if (isLive) {
      loop();
    } else {
      trackedDetectionsRef.current = [];
    }

    return () => {
      active = false;
    };
  }, [isLive]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    
    setFile(selected);
    if (preview) URL.revokeObjectURL(preview); // cleanup old URL
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const RAW_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const API_URL = RAW_URL.replace(/\/$/, "");
      const response = await fetch(`${API_URL}/predict/image`, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (isMounted.current) setResult(data);
    } catch (err: any) {
      if (isMounted.current) setError(err.message || t("detect.error"));
    } finally {
      if (isMounted.current) setLoading(false);
    }
  };

  const handleDownloadImage = () => {
    if (!preview || !result) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);

      // Draw bounding boxes
      result.detections.forEach(det => {
        const { x1, y1, x2, y2 } = det.box;
        const color = CLASS_COLORS[det.class_name] || "#ffffff";
        
        // Rect
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(2, img.width / 400);
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        // Background for text
        const fontSize = Math.max(14, img.width / 50);
        ctx.font = `bold ${fontSize}px sans-serif`;
        const translatedLabel = t(`label.${det.class_name}`);
        const text = `${translatedLabel} ${Math.round(det.confidence * 100)}%`;
        
        const textWidth = ctx.measureText(text).width;
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - fontSize - 6, textWidth + 8, fontSize + 6);
        
        // Text
        ctx.fillStyle = "#ffffff";
        ctx.fillText(text, x1 + 4, y1 - 6);
      });

      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/jpeg", 0.9);
      a.download = "safestreet_detection_result.jpg";
      a.click();
    };
    img.src = preview;
  };

  const takeSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (video.videoWidth === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      if (!blob) return;
      
      const snapshotFile = new File([blob], "snapshot.jpg", { type: "image/jpeg" });
      setFile(snapshotFile);
      if (preview) URL.revokeObjectURL(preview);
      setPreview(URL.createObjectURL(snapshotFile));
      setResult(null);
      setError(null);
      
      setActiveTab("image");
    }, "image/jpeg", 1.0);
  };

  const renderBoundingBoxes = (targetResult: PredictionResponse | null, isLiveFeed: boolean = false) => {
    if (!targetResult) return null;

    let detectionsToRender: TrackedDetection[];

    if (isLiveFeed) {
      detectionsToRender = matchDetections(
        targetResult.detections, 
        trackedDetectionsRef.current, 
        targetResult.image_size.width, 
        targetResult.image_size.height
      );
      trackedDetectionsRef.current = detectionsToRender;
    } else {
      detectionsToRender = targetResult.detections.map(d => ({ ...d, id: Math.random().toString() }));
    }

    return detectionsToRender.map((det) => {
      const { x1, y1, x2, y2 } = det.box;
      const { width, height } = targetResult.image_size;
      
      const left = (x1 / width) * 100;
      const top = (y1 / height) * 100;
      const boxWidth = ((x2 - x1) / width) * 100;
      const boxHeight = ((y2 - y1) / height) * 100;
      
      const color = CLASS_COLORS[det.class_name] || "#ffffff";
      const translatedLabel = t(`label.${det.class_name}`);

      return (
        <div 
          key={det.id} 
          // Ditambahkan transisi CSS untuk efek pergerakan pelumas (smoothing)
          className={`absolute border-2 pointer-events-none ${isLiveFeed ? 'transition-all duration-300 ease-out' : ''}`}
          style={{
            left: `${left}%`,
            top: `${top}%`,
            width: `${boxWidth}%`,
            height: `${boxHeight}%`,
            borderColor: color,
            backgroundColor: `${color}20`
          }}
        >
          <span 
            className="absolute top-0 left-0 -translate-y-full px-1.5 py-0.5 text-[9px] md:text-[11px] font-bold whitespace-nowrap text-white rounded-t-sm shadow-sm"
            style={{ backgroundColor: color }}
          >
            {translatedLabel} {Math.round(det.confidence * 100)}%
          </span>
        </div>
      );
    });
  };

  const renderStats = (targetResult: PredictionResponse | null, isLiveLoading: boolean) => {
    if (!targetResult && !isLiveLoading) {
      return <p className="text-zinc-500 italic text-sm md:text-base">No results yet.</p>;
    }

    if (!targetResult && isLiveLoading) {
      return (
        <p className="text-zinc-400 animate-pulse flex items-center gap-2 text-sm md:text-base">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></span>
          {t("detect.processing")}
        </p>
      );
    }

    if (!targetResult) return null;

    return (
      <div className="space-y-4 md:space-y-6 animate-in fade-in duration-300">
        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <div className="bg-black/50 p-3 md:p-4 rounded-xl border border-zinc-800">
            <p className="text-xs md:text-sm text-zinc-400 mb-1">{t("detect.inferenceTime")}</p>
            <p className="text-lg md:text-2xl font-bold text-white">{targetResult.inference_ms.toFixed(1)} <span className="text-xs md:text-sm text-zinc-500 font-normal">ms</span></p>
          </div>
          <div className="bg-black/50 p-3 md:p-4 rounded-xl border border-zinc-800">
            <p className="text-xs md:text-sm text-zinc-400 mb-1">{t("detect.objectsDetected")}</p>
            <p className="text-lg md:text-2xl font-bold text-white">{targetResult.detections.length}</p>
          </div>
        </div>

        <div>
          <h4 className="text-xs md:text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-2 md:mb-3">{t("detect.objectsDetected")}</h4>
          {targetResult.detections.length === 0 ? (
            <p className="text-zinc-500 text-sm">No objects detected.</p>
          ) : (
            <ul className="space-y-2 md:space-y-3 max-h-[250px] overflow-y-auto pr-2 custom-scrollbar">
              {targetResult.detections.map((det, i) => (
                <li key={i} className="flex items-center justify-between bg-black/30 p-2 md:p-3 rounded-lg border border-zinc-800/50">
                  <div className="flex items-center gap-2 md:gap-3">
                    <span 
                      className="w-2 h-2 md:w-3 md:h-3 rounded-full shrink-0" 
                      style={{ backgroundColor: CLASS_COLORS[det.class_name] || "#ffffff" }}
                    />
                    <span className="text-zinc-200 capitalize text-xs md:text-sm truncate">{t(`label.${det.class_name}`)}</span>
                  </div>
                  <span className="text-zinc-400 text-xs md:text-sm font-mono shrink-0">{Math.round(det.confidence * 100)}%</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 md:space-y-8">
      
      <div className="flex bg-zinc-900/80 p-1.5 rounded-xl w-full max-w-xs mx-auto border border-zinc-800 backdrop-blur-md">
        <button 
          onClick={() => setActiveTab("image")} 
          className={`flex-1 py-2 md:py-2.5 rounded-lg text-sm font-semibold transition-all ${
            activeTab === "image" ? "bg-white text-black shadow-lg" : "text-zinc-400 hover:text-white"
          }`}
        >
          {t("detect.uploadImage")}
        </button>
        <button 
          onClick={() => setActiveTab("camera")} 
          className={`flex-1 py-2 md:py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
            activeTab === "camera" ? "bg-white text-black shadow-lg" : "text-zinc-400 hover:text-white"
          }`}
        >
          {isLive && <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>}
          {t("detect.liveVideo")}
        </button>
      </div>

      {error && (
        <div className="p-3 md:p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm md:text-base text-center break-words">
          {error}
        </div>
      )}

      <canvas ref={canvasRef} className="hidden" />

      {activeTab === "image" && (
        <div className="space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div 
            className="relative flex flex-col items-center justify-center p-8 md:p-12 border-2 border-dashed border-zinc-700 rounded-2xl md:rounded-3xl bg-zinc-900/50 hover:bg-zinc-900/80 transition-colors cursor-pointer group"
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
            />
            <div className="h-12 w-12 md:h-16 md:w-16 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 mb-3 md:mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6 md:w-8 md:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-lg md:text-xl font-semibold text-white mb-1 md:mb-2 text-center">{t("detect.chooseImage")}</h3>
            <p className="text-xs md:text-sm text-zinc-400 text-center">(JPEG, PNG)</p>
          </div>

          {preview && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
              <div className="lg:col-span-2 space-y-4">
                <div className="flex justify-center rounded-xl md:rounded-2xl overflow-hidden border border-zinc-800 bg-black shadow-2xl relative w-full">
                  <div className="relative inline-flex max-w-full">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={preview} alt="Preview" className="max-h-[50vh] md:max-h-[70vh] w-auto max-w-full block" />
                    {renderBoundingBoxes(result, false)}
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row justify-end gap-3">
                  {result && (
                    <button 
                      onClick={handleDownloadImage}
                      className="w-full md:w-auto px-6 py-3 rounded-xl md:rounded-full bg-zinc-800 text-white font-semibold hover:bg-zinc-700 transition-colors flex items-center justify-center gap-2 border border-zinc-700"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {t("detect.downloadImage")}
                    </button>
                  )}
                  <button 
                    onClick={handleUpload}
                    disabled={loading}
                    className="w-full md:w-auto px-6 md:px-8 py-3 rounded-xl md:rounded-full bg-blue-600 text-white font-semibold hover:bg-blue-500 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                  >
                    {loading && (
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {loading ? t("detect.processing") : "Run Detection"}
                  </button>
                </div>
              </div>
              
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl md:rounded-2xl p-4 md:p-6 backdrop-blur-sm h-fit shadow-xl">
                <h3 className="text-lg md:text-xl font-bold text-white mb-4 md:mb-6">Detection Results</h3>
                {renderStats(result, loading)}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "camera" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="lg:col-span-2 space-y-4">
            
            <div className="flex justify-center rounded-xl md:rounded-2xl overflow-hidden border border-zinc-800 bg-black shadow-2xl relative min-h-[250px] md:min-h-[300px] w-full">
              {!isStreamReady && !error && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 p-4 text-center">
                  {isLive ? (
                    <>
                      <svg className="animate-spin h-6 w-6 md:h-8 md:w-8 text-zinc-600 mb-3 md:mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="text-sm md:text-base">Requesting Camera Access...</span>
                    </>
                  ) : (
                    <div className="flex flex-col items-center gap-3">
                      <svg className="w-10 h-10 md:w-12 md:h-12 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm md:text-base">Camera is off. Click "Start Live" to activate.</span>
                    </div>
                  )}
                </div>
              )}
              
              <div className="relative inline-flex max-w-full">
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted 
                  className="max-h-[50vh] md:max-h-[70vh] w-auto max-w-full block" 
                />
                
                <div className="absolute inset-0">
                  {isLive && renderBoundingBoxes(liveResult, true)}
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3 md:gap-4 bg-zinc-900/50 p-3 md:p-4 rounded-xl md:rounded-2xl border border-zinc-800 backdrop-blur-sm">
              <button 
                onClick={toggleCameraFacingMode}
                className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-zinc-800 text-zinc-300 text-sm md:text-base font-medium hover:bg-zinc-700 transition-colors flex justify-center items-center gap-2"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Flip
              </button>
              
              <div className="flex flex-1 sm:flex-none gap-2 md:gap-3">
                <button 
                  onClick={takeSnapshot}
                  disabled={!isLive}
                  className="flex-1 sm:flex-none px-3 md:px-5 py-2.5 rounded-lg border border-zinc-700 text-white text-sm md:text-base font-semibold hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex justify-center items-center gap-1.5"
                >
                  <span className="text-base md:text-lg">📸</span> Snap
                </button>
                <button 
                  onClick={toggleLive}
                  className={`flex-[2] sm:flex-none px-4 md:px-6 py-2.5 rounded-lg text-white text-sm md:text-base font-semibold transition-colors flex justify-center items-center gap-2 ${
                    isLive 
                      ? "bg-red-600 hover:bg-red-700 shadow-[0_0_15px_rgba(220,38,38,0.4)]" 
                      : "bg-blue-600 hover:bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                  }`}
                >
                  {isLive ? (
                    <>
                      <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-white rounded-full animate-pulse"></span>
                      {t("detect.stopCamera")}
                    </>
                  ) : (
                    "▶ " + t("detect.startCamera")
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl md:rounded-2xl p-4 md:p-6 backdrop-blur-sm h-fit shadow-xl">
            <h3 className="text-lg md:text-xl font-bold text-white mb-4 md:mb-6">Live Feed Stats</h3>
            {!isLive ? (
              <p className="text-zinc-500 italic text-sm md:text-base">Click "Start Live" to analyze the camera feed in real-time.</p>
            ) : (
              renderStats(liveResult, isLive && !liveResult)
            )}
          </div>
        </div>
      )}

    </div>
  );
}
