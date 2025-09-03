"use client";
import React, { useEffect, useRef, useState } from "react";
import { ensureTenant, getTenant } from "@/lib/tenant";
import { AskForm } from "@/components/AskForm";
import { StreamAnswer } from "@/components/StreamAnswer";
import type { SourcePreview } from "@/lib/types";

export default function AskPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [sources, setSources] = useState<SourcePreview[] | null>(null);
  const [answer, setAnswer] = useState("");
  const [think, setThink] = useState<string | null>(null);

  // Streaming parser state to handle optional <think>...</think>
  const modeRef = useRef<"pending" | "in_think" | "visible">("pending");
  const bufRef = useRef<string>("");

  const resetStreamState = () => {
    setAnswer("");
    setThink(null);
    setSources(null);
    modeRef.current = "pending";
    bufRef.current = "";
  };

  const handleChunk = (chunk: string) => {
    bufRef.current += chunk;
    // Process buffer based on current mode; loop in case multiple transitions happen in one chunk
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const mode = modeRef.current;
      const buf = bufRef.current;
      if (mode === "pending") {
        const trimmed = buf.replace(/^\s+/, "");
        // Not enough data to decide yet
        if (trimmed.length < 7) return;
        if (trimmed.startsWith("<think>")) {
          // Enter thoughts mode, drop the opening tag and any leading spaces
          const idx = buf.indexOf("<think>");
          bufRef.current = buf.slice(idx + 7);
          modeRef.current = "in_think";
          continue;
        } else {
          // No thoughts; flush buffer to visible answer
          setAnswer((prev) => prev + buf);
          bufRef.current = "";
          modeRef.current = "visible";
          return;
        }
      } else if (mode === "in_think") {
        const closeIdx = buf.indexOf("</think>");
        if (closeIdx === -1) {
          // All buffer is still thoughts
          setThink((prev) => (prev || "") + buf);
          bufRef.current = "";
          return;
        } else {
          // Append thoughts up to closing tag, then switch to visible and keep remainder
          const thoughtPart = buf.slice(0, closeIdx);
          setThink((prev) => (prev || "") + thoughtPart);
          const remainder = buf.slice(closeIdx + 8); // length of </think>
          bufRef.current = remainder;
          modeRef.current = "visible";
          continue;
        }
      } else {
        // visible mode
        if (buf.length === 0) return;
        setAnswer((prev) => prev + buf);
        bufRef.current = "";
        return;
      }
    }
  };

  useEffect(() => {
    const t = getTenant();
    if (t) setTenant(t); else ensureTenant().then(setTenant);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Задайте вопрос</h1>
      <AskForm
        tenant={tenant}
        onNewAnswer={resetStreamState}
        onContext={setSources}
        onText={handleChunk}
      />
      <StreamAnswer answer={answer} sources={sources || []} think={think} />
    </div>
  );
}
