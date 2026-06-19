"use client";

import { useEffect, useMemo, useState } from "react";
import { Shell } from "../components/Shell";
import { MetricCard } from "../components/MetricCard";
import { SectionView } from "../components/SectionView";
import { ExampleInfo, ReportResponse, generateReport, getExamples } from "../lib/api";

const fallbackInput = JSON.stringify({
  project: "MetaSec DevSecOps Suite",
  environment: "production",
  findings: [
    {
      title: "Public administrative port exposed",
      severity: "critical",
      category: "Network Exposure",
      source: "Cloudline",
      target: "aws_security_group.web_admin",
      description: "SSH is open to the internet on a production-facing security group.",
      impact: "Management-plane access is reachable from the internet.",
      remediation: "Restrict administrative access to VPN, bastion, or approved ranges."
    }
  ]
}, null, 2);

function normalizeInput(raw: string) {
  const parsed = JSON.parse(raw);
  return {
    title: parsed.title || "DevSecOps Review Report",
    project: parsed.project || "Unnamed project",
    environment: parsed.environment || "unspecified",
    audience: parsed.audience || "mixed",
    output_format: parsed.output_format || "both",
    findings: parsed.findings || [],
    include_remediation_plan: true,
    include_executive_summary: true,
    include_technical_details: true,
    notes: parsed.notes || undefined
  };
}

export default function Home() {
  const [raw, setRaw] = useState(fallbackInput);
  const [examples, setExamples] = useState<ExampleInfo[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getExamples().then(setExamples).catch(() => setExamples([]));
  }, []);

  const severityText = useMemo(() => {
    if (!report) return "No report yet";
    return Object.entries(report.summary.severity_counts).map(([key, value]) => `${key}: ${value}`).join(" · ");
  }, [report]);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const payload = normalizeInput(raw);
      const result = await generateReport(payload);
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate report");
    } finally {
      setLoading(false);
    }
  }

  function loadExample(example: ExampleInfo) {
    setRaw(JSON.stringify(example.content, null, 2));
    setReport(null);
    setError(null);
  }

  return (
    <Shell>
      <section className="hero">
        <div>
          <p className="eyebrow">Report generator</p>
          <h1>Turn analyzer findings into stakeholder-ready reports.</h1>
          <p>Dossier normalizes results from Podscope, Dockyard, Gatehouse, Stacklint, Tracepack, Signalbook, and Cloudline into clean executive and technical output.</p>
        </div>
        <button onClick={run} disabled={loading}>{loading ? "Generating..." : "Generate report"}</button>
      </section>

      <section className="grid metrics">
        <MetricCard label="Score" value={report ? String(report.summary.score) : "--"} note={report ? `Grade ${report.summary.grade}` : "Generate a report"} />
        <MetricCard label="Findings" value={report ? String(report.summary.total_findings) : "--"} note={severityText} />
        <MetricCard label="Highest risk" value={report ? report.summary.highest_severity : "--"} note="Based on normalized severity" />
      </section>

      <section className="workspace">
        <div className="panel inputPanel">
          <div className="panelHeader">
            <div>
              <h2>Input bundle</h2>
              <p>Paste JSON from any analyzer or load a sample.</p>
            </div>
          </div>
          <div className="examples">
            {examples.map((example) => <button key={example.id} onClick={() => loadExample(example)}>{example.name}</button>)}
          </div>
          <textarea value={raw} onChange={(event) => setRaw(event.target.value)} spellCheck={false} />
          {error && <div className="errorBox">{error}</div>}
        </div>

        <div className="panel reportPanel">
          <div className="panelHeader">
            <div>
              <h2>Report preview</h2>
              <p>Executive summary, technical details, and remediation plan.</p>
            </div>
          </div>
          {!report && <div className="emptyState">Generate a report to preview sections and exportable Markdown or HTML.</div>}
          {report && (
            <div className="sections">
              {report.sections.map((section) => <SectionView key={section.title} title={section.title} body={section.body} />)}
            </div>
          )}
        </div>
      </section>

      {report?.markdown && (
        <section className="panel exportPanel">
          <div className="panelHeader">
            <div>
              <h2>Markdown export</h2>
              <p>Copy this into a ticket, wiki, pull request, or report repository.</p>
            </div>
          </div>
          <pre>{report.markdown}</pre>
        </section>
      )}
    </Shell>
  );
}
