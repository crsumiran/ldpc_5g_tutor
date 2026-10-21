"use client";

import type { CheckpointProgress, TheoryPage } from "../../lib/contracts";

type Props = { checkpoints: CheckpointProgress[]; activeId: string; onSelect: (id: string) => void; python?: boolean; theoryPages?: TheoryPage[]; theoryIndex?: number; onTheory?: (index: number) => void };

export function CourseRail({ checkpoints, activeId, onSelect, python = false, theoryPages = [], theoryIndex = -1, onTheory }: Props) {
  const passed = checkpoints.filter((item) => item.status === "passed").length;
  const optical = checkpoints[0]?.id.startsWith("FLOW-");
  return (
    <aside className="course-rail" aria-label="Course checkpoints">
      <div className="rail-kicker">{optical ? "OPTICAL FLOW / NUMPY" : python ? "LDPC / PYTHON" : "CACHE LAB / 01"}</div>
      <div className="rail-title">{optical ? "From gradients to motion" : python ? "Bits to accelerator" : "Build a cache"}</div>
      <div className="rail-progress" aria-label={`${passed} of ${checkpoints.length} checkpoints passed`}>
        <span style={{ width: `${(passed / Math.max(checkpoints.length, 1)) * 100}%` }} />
      </div>
      <div className="rail-progress-label"><span>{passed}/{checkpoints.length}</span><span>complete</span></div>
      <nav>
        {python && theoryPages.length > 0 && <><div className="rail-section-label">START HERE · THEORY</div><ol className="checkpoint-list">{theoryPages.map((page,i) => <li key={page.id}><button className={`checkpoint-link ${theoryIndex === i ? "is-active" : ""}`} onClick={() => onTheory?.(i)} aria-current={theoryIndex === i ? "page" : undefined}><span className="checkpoint-icon">{i+1}</span><span className="checkpoint-copy"><strong>{page.title}</strong><small>Read & explore · no test</small></span></button></li>)}</ol></>}
        <div className="rail-section-label">{python ? "THE LEARNING PATH" : "THE SIGNAL PATH"}</div>
        <ol className="checkpoint-list">
          {checkpoints.map((item, index) => {
            const locked = item.status === "locked";
            return (
              <li key={item.id}>
                <button className={`checkpoint-link ${theoryIndex < 0 && activeId === item.id ? "is-active" : ""}`} disabled={locked} onClick={() => onSelect(item.id)} aria-current={theoryIndex < 0 && activeId === item.id ? "step" : undefined}>
                  <span className={`checkpoint-icon status-${item.status}`}>{item.status === "passed" ? "✓" : locked ? "·" : String(index + 1).padStart(2, "0")}</span>
                  <span className="checkpoint-copy"><strong>{item.title}</strong><small>{item.status === "passed" ? "Passed" : item.status === "locked" ? "Locked" : `${item.estimated_minutes} min`}</small></span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>
      <div className="rail-footnote"><span className="signal-dot" /> {python ? "Python · public checks only" : "Icarus sandbox ready"}</div>
    </aside>
  );
}
