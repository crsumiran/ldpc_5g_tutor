"use client";

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { CacheArchitecture, CacheTable } from "../components/cache/CacheArchitecture";
import { ExecutionPanel } from "../components/notebook/ExecutionPanel";
import { NotebookCell } from "../components/notebook/NotebookCell";
import { CourseRail } from "../components/shell/CourseRail";
import { TutorRail } from "../components/tutor/TutorRail";
import { VerilogEditor } from "../components/editor/VerilogEditor";
import { askTutor, createSession, getAvailableGuideModels, getCourse, getFiles, getMessages, getSession, saveFile, startRun, testOpenRouterConnection } from "../lib/api";
import type { AvailableGuideModel, Checkpoint, CourseResponse, LabFile, LabMessage, LabRun, LabSession } from "../lib/contracts";
import { pollRun } from "../lib/run-polling";
import { LdpcLesson, LessonText } from "../components/ldpc/LdpcLesson";
import { LdpcPrimer } from "../components/ldpc/LdpcPrimer";

const FEATURED_FREE_MODELS: AvailableGuideModel[] = [
  { id: "qwen/qwen3.8-27b:free", name: "Qwen3.8 27B" },
  { id: "nvidia/nemotron-3-ultra-550b-a55b:free", name: "Nemotron 3 Ultra" },
];

function copyLines(text: string) {
  return text.split("\n").filter(Boolean).map((line, index) => {
    if (line.startsWith("# ")) return <h3 key={index}>{line.slice(2)}</h3>;
    if (line.startsWith("## ")) return <h4 key={index}>{line.slice(3)}</h4>;
    if (line.startsWith("- ")) return <li key={index}>{line.slice(2)}</li>;
    if (line.startsWith("```")) return null;
    return <p key={index}>{line}</p>;
  });
}

function firstAvailable(session: LabSession) {
  return session.checkpoints.find((checkpoint) => checkpoint.status !== "locked" && checkpoint.status !== "passed")?.id ?? session.checkpoints[session.checkpoints.length - 1]?.id ?? "CACHE-01";
}

