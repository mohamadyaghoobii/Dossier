import type { Severity } from "../lib/api";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];
const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "var(--critical)",
  high: "var(--high)",
  medium: "var(--medium)",
  low: "var(--low)",
  info: "var(--info)"
};

export function Badge({ severity }: { severity: string }) {
  const sev = (SEVERITY_ORDER as string[]).includes(severity) ? severity : "info";
  return <span className={`badge ${sev}`}>{severity}</span>;
}

export function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="metric">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      <div className="note">{note}</div>
    </div>
  );
}

function gradeColor(grade: string): string {
  if (grade === "A") return "var(--good)";
  if (grade === "B") return "var(--low)";
  if (grade === "C") return "var(--medium)";
  if (grade === "D") return "var(--high)";
  return "var(--critical)";
}

export function ScoreRing({ value, grade, posture }: { value: number; grade: string; posture: string }) {
  const color = gradeColor(grade);
  return (
    <div className="metric">
      <div className="label">Report Score</div>
      <div className="score-ring">
        <div className="ring" style={{ ["--p" as string]: value, ["--ring-color" as string]: color }}>
          <div className="inner">
            <b>{value}</b>
          </div>
        </div>
        <div>
          <span className="grade-pill" style={{ background: "rgba(148,163,184,0.12)", color }}>
            Grade {grade}
          </span>
          <div className="note" style={{ marginTop: 6 }}>{posture}</div>
        </div>
      </div>
    </div>
  );
}

export function SeverityBreakdown({ counts }: { counts: Record<string, number> }) {
  const max = Math.max(1, ...SEVERITY_ORDER.map((s) => counts[s] || 0));
  return (
    <div>
      {SEVERITY_ORDER.map((s) => {
        const count = counts[s] || 0;
        return (
          <div className="bar-row" key={s}>
            <span className="name">{s}</span>
            <span className="bar-track">
              <span
                className="bar-fill"
                style={{ width: `${(count / max) * 100}%`, background: SEVERITY_COLOR[s] }}
              />
            </span>
            <span className="count">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

export function CountList({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return <p className="note">No data.</p>;
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <div>
      {entries.map(([name, count]) => (
        <div className="bar-row" key={name}>
          <span className="name" style={{ width: 110, textTransform: "none" }}>{name}</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${(count / max) * 100}%`, background: "var(--accent)" }} />
          </span>
          <span className="count">{count}</span>
        </div>
      ))}
    </div>
  );
}
