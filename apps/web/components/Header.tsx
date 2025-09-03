"use client";
import Link from "next/link";
import { TenantBadge } from "@/components/TenantBadge";
import { resetTenant } from "@/lib/apiClient";
import { ensureTenant, getTenant, setTenant } from "@/lib/tenant";
import { useEffect, useState } from "react";

export function Header() {
  const [tenant, setTenantState] = useState<string | null>(null);
  useEffect(() => {
    const t = getTenant();
    if (t) setTenantState(t); else ensureTenant().then(setTenantState);
  }, []);

  const onReset = async () => {
    if (!tenant) return;
    try {
      await resetTenant(tenant);
      const t = await ensureTenant();
      setTenant(t);
      setTenantState(t);
      alert("Сессия сброшена");
    } catch (e) {
      alert((e as any)?.message || "Ошибка сброса");
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto max-w-5xl px-4 py-3 flex items-center justify-between gap-4">
        <nav className="flex items-center gap-5">
          <Link href="/" className="font-semibold tracking-tight text-neutral-900">DocRAG</Link>
          <Link href="/upload" className="text-neutral-700 hover:text-neutral-900 transition-colors">Загрузка</Link>
          <Link href="/ask" className="text-neutral-700 hover:text-neutral-900 transition-colors">Вопрос</Link>
          <Link href="/debug/search" className="text-neutral-400 hover:text-neutral-700 transition-colors">Debug</Link>
        </nav>
        <div className="flex items-center gap-3">
          {tenant && <TenantBadge tenant={tenant} />}
          <button onClick={onReset} className="btn-secondary">Сброс</button>
        </div>
      </div>
    </header>
  );
}
