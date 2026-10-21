import type { ReactNode } from "react";

type Props = { number: string; label: string; tone?: "neutral" | "active" | "result" | "hint"; children: ReactNode; actions?: ReactNode };

export function NotebookCell({ number, label, tone = "neutral", children, actions }: Props) {
  return (
    <section className={`notebook-cell cell-${tone}`}>
      <div className="cell-gutter"><span>[{number}]</span><i /></div>
      <div className="cell-main">
        <div className="cell-header"><div><span className="cell-type">{label}</span></div>{actions}</div>
        {children}
      </div>
    </section>
  );
}
