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
      <button disabled={!tenant || selected.length===0 || loading} onClick={onUpload} className="rounded-xl px-4 py-2 shadow-sm bg-neutral-100 hover:bg-neutral-200 disabled:opacity-50">Индексировать</button>
      <UploadList result={result} status={status} />
      { (result?.job_id === "sync" || status?.status === "done") && (
        <Link href="/ask" className="inline-block rounded-xl px-4 py-2 shadow-sm bg-green-100 hover:bg-green-200">Перейти к вопросам</Link>
      )}
    </div>
  );
}
