"use client";

import { useEffect, useMemo, useState } from "react";
import { Shell, NavKey } from "../components/Shell";
import { Badge, CountList, Metric, ScoreRing, SeverityBreakdown } from "../components/ui";
import { renderMarkdown } from "../lib/markdown";
import {
  ExampleInfo,
  GroupBy,
  ReportFormat,
  ReportResponse,
  ReportType,
  TemplateInfo,
  generateReport,
  getExamples,
  getTemplates
} from "../lib/api";

const REPORT_TYPES: { id: ReportType; label: string }[] = [
  { id: "executive", label: "Executive" },
  { id: "technical", label: "Technical" },
  { id: "remediation", label: "Remediation" },
  { id: "compliance", label: "Compliance" },
  { id: "board_summary", label: "Board" }
];

const FORMATS: { id: ReportFormat; label: string }[] = [
  { id: "both", label: "Both" },
  { id: "markdown", label: "Markdown" },
  { id: "html", label: "HTML" }
];

const GROUPS: { id: GroupBy; label: string }[] = [
  { id: "severity", label: "Severity" },
  { id: "module", label: "Module" },
  { id: "category", label: "Category" },
  { id: "asset", label: "Asset" }
];

const STARTER = JSON.stringify(
  {
    project: "Payments Platform",
    organization: "MetaSec",
    environment: "production",
    findings: [
      {
        title: "Public administrative port exposed",
        severity: "critical",
        status: "fail",
        source: "Cloudline",
        asset: "aws_security_group.web_admin",
        description: "SSH is open to the internet on a production-facing security group.",
        impact: "The management plane is reachable from the internet.",
        remediation: "Restrict administrative access to a VPN, bastion, or approved ranges."
      }
    ]
  },
  null,
  2
);

type Tab = "summary" | "markdown" | "html";