export default function Home() {
  const [course, setCourse] = useState<CourseResponse | null>(null);
  const [session, setSession] = useState<LabSession | null>(null);
  const [files, setFiles] = useState<Record<string, string>>({});
  const [fileMeta, setFileMeta] = useState<LabFile[]>([]);
  const [messages, setMessages] = useState<LabMessage[]>([]);
  const [activeId, setActiveId] = useState("CACHE-01");
  const [theoryIndex, setTheoryIndex] = useState(-1);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<LabRun | null>(null);
  const [runStale, setRunStale] = useState(false);
  const [diagnosticLine, setDiagnosticLine] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "dirty" | "error">("saved");
  const [tutorBusy, setTutorBusy] = useState(false);
  const [tutorStatus, setTutorStatus] = useState("");
  const [mobilePanel, setMobilePanel] = useState<"rail" | "tutor" | null>(null);
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [openRouterKey, setOpenRouterKey] = useState("");
  const [modelChoice, setModelChoice] = useState("");
  const [customModel, setCustomModel] = useState("");
  const [availableModels, setAvailableModels] = useState<AvailableGuideModel[] | null>(null);
  const [modelCheckBusy, setModelCheckBusy] = useState(false);
  const [modelCheckError, setModelCheckError] = useState<string | null>(null);
  const [allowModelFallbacks, setAllowModelFallbacks] = useState(true);
  const [connectionTestBusy, setConnectionTestBusy] = useState(false);
  const [connectionTestStatus, setConnectionTestStatus] = useState<{ ok: boolean; message: string } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const tutorRequestRef = useRef(false);
  const tutorAbortRef = useRef<AbortController | null>(null);
  const hydratedRef = useRef(false);

  useEffect(() => () => tutorAbortRef.current?.abort(), []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const requestedCourse = new URLSearchParams(window.location.search).get("course");
        const COURSE_ID = requestedCourse === "ldpc-5g" || requestedCourse === "optical-flow" ? requestedCourse : "cache-lab";
        const storageKey = COURSE_ID === "cache-lab" ? "rtl-lab-session" : COURSE_ID === "ldpc-5g" ? "ldpc-lab-session" : "optical-flow-lab-session";
        const nextCourse = await getCourse(COURSE_ID);
        if (cancelled) return;
        setCourse(nextCourse);
        if (nextCourse.manifest.toolchain === "python" && nextCourse.theory_pages?.length) {
          const savedView = window.localStorage.getItem(COURSE_ID === "ldpc-5g" ? "ldpc-theory-view-v1" : "optical-flow-theory-view-v1");
          const savedIndex = savedView === null ? 0 : Number(savedView);
          setTheoryIndex(Number.isInteger(savedIndex) && savedIndex >= -1 && savedIndex < nextCourse.theory_pages.length ? savedIndex : 0);
        }
        let nextSession: LabSession | null = null;
        const savedSessionId = window.localStorage.getItem(storageKey);
        if (savedSessionId) {
          try { nextSession = await getSession(savedSessionId); if (nextSession.course_id !== COURSE_ID) nextSession = null; } catch { window.localStorage.removeItem(storageKey); }
        }
        if (!nextSession) nextSession = await createSession(COURSE_ID);
        if (cancelled) return;
        window.localStorage.setItem(storageKey, nextSession.id);
        setSession(nextSession);
        setActiveId(firstAvailable(nextSession));
        const [nextFiles, nextMessages] = await Promise.all([getFiles(nextSession.id), getMessages(nextSession.id)]);
        if (cancelled) return;
        setFileMeta(nextFiles);
        setFiles(Object.fromEntries(nextFiles.map((file) => [file.path, file.content])));
        setMessages(nextMessages);
        hydratedRef.current = true;
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Unable to load the lab");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; abortRef.current?.abort(); };
  }, []);

  const checkpoint = useMemo<Checkpoint | null>(() => course?.manifest.checkpoints.find((item) => item.id === activeId) ?? null, [course, activeId]);
  const isPython = course?.manifest.toolchain === "python";
  const isOptical = course?.manifest.id === "optical-flow";
  const theoryPages = course?.theory_pages ?? [];
  const readingTheory = isPython && theoryIndex >= 0 && theoryIndex < theoryPages.length;
  const selectedFile = activeFile ?? checkpoint?.editable_files[0] ?? fileMeta.find((file) => file.editable)?.path ?? "rtl/cache_address_decode.v";
  const code = files[selectedFile] ?? "";
  const passedCount = session?.passed_checkpoint_ids.length ?? 0;
  const selectedModelLabel = modelChoice === "custom" ? "Custom" : modelChoice.includes("31b") ? "Gemma 31B" : modelChoice.includes("26b") ? "Gemma 26B" : modelChoice.includes("north-mini") ? "North Mini" : modelChoice.includes("qwen3.8-27b") ? "Qwen 27B" : modelChoice.includes("nemotron") ? "Nemotron" : modelChoice ? (modelChoice.split("/").pop()?.replace(":free", "").slice(0, 19) ?? "Selected") : "Default";
  const initialModelChoices: AvailableGuideModel[] = [
    { id: "google/gemma-4-31b-it:free", name: "Gemma 4 31B" },
    { id: "google/gemma-4-26b-a4b-it:free", name: "Gemma 4 26B A4B" },
    { id: "cohere/north-mini-code:free", name: "North Mini Code" },
  ];
  const modelChoices = [
    ...(availableModels ?? initialModelChoices),
    ...FEATURED_FREE_MODELS,
  ].filter((model, index, all) => all.findIndex((candidate) => candidate.id === model.id) === index);
  const selectedModelUnlisted = Boolean(availableModels && modelChoice && modelChoice !== "custom" && !availableModels.some((model) => model.id === modelChoice));

  useEffect(() => {
    if (!hydratedRef.current || !session || !selectedFile || !(selectedFile in files)) return;
    setSaveStatus("dirty");
    const timer = window.setTimeout(async () => {
      setSaveStatus("saving");
      try { await saveFile(session.id, selectedFile, files[selectedFile]); setSaveStatus("saved"); } catch { setSaveStatus("error"); }
    }, 700);
    return () => window.clearTimeout(timer);
  }, [selectedFile, files, session]);

  useEffect(() => {
    if (checkpoint) setActiveFile(checkpoint.editable_files[0] ?? checkpoint.source_files[0]);
  }, [checkpoint]);

  function updateCode(value: string) {
    if (lastRun) setRunStale(true);
    setFiles((current) => ({ ...current, [selectedFile]: value }));
  }

  async function runCheckpoint(mode: "compile" | "test" | "submit") {
    if (!session || !checkpoint || saveStatus === "saving") return;
    abortRef.current?.abort();
    setError(null);
    try {
      setSaveStatus("saving");
      await Promise.all(checkpoint.source_files.filter(path => fileMeta.some(file => file.path === path && file.editable)).map(path => saveFile(session.id, path, files[path] ?? "")));
      setSaveStatus("saved");
      const started = await startRun(session.id, checkpoint.id, mode);
      setLastRun({ id: started.run_id, checkpoint_id: checkpoint.id, mode, status: "queued", source_hash: "", result: null });
      const controller = new AbortController();
      abortRef.current = controller;
      const completed = await pollRun(started.run_id, setLastRun, controller.signal);
      setLastRun(completed);
      setRunStale(false);
      const [refreshed, refreshedFiles] = await Promise.all([getSession(session.id), getFiles(session.id)]);
      setSession(refreshed);
      setFileMeta(refreshedFiles);
      setFiles((current) => ({ ...Object.fromEntries(refreshedFiles.map((file) => [file.path, file.content])), ...current }));
    } catch (runError) {
      if (!(runError instanceof DOMException && runError.name === "AbortError")) setError(runError instanceof Error ? runError.message : "The sandbox could not run this checkpoint");
    }
  }

  async function sendTutorMessage(message: string, requestedHintLevel = 0) {
    if (!session || !checkpoint || !message.trim() || tutorRequestRef.current || connectionTestBusy) return;
    const selectedModel = modelChoice === "custom" ? customModel.trim() : modelChoice;
    if (modelChoice === "custom" && !selectedModel) {
      setError("Enter an OpenRouter model ID in AI settings before asking the guide.");
      setAiSettingsOpen(true);
      return;
    }
    if (modelChoice === "custom" && !openRouterKey.trim()) {
      setError("Enter your own OpenRouter key for a custom model; custom models may have usage charges.");
      setAiSettingsOpen(true);
      return;
    }
    tutorRequestRef.current = true;
    setTutorBusy(true);
    setTutorStatus("Connecting to the guide…");
    const controller = new AbortController();
    tutorAbortRef.current = controller;
    try {
      await Promise.all(checkpoint.source_files.filter(path => fileMeta.some(file => file.path === path && file.editable)).map(path => saveFile(session.id, path, files[path] ?? "")));
      await askTutor(session.id, { checkpoint_id: checkpoint.id, theory_page_id: readingTheory ? theoryPages[theoryIndex].id : undefined, message, run_id: readingTheory ? undefined : lastRun?.id, requested_hint_level: requestedHintLevel, selected_file: selectedFile, model: selectedModel || undefined, allow_model_fallbacks: allowModelFallbacks }, openRouterKey.trim() || undefined, setTutorStatus, controller.signal);
      setMessages(await getMessages(session.id));
      setMobilePanel("tutor");
    } catch (tutorError) {
      if (!(tutorError instanceof DOMException && tutorError.name === "AbortError")) {
        setError(tutorError instanceof Error ? tutorError.message : "The tutor is unavailable");
      }
    } finally { tutorRequestRef.current = false; tutorAbortRef.current = null; setTutorBusy(false); }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    const message = question.trim();
    if (!message) return;
    if (modelChoice === "custom" && !customModel.trim()) {
      setError("Enter an OpenRouter model ID in AI settings before asking the guide.");
      setAiSettingsOpen(true);
      return;
    }
    if (modelChoice === "custom" && !openRouterKey.trim()) {
      setError("Enter your own OpenRouter key for a custom model; custom models may have usage charges.");
      setAiSettingsOpen(true);
      return;
    }
    setQuestion("");
    await sendTutorMessage(message);
  }

  async function hint() {
    const nextLevel = Math.min(3, Math.max(1, ...messages.map((message) => message.hint_level + 1)));
    if (!checkpoint) return;
    if (readingTheory) {
      await sendTutorMessage(`Explain the main idea of ${theoryPages[theoryIndex].title} with one small example. ${isOptical ? "I know image gradients and filtering; explain the optical-flow reasoning." : "I have not studied LDPC before."}`);
      return;
    }
    const hintQuestion = `I am stuck on ${checkpoint.title}. Please give me hint ${nextLevel} without writing the solution.`;
    await sendTutorMessage(hintQuestion, nextLevel);
  }

  async function checkAvailableModels() {
    setModelCheckBusy(true);
    setModelCheckError(null);
    try {
      const result = await getAvailableGuideModels(openRouterKey.trim() || undefined);
      setAvailableModels(result.models);
    } catch (checkError) {
      setAvailableModels(null);
      setModelCheckError(checkError instanceof Error ? checkError.message : "Unable to check OpenRouter models");
    } finally {
      setModelCheckBusy(false);
    }
  }

  async function testGuideConnection() {
    if (tutorRequestRef.current || connectionTestBusy) return;
    const selectedModel = modelChoice === "custom" ? customModel.trim() : modelChoice;
    if (modelChoice === "custom" && !selectedModel) {
      setConnectionTestStatus({ ok: false, message: "Enter a custom model ID first." });
      return;
    }
    setConnectionTestBusy(true);
    setConnectionTestStatus(null);
    try {
      const result = await testOpenRouterConnection(selectedModel || undefined, allowModelFallbacks, openRouterKey.trim() || undefined);
      const route = result.fallback_used ? `Requested ${result.requested_model}; backup served ${result.served_model}.` : `${result.served_model} responded successfully.`;
      setConnectionTestStatus({ ok: true, message: `${result.engine === "opencode" ? "OpenCode: " : ""}${route} Using ${result.key_source} key.` });
    } catch (testError) {
      setConnectionTestStatus({ ok: false, message: testError instanceof Error ? testError.message : "OpenRouter connection failed" });
    } finally {
      setConnectionTestBusy(false);
    }
  }

  function selectTheory(index: number) {
    setTheoryIndex(index);
    window.localStorage.setItem(isOptical ? "optical-flow-theory-view-v1" : "ldpc-theory-view-v1", String(index));
    setMobilePanel(null);
    window.scrollTo({ top: 0 });
  }

  function selectCheckpoint(id: string) {
    if (isPython) selectTheory(-1);
    if (id === activeId) { setMobilePanel(null); return; }
    setActiveId(id); setLastRun(null); setMobilePanel(null);
    setDiagnosticLine(null);
  }

  if (loading) return <main className="loading-screen"><div className="loading-mark">⌁</div><p>Warming up the lab bench…</p></main>;
  if (error && !course) return <main className="loading-screen error-screen"><div className="error-mark">!</div><h1>Lab connection interrupted</h1><p>{error}</p><button className="primary-button" onClick={() => window.location.reload()}>Retry connection</button></main>;
  if (!course || !session || !checkpoint) return null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">⌁</span><span><strong>{isOptical ? "FLOW LAB" : isPython ? "LDPC LAB" : "RTL LAB"}</strong><small>{isOptical ? "motion estimation with NumPy" : "interactive hardware studio"}</small></span></div>
        <div className="course-breadcrumb"><a href="/?course=cache-lab">CACHE</a><i>/</i><a href="/?course=ldpc-5g">LDPC</a><i>/</i><a href="/?course=optical-flow">OPTICAL FLOW</a><strong>{isOptical ? "PIXELS → MOTION" : isPython ? "BITS → HARDWARE" : "DIRECT-MAPPED CACHE"}</strong></div>
        <div className="topbar-actions"><button className="mobile-toggle" onClick={() => setMobilePanel(mobilePanel === "rail" ? null : "rail")} aria-label="Open checkpoint navigation">☰</button><span className="connection-status"><span className="signal-dot" /> sandbox online</span><span className="save-status">{saveStatus === "saved" ? "Saved" : saveStatus === "saving" ? "Saving…" : saveStatus === "dirty" ? "Unsaved" : "Save error"}</span><button className="ai-settings-button" onClick={() => setAiSettingsOpen((open) => !open)} aria-expanded={aiSettingsOpen} aria-controls="ai-settings-panel" aria-label={`AI settings, ${selectedModelLabel}${openRouterKey ? ", key set" : ""}`}>✦ <span className="ai-label-full">AI · {selectedModelLabel}{openRouterKey ? " · key set" : ""}</span><span className="ai-label-short">AI · {selectedModelLabel}</span></button><button className="mobile-toggle" onClick={() => setMobilePanel(mobilePanel === "tutor" ? null : "tutor")} aria-label="Open tutor">✦</button></div>
        {aiSettingsOpen && <div className="ai-settings-panel" id="ai-settings-panel">
          <div className="ai-settings-heading"><strong>Guide model</strong><button onClick={() => setAiSettingsOpen(false)} aria-label="Close AI settings">×</button></div>
          <label htmlFor="openrouter-key">OpenRouter API key</label>
          <input id="openrouter-key" type="password" autoComplete="off" spellCheck={false} placeholder="sk-or-v1-…" value={openRouterKey} onChange={(event) => { setOpenRouterKey(event.target.value); setAvailableModels(null); setModelCheckError(null); setConnectionTestStatus(null); }} />
          <p>Sent only when you ask the guide. Kept in this tab until refresh; never saved to your lab.</p>
          {openRouterKey && <button className="ai-clear-key" onClick={() => { setOpenRouterKey(""); setAvailableModels(null); }}>Clear key</button>}
          <button className="ai-check-models" onClick={() => void checkAvailableModels()} disabled={modelCheckBusy}>{modelCheckBusy ? "Checking…" : "Check models available to this key"}</button>
          {modelCheckError && <p className="ai-model-error" role="alert">{modelCheckError}</p>}
          {availableModels && <p className="ai-model-result" role="status">{availableModels.length} free model{availableModels.length === 1 ? "" : "s"} allowed for this key. Availability can still change.</p>}
          {selectedModelUnlisted && <p className="ai-model-error" role="status">This model is not listed for the checked key. You can still try its free route; OpenRouter may reject it if the key&apos;s access rules restrict it.</p>}
          <div className="ai-model-heading">Model <span>Selected: {selectedModelLabel}</span></div>
          <div className="ai-model-options" role="radiogroup" aria-label="Guide model">
            {[
              { value: "", label: "Server default", detail: "free fallbacks" },
              ...modelChoices.map((model) => ({ value: model.id, label: model.name, detail: availableModels && !availableModels.some((available) => available.id === model.id) ? "free · try route" : "free" })),
              { value: "custom", label: "Custom model ID", detail: "use your key" },
            ].map((choice) => <label className={`ai-model-option ${modelChoice === choice.value ? "ai-model-selected" : ""}`} key={choice.value}>
              <input type="radio" name="guide-model" value={choice.value} checked={modelChoice === choice.value} onChange={() => setModelChoice(choice.value)} />
              <span>{choice.label}</span><small>{choice.detail}</small>
            </label>)}
          </div>
          {modelChoice === "custom" && <input aria-label="Custom OpenRouter model ID" placeholder="provider/model-name" spellCheck={false} value={customModel} onChange={(event) => setCustomModel(event.target.value)} />}
          <label className="ai-fallback-toggle"><input type="checkbox" checked={allowModelFallbacks} onChange={(event) => { setAllowModelFallbacks(event.target.checked); setConnectionTestStatus(null); }} /><span>Use another configured free model if this one is rate-limited or unavailable</span></label>
          <p>OpenCode manages model streaming and retries. Connection tests use model requests; OpenRouter account and provider limits still apply.</p>
          <p>An entered key is used by the isolated guide service in memory and removed after the request. It is not saved with your assignments or chat.</p>
          <p>The guide always reports the model that actually answered. Custom models require your key and may have usage charges.</p>
          <button className="ai-test-connection" onClick={() => void testGuideConnection()} disabled={connectionTestBusy || tutorBusy}>{connectionTestBusy ? "Testing…" : "Test guide connection"}</button>
          {connectionTestStatus && <p className={connectionTestStatus.ok ? "ai-model-result" : "ai-model-error"} role="status">{connectionTestStatus.message}</p>}
        </div>}
      </header>
      <div className="workspace-grid">
        <div className={`mobile-drawer ${mobilePanel === "rail" ? "drawer-open" : ""}`}><CourseRail python={isPython} checkpoints={session.checkpoints} activeId={activeId} onSelect={selectCheckpoint} theoryPages={theoryPages} theoryIndex={theoryIndex} onTheory={selectTheory} /></div>
        <div className="desktop-rail"><CourseRail python={isPython} checkpoints={session.checkpoints} activeId={activeId} onSelect={selectCheckpoint} theoryPages={theoryPages} theoryIndex={theoryIndex} onTheory={selectTheory} /></div>
        <main className="notebook" id="main-content">
          {readingTheory ? <LdpcPrimer key={theoryPages[theoryIndex].id} pages={theoryPages} index={theoryIndex} progress={session.checkpoints} onPage={selectTheory} onAssignment={selectCheckpoint} onResume={() => selectTheory(-1)} onAsk={q => void sendTutorMessage(q)} busy={tutorBusy} /> : <>
          <div className="notebook-heading"><div><div className="eyebrow">CHECKPOINT {checkpoint.id} / {session.checkpoints.length}</div><h1>{checkpoint.title}</h1><p className="heading-goal">{checkpoint.goal}</p></div><div className="heading-stats"><span className={`difficulty difficulty-${checkpoint.difficulty}`}>{checkpoint.difficulty}</span><span>◷ {checkpoint.estimated_minutes} min</span><span>⌘ {checkpoint.concepts.length} concepts</span></div></div>
          {isPython && theoryPages.length > 0 && <div className="primer-toolbar"><span>What is this function for? Start with its theory.</span><button className="secondary-button" onClick={() => { const relevant = [...theoryPages].reverse().find(page => page.connections.some(link => link.id === checkpoint.id)); selectTheory(relevant ? theoryPages.indexOf(relevant) : 0); }}>Read the theory behind this assignment →</button><button className="text-button" onClick={() => selectTheory(0)}>Start from the beginning</button></div>}

          {!checkpoint.id.startsWith("FLOW-") && <NotebookCell number="01" label="ASSIGNMENT BRIEF">
            <div className="brief-grid"><div className="brief-copy">{copyLines(course.overview).slice(0, 3)}</div><div className="goal-box"><span className="goal-icon">◎</span><div><span className="micro-label">YOUR MISSION</span><strong>{checkpoint.goal}</strong><small>Implement <code>{checkpoint.module}</code> · edit {checkpoint.editable_files.join(", ")}</small></div></div></div>
            <div className="concept-row">{checkpoint.concepts.map((concept) => <span key={concept}>{concept}</span>)}</div>
          </NotebookCell>}

          {isPython ? <LdpcLesson key={checkpoint.id} checkpoint={checkpoint} /> : <CacheArchitecture activeId={checkpoint.id} traceCount={lastRun?.result?.traces.length ?? 0} />}

          <NotebookCell number="02" label="READ THE CONTRACT">
            {checkpoint.input_reference ? <LessonText text={checkpoint.input_reference}/> : <><div className="contract-layout"><div className="contract-copy"><h2>What your {isPython ? "function" : "module"} must do</h2><p>{checkpoint.description}</p><ul className="requirement-list">{checkpoint.requirements.map((requirement) => <li key={requirement}><code>{requirement}</code></li>)}</ul></div>{!isPython && <div className="cache-card"><CacheTable /></div>}</div>
            {isPython && <details><summary>Course scope, conventions and next milestones</summary><LessonText text={course.overview} /></details>}
            <details className="architecture-details"><summary>Open architecture notes</summary><div className="markdown-copy">{copyLines(course.architecture)}</div></details></>}
          </NotebookCell>

          <NotebookCell number="03" label={`CODE CELL · ${selectedFile}`} tone="active" actions={<div className="cell-actions"><button className="secondary-button" onClick={() => void runCheckpoint("compile")} disabled={saveStatus === "saving" || lastRun?.status === "running"}>{isPython ? "Check syntax" : "Compile & elaborate"} <kbd>⌘↵</kbd></button><button className="primary-button" onClick={() => void runCheckpoint("test")} disabled={saveStatus === "saving" || lastRun?.status === "running"}>Run public tests <span>▶</span></button></div>}>
            <div className="editor-tabs">{checkpoint.source_files.map((path) => <button key={path} className={path === selectedFile ? "tab-selected" : ""} onClick={() => setActiveFile(path)}>{path.split("/").pop()}</button>)}</div>
             <div className="editor-wrap"><div className="editor-label"><span className="file-led" /> {selectedFile}<span>{isPython ? "PYTHON · NUMPY" : "VERILOG-2001"}</span></div><VerilogEditor key={selectedFile} language={isPython ? "python" : "verilog"} value={code} onChange={updateCode} onCompile={() => void runCheckpoint("compile")} focusLine={diagnosticLine} disabled={!fileMeta.find((file) => file.path === selectedFile)?.editable} /></div>
            <div className="editor-footer"><span>Tab inserts spaces</span><span>⌘↵ {isPython ? "syntax" : "compile"}</span><span>Lines {code.split("\n").length}</span></div>
          </NotebookCell>

          <NotebookCell number="04" label="EXECUTION RESULT" tone="result" actions={<button className="submit-button" onClick={() => void runCheckpoint("submit")} disabled={saveStatus === "saving" || lastRun?.status === "running"}>Submit checkpoint <span>↗</span></button>}>
            {runStale && <p role="status">Source changed since this run. Rerun before interpreting the old result.</p>}
            <ExecutionPanel python={isPython} run={lastRun} onDiagnostic={setDiagnosticLine} />
          </NotebookCell>

          {lastRun?.result?.passed && lastRun.mode !== "compile" && <NotebookCell number="05" label="REFLECTION" tone="hint"><div className="reflection"><span className="reflection-mark">✦</span><div><h2>Visible checks passed. Make the idea yours.</h2><p>{checkpoint.reflection || "Before moving on, explain the invariant your implementation preserves."}</p><button className="text-button" onClick={() => void sendTutorMessage(`I passed the visible checks for ${checkpoint.title}. Ask me one reflection question about this checkpoint's main invariant, then discuss my answer without giving me a new implementation hint.`)} disabled={tutorBusy}>Discuss this with the guide ↗</button></div></div></NotebookCell>}
          <div className="notebook-end"><span>END OF CHECKPOINT</span><i>·</i><span>{passedCount} of {session.checkpoints.length} cleared</span></div>
          </>}
        </main>
        <div className={`mobile-drawer tutor-drawer ${mobilePanel === "tutor" ? "drawer-open" : ""}`}><TutorRail courseId={course.manifest.id} python={isPython} messages={messages} run={lastRun} question={question} setQuestion={setQuestion} onAsk={ask} onHint={() => void hint()} busy={tutorBusy || connectionTestBusy} status={connectionTestBusy ? "Testing guide connection…" : tutorStatus} onCancel={tutorBusy ? () => tutorAbortRef.current?.abort() : undefined} /></div>
        <div className="desktop-tutor"><TutorRail courseId={course.manifest.id} python={isPython} messages={messages} run={lastRun} question={question} setQuestion={setQuestion} onAsk={ask} onHint={() => void hint()} busy={tutorBusy || connectionTestBusy} status={connectionTestBusy ? "Testing guide connection…" : tutorStatus} onCancel={tutorBusy ? () => tutorAbortRef.current?.abort() : undefined} /></div>
      </div>
      {error && <div className="toast" role="alert"><strong>Something needs attention</strong><span>{error}</span><button onClick={() => setError(null)}>×</button></div>}
    </div>
  );
}
