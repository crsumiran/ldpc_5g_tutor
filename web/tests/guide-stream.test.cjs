const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const ts = require('typescript');

function apiFor(text) {
  const file = path.resolve(__dirname, '../src/lib/api.ts');
  const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  });
  const bytes = new TextEncoder().encode(text);
  let offset = 0;
  const body = new ReadableStream({
    pull(controller) {
      if (offset === bytes.length) return controller.close();
      controller.enqueue(bytes.slice(offset, offset + 3));
      offset = Math.min(offset + 3, bytes.length);
    },
  });
  const exports = {};
  vm.runInNewContext(compiled.outputText, {
    exports, require: createRequire(file), TextDecoder,
    fetch: async () => new Response(body, { headers: { 'Content-Type': 'text/event-stream' } }),
  });
  return exports;
}

test('guide stream handles split frames, Unicode and heartbeats', async () => {
  const result = { reply: { summary: 'Useful answer', error_category: 'none', next_step: 'Trace the handshake' }, content: 'Useful answer' };
  const api = apiFor(': keepalive\n\nevent: status\ndata: {"message":"Thinking…"}\n\nevent: result\ndata: ' + JSON.stringify(result) + '\n\n');
  const statuses = [];
  const answer = await api.askTutor('learner', { checkpoint_id: 'CACHE-01', message: 'Why?' }, undefined, text => statuses.push(text));
  assert.equal(answer.content, result.content);
  assert.deepEqual(statuses, ['Thinking…']);
});

test('guide stream surfaces an API error event', async () => {
  const api = apiFor('event: error\ndata: {"detail":"Checkpoint is locked"}\n\n');
  await assert.rejects(api.askTutor('learner', { checkpoint_id: 'CACHE-06', message: 'Why?' }), /Checkpoint is locked/);
});

test('a truncated stream is not accepted as a successful answer', async () => {
  const api = apiFor('event: status\ndata: {"message":"Thinking"}\n\n');
  await assert.rejects(api.askTutor('learner', { checkpoint_id: 'CACHE-01', message: 'Why?' }), /ended before an answer/);
});
