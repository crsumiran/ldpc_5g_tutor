import type { LabRun } from "../../lib/contracts";

type Props = { run: LabRun | null; onDiagnostic: (line: number) => void; python?: boolean };

export function ExecutionPanel({ run, onDiagnostic, python = false }: Props) {
  if (!run) return <div className="empty-result"><span className="terminal-prompt">$</span><span>Run the cell to see compiler and test evidence here.</span></div>;
  if (run.status === "error") return <div className="error-result">The sandbox could not finish this run. Check the API runner and try again.</div>;
  if (run.status !== "done") return <div className="running-result"><span className="spinner" /> {run.status === "queued" ? "Queued in the sandbox…" : "Running isolated checks…"}</div>;
  const result = run.result;
  if (!result) return <div className="error-result">The runner returned no result. Try again.</div>;
  const noPublicChecks = result.compile.ok && run.mode !== "compile" && result.tests.cases.length === 0 && result.tests.passed === 0;
  const testsIncomplete = result.timed_out || noPublicChecks;
  const banner = result.passed ? (run.mode === "compile" ? "Syntax/compile check passed — tests not run" : "Checkpoint passed") : result.timed_out ? "Execution timed out before public checks completed" : noPublicChecks ? "No public checks completed" : result.compile.ok ? `${result.tests.failed + result.tests.errors} public check(s) need attention` : "Syntax or compilation failed";
  return (
    <div className="execution-panel" aria-live="polite">
      <div className={`result-banner ${result.passed ? "result-pass" : "result-fail"}`}><span className="result-mark">{result.passed ? "✓" : "!"}</span><div><strong>{banner}</strong><small>{result.runtime_ms} ms · {python ? "Python · public-only verification" : run.mode === "submit" ? "public + hidden verification" : "formative public checks"}</small></div></div>
      <div className="stage-row"><span className={result.compile.ok ? "stage-done" : "stage-failed"}>{result.compile.ok ? "✓ compiled" : "× compilation"}</span><span className={result.compile.ok ? "stage-done" : "stage-failed"}>{result.compile.ok ? python ? "✓ fresh process" : "✓ elaborated" : "× elaboration"}</span><span className={testsIncomplete || result.tests.failed || result.tests.errors ? "stage-failed" : "stage-done"}>{run.mode === "compile" ? "— tests not run" : testsIncomplete ? "× tests incomplete" : result.tests.failed || result.tests.errors ? "× tests" : "✓ tests"}</span></div>
      {result.diagnostics.length > 0 && <div className="diagnostic-list"><div className="mini-heading"><span>DIAGNOSTICS</span><small>click a line to jump</small></div>{result.diagnostics.map((diagnostic, index) => <button key={`${diagnostic.file}-${diagnostic.line}-${index}`} onClick={() => diagnostic.line && onDiagnostic(diagnostic.line)}><span>{diagnostic.severity === "warning" ? "△" : "×"}</span><strong>{diagnostic.file ? `${diagnostic.file}:${diagnostic.line ?? "?"}` : diagnostic.category}</strong><em>{diagnostic.message}</em></button>)}</div>}
{run.mode !== "compile" && (<div className="test-list"><div className="mini-heading"><span>PUBLIC TESTS</span><small>{result.tests.passed} passed · {result.tests.failed} failed</small></div>{result.tests.cases.length === 0 ? <p className="muted-copy">{result.timed_out ? "The testbench stopped before it could report a result. 0/0 is not a pass." : "The testbench did not emit named cases; 0/0 is not a pass."}</p> : result.tests.cases.map((test) => <div className="test-row" key={test.name}><span className={test.status === "pass" ? "test-pass" : "test-fail"}>{test.status === "pass" ? "✓" : "×"}</span><code>{test.name}</code>{test.message && <small>{test.message}</small>}</div>)}</div>)}
      {run.mode === "submit" && result.hidden && <div className="hidden-summary"><span className="lock-mark">▣</span><strong>Hidden verification</strong><span>{result.hidden.passed} passed · {result.hidden.failed + result.hidden.errors} failed</span></div>}
      {result.artifacts.length > 0 && <div className="artifact-row">{result.artifacts.map((artifact) => <a key={artifact.name} href={artifact.url ?? "#"}>↗ Download {artifact.name}</a>)}</div>}
      <details className="raw-output" open={python && result.output.includes("EXPECTED OUTPUT:")}><summary>{python && result.output.includes("EXPECTED OUTPUT:") ? "Inputs, expected outputs and actual results" : "Raw runner output"}</summary><pre>{result.output}</pre></details>
    </div>
  );
}
