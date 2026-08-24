import api from "./api";

/**
 * AI API — MemorAI (backend: apps/ai/views).
 *
 * Jobs assíncronos seguem o padrão Celery:
 *   - GET  /ai/report/         -> 202 com {task_id, status} (pendente) OU 200 com relatório pronto
 *   - POST /ai/suggestions/    -> idem
 *   - GET  /ai/tasks/{id}/     -> poll (202 pending, 200 done, 200 FAILURE)
 *
 * Em dev/test com Celery eager (settings/test), /report/ já volta pronto (200).
 */

export interface TaskAcknowledgment {
  task_id: string;
  status: string;
}

export interface ReportMetrics {
  total_reviews: number;
  total_lapses: number;
  avg_reps: number;
  last_review_at: string;
}

export interface ReportResponse {
  user_id: number | null;
  metrics: ReportMetrics;
  text: string;
  status: string;
  prompt_version: string;
  model: string;
  provider: string;
  tokens_in: number;
  tokens_out: number;
}

export type TaskStatus = "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED";

export interface TaskResult {
  task_id: string;
  status: TaskStatus | string;
  result: ReportResponse | null;
}

function isReport(payload: unknown): payload is ReportResponse {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "metrics" in payload &&
    "text" in payload
  );
}

export const aiApi = {
  /** GET /ai/report/ — dispara relatório assíncrono (ou recebe pronto em dev). */
  async startReport(language: "pt" | "en" = "pt"): Promise<ReportResponse | TaskAcknowledgment> {
    const { data, status } = await api.get("/ai/report/", {
      params: { language },
      validateStatus: (s) => s === 200 || s === 202,
    });
    if (status === 202) return data as TaskAcknowledgment;
    return data as ReportResponse;
  },

  /** GET /ai/tasks/{id}/ — poll de tarefa assíncrona. */
  async pollTask(taskId: string): Promise<TaskResult> {
    const { data } = await api.get<TaskResult>(`/ai/tasks/${taskId}/`);
    // Normaliza result: pode vir como objeto pronto (SUCCESS) ou null.
    if (data.result && isReport(data.result)) {
      return { ...data, result: data.result };
    }
    return { ...data, result: null };
  },

  /**
   * Helper que bloqueia ate o relatório ficar pronto. Faz polling com
   * backoff exponencial (1s, 1.5s, 2.5s…) ate maxAttempts. Usa linguagem pt.
   */
  async fetchReport(opts: {
    language?: "pt" | "en";
    maxAttempts?: number;
    onPending?: (status: string) => void;
    signal?: AbortSignal;
  } = {}): Promise<ReportResponse> {
    const { language = "pt", maxAttempts = 12, onPending, signal } = opts;
    const first = await aiApi.startReport(language);
    if ("metrics" in first) return first; // eager (dev/test) ja voltou pronto

    // async: poll
    let attempt = 0;
    let delay = 1000;
    while (attempt < maxAttempts) {
      if (signal?.aborted) throw new Error("aborted");
      // eslint-disable-next-line no-loop-func
      await new Promise((r) => setTimeout(r, delay));
      const task = await aiApi.pollTask(first.task_id);
      onPending?.(task.status);
      if (task.status === "SUCCESS" && task.result) return task.result;
      if (task.status === "FAILURE") throw new Error("report-task-failed");
      attempt += 1;
      delay = Math.min(8000, Math.round(delay * 1.5));
    }
    throw new Error("report-timeout");
  },
};
