import type { ReactNode } from "react";

const items = ["Workbench", "Templates", "Findings", "Exports", "History", "Settings"];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">D</div>
          <div>
            <strong>Dossier</strong>
            <span>Report workbench</span>
          </div>
        </div>
        <nav>
          {items.map((item, index) => (
            <a className={index === 0 ? "active" : ""} key={item}>{item}</a>
          ))}
        </nav>
        <div className="sidebarNote">
          <span>OpsDeck contract</span>
          <strong>Stable JSON output</strong>
        </div>
      </aside>
      <section className="content">{children}</section>
    </main>
  );
}
