"use client";
import { useState } from "react";

export function TenantBadge({ tenant }: { tenant: string }) {
  const [copied, setCopied] = useState(false);
  const short = tenant.slice(0, 8);
  return (
    <button
      className="text-xs bg-neutral-100 rounded px-2 py-1"
      title="Нажмите для копирования"
      onClick={async () => {
        await navigator.clipboard.writeText(tenant);
        setCopied(true); setTimeout(() => setCopied(false), 1500);
      }}
    >
      TENANT: {short}{copied ? " ✓" : ""}
    </button>
  );
}

