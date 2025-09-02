import React from 'react'
import type { SourcePreview } from "@/lib/types";
import { HighlightedSnippet } from "@/components/HighlightedSnippet";

export function SourcesList({ sources }: { sources: SourcePreview[] }){
  if (!sources || sources.length === 0) return (
    <div className="text-sm text-neutral-600">Источники не найдены</div>
  );
  const items = [...sources].sort((a,b)=> b.score - a.score);
  return (
    <div className="space-y-3">
      <h3 className="font-semibold">Источники ({items.length})</h3>
      {items.map((s) => (
        <div key={s.id} className="border rounded-xl p-3 bg-white">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">{s.filename || "(без имени)"} {s.page ? `(стр. ${s.page})` : ""}</div>
            <div className="text-xs text-neutral-500">score: {s.score.toFixed(2)}</div>
          </div>
          <HighlightedSnippet snippet={s.snippet} ranges={s.highlights} />
        </div>
      ))}
    </div>
  );
}
