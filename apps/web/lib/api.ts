export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type ReportType = "executive" | "technical" | "remediation" | "compliance" | "board_summary";
export type ReportFormat = "markdown" | "html" | "both";
export type GroupBy = "severity" | "module" | "category" | "asset";

export type ReportOptions = {
  include_evidence: boolean;
  include_passed: boolean;
  include_references: boolean;
  include_remediation: boolean;
  include_appendix: boolean;
  sort_by_severity: boolean;
  group_by: GroupBy;
};

export type ReportRequest = {
  report_type: ReportType;
  title?: string;
  project: string;
  organization: string;
  environment: string;
  output_format: ReportFormat;
  findings: Record<string, unknown>[];
  options: ReportOptions;
  notes?: string;
};

export type RiskItem = {
  title: string;
  severity: Severity;
  module: string;
  asset: string;
  priority_score: number;
  reason: string;
};

export type Score = {
  value: number;
  grade: string;
  posture: string;
  explanation: string;
  breakdown: { severity: Severity; count: number; deduction: number }[];
};

export type Aggregation = {
  total_findings: number;
  actionable_findings: number;
  severity_counts: Record<string, number>;
  status_counts: Record<string, number>;
  module_counts: Record<string, number>;
  category_counts: Record<string, number>;
  affected_assets: number;
  highest_severity: string;
  top_risks: RiskItem[];
  quick_wins: RiskItem[];
  recommended_next_steps: string[];
};

export type NormalizedFinding = {
  id: string;
  title: string;
  severity: Severity;
  status: string;
  category: string;
  module: string;
  asset: string;
  priority_score: number;
  quick_win: boolean;
};

export type Section = { id: string; title: string; body: string };

export type ReportResponse = {
  metadata: {
    report_type: ReportType;
    title: string;
    project: string;
    organization: string;
    environment: string;
    audience: string;
    generated_at: string;
    version: string;
  };
  score: Score;
  aggregation: Aggregation;
  normalized_findings: NormalizedFinding[];
  sections: Section[];
  markdown: string | null;
  html: string | null;
};

export type TemplateInfo = {
  id: ReportType;
  name: string;
  report_type: ReportType;
  audience: string;
  description: string;
  output_style: string;
  sections: string[];
  min_severity: Severity;
  includes_passed: boolean;
};

export type ExampleInfo = {
  id: string;
  name: string;
  module: string;
  description: string;
  content: Record<string, unknown>;
};

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed (${response.status})`);
  }
  return response.json();
}

export function getExamples(): Promise<ExampleInfo[]> {
  return getJson<ExampleInfo[]>("/api/examples");
}

export function getTemplates(): Promise<TemplateInfo[]> {
  return getJson<TemplateInfo[]>("/api/templates");
}

export async function generateReport(payload: ReportRequest): Promise<ReportResponse> {
  const response = await fetch(`${baseUrl}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    let message = `Report generation failed (${response.status})`;
    try {
      const detail = await response.json();
      if (detail?.detail) message = JSON.stringify(detail.detail);
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return response.json();
}
