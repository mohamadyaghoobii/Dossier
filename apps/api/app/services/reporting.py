from datetime import datetime, timezone

from app.schemas import (
    NormalizedFinding,
    ReportMetadata,
    ReportRequest,
    ReportResponse,
)
from app.services.normalization import normalize_findings
from app.services.prioritization import prioritize
from app.services.renderers import render_html, render_markdown
from app.services.scoring import aggregate, compute_score
from app.services.sections import ReportContext, build_sections
from app.services.templates import get_template

VERSION = "0.2.0"

DEFAULT_TITLES = {
    "executive": "Executive Risk Brief",
    "technical": "Technical Security Report",
    "remediation": "Remediation Plan",
    "compliance": "Compliance Summary",
    "board_summary": "Board Risk Summary",
}

DEFAULT_AUDIENCE = {
    "executive": "executive",
    "technical": "technical",
    "remediation": "technical",
    "compliance": "security",
    "board_summary": "board",
}


def normalize_request_findings(request: ReportRequest) -> list[NormalizedFinding]:
    findings, _ = normalize_findings(request.findings, default_project=request.project)
    return prioritize(findings)


def generate_report(request: ReportRequest) -> ReportResponse:
    template = get_template(request.report_type)
    findings = normalize_request_findings(request)
    score = compute_score(findings)
    aggregation = aggregate(findings)

    audience = request.audience or DEFAULT_AUDIENCE.get(request.report_type, "mixed")
    title = request.title or DEFAULT_TITLES.get(request.report_type, "Security Report")
    metadata = ReportMetadata(
        report_type=request.report_type,
        title=title,
        project=request.project,
        organization=request.organization,
        environment=request.environment,
        audience=audience,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        version=VERSION,
    )

    ctx = ReportContext(
        request=request,
        options=request.options,
        template=template,
        findings=findings,
        score=score,
        aggregation=aggregation,
    )
    sections = build_sections(ctx)

    markdown = None
    html = None
    if request.output_format in ("markdown", "both"):
        markdown = render_markdown(metadata, score, aggregation, sections)
    if request.output_format in ("html", "both"):
        html = render_html(metadata, score, aggregation, sections)

    return ReportResponse(
        metadata=metadata,
        score=score,
        aggregation=aggregation,
        normalized_findings=findings,
        sections=sections,
        markdown=markdown,
        html=html,
    )
