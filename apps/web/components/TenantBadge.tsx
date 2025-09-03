"use client";
import { useState } from "react";

export function TenantBadge({ tenant }: { tenant: string }) {
  const [copied, setCopied] = useState(false);
  const short = tenant.slice(0, 8);
  return (
    <button
      className="text-xs inline-flex items-center gap-1 bg-neutral-100 rounded-lg px-2 py-1 border"
      title="Нажмите для копирования"
      onClick={async () => {
        await navigator.clipboard.writeText(tenant);
        setCopied(true); setTimeout(() => setCopied(false), 1500);
      }}
    >
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500" />
      TENANT: {short}{copied ? " ✓" : ""}
    </button>
  );
}
