"use client";
import { useState } from "react";
import type { TeachingFixture, TeachingView } from "../../lib/contracts";

function ViewTable({view}: {view: TeachingView}) {
  const [selected,setSelected]=useState(-1);
  const cycles=view.columns[0]==="Issue cycle";
  return <section><h3>{view.title}</h3>{cycles&&<p>Select an issue cycle to follow its reads, computation, writes and dependency. This is the declared toy schedule, not measured timing.</p>}<div style={{overflowX:"auto",maxWidth:"100%"}}><table><thead><tr>{view.columns.map((column,i)=><th key={i} scope="col">{column}</th>)}</tr></thead><tbody>{view.rows.map((row,i)=><tr key={i} style={selected===i?{background:"#d9f1ee"}:undefined}>{row.map((value,j)=><td key={j}>{cycles&&j===0?<button aria-label={`Select issue cycle ${value}`} onClick={()=>setSelected(i)}>{String(value)}</button>:String(value)}</td>)}</tr>)}</tbody></table></div><p className="ldpc-caption">{view.caption}</p></section>;
}

function EdgeMap({fixture}: {fixture: TeachingFixture}) {
  const [selected,setSelected]=useState(0);
  const edges=fixture.edges||[], matrix=fixture.matrix||[];
  if (!edges.length) return null;
  const edge=edges[selected];
  return <section><p>Select the same global edge in the matrix or edge list. The highlighted graph line and message addresses follow your selection.</p>
    <div className="ldpc-controls">{edges.map((e,i)=><button key={e.id} className={i===selected?"selected":""} onClick={()=>setSelected(i)}>{e.id}: c{e.check} ↔ b{e.bit}</button>)}</div>
    <div style={{overflowX:"auto"}}><table><tbody>{matrix.map((row,c)=><tr key={c}><th scope="row">c{c}</th>{row.map((value,b)=><td key={b}>{value?<button aria-label={`Select edge c${c} b${b}`} className={c===edge.check&&b===edge.bit?"selected":""} onClick={()=>setSelected(edges.findIndex(e=>e.check===c&&e.bit===b))}>{edges.find(e=>e.check===c&&e.bit===b)?.id}</button>:"0"}</td>)}</tr>)}</tbody></table></div>
    <svg viewBox="0 0 560 180" role="img" aria-label={`Tanner graph highlighting ${edge.id}`}>
      {edges.map((e,i)=><line key={e.id} x1={40+e.bit*94} y1={40} x2={90+e.check*185} y2={130} stroke={i===selected?"#087f85":"#c8d2d5"} strokeWidth={i===selected?5:1}/>)}
      {matrix[0].map((_,b)=><g key={b}><circle cx={40+b*94} cy={28} r={21} fill={b===edge.bit?"#d9f1ee":"#f3f5f5"}/><text x={40+b*94} y={32} textAnchor="middle">b{b}</text></g>)}
      {matrix.map((_,c)=><g key={c}><rect x={66+c*185} y={128} width={48} height={34} rx={5} fill={c===edge.check?"#d9f1ee":"#f3f5f5"}/><text x={90+c*185} y={149} textAnchor="middle">c{c}</text></g>)}
    </svg><p role="status">{edge.id}: bit b{edge.bit} → check c{edge.check} uses q[{selected}]; check → bit uses r[{selected}]. Dense teaching-array address: [{edge.check}, {edge.bit}]. Edge IDs belong to this fixture, not every graph.</p></section>;
}

export function RevisionVisual({fixture}: {fixture: TeachingFixture}) {
  const [variant,setVariant]=useState(-1),[step,setStep]=useState(0),[revealed,setRevealed]=useState(false);
  const views=variant<0?fixture.views:fixture.variants?.[variant].views||fixture.views;
  const safeStep=Math.min(step,views.length-1);
  return <div className="ldpc-visual"><h2>{fixture.label}</h2><p className="ldpc-caption">Provided worked fixture—not your program&apos;s output. {fixture.visual_spec.data_origin}</p>
    {fixture.kind==="edges"&&<EdgeMap fixture={fixture}/>}
    {fixture.id==="variable-contributions"&&<div className="primer-flow" aria-label="Variable contribution flow"><div><strong>Channel L + all incoming r → posterior A</strong><p>Fixed radio evidence + changing advice → current combined score</p></div><div><strong>A − destination&apos;s r → outgoing q</strong><p>Remove the recipient&apos;s contribution before sending evidence back.</p></div></div>}
    {!!fixture.variants?.length&&<label>Controlled experiment <select aria-label="Worked fixture variant" value={variant} onChange={e=>{setVariant(Number(e.target.value));setStep(0);}}><option value={-1}>Baseline</option>{fixture.variants.map((v,i)=><option key={i} value={i}>{v.label}</option>)}</select></label>}
    <p>{fixture.visual_spec.expected_observation}</p>
    <p>Make your prediction first. Then reveal the authored intermediate values and compare your reasoning.</p><button onClick={()=>setRevealed(v=>!v)}>{revealed?"Hide worked results":"Reveal worked results"}</button>
    {revealed&&<><div className="ldpc-stepper" role="group" aria-label="Worked trace steps">{views.map((view,i)=><button key={i} className={i===safeStep?"selected":""} onClick={()=>setStep(i)}>{i+1}. {view.title}</button>)}</div>
    {views[safeStep]&&<ViewTable view={views[safeStep]}/>}</>}
    <details><summary>Complete trace · accessible text and tables</summary>{views.map((view,i)=><ViewTable key={i} view={view}/>)}<p>{fixture.visual_spec.caption}</p></details>
  </div>;
}
