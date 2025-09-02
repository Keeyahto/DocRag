const MAX_FILES_PER_REQUEST = Number(process.env.NEXT_PUBLIC_MAX_FILES_PER_REQUEST || 3);
const MAX_FILE_MB = Number(process.env.NEXT_PUBLIC_MAX_FILE_MB || 30);

export function validateFiles(files: File[]): { ok: true } | { ok: false, message: string }{
  if (files.length === 0) return { ok: false, message: 'Не выбраны файлы' };
  if (files.length > MAX_FILES_PER_REQUEST) return { ok: false, message: `Слишком много файлов (>${MAX_FILES_PER_REQUEST})` };
  const allowed = ['pdf','md','txt','docx'];
  for (const f of files) {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (!ext || !allowed.includes(ext)) return { ok: false, message: `Неподдерживаемый файл: ${f.name}` };
    const mb = f.size / (1024*1024);
    if (mb > MAX_FILE_MB) return { ok: false, message: `Файл слишком большой (${f.name})` };
  }
  return { ok: true };
}

