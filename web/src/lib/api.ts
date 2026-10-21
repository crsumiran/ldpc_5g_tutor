import type { AvailableGuideModel, CourseResponse, LabFile, LabMessage, LabRun, LabSession, OpenRouterConnectionResult, TutorReply } from "./contracts";
import { z } from "zod";

const courseSchema = z.object({ manifest: z.object({ id: z.string(), title: z.string(), checkpoints: z.array(z.object({ id: z.string(), title: z.string(), status: z.string().optional() }).passthrough()) }).passthrough(), overview: z.string(), architecture: z.string() }).passthrough();
const sessionSchema = z.object({ id: z.string(), course_id: z.string(), checkpoints: z.array(z.object({ id: z.string(), status: z.string() }).passthrough()) }).passthrough();
const filesSchema = z.array(z.object({ path: z.string(), content: z.string(), editable: z.boolean() }));
const runSchema = z.object({ id: z.string(), checkpoint_id: z.string(), mode: z.enum(["compile", "test", "submit"]), status: z.enum(["queued", "running", "done", "error"]), result: z.unknown().nullable() }).passthrough();
const messagesSchema = z.array(z.object({ id: z.string(), role: z.enum(["user", "assistant"]), content: z.string() }).passthrough());
const tutorSchema = z.object({ reply: z.object({ summary: z.string(), error_category: z.string(), next_step: z.string() }).passthrough(), content: z.string() }).passthrough();

async function request<T>(path: string, init?: RequestInit, schema?: z.ZodTypeAny): Promise<T> {
  const response = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  if (schema) {
    const parsed = schema.safeParse(body);
    if (!parsed.success) throw new Error(`Invalid API response from ${path}`);
    return parsed.data as T;
  }
  return body as T;
}

export function getCourse(courseId: string) { return request<CourseResponse>(`/api/courses/${courseId}`, undefined, courseSchema); }

export function createSession(courseId: string) {
  return request<LabSession>(`/api/courses/${courseId}/sessions`, { method: "POST", body: JSON.stringify({ learner_key: "local" }) }, sessionSchema);
}

export function getSession(sessionId: string) { return request<LabSession>(`/api/lab-sessions/${sessionId}`, undefined, sessionSchema); }

export function getFiles(sessionId: string) { return request<LabFile[]>(`/api/lab-sessions/${sessionId}/files`, undefined, filesSchema); }

export function saveFile(sessionId: string, path: string, content: string) {
  return request<{ path: string; saved: boolean }>(`/api/lab-sessions/${sessionId}/files/${path}`, { method: "PUT", body: JSON.stringify({ content }) });
}

export function startRun(sessionId: string, checkpointId: string, mode: "compile" | "test" | "submit") {
  return request<{ run_id: string; job_id: string; status: string }>(`/api/lab-sessions/${sessionId}/runs`, { method: "POST", body: JSON.stringify({ checkpoint_id: checkpointId, mode }) });
}

export function getRun(runId: string) { return request<LabRun>(`/api/lab-runs/${runId}`, undefined, runSchema); }

export function getMessages(sessionId: string) { return request<LabMessage[]>(`/api/lab-sessions/${sessionId}/messages`, undefined, messagesSchema); }

export async function askTutor(sessionId: string, body: { checkpoint_id: string; theory_page_id?: string; message: string; run_id?: string; requested_hint_level?: number; selected_file?: string; model?: string; allow_model_fallbacks?: boolean }, apiKey?: string, onStatus?: (text: string) => void, signal?: AbortSignal) {
  const response = await fetch(`/api/lab-sessions/${sessionId}/tutor/stream`, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json", ...(apiKey ? { "X-OpenRouter-Api-Key": apiKey } : {}) },
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || `Guide request failed (${response.status})`);
  }
  if (!response.body) throw new Error("The guide returned no response stream.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) throw new Error("The guide connection ended before an answer arrived. Please retry.");
      buffer += decoder.decode(value, { stream: true });
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split("\n");
        const event = lines.find((line) => line.startsWith("event: "))?.slice(7);
        const data = lines.filter((line) => line.startsWith("data: ")).map((line) => line.slice(6)).join("\n");
        if (!data) continue;
        const parsed = JSON.parse(data);
        if (event === "status") onStatus?.(parsed.message);
        if (event === "error") throw new Error(parsed.detail || "The guide request failed.");
        if (event === "result") {
          const validated = tutorSchema.safeParse(parsed);
          if (!validated.success) throw new Error("The guide returned an invalid answer.");
          return validated.data as { reply: TutorReply; content: string; run_id?: string | null };
        }
      }
    }
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export function testOpenRouterConnection(model: string | undefined, allowModelFallbacks: boolean, apiKey?: string) {
  return request<OpenRouterConnectionResult>("/api/openrouter/test", {
    method: "POST",
    body: JSON.stringify({ model, allow_model_fallbacks: allowModelFallbacks }),
    headers: apiKey ? { "X-OpenRouter-Api-Key": apiKey } : undefined,
    cache: "no-store",
  }, z.object({
    ok: z.boolean(), requested_model: z.string(), served_model: z.string(),
    fallback_used: z.boolean(), key_source: z.enum(["entered", "server"]),
    engine: z.string().optional(),
  }));
}

export function getAvailableGuideModels(apiKey?: string) {
  return request<{ models: AvailableGuideModel[]; key_source: "entered" | "server" }>("/api/openrouter/models", {
    headers: apiKey ? { "X-OpenRouter-Api-Key": apiKey } : undefined,
    cache: "no-store",
  }, z.object({ models: z.array(z.object({ id: z.string(), name: z.string() })), key_source: z.enum(["entered", "server"]) }));
}
