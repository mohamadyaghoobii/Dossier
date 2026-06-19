export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Finding = {
  title: string;
  severity: Severity;
  category: string;
  source: string;
  target: string;
  description: string;
  impact: string;
  remediation: string;
  status?: string;
};

export type ReportRequest = {
  title: string;
  project: string;
  environment: string;
  audience: "executive" | "technical" | "mixed";
  output_format: "markdown" | "html" | "both";
  findings: Finding[];
  include_remediation_plan: boolean;
  include_executive_summary: boolean;
  include_technical_details: boolean;
  notes?: string;
};

export type ReportResponse = {
  title: string;
  project: string;
  environment: string;
  summary: {
    score: number;
    grade: string;
    total_findings: number;
    severity_counts: Record<string, number>;
    category_counts: Record<string, number>;
    source_counts: Record<string, number>;
    highest_severity: string;
    recommended_focus: string[];
  };
  sections: { title: string; body: string }[];
  markdown: string | null;
  html: string | null;
};

export type ExampleInfo = {
  id: string;
  name: string;
  description: string;
  content: Record<string, unknown>;
};

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function getExamples(): Promise<ExampleInfo[]> {
  const response = await fetch(`${baseUrl}/api/examples`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load examples");
  }
  return response.json();
}

export async function generateReport(payload: ReportRequest): Promise<ReportResponse> {
  const response = await fetch(`${baseUrl}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Report generation failed");
  }
  return response.json();
}
