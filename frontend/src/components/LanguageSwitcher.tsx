"use client";

import { useLanguage } from "@/context/LanguageContext";

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="absolute top-6 right-6 z-50 flex space-x-2">
      <button
        onClick={() => setLanguage("en")}
        className={`px-3 py-1 text-sm font-medium rounded-full transition-colors ${
          language === "en" ? "bg-white text-black" : "bg-zinc-800 text-zinc-400 hover:text-white"
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLanguage("id")}
        className={`px-3 py-1 text-sm font-medium rounded-full transition-colors ${
          language === "id" ? "bg-white text-black" : "bg-zinc-800 text-zinc-400 hover:text-white"
        }`}
      >
        ID
      </button>
    </div>
  );
}
