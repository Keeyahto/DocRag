import type { IndexAcceptedResponse, IndexSyncResponse, StatusResponse, QAResponse, SourcePreview, ErrorEnvelope } from "@/lib/types";
import { parseSSE } from "@/lib/sse";

// Default to API on localhost:8000 when not provided via env
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit, opts?: { tenant?: string, expectJson?: boolean }): Promise<T> {
  const headers = new Headers(init?.headers || {});
  headers.set('Accept', 'application/json');
  if (!headers.has('Content-Type') && init?.body && !(init?.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (opts?.tenant) headers.set('X-Tenant-ID', opts.tenant);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      const err = await res.json() as ErrorEnvelope;
      throw new Error(err?.detail?.error?.message || `HTTP ${res.status}`);
    }
    throw new Error(`HTTP ${res.status}`);
  }
  if (opts?.expectJson === false) return undefined as unknown as T;
  return await res.json() as T;
}

export async function createTenant(): Promise<{ tenant: string }>{
  return apiFetch('/tenant/new', { method: 'POST' });
}

export async function indexFiles(tenant: string, files: File[]): Promise<IndexAcceptedResponse | IndexSyncResponse> {
  const fd = new FormData();
  files.forEach(f => fd.append('files', f));
  return apiFetch('/index', { method: 'POST', body: fd }, { tenant });
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  return apiFetch(`/status/${jobId}`, { method: 'GET' });
}

export async function ask(tenant: string, question: string, topK?: number): Promise<QAResponse> {
  return apiFetch('/answer', { method: 'POST', body: JSON.stringify({ question, top_k: topK }) }, { tenant });
}

export async function askStream(
  tenant: string,
  question: string,
  topK: number|undefined,
  onContext: (sources: SourcePreview[]) => void,
  onToken: (t: string) => void,
  onDone: () => void,
  onError: (m: string) => void,
): Promise<void> {
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');
  headers.set('Accept', 'text/event-stream');
  headers.set('X-Tenant-ID', tenant);
  const res = await fetch(`${API_BASE}/answer/stream`, { method: 'POST', headers, body: JSON.stringify({ question, top_k: topK }) });
  if (!res.ok || !res.body) {
    onError(`HTTP ${res.status}`);
    return;
  }
  await parseSSE(res.body, { onContext, onToken, onDone, onError });
}

export async function search(tenant: string, q: string, k?: number): Promise<{ results: SourcePreview[] }>{
  const sp = new URLSearchParams({ tenant, q });
  if (k) sp.set('k', String(k));
  return apiFetch(`/search?${sp.toString()}`, { method: 'GET' });
}

export async function resetTenant(tenant: string): Promise<{ deleted: boolean }>{
  return apiFetch('/reset', { method: 'POST' }, { tenant });
}
