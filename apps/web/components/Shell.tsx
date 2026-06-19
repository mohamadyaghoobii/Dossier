"use client";

import type { ReactNode } from "react";

export type NavKey = "workbench" | "templates" | "about";

const items: { key: NavKey; label: string }[] = [
  { key: "workbench", label: "Report Workbench" },
  { key: "templates", label: "Templates" },
  { key: "about", label: "About & Docs" }
];

export function Shell({
  active,
  onNavigate,
  children
}: {
  active: NavKey;
  onNavigate: (key: NavKey) => void;
  children: ReactNode;
}) {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">D</div>
          <div>
            <strong>Dossier</strong>
            <span>Reporting engine</span>
          </div>
        </div>
        <nav className="nav">
          {items.map((item) => (
            <button
              key={item.key}
              className={active === item.key ? "active" : ""}
              onClick={() => onNavigate(item.key)}
            >
              <span className="dot" />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span>OpsDeck contract</span>
          <strong>Stable JSON output</strong>
          <p>Normalized findings, scoring, and Markdown/HTML exports ready for platform ingestion.</p>
        </div>
      </aside>
      <section className="content">{children}</section>
    </main>
  );
}
