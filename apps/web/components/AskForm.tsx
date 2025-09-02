"use client";
import React, { useState } from "react";
import { ask, askStream } from "@/lib/apiClient";

export function AskForm({ tenant, onNewAnswer, onContext, onText }:{ tenant: string|null, onNewAnswer:()=>void, onContext:(s:any)=>void, onText:(t:string)=>void }){
  const [q, setQ] = useState("");
  const [k, setK] = useState<number>(Number(process.env.NEXT_PUBLIC_TOP_K || 5));
  const [loading, setLoading] = useState(false);
  const can = !!tenant && q.trim().length>0 && !loading;

  const submitPlain = async () => {
    if (!tenant) return;
    setLoading(true); onNewAnswer();
    try {
      const res = await ask(tenant, q, k);
      onContext(res.sources);
      onText(res.answer);
    } catch (e) {
      alert((e as any)?.message || "Ошибка запроса");
    } finally { setLoading(false); }
  };

  const submitStream = async () => {
    if (!tenant) return;
    setLoading(true); onNewAnswer();
    try {
      await askStream(tenant, q, k, onContext, (t)=>onText(t), ()=>setLoading(false), (m)=>{ alert(m); setLoading(false); });
    } catch(e){ setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <textarea value={q} onChange={e=>setQ(e.target.value)} placeholder="Ваш вопрос" className="w-full border rounded px-3 py-2 h-28" />
      <div className="flex items-center gap-3">
        <label className="text-sm text-neutral-700">top_k</label>
        <input type="number" value={k} min={1} onChange={e=>setK(Number(e.target.value))} className="w-20 border rounded px-2 py-1" />
      </div>
      <div className="flex gap-3">
        <button disabled={!can} onClick={submitPlain} className="rounded-xl px-4 py-2 bg-neutral-100 hover:bg-neutral-200 disabled:opacity-50">Спросить (без стрима)</button>
        <button disabled={!can} onClick={submitStream} className="rounded-xl px-4 py-2 bg-neutral-100 hover:bg-neutral-200 disabled:opacity-50">Стримить ответ</button>
      </div>
    </div>
  );
}
