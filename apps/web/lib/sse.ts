export type SSEHandlers = {
  onContext?: (sources: any[]) => void;
  onToken?: (t: string) => void;
  onDone?: () => void;
  onError?: (m: string) => void;
};

export async function parseSSE(stream: ReadableStream<Uint8Array>, handlers: SSEHandlers) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flush = (chunk: string) => {
    buffer += chunk;
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const lines = block.split(/\r?\n/);
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      try {
        if (event === "context") {
          const obj = JSON.parse(data);
          handlers.onContext?.(obj.sources || []);
        } else if (event === "token") {
          const obj = JSON.parse(data);
          if (obj.t) handlers.onToken?.(obj.t);
        } else if (event === "done") {
          handlers.onDone?.();
        } else if (event === "error") {
          const obj = JSON.parse(data);
          handlers.onError?.(obj.message || "stream error");
        }
      } catch {
        // ignore parse errors
      }
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      flush(decoder.decode(value, { stream: true }));
    }
  } catch (e) {
    handlers.onError?.((e as any)?.message || "network error");
  }
}

