from typing import Any, Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Audience = Literal["executive", "technical", "mixed"]
ReportFormat = Literal["markdown", "html", "both"]


class Finding(BaseModel):
    title: str
    severity: Severity = "info"
    category: str = "General"
    source: str = "unknown"
    target: str = "unknown"
    description: str = ""
    impact: str = ""
    remediation: str = ""
    status: str = "open"
    evidence: str | None = None
    references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    title: str = "Security Review Report"
    project: str = "Unnamed project"
    environment: str = "unspecified"
    audience: Audience = "mixed"
    output_format: ReportFormat = "both"
    findings: list[Finding] = Field(default_factory=list)
    include_remediation_plan: bool = True
    include_executive_summary: bool = True
    include_technical_details: bool = True
    notes: str | None = None


class Section(BaseModel):
    title: str
    body: str


class ReportSummary(BaseModel):
    score: int
    grade: str
    total_findings: int
    severity_counts: dict[str, int]
    category_counts: dict[str, int]
    source_counts: dict[str, int]
    highest_severity: str
    recommended_focus: list[str]


class ReportResponse(BaseModel):
    title: str
    project: str
    environment: str
    summary: ReportSummary
    sections: list[Section]
    markdown: str | None = None
    html: str | None = None


class TemplateInfo(BaseModel):
    id: str
    name: str
    audience: Audience
    description: str
    sections: list[str]


class ExampleInfo(BaseModel):
    id: str
    name: str
    description: str
    content: dict[str, Any]
