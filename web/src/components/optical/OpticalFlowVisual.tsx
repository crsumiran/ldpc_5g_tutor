"use client";
import { useEffect, useState, type ReactNode } from "react";
import type { OpticalVisualId } from "../../lib/contracts";

const fmt=(n:number)=>Number(n.toFixed(4)).toString();
const grid=(h:number,w:number,fn:(x:number,y:number)=>number)=>Array.from({length:h},(_,y)=>Array.from({length:w},(_,x)=>fn(x,y)));
function sample(image:number[][],x:number,y:number):number|null {
  const h=image.length,w=image[0].length;
  if(x<0||y<0||x>w-1||y>h-1)return null;
  const x0=Math.floor(x),y0=Math.floor(y),x1=Math.min(x0+1,w-1),y1=Math.min(y0+1,h-1),a=x-x0,b=y-y0;
  return (1-a)*(1-b)*image[y0][x0]+a*(1-b)*image[y0][x1]+(1-a)*b*image[y1][x0]+a*b*image[y1][x1];
}
function Slider({label,value,set,min=-2,max=2,step=.25}:{label:string;value:number;set:(n:number)=>void;min?:number;max?:number;step?:number}) {
  return <label className="flow-slider">{label}: <output>{fmt(value)}</output><input aria-label={label} type="range" min={min} max={max} step={step} value={value} onChange={e=>set(Number(e.target.value))}/></label>;
}
function Pixels({values,label,selected,residual=false,scaleMax}:{values:(number|null)[][];label:string;selected?:[number,number];residual?:boolean;scaleMax?:number}) {
  const h=values.length,w=values[0].length,max=scaleMax??Math.max(1,...values.flat().map(v=>Math.abs(v??0)));
  return <figure><figcaption>{label}</figcaption><svg viewBox={`0 0 ${w*24} ${h*24}`} role="img" aria-label={label}>
    {values.flatMap((row,y)=>row.map((v,x)=>{
      const gray=Math.round(Math.max(0,Math.min(1,(v??0)/max))*230);
      const color=v===null?"#ca8a04":residual?`rgb(${Math.round(Math.min(1,Math.abs(v)/max)*220)},${v>=0?90:30},${v<0?180:30})`:`rgb(${gray},${gray},${gray})`;
      return <g key={`${x},${y}`}><rect x={x*24+1} y={y*24+1} width={22} height={22} fill={color}/>{selected?.[0]===x&&selected?.[1]===y&&<rect x={x*24+2} y={y*24+2} width={20} height={20} fill="none" stroke="#21dfdc" strokeWidth={3}/>}<title>{`(${x},${y}): ${v===null?"outside":fmt(v)}`}</title></g>;
    }))}
  </svg></figure>;
}
function Table({columns,rows}:{columns:string[];rows:ReactNode[][]}) {
  return <div className="flow-table" tabIndex={0} role="region" aria-label={columns.join(", ")+" table"}><table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{row.map((v,j)=><td key={j}>{v}</td>)}</tr>)}</tbody></table></div>;
}
function Playback({step,setStep,max}:{step:number;setStep:(n:number|((n:number)=>number))=>void;max:number}) {
  const [playing,setPlaying]=useState(false),[reduced,setReduced]=useState(false);
  useEffect(()=>{const query=window.matchMedia("(prefers-reduced-motion: reduce)");const changed=()=>{setReduced(query.matches);if(query.matches)setPlaying(false);};changed();query.addEventListener("change",changed);return()=>query.removeEventListener("change",changed);},[]);
  useEffect(()=>{
    if(!playing||reduced)return;
    const timer=window.setInterval(()=>setStep(n=>Math.min(max,n+1)),900);
    const hide=()=>{if(document.hidden)setPlaying(false);};document.addEventListener("visibilitychange",hide);
    return()=>{window.clearInterval(timer);document.removeEventListener("visibilitychange",hide);};
  },[playing,reduced,max,setStep]);
  useEffect(()=>{if(step>=max)setPlaying(false);},[step,max]);
  return <div className="ldpc-controls"><button disabled={reduced||step===max} onClick={()=>setPlaying(!playing)}>{playing?"Pause":"Play"}</button><button disabled={step===max} onClick={()=>{setPlaying(false);setStep(n=>Math.min(max,n+1));}}>Single step</button><span>Step {step}/{max}</span>{reduced&&<span>Reduced motion: use Single step.</span>}</div>;
}
function Motion({alignment=false}:{alignment?:boolean}) {
  const [u,setU]=useState(0),[v,setV]=useState(0),[kind,setKind]=useState("texture"),[offset,setOffset]=useState(0),[motion,setMotion]=useState(.5),[step,setStep]=useState(0),[x,setX]=useState(2),[y,setY]=useState(2);
  const shift=motion*(alignment?1:step/4);
  const texture=(xx:number,yy:number)=>kind==="flat"?4:kind==="edge"?xx:xx*yy;
  const first=grid(5,5,texture),second=grid(5,5,(xx,yy)=>texture(xx-shift,yy)+offset);
  const sceneScale=Math.max(1,...first.flat(),...second.flat());
  const warped=first.map((row,yy)=>row.map((_,xx)=>sample(second,xx+u,yy+v)));
  const residual=first.map((row,yy)=>row.map((a,xx)=>warped[yy][xx]===null?null:warped[yy][xx]!-a));
  const supported=residual.flat().filter((a):a is number=>a!==null);
  const rms=Math.sqrt(supported.reduce((s,r)=>s+r*r,0)/Math.max(1,supported.length));
  return <>
    <p>{alignment?"Scene controls change Frame 1, sampled Frame 1 and residual. Proposed flow changes only sampled Frame 1, residual and support. Selected coordinates choose the numeric readout in every panel.":"Scene motion sets the full horizontal displacement. Playback reveals times 0, ¼, ½, ¾ and 1; only the later frame and correspondence arrow move. Start with Single step."}</p>
    <div className="ldpc-controls"><label>Scene texture <select aria-label="Flow scene" value={kind} onChange={e=>setKind(e.target.value)}><option value="texture">Textured patch x·y</option><option value="edge">Vertical ramp / edge direction</option><option value="flat">Flat region</option></select></label><label>Brightness change <select aria-label="Brightness change" value={offset} onChange={e=>setOffset(Number(e.target.value))}><option value={0}>None</option><option value={.15}>+0.15</option></select></label></div>
    <output className="flow-change-output" aria-label="Live scene and brightness readout" aria-live="polite" aria-atomic="true">
      <strong>{kind==="texture"?"Textured patch x·y":kind==="edge"?"Vertical ramp / edge direction":"Flat region"}</strong>
      <span>Brightness offset {offset>=0?"+":""}{fmt(offset)} · At ({x},{y}): I0={fmt(first[y][x])}, I1={fmt(second[y][x])}, It={fmt(second[y][x]-first[y][x])}</span>
    </output>
    <Slider label="Scene horizontal motion" value={motion} set={setMotion} min={0} max={2}/>
    {!alignment&&<Playback step={step} setStep={setStep} max={4}/>}
    {alignment&&<><Slider label="Proposed horizontal flow" value={u} set={setU}/><Slider label="Proposed vertical flow" value={v} set={setV}/></>}
    <div className="flow-panels"><Slider label="Selected x" value={x} set={setX} min={0} max={4} step={1}/><Slider label="Selected y" value={y} set={setY} min={0} max={4} step={1}/></div>
    <div className="flow-panels"><Pixels values={first} label="Frame 0 · reference" selected={[x,y]} scaleMax={sceneScale}/><Pixels values={second} label="Frame 1 · scene motion" selected={[x,y]} scaleMax={sceneScale}/>{alignment&&<><Pixels values={warped} label="Frame 1 · proposed lookup" selected={[x,y]}/><Pixels values={residual} label="Sampled minus reference" selected={[x,y]} residual/></>}</div>
    {!alignment&&<><svg viewBox="0 0 440 95" role="img" aria-label={`Correspondence from (${x},${y}) to (${fmt(x+shift)},${y})`}><text x={12} y={18}>Frame 0</text><text x={255} y={18}>Frame 1 · time {step}/4</text><circle cx={35+x*20} cy={50} r={7} fill="#087f85"/><path d={`M ${44+x*20} 50 L ${260+(x+shift)*20} 50 l -10 -6 m 10 6 l -10 6`} stroke="#087f85" strokeWidth={2} fill="none"/><circle cx={270+(x+shift)*20} cy={50} r={7} fill="#a04412"/><text x={12} y={85}>p=({x},{y}) → ({fmt(x+shift)},{y})</text></svg><p role="status">Time {step}/4. Displacement [{fmt(shift)},0]. Fixed-position I0={fmt(first[y][x])}, I1={fmt(second[y][x])}, It={fmt(second[y][x]-first[y][x])}. Corresponding intensity at ({fmt(x+shift)},{y}) is {x+shift<=4?fmt(sample(second,x+shift,y)!):"outside the crop"}.</p><button onClick={()=>setStep(0)}>Rewind timeline</button></>}
    {alignment&&<p role="status">Selected ({x},{y}): I0={fmt(first[y][x])}; lookup ({fmt(x+u)},{fmt(y+v)}); sampled={warped[y][x]===null?"outside":fmt(warped[y][x]!)}; residual={residual[y][x]===null?"unmeasured":fmt(residual[y][x]!)}. Photometric RMS: {rms.toFixed(4)} over {supported.length}/25 samples. Scene [{fmt(shift)},0]; proposed [{fmt(u)},{fmt(v)}].</p>}
    <p>{kind==="flat"?"Intentional invariance: flat intensity does not change under supported motion. Only borders and the validity count can change; lighting still changes brightness.":kind==="edge"?"Intentional invariance: the vertical ramp has no vertical gradient. Changing proposed v leaves interior intensities unchanged; border support can change.":"Texture changes across both axes. Frame 0 and frame 1 share one intensity scale so brightness changes remain visible."} Amber means outside the image.</p>
  </>;
}
function Patch({ambiguity=false}:{ambiguity?:boolean}) {
  const [selected,setSelected]=useState(4),[u,setU]=useState(.5),[v,setV]=useState(-.25),[kind,setKind]=useState("corner");
  const rows=Array.from({length:9},(_,i)=>{const x=i%3+1,y=Math.floor(i/3)+1;return {x,y,ix:y,iy:x,b:.5*y-.25*x};});
  const error=rows.reduce((s,r)=>s+(r.ix*u+r.iy*v-r.b)**2,0),r=rows[selected];
  if(ambiguity){
    const gs=kind==="flat"?[[0,0],[0,0]]:kind==="edge"?[[1,0],[1,0]]:[[1,0],[0,1]];
    const b=gs.map(([ix,iy])=>ix*.5-iy*.25),e=gs.reduce((s,[ix,iy],i)=>s+(ix*u+iy*v-b[i])**2,0);
    return <><label>Evidence <select aria-label="Gradient evidence" value={kind} onChange={e=>setKind(e.target.value)}><option value="flat">Flat</option><option value="edge">Edge</option><option value="corner">Corner</option></select></label><Slider label="Candidate u" value={u} set={setU}/><Slider label="Candidate v" value={v} set={setV}/><svg viewBox="0 0 330 110" role="img" aria-label={`${kind} gradient evidence`}><rect x={10} y={10} width={90} height={90} fill="#c8d2d5"/>{kind!=="flat"&&<rect x={55} y={10} width={45} height={90} fill="#087f85"/>}{kind==="corner"&&<rect x={10} y={55} width={45} height={45} fill="#087f85"/>}<text x={120} y={40}>Ix direction →</text><text x={120} y={70}>{kind==="corner"?"Iy direction ↓":"No vertical evidence"}</text></svg><p role="status">G={kind==="flat"?"[[0,0],[0,0]]":kind==="edge"?"[[1,0],[0,0]]":"[[0.5,0],[0,0.5]]"}; eigenvalues {kind==="flat"?"[0,0]":kind==="edge"?"[0,1]":"[0.5,0.5]"}. Squared error={fmt(e)}. {kind==="flat"?"Intentional invariance: neither u nor v is observable.":kind==="edge"?"Intentional invariance: v does not enter any equation.":"Both candidate components affect the fit."}</p><p>This diagram uses two idealized gradient observations {JSON.stringify(gs)}, with b={JSON.stringify(b)}, to isolate the missing direction. The nine-row x·y patch has eigenvalues 2/3 and 26/3.</p></>;
  }
  return <><p>Select a patch pixel to connect its coordinate to its equation. Candidate controls change the squared error across all nine equations.</p><div className="flow-patch" role="group" aria-label="Patch selection">{rows.map((r,i)=><button key={i} aria-pressed={selected===i} onClick={()=>setSelected(i)}>({r.x},{r.y})<br/>I0={r.x*r.y}</button>)}</div><p role="status">Row {selected+1}, ({r.x},{r.y}): {r.ix}u + {r.iy}v = {fmt(r.b)}. Prediction={fmt(r.ix*u+r.iy*v)}; equation residual={fmt(r.ix*u+r.iy*v-r.b)}. Total squared error={fmt(error)}.</p><Slider label="Candidate u" value={u} set={setU}/><Slider label="Candidate v" value={v} set={setV}/><Table columns={["(x,y)","[Ix,Iy]","b = −It","Aq−b"]} rows={rows.map(r=>[`(${r.x},${r.y})`,`[${r.ix},${r.iy}]`,fmt(r.b),fmt(r.ix*u+r.iy*v-r.b)])}/><p>A.T@A=[[42,36],[36,42]]; A.T@b=[12,7.5]. The selected cell does not change the patch or its fit.</p></>;
}
function Sampling(){
  const [x,setX]=useState(.25),[y,setY]=useState(.5);
  const weights=[(1-x)*(1-y),x*(1-y),(1-x)*y,x*y],values=[0,10,20,30];
  return <><Slider label="Sample x" value={x} set={setX} min={0} max={1}/><Slider label="Sample y" value={y} set={setY} min={0} max={1}/><svg viewBox="0 0 340 205" role="img" aria-label="Four interpolation neighbors and query"><path d="M60 35 H260 V165 H60 Z" stroke="#8a9b9e" fill="none"/>{values.map((v,i)=><g key={i}><circle cx={60+(i%2)*200} cy={35+Math.floor(i/2)*130} r={10} fill="#087f85"/><text x={60+(i%2)*200} y={18+Math.floor(i/2)*177} textAnchor="middle">I={v}, w={fmt(weights[i])}</text></g>)}<circle cx={60+x*200} cy={35+y*130} r={6} fill="#d24c18"/></svg><Table columns={["Neighbor","Weight","Intensity","Contribution"]} rows={values.map((v,i)=>[`(${i%2},${Math.floor(i/2)})`,fmt(weights[i]),v,fmt(v*weights[i])])}/><p role="status">At ({fmt(x)},{fmt(y)}), weights sum to {fmt(weights.reduce((a,b)=>a+b,0))}; sampled intensity={fmt(values.reduce((s,v,i)=>s+v*weights[i],0))}. Valid=True. The red point changes with both controls.</p></>;
}
function Refinement(){
  const [step,setStep]=useState(0);const u=step<3?.25:.5;
  const reference=grid(3,3,(x,y)=>(x+1)*(y+1)), sampled=grid(3,3,(x,y)=>(x+1+u-.5)*(y+1));
  const rows=Array.from({length:9},(_,i)=>{const x=i%3+1,y=Math.floor(i/3)+1,ref=x*y,sampled=(x+u-.5)*y;return [`(${x},${y})`,`(${fmt(x+u)},${y})`,ref,fmt(sampled),fmt(sampled-ref)];});
  return <><p>True motion [0.5,0]; initial estimate [0.25,0]; fixed center (2,2). Playback changes only the demonstrated calculation, never learner code.</p><Playback step={step} setStep={setStep} max={4}/><ol className="flow-stages">{["Choose the reference patch","Sample with the center’s estimate","Fit reference minus sampled","Add the correction","Resample the original frame"].map((s,i)=><li key={s} aria-current={step===i?"step":undefined}>{s}</li>)}</ol><div className="flow-panels"><Pixels values={reference} label="Reference 3×3 patch"/><Pixels values={sampled} label="Translated samples"/><Pixels values={sampled.map((row,y)=>row.map((v,x)=>v-reference[y][x]))} label="Patch residual" residual/></div><Table columns={["Reference coordinate","Read I1 at","I0","Sampled I1","Residual"]} rows={rows}/><p role="status">Step {step}: center flow=[{fmt(u)},0]. {step<2?"Residual rows = −0.25, −0.5, −0.75. Each row has three equal residuals.":step===2?"A.T@b=[10.5,9]; A.T@A=[[42,36],[36,42]]; fitted correction=[0.25,0].":step===3?"Update: [0.25,0]+[0.25,0]=[0.5,0]. Table shows updated sampling.":"Residual is zero. A second fit gives correction [0,0]."}</p><p>The table shows actual bilinear samples of I1=(x−0.5)y. Every lookup uses the same center estimate; the surrounding flow field is not used.</p></>;
}
function Pyramid(){
  const [level,setLevel]=useState(0);const h=[17,9,5],w=[21,11,6],spacing=2**level;
  return <><p>Select a level to change its grid, coordinate spacing and vector units. The arrow always represents the same original displacement [8,−4].</p><div className="ldpc-controls">{h.map((_,i)=><button key={i} aria-pressed={i===level} onClick={()=>setLevel(i)}>Level {i} · {h[i]}×{w[i]}</button>)}</div><svg viewBox="0 0 440 210" role="img" aria-label={`Level ${level} grid and displacement`}>
    {Array.from({length:h[level]},(_,y)=>Array.from({length:w[level]},(_,x)=><circle key={`${x},${y}`} cx={20+x*spacing*9} cy={30+y*spacing*9} r={2} fill="#899b9f"/>))}<path d="M 92 102 L 164 66 l -10 0 m 10 0 l -5 9" fill="none" stroke="#087f85" strokeWidth={3}/><text x={15} y={202}>One grid step = {spacing} original pixel{spacing>1?"s":""}</text></svg><p role="status">Level {level}: {h[level]}×{w[level]}, spacing {spacing}. Point (8,8) → ({8/spacing},{8/spacing}); displacement [{8/spacing},{-4/spacing}] level pixels.</p><Table columns={["Level","Shape","Spacing","Displacement"]} rows={h.map((hh,i)=>[i,`${hh}×${w[i]}`,2**i,`[${8/2**i},${-4/2**i}]`])}/><p>Upward transition: interpolate the field grid, then double both components. 5×7 → 3×4 still uses spacing two, not width ratio 7/4.</p></>;
}
function Evaluation(){
  const [mask,setMask]=useState([true,true,false,false,false,false]);const errors=[5,0,2,4,1,3],count=mask.filter(Boolean).length,mean=errors.reduce((s,e,i)=>s+(mask[i]?e:0),0)/count;
  return <><p>Select the evaluation mask. The first two vector differences are [3,4] and [0,0]. The other four are [2,0], [4,0], [1,0], [3,0]. Excluded entries are unmeasured, not zero.</p><div className="flow-patch" role="group" aria-label="Evaluation mask">{errors.map((e,i)=><button key={i} aria-pressed={mask[i]} onClick={()=>setMask(ms=>ms.map((m,j)=>i===j?!m:m))}>({i%3},{Math.floor(i/3)})<br/>{mask[i]?`error ${e}`:"NaN · excluded"}</button>)}</div><p role="status">Count={count}/6; coverage={(count/6*100).toFixed(1)}%; mean endpoint error={count?fmt(mean):"NaN (no measurements)"} pixels.</p></>;
}
function Consistency(){
  const [bias,setBias]=useState(0),[valid,setValid]=useState(true),[threshold,setThreshold]=useState(.5);const back=-.5+bias,round=Math.abs(.5+back);
  return <><p>Start p=(1,1), forward=[0.5,0], destination d=(1.5,1). The backward bias changes both reverse samples and the return point. Threshold changes only acceptance; validity changes only support.</p><Slider label="Backward horizontal bias" value={bias} set={setBias} min={-.5} max={.5}/><Slider label="Round-trip threshold" value={threshold} set={setThreshold} min={0} max={.5} step={.05}/><label><input type="checkbox" checked={valid} onChange={e=>setValid(e.target.checked)}/> Backward sample (2,1) valid</label><svg viewBox="0 0 420 135" role="img" aria-label="Forward and backward round-trip paths"><path d="M 130 40 H230 l -9 -6 m 9 6 l -9 6" fill="none" stroke="#087f85" strokeWidth={3}/><path d={`M230 75 H${130+bias*200} l 9 -6 m -9 6 l 9 6`} fill="none" stroke="#aa5014" strokeWidth={3}/><text x={85} y={20}>p=(1,1)</text><text x={230} y={20}>d=(1.5,1)</text><text x={60} y={115}>Return ({fmt(1+bias)},1)</text></svg><p role="status">B(1,1)=[{fmt(-.25+bias)},0], B(2,1)=[{fmt(-.75+bias)},0]. Half-weight sample=[{fmt(back)},0]. Round-trip error={fmt(round)}; sampled validity={valid?1:.5}; consistent={String(valid&&round<=threshold)}.</p><p>Forward source and destination are in bounds in this example. An invalid contributing reverse sample rejects the path even when the return error is zero.</p></>;
}
const titles:Record<OpticalVisualId,string>={correspondence:"Follow the moving pattern",patch:"Select a pixel, read its equation",ambiguity:"Which motion direction can you see?",sampling:"Four neighbors, one sampled intensity",alignment:"Test a proposed forward lookup",refinement:"Sample, fit, update, repeat",pyramid:"One displacement in three pixel units",evaluation:"Choose the evaluation mask",consistency:"Follow the return path"};
export function OpticalFlowVisual({id="alignment"}:{id?:OpticalVisualId}) {
  const [version,setVersion]=useState(0);
  return <section className="flow-visual" aria-label={titles[id]} data-visual={id}><h3>{titles[id]}</h3><p className="ldpc-caption">Supplied demonstration · deterministic teaching values, separate from learner results. Controls run locally.</p><div key={`${id}-${version}`}>
    {id==="correspondence"&&<Motion/>}{id==="alignment"&&<Motion alignment/>}{id==="patch"&&<Patch/>}{id==="ambiguity"&&<Patch ambiguity/>}{id==="sampling"&&<Sampling/>}{id==="refinement"&&<Refinement/>}{id==="pyramid"&&<Pyramid/>}{id==="evaluation"&&<Evaluation/>}{id==="consistency"&&<Consistency/>}
    </div><button className="secondary-button" onClick={()=>setVersion(n=>n+1)}>Reset demonstration</button><small className="flow-keyboard">Keyboard: Tab to a control, arrows adjust sliders, Space activates buttons. Reset restores all values and stops playback.</small></section>;
}
