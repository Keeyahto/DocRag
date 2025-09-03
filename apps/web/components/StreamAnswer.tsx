"use client";
import React, { useState } from 'react'
import type { SourcePreview } from "@/lib/types";
import { SourcesList } from "@/components/SourcesList";

export function StreamAnswer({ answer, sources, think }: { answer: string, sources: SourcePreview[], think?: string | null }){
  const [open, setOpen] = useState(false);
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="card">
        <div className="card-body">
          {think && (
            <div className="mb-3">
              <button className="btn-ghost text-blue-700" onClick={()=>setOpen(o=>!o)}>
                {open ? "Скрыть процесс размышления" : "Показать процесс размышления"}
              </button>
              {open && (
                <pre className="mt-2 max-h-56 overflow-auto rounded-xl border bg-neutral-50 p-3 text-xs text-neutral-700 whitespace-pre-wrap">
                  {think}
                </pre>
              )}
            </div>
          )}
          <h3 className="font-semibold mb-2">Ответ</h3>
          <div className="whitespace-pre-wrap text-neutral-800 min-h-[6rem]">
            {answer ? answer : (
              <div className="space-y-2">
                <div className="h-4 w-2/3 bg-neutral-200 rounded animate-pulse" />
                <div className="h-4 w-1/2 bg-neutral-200 rounded animate-pulse" />
              </div>
            )}
          </div>
        </div>
      </div>
      <div>
        <SourcesList sources={sources} />
      </div>
    </div>
  );
}
