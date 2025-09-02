export interface FileInfo { filename: string; size_bytes: number; mime?: string | null }
export type JobStatus = "queued" | "working" | "done" | "error";

export interface IndexAcceptedResponse {
  job_id: string; tenant: string; files: FileInfo[];
}
export type IndexSyncResponse = IndexAcceptedResponse;

export interface StatusResponse {
  job_id: string; tenant?: string | null; status: JobStatus; progress: number; error?: string | null;
}

export type HighlightRange = [number, number];

export interface SourcePreview {
  id: string;
  score: number;
  filename?: string | null;
  page?: number | null;
  snippet: string;
  highlights: HighlightRange[];
}

export interface QAResponse {
  answer: string;
  sources: SourcePreview[];
}

export interface ErrorEnvelope {
  detail: { error: { code: number; type: string; message: string } };
}

export interface HealthResponse {
  status: "ok"; env: string; embed_backend: string; embed_model: string; llm_backend: string; llm_model: string;
}

