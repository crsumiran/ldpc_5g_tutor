// Read-only teaching export. Never includes learner code, keys or author baselines.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../curriculum/optical_flow');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const m=JSON.parse(read('manifest.json')),pages=JSON.parse(read('theory.json'));
const lines=['# Optical flow with NumPy','', 'Teaching-text snapshot: 18 October 2026. Five chapters, twelve learner-written functions and 36 public checks. Demonstrations use supplied deterministic values, separate from learner results. The numerical explanations below also form the tutor context.','',read('overview.md'),''];
for(const p of pages){
  lines.push(`## ${p.title}`,'',p.goal,'');
  for(const s of p.sections){lines.push(`### ${s.title}`,'',s.text,'');if(s.visual)lines.push(`Interactive demonstration: ${s.visual}. Its worked numerical explanation is included above; controls run locally.`,'');}
  lines.push('Check your understanding: '+p.question,'',p.answer,'','Next assignments: '+p.connections.map(c=>`${c.id} — ${c.why}`).join(' '),'');
}
for(const c of m.checkpoints){
  lines.push(`## ${c.id}: ${c.title}`,'',c.lesson,'','### Input/output reference and invocation','',c.input_reference,'','<details><summary>Hints</summary>','',...c.hints.map((h,i)=>`${i+1}. ${h}`),'','</details>','','<details><summary>Experiment and reflection</summary>','',c.experiment,'',c.prediction,'',c.reflection,'','</details>','');
}
process.stdout.write(lines.join('\n')+'\n');
