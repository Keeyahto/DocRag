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
    <header className="bg-white border-b">
      <div className="container mx-auto max-w-5xl px-4 py-3 flex items-center justify-between gap-4">
        <nav className="flex items-center gap-4">
          <Link href="/" className="font-bold">DocRAG</Link>
          <Link href="/upload">Загрузка</Link>
          <Link href="/ask">Вопрос</Link>
          <Link href="/debug/search" className="text-neutral-500">Debug</Link>
        </nav>
        <div className="flex items-center gap-3">
          {tenant && <TenantBadge tenant={tenant} />}
          <button onClick={onReset} className="rounded-xl px-3 py-1.5 bg-neutral-100 hover:bg-neutral-200">Сброс</button>
        </div>
      </div>
    </header>
  );
}

