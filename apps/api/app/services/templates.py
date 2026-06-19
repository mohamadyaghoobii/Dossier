from dataclasses import dataclass, field

from app.schemas import Audience, ReportType, Severity, SEVERITY_ORDER


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    report_type: ReportType
    audience: Audience
    description: str
    output_style: str
    sections: list[str]
    min_severity: Severity = "info"
    includes_passed: bool = False
    fields: list[str] = field(default_factory=list)


TEMPLATES: dict[ReportType, Template] = {
    "executive": Template(
        id="executive",
        name="Executive Brief",
        report_type="executive",
        audience="executive",
        description="Business-focused snapshot with score, posture, key risks, and priorities in non-technical language.",
        output_style="Narrative, concise, leadership-ready",
        sections=[
            "executive_summary",
            "score_card",
            "risk_posture",
            "top_risks",
            "top_affected_areas",
            "remediation_priorities",
        ],
        min_severity="medium",
        fields=["title", "severity", "module", "impact"],
    ),
    "technical": Template(
        id="technical",
        name="Technical Report",
        report_type="technical",
        audience="technical",
        description="Full findings with severity sections, affected resources, evidence, remediation, and module breakdown.",
        output_style="Detailed, structured, engineering-ready",
        sections=[
            "overview",
            "score_card",
            "severity_table",
            "module_table",
            "category_table",
            "findings",
            "appendix",
        ],
        min_severity="info",
        includes_passed=True,
        fields=[
            "title",
            "severity",
            "status",
            "module",
            "category",
            "asset",
            "file_path",
            "description",
            "impact",
            "remediation",
            "evidence",
            "references",
        ],
    ),
    "remediation": Template(
        id="remediation",
        name="Remediation Plan",
        report_type="remediation",
        audience="technical",
        description="Prioritized, sprint-friendly action list with quick wins, high-impact fixes, owners, and effort placeholders.",
        output_style="Action-oriented, prioritized backlog",
        sections=[
            "overview",
            "quick_wins",
            "remediation_plan",
            "recommended_order",
        ],
        min_severity="info",
        fields=["title", "severity", "module", "asset", "remediation"],
    ),
    "compliance": Template(
        id="compliance",
        name="Compliance Summary",
        report_type="compliance",
        audience="security",
        description="Control-style grouping with pass/fail summary and evidence-oriented structure, framework-agnostic by default.",
        output_style="Control-grouped, evidence-oriented",
        sections=[
            "overview",
            "control_summary",
            "control_groups",
            "evidence_index",
        ],
        min_severity="info",
        includes_passed=True,
        fields=["title", "severity", "status", "category", "asset", "evidence"],
    ),
    "board_summary": Template(
        id="board_summary",
        name="Board Summary",
        report_type="board_summary",
        audience="board",
        description="One-page risk snapshot with score, trend placeholder, top five issues, and recommended next actions.",
        output_style="One-page, very high level",
        sections=[
            "risk_snapshot",
            "score_card",
            "top_five_issues",
            "next_actions",
        ],
        min_severity="high",
        fields=["title", "severity"],
    ),
}


def get_template(report_type: ReportType) -> Template:
    return TEMPLATES.get(report_type, TEMPLATES["technical"])


def severity_at_least(severity: Severity, minimum: Severity) -> bool:
    return SEVERITY_ORDER.index(severity) <= SEVERITY_ORDER.index(minimum)
