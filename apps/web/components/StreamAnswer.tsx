import type { SourcePreview } from "@/lib/types";
import { SourcesList } from "@/components/SourcesList";

export function StreamAnswer({ answer, sources }: { answer: string, sources: SourcePreview[] }){
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="border rounded-xl p-4 bg-white">
        <h3 className="font-semibold mb-2">Ответ</h3>
        <div className="whitespace-pre-wrap text-neutral-800 min-h-[6rem]">{answer || "(ожидание ответа)"}</div>
      </div>
      <div>
        <SourcesList sources={sources} />
      </div>
    </div>
  );
}

