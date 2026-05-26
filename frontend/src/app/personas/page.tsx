"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchPersonas, Persona } from "@/lib/api";

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    fetchPersonas()
      .then(setPersonas)
      .catch(() => setError("加载角色失败"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">
        选择你的AI伴侣
      </h1>
      <p className="text-gray-500 mb-8">Choose your companion</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
        {personas.map((p) => (
          <div
            key={p.id}
            onClick={() => router.push(`/chat?persona_id=${p.id}`)}
            className="bg-white/80 backdrop-blur rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all cursor-pointer border border-orange-100 hover:border-orange-300"
          >
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              {p.name}
            </h2>
            <p className="text-sm text-gray-600 mb-3">{p.personality}</p>
            <p className="text-xs text-gray-400 line-clamp-3">
              {p.speaking_style}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
