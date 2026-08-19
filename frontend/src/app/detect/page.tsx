"use client";

import Detector from "@/components/Detector";
import { useLanguage } from "@/context/LanguageContext";

export default function DetectPage() {
  const { t } = useLanguage();

  return (
    <main className="min-h-screen bg-black p-4 md:p-8 pt-16 md:pt-24 relative overflow-hidden">
      {/* Optimized Background Gradients (Fix for mobile freezing) */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.12),_transparent_40%),radial-gradient(circle_at_bottom_right,_rgba(147,51,234,0.12),_transparent_40%)]" />

      <div className="relative z-10 max-w-7xl mx-auto">
        <div className="mb-8 md:mb-12 text-center animate-in fade-in slide-in-from-top-4 duration-700">
          <h1 className="text-3xl md:text-5xl font-bold text-white mb-3 md:mb-4 tracking-tight">{t("detect.pageTitle")}</h1>
          <p className="text-sm md:text-lg text-zinc-400 max-w-2xl mx-auto px-2">
            {t("detect.pageSubtitle")}
          </p>
        </div>
        
        <div className="animate-in fade-in zoom-in-95 duration-700 delay-150 fill-mode-both">
          <Detector />
        </div>
      </div>
    </main>
  );
}
