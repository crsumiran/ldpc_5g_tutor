// Read-only export: stdout is the complete review Markdown. Never exports
// learner work, credentials, target implementations or private author baselines.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir=path.join(root,'curriculum/ldpc_5g');
const read=name=>fs.readFileSync(path.join(dir,name),'utf8');
const json=name=>JSON.parse(read(name));
const manifest=json('manifest.json'), revisions=json('lesson_revisions.json'),fixtures=json('fixtures.json');
if(process.argv.includes('--theory-only')){
  const story=['# Understanding LDPC: the beginner story','', 'The main reading text from the six theory chapters. Extra formulas, tables and programming references remain available in the tutor, but are omitted here to keep the story continuous.',''];
  json('theory.json').forEach((p,i)=>{story.push(`## Chapter ${i+1}: ${p.title}`,'');p.sections.forEach((s,j)=>{if(j>0)story.push(`### ${s.title}`,'');story.push(s.text,'');});});
  process.stdout.write(story.join('\n')+'\n');process.exit(0);
}
const lines=['# Revised LDPC teaching review','', 'Snapshot: 10 October 2026. Current beginner theory, self-contained assignment prose and supplied visual traces. This is not execution evidence or a complete NR accelerator. See docs/LDPC_REVISION_STATUS.md for implemented versus pending scope.',''];
const put=(...parts)=>lines.push(...parts,'');
const renderFixture=id=>{
  const f=fixtures[id];put(`### Worked visual: ${f.label}`,`Fixture: ${id}. ${f.visual_spec.data_origin}`,f.visual_spec.expected_observation);
  const render=v=>{put(`#### ${v.title}`);put('| '+v.columns.join(' | ')+' |','| '+v.columns.map(()=>'---').join(' | ')+' |',...v.rows.map(r=>'| '+r.map(x=>String(x).replaceAll('|','\\|')).join(' | ')+' |'),v.caption);};
  f.views.forEach(render);for(const v of f.variants||[]){put(`#### Controlled variant: ${v.label}`);v.views.forEach(render);}put('Visual specification:', '```json',JSON.stringify(f.visual_spec,null,2),'```');
};
put('## Overview',read(manifest.overview_file),'## Architecture',read(manifest.architecture_file));
const theoryFixtures={'parity':'toy-encode','sparse-graph':'toy-edges','decoding':'flooding-chain'};
for(const p of json('theory.json')){put(`## Theory: ${p.title}`,p.goal);p.sections.forEach(s=>put(`### ${s.title}`,s.text));if(p.optional_sections?.length){put('<details>','<summary>Optional reference material — not part of the main story</summary>');p.optional_sections.forEach(s=>put(`### ${s.title}`,s.text));put('</details>');}put('### Understanding check',p.question,p.answer);if(theoryFixtures[p.id])renderFixture(theoryFixtures[p.id]);put('### Assignment connections',...p.connections.map(c=>`${c.id}: ${c.why}`));}
for(const source of manifest.checkpoints){const c={...source,...revisions[source.id]};put(`## ${c.id}: ${c.title}`,c.goal,c.lesson,'### Input/output contract',...c.requirements.map(r=>'- '+r),'### Prediction',c.prediction);renderFixture(c.fixture_id);put('### Experiment',c.experiment,'### Progressive hints',...c.hints.map((h,i)=>`${i+1}. ${h}`),'### Optional maths / reading',c.optional_math,'### Optional hardware',c.optional_hardware,'### Misconception',c.misconception,'### Reflection',c.reflection,'### Completion',c.completion,'### Takeaway',c.takeaway,`Public cases: ${c.expected_public_checks}; prerequisite IDs: ${c.prerequisites.join(', ')||'none'}.`);}
process.stdout.write(lines.join('\n')+'\n');
