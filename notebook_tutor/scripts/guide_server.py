"""Local browser Q&A via isolated OpenCode CLI and OpenRouter's free router.

Run from a terminal, never a notebook cell. The OpenRouter key is read by
getpass, kept in process memory, and passed only to a short-lived OpenCode
child. No model text is sent to the browser until the child finishes and basic
response checks run.
"""

import argparse
import getpass
import html
import json
import os
import shutil
import signal
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CONFIG = Path(__file__).resolve().parents[1] / 'guide_opencode.json'
MODEL = 'openrouter/openrouter/free'
KEY = None


def ask(question):
    if not isinstance(question, str) or not question.strip() or len(question) > 5000:
        raise ValueError('Question must contain 1 to 5000 characters')
    prompt = ('Assignment: implement the text path of Qwen3.6-27B using NumPy, '
              'with public operator checks and optional full-checkpoint parity. '
              'Only observed public checks decide pass/fail.\n\nLearner question:\n' + question)
    with tempfile.TemporaryDirectory(prefix='qwen-guide-') as private:
        p = Path(private)
        for name in ('config', 'data', 'cache', 'state', 'work'):
            (p / name).mkdir()
        env = {k: v for k, v in os.environ.items()
               if k not in ('OPENROUTER_API_KEY', 'OPENCODE_CONFIG')}
        env.update({
            'OPENROUTER_API_KEY': KEY,
            'OPENCODE_CONFIG': str(CONFIG),
            'OPENCODE_DISABLE_PROJECT_CONFIG': '1',
            'OPENCODE_DISABLE_AUTOUPDATE': '1',
            'XDG_CONFIG_HOME': str(p / 'config'),
            'XDG_DATA_HOME': str(p / 'data'),
            'XDG_CACHE_HOME': str(p / 'cache'),
            'XDG_STATE_HOME': str(p / 'state'),
        })
        command = ['opencode', 'run', '--pure', '--agent', 'tutor', '--model', MODEL,
                   '--dir', str(p / 'work'), prompt]
        process = subprocess.Popen(command, cwd=p / 'work', env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        try:
            stdout, _stderr = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise
        answer = stdout.strip()
        if process.returncode or not answer:
            raise RuntimeError('The free model did not return an answer; check OpenCode and OpenRouter availability.')
        if KEY in answer or len(answer) > 16000:
            raise RuntimeError('The guide response failed output checks.')
        return answer


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Qwen NumPy guide</title>
<style>body{font:16px system-ui;max-width:50rem;margin:3rem auto;padding:0 1rem}textarea{width:100%;height:9rem}button{padding:.6rem 1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f3f3;padding:1rem}</style>
<h1>Qwen NumPy guide</h1><p>Ask about a concept or paste a short public check failure. The free model is advisory; public checks decide pass/fail.</p>
<form method="post" action="/ask"><label for="q">Question</label><textarea name="q" id="q" maxlength="5000" required></textarea><br><button>Ask</button></form>{answer}</html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Keep questions and provider failures out of access logs.

    def _write(self, status, body):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _write_json(self, status, payload):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != '/':
            return self._write(404, 'Not found')
        self._write(200, PAGE.replace('{answer}', ''))

    def do_POST(self):
        from urllib.parse import parse_qs
        if self.path not in ('/ask', '/api/ask') or self.headers.get('Origin') not in (
                None, f'http://127.0.0.1:{self.server.server_port}'):
            return self._write(403, 'Forbidden')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self._write(400, 'Invalid content length')
        if size < 1 or size > 12000:
            return self._write(413, 'Question too long')
        raw = self.rfile.read(size).decode('utf-8')
        if self.path == '/api/ask':
            try:
                question = json.loads(raw)['question']
            except (ValueError, KeyError, TypeError):
                return self._write_json(400, {'error': 'Expected JSON with question'})
        else:
            form = parse_qs(raw, keep_blank_values=True)
            question = form.get('q', [''])[0]
        try:
            answer = ask(question)
            if self.path == '/api/ask':
                return self._write_json(200, {'answer': answer, 'requested_model': MODEL})
            box = '<h2>Guide answer</h2><pre>' + html.escape(answer) + '</pre>'
            status = 200
        except (ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            if self.path == '/api/ask':
                return self._write_json(400, {'error': str(exc)})
            box = '<h2>Guide unavailable</h2><pre>' + html.escape(str(exc)) + '</pre>'
            status = 400
        self._write(status, PAGE.replace('{answer}', box))


def main():
    global KEY, MODEL
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='openrouter/free',
                        help='OpenRouter free router or a specific model ending :free')
    args = parser.parse_args()
    if args.model != 'openrouter/free' and not args.model.endswith(':free'):
        raise SystemExit('Select openrouter/free or a model slug ending :free.')
    if not all(ch.isalnum() or ch in '/:._-' for ch in args.model):
        raise SystemExit('Invalid model slug.')
    MODEL = 'openrouter/' + args.model
    if not shutil.which('opencode'):
        raise SystemExit('Install OpenCode before starting the guide.')
    KEY = getpass.getpass('OpenRouter API key (input hidden): ').strip()
    if not KEY:
        raise SystemExit('A key is required for OpenRouter questions.')
    server = ThreadingHTTPServer(('127.0.0.1', 3010), Handler)
    print('Qwen guide: http://127.0.0.1:3010')
    try:
        server.serve_forever()
    finally:
        KEY = None
        server.server_close()


if __name__ == '__main__':
    main()
