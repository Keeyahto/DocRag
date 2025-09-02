"use client";
import { useEffect, useState } from "react";
import { getTenant, ensureTenant } from "@/lib/tenant";
import { search } from "@/lib/apiClient";
import type { SourcePreview } from "@/lib/types";
import { SourcesList } from "@/components/SourcesList";

export default function DebugSearchPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SourcePreview[]>([]);

  useEffect(() => {
    const t = getTenant();
    if (t) setTenant(t); else ensureTenant().then(setTenant);
  }, []);

  const onSearch = async () => {
    if (!tenant || !q) return;
    try {
      const res = await search(tenant, q);
      setResults(res.results || []);
    } catch (e) {
      alert((e as any)?.message || "Ошибка поиска");
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Debug Search</h1>
      <div className="flex gap-2">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Введите запрос" className="border rounded px-3 py-2 flex-1" />
        <button onClick={onSearch} className="rounded-xl px-4 py-2 bg-neutral-100 hover:bg-neutral-200">Поиск</button>
      </div>
      <SourcesList sources={results} />
    </div>
  );
}

