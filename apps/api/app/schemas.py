from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Status = Literal["fail", "warn", "pass", "info", "accepted", "mitigated"]
Audience = Literal["executive", "technical", "security", "mixed", "board"]
ReportType = Literal["executive", "technical", "remediation", "compliance", "board_summary"]
ReportFormat = Literal["markdown", "html", "both"]
GroupBy = Literal["severity", "module", "category", "asset"]

SEVERITY_ORDER: list[Severity] = ["critical", "high", "medium", "low", "info"]


class RawFinding(BaseModel):
    model_config = ConfigDict(extra="allow")


class NormalizedFinding(BaseModel):
    id: str
    title: str
    severity: Severity = "info"
    status: Status = "fail"
    category: str = "General"
    module: str = "unknown"
    tool: str = "unknown"
    project: str | None = None
    asset: str = "unspecified"
    file_path: str | None = None
    line: int | None = None
    description: str = ""
    impact: str = ""
    remediation: str = ""
    evidence: str | None = None
    references: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    created_at: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority_score: float = 0.0
    priority_reasons: list[str] = Field(default_factory=list)
    quick_win: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportOptions(BaseModel):
    include_evidence: bool = True
    include_passed: bool = False
    include_references: bool = True
    include_remediation: bool = True
    include_appendix: bool = True
    sort_by_severity: bool = True
    group_by: GroupBy = "severity"


class ReportRequest(BaseModel):
    report_type: ReportType = "technical"
    title: str | None = None
    project: str = "Unnamed project"
    organization: str = "Internal"
    environment: str = "unspecified"
    audience: Audience | None = None
    output_format: ReportFormat = "both"
    findings: list[dict[str, Any]] = Field(default_factory=list)
    options: ReportOptions = Field(default_factory=ReportOptions)
    notes: str | None = None


class NormalizeRequest(BaseModel):
    findings: list[dict[str, Any]] = Field(default_factory=list)
    project: str | None = None


class NormalizeResponse(BaseModel):
    count: int
    findings: list[NormalizedFinding]
    dropped: int = 0


class ScoreBreakdown(BaseModel):
    severity: Severity
    count: int
    deduction: float


class Score(BaseModel):
    value: int
    grade: str
    posture: str
    explanation: str
    breakdown: list[ScoreBreakdown]


class RiskItem(BaseModel):
    title: str
    severity: Severity
    module: str
    asset: str
    priority_score: float
    reason: str


class Aggregation(BaseModel):
    total_findings: int
    actionable_findings: int
    severity_counts: dict[str, int]
    status_counts: dict[str, int]
    module_counts: dict[str, int]
    category_counts: dict[str, int]
    affected_assets: int
    highest_severity: str
    top_risks: list[RiskItem]
    quick_wins: list[RiskItem]
    recommended_next_steps: list[str]


class Section(BaseModel):
    id: str
    title: str
    body: str


class ReportMetadata(BaseModel):
    report_type: ReportType
    title: str
    project: str
    organization: str
    environment: str
    audience: Audience
    generated_at: str
    generator: str = "Dossier"
    version: str


class ReportResponse(BaseModel):
    metadata: ReportMetadata
    score: Score
    aggregation: Aggregation
    normalized_findings: list[NormalizedFinding]
    sections: list[Section]
    markdown: str | None = None
    html: str | None = None


class TemplateField(BaseModel):
    id: str
    name: str
    report_type: ReportType
    audience: Audience
    description: str
    output_style: str
    sections: list[str]
    min_severity: Severity
    includes_passed: bool


class ExampleInfo(BaseModel):
    id: str
    name: str
    description: str
    module: str
    content: dict[str, Any]


class AIRequest(BaseModel):
    report_type: ReportType = "executive"
    project: str = "Unnamed project"
    organization: str = "Internal"
    findings: list[dict[str, Any]] = Field(default_factory=list)
    instructions: str | None = None


class AIResponse(BaseModel):
    provider: str
    model: str | None = None
    generated: bool
    content: str
    note: str | None = None
