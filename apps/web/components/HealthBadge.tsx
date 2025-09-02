"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/apiClient";
import type { HealthResponse } from "@/lib/types";

export function HealthBadge(){
  const [h, setH] = useState<HealthResponse | null>(null);
  useEffect(()=>{ apiFetch<HealthResponse>("/health").then(setH).catch(()=>{}); },[]);
  return (
    <div className="text-sm text-neutral-700 flex items-center gap-2">
      <span className={`inline-block w-2.5 h-2.5 rounded-full ${h? 'bg-green-500':'bg-neutral-400'}`}/>
      {h? <span>{h.embed_backend}:{h.embed_model} • {h.llm_backend}:{h.llm_model}</span> : <span>backend...</span>}
    </div>
  );
}

