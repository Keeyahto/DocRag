import Link from "next/link";
import { HealthBadge } from "@/components/HealthBadge";

export default function Page() {
  return (
    <div className="space-y-10">
      <section className="text-center space-y-4">
        <h1 className="text-3xl font-bold">DocRAG — локальный RAG по вашим документам</h1>
        <p className="text-neutral-700">PDF/MD/TXT/DOCX • FAISS • потоковые ответы • Telegram-бот</p>
        <div className="flex items-center gap-3 justify-center">
          <Link href="/upload" className="rounded-xl px-4 py-2 shadow-sm bg-neutral-100 hover:bg-neutral-200">Загрузить документы</Link>
          <Link href="/ask" className="rounded-xl px-4 py-2 shadow-sm bg-neutral-100 hover:bg-neutral-200">Задать вопрос</Link>
        </div>
      </section>
      <section className="grid md:grid-cols-3 gap-4">
        {[1,2,3].map((i) => (
          <div key={i} className="border rounded-xl p-4 bg-white shadow-sm">
            <h3 className="font-semibold mb-2">Шаг {i}</h3>
            <p className="text-sm text-neutral-700">
              {i===1 && "Загрузите документы на странице загрузки."}
              {i===2 && "Подождите индексации (или сразу, если синхронно)."}
              {i===3 && "Задайте вопрос — получите ответ и источники."}
            </p>
          </div>
        ))}
      </section>
      <div className="flex justify-center"><HealthBadge /></div>
    </div>
  );
}

