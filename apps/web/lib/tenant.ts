export function getTenant(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('docrag_tenant');
}

export function setTenant(id: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('docrag_tenant', id);
}

export async function ensureTenant(apiBase?: string): Promise<string> {
  const current = getTenant();
  if (current) return current;
  const base = apiBase || process.env.NEXT_PUBLIC_API_BASE_URL || '';
  const res = await fetch(`${base}/tenant/new`, { method: 'POST' });
  if (!res.ok) throw new Error('Не удалось создать tenant');
  const data = await res.json();
  setTenant(data.tenant);
  return data.tenant;
}

