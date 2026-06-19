from fastapi import APIRouter
from app.schemas import ReportRequest, ReportResponse, TemplateInfo, ExampleInfo
from app.services.examples import TEMPLATES, load_examples
from app.services.reporting import generate_report

router = APIRouter()


@router.get("/templates", response_model=list[TemplateInfo])
def templates() -> list[TemplateInfo]:
    return [TemplateInfo(**item) for item in TEMPLATES]


@router.get("/examples", response_model=list[ExampleInfo])
def examples() -> list[ExampleInfo]:
    return [ExampleInfo(**item) for item in load_examples()]


@router.post("/generate", response_model=ReportResponse)
def generate(payload: ReportRequest) -> ReportResponse:
    return generate_report(payload)
