export function Footer() {
  return (
    <footer className="border-t bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto max-w-5xl px-4 py-4 text-sm text-neutral-600 flex items-center justify-between">
        <span className="inline-flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-sky-400 to-blue-600 animate-pulse" />
          Demo • RU/EN
        </span>
        <span>© DocRAG</span>
      </div>
    </footer>
  );
}
