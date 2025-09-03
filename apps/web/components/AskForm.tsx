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
    <div className="card">
      <div className="card-body space-y-4">
        <textarea value={q} onChange={e=>setQ(e.target.value)} placeholder="Ваш вопрос" className="input w-full h-32" />
        <div className="flex items-center gap-3">
          <label className="label">top_k</label>
          <input type="number" value={k} min={1} onChange={e=>setK(Number(e.target.value))} className="input w-24" />
          {loading && (
            <div className="flex-1">
              <div className="progress"><div className="progress-bar w-1/3 animate-[progress_1.2s_ease-in-out_infinite]" /></div>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <button disabled={!can} onClick={submitPlain} className="btn-secondary">Спросить (без стрима)</button>
          <button disabled={!can} onClick={submitStream} className="btn-primary">
            {loading && (<span className="inline-block h-4 w-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin" />)}
            Стримить ответ
          </button>
        </div>
      </div>
    </div>
  );
}
