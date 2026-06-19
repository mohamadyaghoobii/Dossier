from fastapi import APIRouter

from app.core.settings import get_settings
from app.schemas import (
    AIRequest,
    AIResponse,
    ExampleInfo,
    NormalizeRequest,
    NormalizeResponse,
    ReportRequest,
    ReportResponse,
    TemplateField,
)
from app.services.ai import get_provider
from app.services.examples import load_examples
from app.services.normalization import normalize_findings
from app.services.prioritization import prioritize
from app.services.reporting import generate_report
from app.services.templates import TEMPLATES

router = APIRouter()


@router.get("/templates", response_model=list[TemplateField])
def templates() -> list[TemplateField]:
    return [
        TemplateField(
            id=t.id,
            name=t.name,
            report_type=t.report_type,
            audience=t.audience,
            description=t.description,
            output_style=t.output_style,
            sections=t.sections,
            min_severity=t.min_severity,
            includes_passed=t.includes_passed,
        )
        for t in TEMPLATES.values()
    ]


@router.get("/examples", response_model=list[ExampleInfo])
def examples() -> list[ExampleInfo]:
    return [ExampleInfo(**item) for item in load_examples()]


@router.post("/normalize", response_model=NormalizeResponse)
def normalize(payload: NormalizeRequest) -> NormalizeResponse:
    findings, dropped = normalize_findings(payload.findings, default_project=payload.project)
    findings = prioritize(findings)
    return NormalizeResponse(count=len(findings), findings=findings, dropped=dropped)


@router.post("/generate", response_model=ReportResponse)
def generate(payload: ReportRequest) -> ReportResponse:
    return generate_report(payload)


@router.post("/ai/summarize", response_model=AIResponse)
def ai_summarize(payload: AIRequest) -> AIResponse:
    settings = get_settings()
    provider = get_provider(settings.ai_provider)
    findings, _ = normalize_findings(payload.findings, default_project=payload.project)
    findings = prioritize(findings)
    return provider.summarize(payload, findings)


@router.post("/ai/remediation-plan", response_model=AIResponse)
def ai_remediation_plan(payload: AIRequest) -> AIResponse:
    settings = get_settings()
    provider = get_provider(settings.ai_provider)
    findings, _ = normalize_findings(payload.findings, default_project=payload.project)
    findings = prioritize(findings)
    return provider.remediation_plan(payload, findings)
