import React from 'react'
import { renderHighlighted } from "@/lib/highlight";

export function HighlightedSnippet({ snippet, ranges }:{ snippet: string, ranges: [number, number][] }){
  return (
    <p className="font-mono text-sm leading-relaxed mt-2">
      {renderHighlighted(snippet, ranges)}
    </p>
  );
}
