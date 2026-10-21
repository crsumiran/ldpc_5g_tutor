import { getRun } from "./api";
import type { LabRun } from "./contracts";

export async function pollRun(runId: string, onUpdate: (run: LabRun) => void, signal?: AbortSignal): Promise<LabRun> {
  let delay = 500;
  while (!signal?.aborted) {
    const run = await getRun(runId);
    onUpdate(run);
    if (run.status === "done" || run.status === "error") return run;
    await new Promise<void>((resolve, reject) => {
      const timer = window.setTimeout(resolve, delay);
      signal?.addEventListener("abort", () => { window.clearTimeout(timer); reject(new DOMException("Aborted", "AbortError")); }, { once: true });
    });
    delay = Math.min(delay + 250, 1500);
  }
  throw new DOMException("Aborted", "AbortError");
}
