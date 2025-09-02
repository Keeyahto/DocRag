import type { StatusResponse } from "@/lib/types";

export function JobStatus({ status }: { status: StatusResponse | null }) {
  if (!status) return null;
  return (
    <div className="mt-2">
      <div className="text-sm">{status.status} • {status.progress}%</div>
      <div className="w-full bg-neutral-200 h-2 rounded">
        <div className="bg-blue-500 h-2 rounded" style={{ width: `${status.progress}%` }} />
      </div>
      {status.error && <pre className="text-xs text-red-700 whitespace-pre-wrap">{status.error}</pre>}
    </div>
  );
}

