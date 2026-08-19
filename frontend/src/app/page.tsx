"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/context/LanguageContext";

export default function Home() {
  const { t } = useLanguage();

  const scrollToAbout = () => {
    document.getElementById("about-section")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Optimized Background Gradients */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.12),_transparent_50%),radial-gradient(circle_at_bottom_right,_rgba(147,51,234,0.12),_transparent_50%)]" />

      <div className="z-10 flex flex-col items-center text-center max-w-4xl space-y-8 min-h-[90vh] justify-center">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
          {t("home.title")}
        </h1>
        
        <p className="text-lg md:text-xl text-zinc-400 max-w-2xl leading-relaxed">
          {t("home.subtitle")}
        </p>

        <div className="flex flex-col sm:flex-row gap-4 w-full justify-center mt-8">
          <Link href="/detect" className="px-8 py-4 rounded-full bg-white text-black font-semibold hover:bg-zinc-200 transition-all active:scale-95 shadow-[0_0_20px_rgba(255,255,255,0.15)] flex items-center justify-center">
            {t("home.launchApp")}
          </Link>
          <button 
            onClick={scrollToAbout}
            className="px-8 py-4 rounded-full bg-zinc-900 text-white font-semibold border border-zinc-800 hover:bg-zinc-800 transition-all active:scale-95"
          >
            {t("home.aboutProject")}
          </button>
        </div>

        <div className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900/50 px-3 py-1 text-sm font-medium text-zinc-300 backdrop-blur-md !mt-2 transition-colors hover:bg-zinc-900/80 cursor-pointer">
          <span className="flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
          YOLOv8 Model Ready
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 !mt-0 w-full text-left">
          <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm hover:border-zinc-700 transition-colors group cursor-default">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">{t("home.feature1.title")}</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">{t("home.feature1.desc")}</p>
          </div>
          <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm hover:border-zinc-700 transition-colors group cursor-default">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">{t("home.feature2.title")}</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">{t("home.feature2.desc")}</p>
          </div>
          <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm hover:border-zinc-700 transition-colors group cursor-default">
            <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">{t("home.feature3.title")}</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">{t("home.feature3.desc")}</p>
          </div>
        </div>
      </div>

      {/* About Section */}
      <section id="about-section" className="z-10 w-full max-w-5xl mt-24 mb-16 pt-16 border-t border-zinc-800/50">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">{t("about.section.title")}</h2>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto mt-6 rounded-full"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
          {/* Datasets */}
          <div className="bg-zinc-900/40 border border-zinc-800 p-8 rounded-3xl backdrop-blur-sm">
            <h3 className="text-2xl font-bold text-white mb-4">{t("about.dataset.title")}</h3>
            <p className="text-zinc-400 leading-relaxed mb-6">{t("about.dataset.desc")}</p>
            <div className="flex flex-wrap gap-3">
              <a href="https://www.kaggle.com/datasets/rohitsuresh15/radroad-anomaly-detection" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-black/50 border border-zinc-700 rounded-lg text-sm text-zinc-300 hover:text-white hover:border-zinc-500 transition-colors flex items-center gap-2">
                RAD Dataset ↗
              </a>
              <a href="https://www.kaggle.com/datasets/lorenzoarcioni/road-damage-dataset-potholes-cracks-and-manholes" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-black/50 border border-zinc-700 rounded-lg text-sm text-zinc-300 hover:text-white hover:border-zinc-500 transition-colors flex items-center gap-2">
                RoadDamage Dataset ↗
              </a>
            </div>
          </div>

          {/* Model Optimization */}
          <div className="bg-zinc-900/40 border border-zinc-800 p-8 rounded-3xl backdrop-blur-sm">
            <h3 className="text-2xl font-bold text-white mb-4">{t("about.model.title")}</h3>
            <p className="text-zinc-400 leading-relaxed">{t("about.model.desc")}</p>
          </div>
        </div>

        {/* Classes List */}
        <div className="mt-8 bg-zinc-900/40 border border-zinc-800 p-8 rounded-3xl backdrop-blur-sm">
          <h3 className="text-2xl font-bold text-white mb-4">{t("about.classes.title")}</h3>
          <p className="text-zinc-400 leading-relaxed mb-6">{t("about.classes.desc")}</p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {["pothole", "crack", "manhole", "speed_bump", "vehicle_small", "vehicle_large", "pedestrian"].map((cls) => (
              <div key={cls} className="flex items-center gap-3 px-4 py-3 bg-black/50 border border-zinc-800 rounded-xl">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="text-zinc-200 capitalize">{t(`label.${cls}`)}</span>
              </div>
            ))}
            <div className="flex items-center gap-3 px-4 py-3 bg-amber-900/10 border border-amber-900/30 rounded-xl">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              <span className="text-zinc-200 capitalize">{t("label.with_helmet")} <span className="text-amber-500/70 text-xs font-mono ml-1">(experimental)</span></span>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 bg-amber-900/10 border border-amber-900/30 rounded-xl">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              <span className="text-zinc-200 capitalize">{t("label.without_helmet")} <span className="text-amber-500/70 text-xs font-mono ml-1">(experimental)</span></span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
