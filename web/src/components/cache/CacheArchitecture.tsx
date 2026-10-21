"use client";

type Props = { activeId: string; traceCount: number };

export function CacheArchitecture({ activeId, traceCount }: Props) {
  const isController = activeId === "CACHE-05" || activeId === "CACHE-06";
  return (
    <section className="architecture-card" aria-labelledby="architecture-title">
      <div className="section-eyebrow">LIVE SCHEMATIC <span className="pulse-dot" /></div>
      <div className="architecture-heading"><h2 id="architecture-title">The cache under construction</h2><span className="architecture-counter">TRACE {String(traceCount).padStart(2, "0")}</span></div>
      <div className="schematic-grid">
        <div className={`schematic-node cpu ${isController ? "node-lit" : ""}`}><span className="node-label">CPU</span><strong>request</strong><small>addr / data / write</small></div>
        <div className="signal-arrow">→</div>
        <div className={`schematic-node cache-core ${isController ? "node-lit" : ""}`}><span className="node-label">CACHE</span><strong>4 × 1 word</strong><small>direct mapped</small></div>
        <div className="signal-arrow">→</div>
        <div className="schematic-node memory"><span className="node-label">MEMORY</span><strong>backing store</strong><small>valid / ready</small></div>
      </div>
      <div className="address-strip" aria-label="Address breakdown">
        <div className="address-tag"><span>TAG</span><strong>7 : 4</strong><small>identity</small></div>
        <div className="address-index"><span>INDEX</span><strong>3 : 2</strong><small>line select</small></div>
        <div className="address-offset"><span>OFFSET</span><strong>1 : 0</strong><small>byte in word</small></div>
      </div>
    </section>
  );
}

export function CacheTable() {
  return (
    <div className="cache-table-wrap">
      <div className="mini-heading"><span>LINE STATE</span><small>cleared on reset</small></div>
      <table className="cache-table"><thead><tr><th>IDX</th><th>VALID</th><th>TAG</th><th>DATA</th></tr></thead><tbody>{[0, 1, 2, 3].map((line) => <tr key={line}><td>{line}</td><td><span className="valid-led" /> 0</td><td className="muted-cell">----</td><td className="muted-cell">--------</td></tr>)}</tbody></table>
    </div>
  );
}
