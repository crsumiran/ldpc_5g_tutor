"use client";

import { useState } from "react";
import type { CheckpointProgress, TheoryPage } from "../../lib/contracts";
import { NotebookCell } from "../notebook/NotebookCell";
import { LessonText, ParityVisual } from "./LdpcLesson";
import { DecodingWalk } from "./DecodingWalk";
import { RevisionVisual } from "./RevisionVisual";
import { OpticalFlowVisual } from "../optical/OpticalFlowVisual";

function Flow({ steps }: { steps: {name: string; detail: string}[] }) {
  return <div className="primer-flow" aria-label="Worked process">{steps.map((step, i) => <div key={step.name}><small>{i + 1}</small><strong>{step.name}</strong><p>{step.detail}</p>{i < steps.length - 1 && <span aria-hidden="true">↓</span>}</div>)}</div>;
}

function Repetition() {
  const [payload, setPayload] = useState(1);
  const [flips, setFlips] = useState([false, true, false]);
  const received = flips.map(f => f ? 1 - payload : payload);
  const estimate = received.reduce((a,b) => a+b,0) >= 2 ? 1 : 0;
  return <><p>One payload bit becomes three copies. Click a received bit to introduce or remove an error.</p>
    <button onClick={() => setPayload(1 - payload)}>Payload: {payload} · change</button>
    <p>Encoder sends <strong>{String(payload).repeat(3)}</strong>. The receiver sees:</p>
    <div className="ldpc-bits">{received.map((b,i) => <button key={i} aria-label={`Received bit ${i}, ${b}${flips[i] ? ", flipped" : ""}`} className={flips[i] ? "selected" : ""} onClick={() => setFlips(fs => fs.map((f,j) => i === j ? !f : f))}><small>position {i}</small><strong>{b}</strong><small>{flips[i] ? "flipped" : "unchanged"}</small></button>)}</div>
    <p role="status">Majority vote estimates payload <strong>{estimate}</strong>. {estimate === payload ? "It matches what we sent." : "It is wrong: more than one flip defeated this code."}</p>
    <p className="ldpc-caption">We show the transmitted value so YOU can compare. The receiver does not have this answer. This is a repetition-code toy, not the 5G LDPC algorithm.</p></>;
}

export function LdpcPrimer({ pages, index, progress, onPage, onAssignment, onResume, onAsk, busy }: {
  pages: TheoryPage[]; index: number; progress: CheckpointProgress[];
  onPage: (index: number) => void; onAssignment: (id: string) => void; onResume: () => void;
  onAsk: (question: string) => void; busy: boolean;
}) {
  const page = pages[index];
  return <>
    <div className="notebook-heading"><div><div className="eyebrow">START HERE · THEORY {index + 1} / {pages.length}</div><h1>{page.title}</h1><p className="heading-goal">{page.goal}</p></div></div>
    <div className="primer-toolbar"><span>Theory pages are ungraded. Read at your own pace.</span><button className="secondary-button" onClick={onResume}>Resume assignments →</button></div>
    <article className="ldpc-article" aria-label="Chapter explanation">
      {page.sections.map((section,i)=><section key={section.title}>{i>0&&<h2>{section.title}</h2>}<LessonText text={section.text}/>{section.visual&&<OpticalFlowVisual key={`${page.id}-${section.visual}`} id={section.visual}/>}</section>)}
    </article>
    {!page.sections.some(section=>section.visual)&&<details key={page.id+"-visual"} className="ldpc-reading-extra"><summary>Optional: explore the explanation visually</summary>
      <div className="ldpc-visual">
        {page.diagram === "flow" && <OpticalFlowVisual/>}
        {page.diagram === "channel" && <Flow steps={[{name:"Payload", detail:"The data you want to deliver"},{name:"Encoder", detail:"Add relationships that protect the bits"},{name:"Channel", detail:"Physical signal + noise; errors can occur"},{name:"Decoder", detail:"Use observations + known rules to estimate the data"}]} />}
        {page.diagram === "repetition" && <Repetition />}
        {(page.diagram === "parity" || page.diagram === "graph") && <><p>Circles are bit values; squares are rules. A line means the rule includes that bit. Start with this valid candidate, then flip b1 to see two overlapping rules fail.</p><ParityVisual /></>}
        {page.diagram === "graph" && <><p>The tiny H has 9 ones out of 18 entries (50%): it is for hand tracing, not representative of practical sparsity. The schematic below has 30 rows × 60 columns and only three connections per row (5%). It illustrates low density, not a validated code or error performance.</p><svg viewBox="0 0 600 300" role="img" aria-label="Schematic sparse matrix: 30 checks, 60 bits, three ones per row"><rect width="600" height="300" fill="#f3f5f5"/>{Array.from({length:30},(_,r)=>[0,17,39].map(offset=><rect key={`${r}-${offset}`} x={((r*7+offset)%60)*10} y={r*10} width={8} height={8} fill="#087f85"/>))}</svg></>}
        {page.diagram === "decoding" && <DecodingWalk />}
        {page.diagram === "hardware" && <Flow steps={[{name:"Mathematical model",detail:"Parity, neighbors, soft messages, iteration"},{name:"Structured data movement",detail:"QC shifts and lifted groups"},{name:"Finite arithmetic",detail:"Scale, round, clip"},{name:"Parallel implementation",detail:"Lane groups, memory access, scheduling"}]} />}
      </div>
    </details>}
    {!!page.optional_sections?.length&&<details key={page.id+"-reference"} className="ldpc-reading-extra"><summary>Optional: formulas, programming and further examples</summary>{page.optional_sections.map(section=><section key={section.title}><h2>{section.title}</h2><LessonText text={section.text}/></section>)}</details>}
    {page.fixture?.views&&<details key={page.id+"-tables"} className="ldpc-reading-extra"><summary>Optional: full worked tables and message addresses</summary><RevisionVisual key={page.id} fixture={page.fixture}/></details>}
    {page.diagram === "hardware" && <p className="ldpc-caption">Standards reference: <a href="https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf" target="_blank" rel="noreferrer">ETSI TS 138 212 V17.9.0 (5G NR coding)</a>. You do not need to read the standard before these exercises.</p>}
    <NotebookCell number="?" label="CHECK YOUR UNDERSTANDING"><p>{page.question}</p><details><summary>Show the explanation</summary><p>{page.answer}</p></details><button className="text-button" disabled={busy} onClick={() => onAsk(`Help me reason through this theory question from scratch: ${page.question}`)}>Discuss this theory with the guide ↗</button></NotebookCell>
    <details className="ldpc-reading-extra" open={page.diagram === "flow" ? true : undefined}><summary>Next: put this chapter into practice</summary><div className="primer-connections">{page.connections.map(link => {
      const checkpoint = progress.find(p => p.id === link.id);
      const locked = checkpoint?.status === "locked";
      return <div key={link.id}><strong>{link.id} · {checkpoint?.title}</strong><p>{link.why}</p><button className="secondary-button" disabled={locked || !checkpoint} onClick={() => onAssignment(link.id)}>{locked ? "Later: complete earlier assignments first" : "Open this assignment →"}</button></div>;
    })}</div></details>
    <nav className="primer-toolbar" aria-label="Theory page navigation"><button className="secondary-button" disabled={index === 0} onClick={() => onPage(index-1)}>← Previous theory page</button>{index < pages.length-1 ? <button className="primary-button" onClick={() => onPage(index+1)}>Next theory page →</button> : <button className="primary-button" onClick={onResume}>Continue to assignments →</button>}</nav>
  </>;
}
