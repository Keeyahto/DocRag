import type { IndexAcceptedResponse, StatusResponse } from "@/lib/types";

export function UploadList({ result, status }: { result: IndexAcceptedResponse | null, status: StatusResponse | null }) {
  if (!result) return null;
  const isSync = result.job_id === "sync";
  return (
    <div className="card">
      <div className="card-body">
        <h3 className="font-semibold mb-2">Результат индексации</h3>
        <div className="text-sm text-neutral-700 space-y-2">
          <div className="flex items-center justify-between">
            <div>Статус: {isSync ? "готово (синхронно)" : (status?.status || "в очереди")}</div>
            {!isSync && status && <div className="badge">{status.progress}%</div>}
          </div>
          {!isSync && status && (
            <div className="progress"><div className="progress-bar" style={{ width: `${status.progress}%` }} /></div>
          )}
          <ul className="list-disc pl-6">
            {result.files.map((f) => (
              <li key={f.filename}>{f.filename} ({Math.round(f.size_bytes/1024)} KB)</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
