from collections import Counter
from app.schemas import Finding, ReportRequest, ReportResponse, ReportSummary, Section
from app.services.renderers import render_html, render_markdown

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEVERITY_POINTS = {
    "critical": 22,
    "high": 14,
    "medium": 8,
    "low": 3,
    "info": 0
}


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 55:
        return "D"
    return "F"


def _counts(findings: list[Finding], field: str) -> dict[str, int]:
    counter = Counter(getattr(item, field) for item in findings)
    return dict(counter)


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counter = Counter(item.severity for item in findings)
    return {severity: counter.get(severity, 0) for severity in SEVERITY_ORDER}


def _highest_severity(counts: dict[str, int]) -> str:
    for severity in SEVERITY_ORDER:
        if counts.get(severity, 0) > 0:
            return severity
    return "none"


def _score(findings: list[Finding]) -> int:
    score = 100
    for finding in findings:
        score -= SEVERITY_POINTS.get(finding.severity, 0)
    return max(0, min(100, score))


def _top_focus(findings: list[Finding]) -> list[str]:
    ordered = sorted(findings, key=lambda item: SEVERITY_ORDER.index(item.severity))
    focus = []
    seen = set()
    for item in ordered:
        key = f"{item.severity}:{item.title}"
        if key in seen:
            continue
        seen.add(key)
        focus.append(f"{item.severity.upper()}: {item.title} on {item.target}")
        if len(focus) == 5:
            break
    return focus


def build_summary(findings: list[Finding]) -> ReportSummary:
    severity_counts = _severity_counts(findings)
    score = _score(findings)
    return ReportSummary(
        score=score,
        grade=_grade(score),
        total_findings=len(findings),
        severity_counts=severity_counts,
        category_counts=_counts(findings, "category"),
        source_counts=_counts(findings, "source"),
        highest_severity=_highest_severity(severity_counts),
        recommended_focus=_top_focus(findings)
    )


def _executive_summary(request: ReportRequest, summary: ReportSummary) -> Section:
    if summary.total_findings == 0:
        body = f"{request.project} has no reported findings in the submitted dataset. The current score is {summary.score} ({summary.grade}). Keep monitoring drift and re-run the report after each major change."
    else:
        focus = "\n".join(f"- {item}" for item in summary.recommended_focus)
        body = (
            f"{request.project} received a report score of {summary.score} ({summary.grade}) for the {request.environment} environment. "
            f"The dataset contains {summary.total_findings} findings, with the highest severity marked as {summary.highest_severity}. "
            f"Leadership attention should focus on the highest-impact issues first.\n\n{focus}"
        )
    return Section(title="Executive Summary", body=body)


def _risk_snapshot(summary: ReportSummary) -> Section:
    severity_lines = "\n".join(f"- {severity.title()}: {count}" for severity, count in summary.severity_counts.items())
    category_lines = "\n".join(f"- {category}: {count}" for category, count in sorted(summary.category_counts.items())) or "- No categories reported"
    source_lines = "\n".join(f"- {source}: {count}" for source, count in sorted(summary.source_counts.items())) or "- No sources reported"
    body = f"Score: {summary.score}\nGrade: {summary.grade}\n\nSeverity distribution:\n{severity_lines}\n\nCategory distribution:\n{category_lines}\n\nSource distribution:\n{source_lines}"
    return Section(title="Risk Snapshot", body=body)


def _technical_details(findings: list[Finding]) -> Section:
    if not findings:
        return Section(title="Technical Details", body="No findings were submitted for technical review.")
    lines = []
    ordered = sorted(findings, key=lambda item: (SEVERITY_ORDER.index(item.severity), item.category, item.title))
    for index, finding in enumerate(ordered, start=1):
        lines.append(f"{index}. [{finding.severity.upper()}] {finding.title}")
        lines.append(f"Source: {finding.source}")
        lines.append(f"Category: {finding.category}")
        lines.append(f"Target: {finding.target}")
        if finding.description:
            lines.append(f"Description: {finding.description}")
        if finding.impact:
            lines.append(f"Impact: {finding.impact}")
        if finding.remediation:
            lines.append(f"Remediation: {finding.remediation}")
        lines.append("")
    return Section(title="Technical Details", body="\n".join(lines).strip())


def _remediation_plan(findings: list[Finding]) -> Section:
    if not findings:
        return Section(title="Remediation Roadmap", body="No remediation actions are required from the submitted findings.")
    buckets = {
        "Immediate": [item for item in findings if item.severity in {"critical", "high"}],
        "Next Sprint": [item for item in findings if item.severity == "medium"],
        "Backlog": [item for item in findings if item.severity in {"low", "info"}]
    }
    lines = []
    for bucket, items in buckets.items():
        lines.append(f"{bucket}:")
        if not items:
            lines.append("- No items")
        else:
            for item in items[:8]:
                action = item.remediation or "Review and define an owner."
                lines.append(f"- {item.title}: {action}")
        lines.append("")
    return Section(title="Remediation Roadmap", body="\n".join(lines).strip())


def generate_report(request: ReportRequest) -> ReportResponse:
    summary = build_summary(request.findings)
    sections = []
    if request.include_executive_summary:
        sections.append(_executive_summary(request, summary))
    sections.append(_risk_snapshot(summary))
    if request.include_technical_details:
        sections.append(_technical_details(request.findings))
    if request.include_remediation_plan:
        sections.append(_remediation_plan(request.findings))
    if request.notes:
        sections.append(Section(title="Analyst Notes", body=request.notes))
    markdown = None
    html = None
    if request.output_format in {"markdown", "both"}:
        markdown = render_markdown(request.title, request.project, request.environment, sections)
    if request.output_format in {"html", "both"}:
        html = render_html(request.title, request.project, request.environment, sections)
    return ReportResponse(
        title=request.title,
        project=request.project,
        environment=request.environment,
        summary=summary,
        sections=sections,
        markdown=markdown,
        html=html
    )