function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function Page() {
  const [nav, setNav] = useState<NavKey>("workbench");
  const [raw, setRaw] = useState(STARTER);
  const [reportType, setReportType] = useState<ReportType>("technical");
  const [format, setFormat] = useState<ReportFormat>("both");
  const [groupBy, setGroupBy] = useState<GroupBy>("severity");
  const [project, setProject] = useState("Payments Platform");
  const [organization, setOrganization] = useState("MetaSec");
  const [environment, setEnvironment] = useState("production");
  const [opts, setOpts] = useState({
    include_evidence: true,
    include_passed: false,
    include_references: true,
    include_remediation: true,
    include_appendix: true
  });

  const [examples, setExamples] = useState<ExampleInfo[]>([]);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getExamples().then(setExamples).catch(() => setExamples([]));
    getTemplates().then(setTemplates).catch(() => setTemplates([]));
  }, []);

  const parseState = useMemo(() => {
    try {
      const parsed = JSON.parse(raw);
      const findings = Array.isArray(parsed) ? parsed : parsed.findings || [];
      return { valid: true as const, count: Array.isArray(findings) ? findings.length : 0, parsed };
    } catch {
      return { valid: false as const, count: 0, parsed: null };
    }
  }, [raw]);

  function loadExample(example: ExampleInfo) {
    const content = example.content as Record<string, unknown>;
    setRaw(JSON.stringify(content, null, 2));
    if (typeof content.project === "string") setProject(content.project);
    if (typeof content.organization === "string") setOrganization(content.organization);
    if (typeof content.environment === "string") setEnvironment(content.environment);
    setReport(null);
    setError(null);
  }

  async function run() {
    if (!parseState.valid) {
      setError("Input is not valid JSON. Fix the editor content and try again.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const parsed = parseState.parsed as Record<string, unknown>;
      const findings = Array.isArray(parsed) ? parsed : (parsed.findings as unknown[]) || [];
      const result = await generateReport({
        report_type: reportType,
        project,
        organization,
        environment,
        output_format: format,
        findings: findings as Record<string, unknown>[],
        options: { ...opts, sort_by_severity: true, group_by: groupBy }
      });
      setReport(result);
      setTab("summary");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate report");
    } finally {
      setLoading(false);
    }
  }

  function copyActive() {
    if (!report) return;
    const text = tab === "html" ? report.html || "" : report.markdown || "";
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  if (nav === "templates") {
    return (
      <Shell active={nav} onNavigate={setNav}>
        <div className="topbar">
          <div>
            <p className="eyebrow">Library</p>
            <h1>Report templates</h1>
            <p>Each template controls sections, ordering, severity filtering, audience, and output style.</p>
          </div>
        </div>
        <div className="sections">
          {templates.map((t) => (
            <div className="section-card" key={t.id}>
              <h3>{t.name}</h3>
              <p className="note" style={{ marginBottom: 8 }}>{t.description}</p>
              <p className="note">
                Audience: <strong>{t.audience}</strong> · Style: {t.output_style} · Min severity: {t.min_severity}
                {t.includes_passed ? " · includes passed checks" : ""}
              </p>
              <div className="chips" style={{ marginTop: 10 }}>
                {t.sections.map((s) => (
                  <span className="chip" key={s}>{s.replace(/_/g, " ")}</span>
                ))}
              </div>
            </div>
          ))}
          {!templates.length && <div className="empty"><p>Templates load from the API. Start the backend on port 8000.</p></div>}
        </div>
      </Shell>
    );
  }

  if (nav === "about") {
    return (
      <Shell active={nav} onNavigate={setNav}>
        <div className="topbar">
          <div>
            <p className="eyebrow">Documentation</p>
            <h1>About Dossier</h1>
            <p>The reporting and documentation engine for the DevSecOps platform ecosystem.</p>
          </div>
        </div>
        <div className="sections">
          <div className="section-card">
            <h3>What it does</h3>
            <p className="note">
              Dossier consumes raw findings from Podscope, Dockyard, Gatehouse, Stacklint, Tracepack,
              Signalbook, Cloudline, and generic tools, then normalizes, scores, and renders them into
              executive, technical, remediation, compliance, and board-level reports.
            </p>
          </div>
          <div className="section-card">
            <h3>Scoring model</h3>
            <p className="note">
              Reports start at 100 and lose points based on severity, confidence, and the number of
              affected assets. Grades range from A (90+) to F (below 55). Every score ships with a
              plain-language explanation.
            </p>
          </div>
          <div className="section-card">
            <h3>Integration contract</h3>
            <p className="note">
              Stable normalized finding schema, stable report request/response schema, and Markdown/HTML
              exports make Dossier ready to plug into OpsDeck as the central reporting module.
            </p>
          </div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell active={nav} onNavigate={setNav}>
      <div className="topbar">
        <div>
          <p className="eyebrow">Report workbench</p>
          <h1>Turn analyzer findings into stakeholder-ready reports</h1>
          <p>
            Paste findings from any module, pick a report type and format, and generate a scored report
            with executive summary, technical detail, and a prioritized remediation plan.
          </p>
        </div>
        <div className="topbar-actions">
          <button className="btn-primary" onClick={run} disabled={loading || !parseState.valid}>
            {loading ? "Generating…" : "Generate report"}
          </button>
        </div>
      </div>

      <div className="workspace">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>Input</h2>
              <p>Findings JSON, report options, and samples</p>
            </div>
          </div>
          <div className="panel-body">
            <div className="field">
              <label>Report type</label>
              <div className="seg">
                {REPORT_TYPES.map((r) => (
                  <button key={r.id} className={reportType === r.id ? "active" : ""} onClick={() => setReportType(r.id)}>
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="row">
              <div className="field">
                <label>Output format</label>
                <div className="seg">
                  {FORMATS.map((f) => (
                    <button key={f.id} className={format === f.id ? "active" : ""} onClick={() => setFormat(f.id)}>
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="field">
                <label>Group findings by</label>
                <div className="seg">
                  {GROUPS.map((g) => (
                    <button key={g.id} className={groupBy === g.id ? "active" : ""} onClick={() => setGroupBy(g.id)}>
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="row">
              <div className="field">
                <label>Project</label>
                <input className="input" value={project} onChange={(e) => setProject(e.target.value)} />
              </div>
              <div className="field">
                <label>Organization</label>
                <input className="input" value={organization} onChange={(e) => setOrganization(e.target.value)} />
              </div>
            </div>

            <div className="field">
              <label>Environment</label>
              <input className="input" value={environment} onChange={(e) => setEnvironment(e.target.value)} />
            </div>

            <div className="field">
              <label>Options</label>
              <div className="toggles">
                {(
                  [
                    ["include_evidence", "Evidence"],
                    ["include_passed", "Passed checks"],
                    ["include_references", "References"],
                    ["include_remediation", "Remediation"],
                    ["include_appendix", "Appendix"]
                  ] as const
                ).map(([key, label]) => (
                  <label className="toggle" key={key}>
                    <input
                      type="checkbox"
                      checked={opts[key]}
                      onChange={(e) => setOpts((prev) => ({ ...prev, [key]: e.target.checked }))}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <div className="field">
              <label>Load a sample</label>
              <div className="chips">
                {examples.map((ex) => (
                  <button className="chip" key={ex.id} onClick={() => loadExample(ex)}>
                    {ex.name} <span className="src">{ex.module}</span>
                  </button>
                ))}
                {!examples.length && <span className="note">Samples load from the API.</span>}
              </div>
            </div>

            <div className="field" style={{ marginBottom: 0 }}>
              <label>Findings JSON</label>
              <textarea
                className={`editor ${parseState.valid ? "" : "invalid"}`}
                value={raw}
                spellCheck={false}
                onChange={(e) => setRaw(e.target.value)}
              />
              <div className="editor-meta">
                <span className={parseState.valid ? "ok" : "bad"}>
                  {parseState.valid ? `Valid JSON · ${parseState.count} finding(s)` : "Invalid JSON"}
                </span>
                <span>{raw.length} chars</span>
              </div>
            </div>

            {error && <div className="alert">{error}</div>}
          </div>
        </div>

        <div>
          {loading && (
            <div className="loading">
              <div className="spinner" />
              <p>Normalizing findings and rendering the report…</p>
            </div>
          )}

          {!loading && !report && (
            <div className="empty">
              <div className="emoji">🗂️</div>
              <h3>No report yet</h3>
              <p>
                Load a sample or paste findings, choose a report type, and click Generate. You will see the
                score, breakdowns, section preview, Markdown, and an HTML preview here.
              </p>
            </div>
          )}

          {!loading && report && (
            <>
              <div className="metrics">
                <ScoreRing value={report.score.value} grade={report.score.grade} posture={report.score.posture} />
                <Metric
                  label="Findings"
                  value={String(report.aggregation.actionable_findings)}
                  note={`${report.aggregation.total_findings} total · highest ${report.aggregation.highest_severity}`}
                />
                <Metric
                  label="Modules"
                  value={String(Object.keys(report.aggregation.module_counts).length)}
                  note={`${report.aggregation.affected_assets} affected asset(s)`}
                />
                <Metric
                  label="Quick wins"
                  value={String(report.aggregation.quick_wins.length)}
                  note="Low-effort, high-value fixes"
                />
              </div>

              <div className="breakdown">
                <div className="panel">
                  <div className="panel-head"><div><h2>Severity breakdown</h2></div></div>
                  <div className="panel-body"><SeverityBreakdown counts={report.aggregation.severity_counts} /></div>
                </div>
                <div className="panel">
                  <div className="panel-head"><div><h2>Module breakdown</h2></div></div>
                  <div className="panel-body"><CountList data={report.aggregation.module_counts} /></div>
                </div>
              </div>

              {report.aggregation.top_risks.length > 0 && (
                <div className="panel" style={{ marginBottom: 16 }}>
                  <div className="panel-head"><div><h2>Top risks</h2><p>Ranked by prioritization engine</p></div></div>
                  <div className="panel-body">
                    <div className="risk-list">
                      {report.aggregation.top_risks.map((risk, i) => (
                        <div className="risk-item" key={`${risk.title}-${i}`}>
                          <span className="rank">{i + 1}</span>
                          <Badge severity={risk.severity} />
                          <span>{risk.title}</span>
                          <span className="meta">{risk.module} · priority {Math.round(risk.priority_score)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="panel">
                <div className="tabs">
                  <button className={tab === "summary" ? "active" : ""} onClick={() => setTab("summary")}>Sections</button>
                  {report.markdown && (
                    <button className={tab === "markdown" ? "active" : ""} onClick={() => setTab("markdown")}>Markdown</button>
                  )}
                  {report.html && (
                    <button className={tab === "html" ? "active" : ""} onClick={() => setTab("html")}>HTML preview</button>
                  )}
                  <div className="tab-actions">
                    {copied && <span className="copied">Copied</span>}
                    {(tab === "markdown" || tab === "html") && (
                      <button className="btn-ghost" onClick={copyActive}>Copy</button>
                    )}
                    {report.markdown && (
                      <button
                        className="btn-ghost"
                        onClick={() => download(`${report.metadata.project}-report.md`, report.markdown || "", "text/markdown")}
                      >
                        Download .md
                      </button>
                    )}
                    {report.html && (
                      <button
                        className="btn-ghost"
                        onClick={() => download(`${report.metadata.project}-report.html`, report.html || "", "text/html")}
                      >
                        Download .html
                      </button>
                    )}
                  </div>
                </div>

                {tab === "summary" && (
                  <div className="panel-body sections">
                    {report.sections.map((section) => (
                      <div className="section-card" key={section.id}>
                        <h3>{section.title}</h3>
                        <div className="md" dangerouslySetInnerHTML={{ __html: renderMarkdown(section.body) }} />
                      </div>
                    ))}
                  </div>
                )}

                {tab === "markdown" && <pre className="raw">{report.markdown}</pre>}

                {tab === "html" && report.html && (
                  <iframe className="html-frame" title="HTML preview" srcDoc={report.html} />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </Shell>
  );
}
