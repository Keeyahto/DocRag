"use client";
import React, { useEffect, useState } from "react";
import { ensureTenant, getTenant } from "@/lib/tenant";
import { AskForm } from "@/components/AskForm";
import { StreamAnswer } from "@/components/StreamAnswer";
import type { SourcePreview } from "@/lib/types";

export default function AskPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [sources, setSources] = useState<SourcePreview[] | null>(null);
  const [answer, setAnswer] = useState("");

  useEffect(() => {
    const t = getTenant();
    if (t) setTenant(t); else ensureTenant().then(setTenant);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Задайте вопрос</h1>
      <AskForm tenant={tenant} onNewAnswer={() => { setAnswer(""); setSources(null); }} onContext={setSources} onText={(t) => setAnswer((prev) => prev + t)} />
      <StreamAnswer answer={answer} sources={sources || []} />
    </div>
  );
}
