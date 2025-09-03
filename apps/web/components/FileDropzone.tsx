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
      className={`card ${drag ? 'ring-2 ring-blue-300' : ''}`}
      onDragOver={(e)=>{ e.preventDefault(); setDrag(true); }}
      onDragLeave={(e)=>{ e.preventDefault(); setDrag(false); }}
      onDrop={(e)=>{ e.preventDefault(); setDrag(false); onSelect(e.dataTransfer.files); }}
    >
      <div className="card-body text-center">
        <div className="mx-auto mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
            <path d="M12 16a1 1 0 0 1-1-1V9.41l-1.3 1.3a1 1 0 0 1-1.4-1.42l3-3a1 1 0 0 1 1.4 0l3 3a1 1 0 0 1-1.4 1.42L13 9.4V15a1 1 0 0 1-1 1Z"/>
            <path d="M6 18a4 4 0 0 1-1.06-7.86A6 6 0 0 1 18 8a5 5 0 0 1 1.67 9.72A3.5 3.5 0 0 1 17 21H9a3 3 0 0 1-3-3Z"/>
          </svg>
        </div>
        <p className="text-neutral-700">Перетащите файлы сюда или</p>
        <label className="mt-2 inline-block btn-secondary cursor-pointer">
          Выбрать файлы
          <input className="hidden" type="file" multiple accept=".pdf,.md,.txt,.docx" onChange={(e)=>onSelect(e.target.files)} />
        </label>
        <p className="mt-2 text-xs text-neutral-500">Поддерживается: PDF, MD, TXT, DOCX</p>
      </div>
    </div>
  );
}
