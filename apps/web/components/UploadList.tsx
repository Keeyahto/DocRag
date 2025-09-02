import type { IndexAcceptedResponse, StatusResponse } from "@/lib/types";

export function UploadList({ result, status }: { result: IndexAcceptedResponse | null, status: StatusResponse | null }) {
  if (!result) return null;
  const isSync = result.job_id === "sync";
  return (
    <div className="border rounded-xl bg-white p-4">
      <h3 className="font-semibold mb-2">Результат индексации</h3>
      <div className="text-sm text-neutral-700 space-y-1">
        <div>Статус: {isSync ? "готово (синхронно)" : (status?.status || "в очереди")}</div>
        {!isSync && status && <div>Прогресс: {status.progress}%</div>}
        <ul className="list-disc pl-6">
          {result.files.map((f) => (
            <li key={f.filename}>{f.filename} ({Math.round(f.size_bytes/1024)} KB)</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

