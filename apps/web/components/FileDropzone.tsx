"use client";
import React, { useCallback, useState } from "react";
import { validateFiles } from "@/lib/validators";

export function FileDropzone({ onFiles }: { onFiles: (fs: File[]) => void }) {
  const [drag, setDrag] = useState(false);
  const onSelect = useCallback((files: FileList | null) => {
    if (!files) return;
    const arr = Array.from(files);
    const val = validateFiles(arr);
    if (val.ok) onFiles(arr); else alert(val.message);
  }, [onFiles]);

  return (
    <div
      className={`border-dashed border rounded-xl p-6 bg-white text-center ${drag ? 'bg-neutral-100' : ''}`}
      onDragOver={(e)=>{ e.preventDefault(); setDrag(true); }}
      onDragLeave={(e)=>{ e.preventDefault(); setDrag(false); }}
      onDrop={(e)=>{ e.preventDefault(); setDrag(false); onSelect(e.dataTransfer.files); }}
    >
      <p className="mb-3">Перетащите файлы сюда или выберите</p>
      <input type="file" multiple accept=".pdf,.md,.txt,.docx" onChange={(e)=>onSelect(e.target.files)} />
    </div>
  );
}
