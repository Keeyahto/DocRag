import Link from "next/link";
import { HealthBadge } from "@/components/HealthBadge";

export default function Page() {
  return (
    <div className="space-y-10">
      <section className="text-center space-y-6">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
          DocRAG — локальный RAG по вашим документам
        </h1>
        <p className="text-neutral-700 max-w-2xl mx-auto">
          PDF/MD/TXT/DOCX • FAISS • потоковые ответы • Telegram-бот
        </p>
        <div className="flex items-center gap-3 justify-center">
          <Link href="/upload" className="btn-primary">Загрузить документы</Link>
          <Link href="/ask" className="btn-secondary">Задать вопрос</Link>
        </div>
      </section>
      <section className="grid md:grid-cols-3 gap-4">
        {[1,2,3].map((i) => (
          <div key={i} className="card">
            <div className="card-body">
              <h3 className="font-semibold mb-2">Шаг {i}</h3>
              <p className="text-sm text-neutral-700">
                {i===1 && "Загрузите документы на странице загрузки."}
                {i===2 && "Подождите индексации (или сразу, если синхронно)."}
                {i===3 && "Задайте вопрос — получите ответ и источники."}
              </p>
            </div>
          </div>
        ))}
      </section>
      <div className="flex justify-center"><HealthBadge /></div>
    </div>
  );
}
