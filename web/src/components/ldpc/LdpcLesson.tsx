"use client";
import { useState, type ReactNode } from "react";
import type { Checkpoint } from "../../lib/contracts";
import { NotebookCell } from "../notebook/NotebookCell";
import { RevisionVisual } from "./RevisionVisual";
import { OpticalFlowVisual } from "../optical/OpticalFlowVisual";

export function LessonText({ text }: { text: string }) {
  const nodes: ReactNode[] = []; let block: string[] | null = null;
  text.split("\n").forEach((line,i)=>{
    if(line.startsWith("~~~") || line.startsWith(String.fromCharCode(96).repeat(3))) {
      if(block !== null) {nodes.push(<pre key={i}>{block.join("\n")}</pre>); block=null;} else block=[];
    } else if(block !== null) block.push(line);
    else if(line.startsWith("## ")) nodes.push(<h3 key={i}>{line.slice(3)}</h3>);
    else if(line.startsWith("# ")) nodes.push(<h2 key={i}>{line.slice(2)}</h2>);
    else if(line.trim()) nodes.push(<p key={i}>{line}</p>);
  });
  return <div className="ldpc-prose">{nodes}</div>;
}
const H=[[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]];
export function ParityVisual() {
  const [bits,setBits]=useState([1,0,1,1,1,0]),[row,setRow]=useState(0);
  const s=H.map(r=>r.reduce((sum,v,i)=>sum^(v&bits[i]),0));
  return <><p>Flip a bit; select a check row. The same connections appear in the graph.</p>
    <div className="ldpc-bits">{bits.map((v,i)=><button key={i} className={H[row][i]?"selected":""} onClick={()=>setBits(b=>b.map((x,j)=>i===j?1-x:x))}><small>b{i}</small><strong>{v}</strong></button>)}</div>
    <div className="ldpc-matrix">{H.map((r,i)=><button key={i} className={row===i?"selected":""} onClick={()=>setRow(i)}>c{i}: [{r.join(" ")}] → {s[i]} {s[i]?"✕ broken":"✓ even"}</button>)}</div>
    <svg viewBox="0 0 560 180" role="img" aria-label={"Tanner graph, active check c"+row}>
      {H.flatMap((r,j)=>r.flatMap((v,i)=>v?[<line key={j+"-"+i} x1={40+i*94} y1={38} x2={90+j*185} y2={132} stroke={j===row?"#087f85":"#c8d2d5"} strokeWidth={j===row?3:1}/>]:[]))}
      {bits.map((v,i)=><g key={i}><circle cx={40+i*94} cy={28} r={22} fill={H[row][i]?"#d9f1ee":"#f3f5f5"}/><text x={40+i*94} y={32} textAnchor="middle">b{i}={v}</text></g>)}
      {s.map((v,i)=><g key={i}><rect x={66+i*185} y={128} width={48} height={34} rx={5} fill={row===i?"#087f85":"#e9eff0"}/><text x={90+i*185} y={149} textAnchor="middle" fill={row===i?"white":"#233"}>c{i}:{v}</text></g>)}
    </svg><p className="ldpc-caption">Toy matrix. Syndrome [{s.join(", ")}]; weight {s.reduce((a,b)=>a+b,0)}. Matrix 1 = one edge. Zero syndrome proves parity validity, not original payload recovery.</p></>;
}
function RotationVisual() {
  const [z,setZ]=useState(8),[shift,setShift]=useState(3); const k=((shift%z)+z)%z;
  return <><div className="ldpc-controls"><label>Z <select value={z} onChange={e=>setZ(Number(e.target.value))}>{[2,8,32,96,104,192,384].map(n=><option key={n}>{n}</option>)}</select></label><label>Right shift <input type="number" min={-768} max={768} value={shift} onChange={e=>setShift(Number(e.target.value)||0)}/></label></div>
    <div className="ldpc-lanes">{Array.from({length:Math.min(z,12)},(_,i)=><div key={i}><small>out[{i}]</small><strong>x{(i-k+z)%z}</strong></div>)}</div>
    <pre>{"out[i] = input[(i - "+k+") mod "+z+"]\ncoefficient "+shift+" → effective shift "+k+"\n"+(z>12?"Showing indices 0..11 of "+z:"All positions shown")}</pre>
    <p className="ldpc-caption">Right VECTOR rotation. Identity columns shifted right give the inverse mapping when multiplying a column vector. Width Z is not codeword length.</p></>;
}
function CnuVisual() {
  const [edge,setEdge]=useState(0),[tie,setTie]=useState(false); const q=tie?[3,3,5,9]:[7,-3,5,-9];
  const other=q.filter((_,i)=>i!==edge), sign=other.reduce((s,v)=>s*(v<0?-1:1),1),m=Math.min(...other.map(Math.abs));
  return <><button onClick={()=>setTie(!tie)}>{tie?"Use signed example":"Try repeated minimum"}</button>
    <div className="ldpc-bits">{q.map((v,i)=><button key={i} className={edge===i?"selected":""} onClick={()=>setEdge(i)}><small>e{i}</small><strong>{v}</strong><small>{edge===i?"exclude":"use"}</small></button>)}</div>
    <pre>{"To e"+edge+": use ["+other.join(", ")+"]\nsign product = "+sign+"; minimum magnitude = "+m+"\noutgoing = "+sign*m+"\nRecipient's own evidence is excluded."}</pre>
    <p className="ldpc-caption">Uncorrected toy Min-Sum. Click the destination edge. Repeated minima must still work after exclusion. OMS/NMS adjust magnitude afterward.</p></>;
}
function IterationVisual() {
  const [step,setStep]=useState(0);
  const states=["Channel [3,-1,2]\nold V→C [[3,-1,0],[0,-1,2]]","All checks read OLD messages\nC→V [[-1,3,0],[0,2,-1]]","posterior = channel + incoming\n[2,4,1] → bits [0,0,0]","new V→C excludes destination\n[[3,1,0],[0,2,2]]\nsyndrome [0,0]"];
  return <><div className="ldpc-stepper">{["1 Channel","2 Checks","3 Posterior","4 Extrinsic"].map((label,i)=><button key={i} className={step===i?"selected":""} onClick={()=>setStep(i)}>{label}</button>)}</div><pre>{states[step]}</pre><p className="ldpc-caption">Worked flooding fixture: H=[[1,1,0],[0,1,1]]. Not your run output. Layered decoding uses a different order; see its remove-old/add-new example.</p></>;
}
function LlrVisual() {
  const [x,setX]=useState(.15);
  return <><label>LLR <input aria-label="LLR value" type="range" min={-5} max={5} step={.05} value={x} onChange={e=>setX(Number(e.target.value))}/></label><div className="ldpc-numberline"><span>−5 · bit 1</span><strong>{x.toFixed(2)} → bit {x<0?1:0}</strong><span>+5 · bit 0</span></div><div className="ldpc-confidence" style={{width:Math.abs(x)/5*100+"%"}}/><p className="ldpc-caption">Magnitude measures confidence. At zero choose bit 0. This is an LLR, not raw channel amplitude.</p></>;
}
function QcVisual() {
  const [k,setK]=useState(1);
  return <><label>Shift identity columns right <select value={k} onChange={e=>setK(Number(e.target.value))}>{[0,1,2,3].map(n=><option key={n}>{n}</option>)}</select></label><div className="ldpc-qc-grid">{Array.from({length:16},(_,i)=>{const yes=i%4===(Math.floor(i/4)+k)%4;return <span className={yes?"selected":""} key={i}>{yes?1:0}</span>;})}</div><p className="ldpc-caption">Z=4 toy block. Each row selects one column; one base entry encodes four edges. Not a BG1/BG2 fixture.</p></>;
}
function FixedVisual() {
  const [w,setW]=useState(4);const lo=-(2**(w-1)),hi=2**(w-1)-1;
  return <><label>Signed width <select value={w} onChange={e=>setW(Number(e.target.value))}>{[4,5,6,8].map(n=><option key={n}>{n}</option>)}</select></label><table><thead><tr><th>Integer code</th><th>Stored</th><th>Action</th></tr></thead><tbody>{[-40,-12,-1,0,7,40].map(x=><tr key={x}><td>{x}</td><td>{Math.min(hi,Math.max(lo,x))}</td><td>{x<lo||x>hi?"clip":"preserve"}</td></tr>)}</tbody></table><p className="ldpc-caption">Saturation range {lo}..{hi}. Quantization scales and rounds before clipping; this table is integer-code saturation only.</p></>;
}
function LaneVisual() {
  const [z,setZ]=useState(104);const groups=Math.ceil(z/32);
  return <><label>Z positions, P=32 <select value={z} onChange={e=>setZ(Number(e.target.value))}>{[2,32,96,104,192,352,384].map(n=><option key={n}>{n}</option>)}</select></label><div className="ldpc-lanes">{Array.from({length:groups},(_,i)=><div key={i}><small>group {i}</small><strong>{Math.min(32,z-i*32)}/32</strong></div>)}</div><pre>{"groups = "+groups+"\nutilization = "+(z/(groups*32)*100).toFixed(2)+"%"}</pre><p className="ldpc-caption">One pass of lane groups, not total decoder cycles. Lanes process lifted positions; minima reduce check neighbors on a separate axis. Memory ports, edge counts and hazards are not modeled yet.</p></>;
}
function BanksVisual() {
  const [collision,setCollision]=useState(true);const addresses=collision?[0,4,1]:[0,1,2,3];
  const counts=[0,1,2,3].map(b=>addresses.filter(a=>a%4===b).length);
  return <><button onClick={()=>setCollision(!collision)}>Try {collision ? "conflict-free reads" : "a colliding group"}</button><pre>{"addresses ["+addresses.join(", ")+"] → bank IDs ["+addresses.map(a=>a%4).join(", ")+"]"}</pre><div className="ldpc-lanes">{counts.map((c,i)=><div key={i}><small>bank {i}</small><strong>{c} reads</strong><span>{c>1?"✕ one-port conflict":"✓ capacity OK"}</span></div>)}</div><p className="ldpc-caption">Modulo mapping, four single-read-port banks. Bank capacity is independent of how many arithmetic lanes are available. Toy issue-group model, not a full decoder schedule.</p></>;
}
export function LdpcLesson({checkpoint}:{checkpoint:Checkpoint}) {
  const [answer,setAnswer]=useState("");
  const visual:Record<string,ReactNode>={parity:<ParityVisual/>,graph:<ParityVisual/>,rotation:<RotationVisual/>,cnu:<CnuVisual/>,iteration:<IterationVisual/>,llr:<LlrVisual/>,qc:<QcVisual/>,fixed:<FixedVisual/>,lanes:<LaneVisual/>,banks:<BanksVisual/>};
  if(checkpoint.id.startsWith("FLOW-")) return <>
    <article className="ldpc-article" aria-label="Assignment explanation"><LessonText text={checkpoint.lesson||""}/></article>
    <details className="ldpc-reading-extra"><summary>Hints for this implementation</summary>{checkpoint.hints.map((hint,i)=><details key={i}><summary>Hint {i+1}</summary><p>{hint}</p></details>)}</details>
    <details className="ldpc-reading-extra"><summary>Try an experiment and reflect</summary><LessonText text={checkpoint.experiment||""}/><p>{checkpoint.prediction}</p><p>{checkpoint.reflection}</p></details>
  </>;
  return <><article className="ldpc-article" aria-label="Assignment explanation"><LessonText text={checkpoint.lesson||""}/></article>
    <NotebookCell number="B" label="VISUAL LAB · PROVIDED TEACHING FIXTURE">{checkpoint.visual==="optical-flow"&&<OpticalFlowVisual/>}{checkpoint.fixture?<RevisionVisual key={checkpoint.id} fixture={checkpoint.fixture}/>:<div className="ldpc-visual">{visual[checkpoint.visual||""]}</div>}{["LDPC-11","LDPC-13"].includes(checkpoint.id)&&<details><summary>Explore right rotation at Z=2,8,32,96,104,192,384</summary><RotationVisual/></details>}</NotebookCell>
    <NotebookCell number="C" label="PREDICT BEFORE YOU CODE"><p>{checkpoint.prediction}</p><textarea aria-label="Your prediction" placeholder="Write your reasoning; send it to the guide to save it in chat." value={answer} onChange={e=>setAnswer(e.target.value)}/><small>Scratch prediction stays in this view. Chat saves messages when sent.</small></NotebookCell>
    <NotebookCell number="D" label="CHANGE ONE THING · EXPERIMENT"><LessonText text={checkpoint.experiment||""}/><p>{checkpoint.misconception}</p><details><summary>Progressive hints · open only what you need</summary>{checkpoint.hints.map((hint,i)=><details key={i}><summary>Hint {i+1}</summary><p>{hint}</p></details>)}</details></NotebookCell>
    <NotebookCell number="E" label="OPTIONAL DEPTH"><details><summary>Optional mathematical derivation / reading</summary><LessonText text={checkpoint.optional_math||""}/></details><details><summary>{checkpoint.id.startsWith("FLOW-")?"Optional implementation and numerical notes":"Optional hardware interpretation"}</summary><LessonText text={checkpoint.optional_hardware||""}/></details></NotebookCell>
    <NotebookCell number="F" label="WHAT COMPLETION MEANS"><p>{checkpoint.takeaway}</p><p>{checkpoint.completion}</p><p>{checkpoint.reflection}</p></NotebookCell></>;
}
