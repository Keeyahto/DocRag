"use client";
import React, { useEffect, useState } from "react";
import { ensureTenant } from "@/lib/tenant";
import { FileDropzone } from "@/components/FileDropzone";
import { UploadList } from "@/components/UploadList";
import { indexFiles, getStatus } from "@/lib/apiClient";
import type { FileInfo, IndexAcceptedResponse, StatusResponse } from "@/lib/types";
import Link from "next/link";

export default function UploadPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [selected, setSelected] = useState<File[]>([]);
  const [result, setResult] = useState<IndexAcceptedResponse | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    ensureTenant().then(setTenant);
  }, []);

  useEffect(() => {
    if (!result || !result.job_id || result.job_id === "sync") return;
    const id = setInterval(async () => {
      try {
        const s = await getStatus(result.job_id);
        setStatus(s);
        if (["done", "error"].includes(s.status)) clearInterval(id);
      } catch (e) {
        clearInterval(id);
      }
    }, 1500);
    return () => clearInterval(id);
  }, [result]);

  const onUpload = async () => {
    if (!tenant || selected.length === 0) return;
    setLoading(true);
    try {
      const res = await indexFiles(tenant, selected);
      setResult(res);
    } catch (e) {
      alert((e as any)?.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Загрузка документов</h1>
      <FileDropzone onFiles={setSelected} />
      <div className="flex items-center gap-3">
        <button disabled={!tenant || selected.length===0 || loading} onClick={onUpload} className="btn-primary">
          {loading && (<span className="inline-block h-4 w-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin" />)}
          Индексировать {selected.length>0 && `(${selected.length})`}
        </button>
        {selected.length>0 && (
          <span className="badge">Выбрано файлов: {selected.length}</span>
        )}
      </div>
      <UploadList result={result} status={status} />
      { (result?.job_id === "sync" || status?.status === "done") && (
        <Link href="/ask" className="inline-block btn-secondary">Перейти к вопросам</Link>
      )}
    </div>
  );
}
