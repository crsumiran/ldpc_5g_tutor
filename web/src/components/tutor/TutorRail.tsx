import type { FormEvent } from "react";
import type { LabMessage, LabRun } from "../../lib/contracts";

type Props = { messages: LabMessage[]; run: LabRun | null; question: string; setQuestion: (value: string) => void; onAsk: (event: FormEvent) => void; onHint: () => void; busy: boolean; status?: string; onCancel?: () => void; python?: boolean; courseId?: string };

export function TutorRail({ messages, run, question, setQuestion, onAsk, onHint, busy, status, onCancel, python = false, courseId }: Props) {
  const optical = courseId === "optical-flow";
  return (
    <aside className="tutor-rail" aria-label="Learning assistant">
      <div className="tutor-tabs"><button className="tab-active">TUTOR</button><button>RUBRIC</button><button>NOTES</button></div>
      <div className="tutor-intro"><span className="tutor-orb">✦</span><div><strong>{optical ? "Motion guide" : "Signal guide"}</strong><small>{optical ? "Concepts, shapes and debugging" : "Socratic mode · no solutions"}</small></div></div>
      <div className="tutor-thread" aria-live="polite">
        {messages.length === 0 ? <div className="tutor-empty"><p>{optical ? "Ask about motion, array shapes, sampling or an actual failing assertion. In assignments, the guide sees your contract, saved source and run evidence. In theory, it sees the chapter you are reading." : python ? "Ask about parity, an LLR, a message update or an actual failing Python assertion. The guide sees this checkpoint and your saved code." : "Ask me to inspect a compile error, explain a cache concept, or help you reason about the next failing test."}</p><span>Concept questions need no run; debugging is sharper with evidence.</span></div> : messages.map((message) => <article className={`message message-${message.role}`} key={message.id}><div className="message-meta">{message.role === "assistant" ? (optical ? "MOTION GUIDE" : "SIGNAL GUIDE") : "YOU"}{message.hint_level > 0 && <span>HINT {message.hint_level}</span>}</div><p>{message.content}</p></article>)}
      </div>
      {busy && <div className="tutor-progress"><p role="status">{status || "Guide is thinking…"}</p>{onCancel && <button type="button" onClick={onCancel}>Stop</button>}</div>}
      {run?.result && !run.result.passed && <div className="evidence-chip"><span className="evidence-icon">!</span><div><strong>Evidence attached</strong><small>{run.result.compile.ok ? `${run.result.tests.failed} failing public tests` : "compiler diagnostics"}</small></div></div>}
      <form className="tutor-composer" onSubmit={onAsk}><label htmlFor="tutor-question">What are you thinking?</label><textarea id="tutor-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={optical ? "e.g. Why do we sample frame1 at x+u?" : python ? "e.g. Why can zero syndrome still mean the wrong payload?" : "e.g. Why is this a miss?"} rows={3} disabled={busy} /><div className="composer-actions"><button type="button" className="hint-button" onClick={onHint} disabled={busy}>✦ Give me a hint</button><button type="submit" className="send-button" disabled={busy || !question.trim()}>{busy ? "Thinking…" : "Ask guide ↗"}</button></div></form>
    </aside>
  );
}
