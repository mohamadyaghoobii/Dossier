from app.services.normalization import (
    normalize_finding,
    normalize_findings,
    normalize_severity,
    normalize_status,
    extract_findings,
)
from app.services.prioritization import prioritize
from app.services.scoring import aggregate, compute_score
from app.services.templates import TEMPLATES, get_template, severity_at_least
from app.services.renderers.html import md_to_html
from app.services.renderers.markdown import render_markdown
from app.schemas import ReportMetadata


def test_severity_aliases() -> None:
    assert normalize_severity("error") == "high"
    assert normalize_severity("warning") == "medium"
    assert normalize_severity("informational") == "info"
    assert normalize_severity("9") == "critical"
    assert normalize_severity(None) == "info"


def test_status_defaults() -> None:
    assert normalize_status("open", "high") == "fail"
    assert normalize_status(None, "high") == "fail"
    assert normalize_status(None, "info") == "info"
    assert normalize_status("risk_accepted", "high") == "accepted"


def test_normalize_field_aliasing() -> None:
    finding = normalize_finding(
        {
            "rule": "Open S3 bucket",
            "risk": "critical",
            "state": "fail",
            "resource": "aws_s3_bucket.public",
            "file": "infra/storage.tf",
            "line": "12",
            "recommendation": "Block public access",
            "scanner": "stacklint",
        }
    )
    assert finding is not None
    assert finding.title == "Open S3 bucket"
    assert finding.severity == "critical"
    assert finding.module == "Stacklint"
    assert finding.file_path == "infra/storage.tf"
    assert finding.line == 12
    assert finding.remediation == "Block public access"
    assert finding.id.startswith("DSR-")


def test_normalize_drops_titleless() -> None:
    findings, dropped = normalize_findings([{"severity": "high"}, {"title": "Valid"}])
    assert len(findings) == 1
    assert dropped == 1


def test_extract_findings_keys() -> None:
    assert len(extract_findings({"results": [{"title": "a"}]})) == 1
    assert len(extract_findings({"issues": [{"title": "a"}, {"title": "b"}]})) == 2
    assert extract_findings([{"title": "a"}]) == [{"title": "a"}]


def test_prioritization_orders_and_flags() -> None:
    findings, _ = normalize_findings(
        [
            {"title": "Public internet exposure", "severity": "high", "status": "fail", "description": "public internet"},
            {"title": "Cosmetic note", "severity": "info", "status": "info"},
            {"title": "Rotate token", "severity": "medium", "status": "fail", "remediation": "Rotate the secret"},
        ]
    )
    prioritize(findings)
    assert findings[0].priority_score >= findings[-1].priority_score
    quick = [f for f in findings if f.quick_win]
    assert any(f.title == "Rotate token" for f in quick)


def test_scoring_explainable_and_capped() -> None:
    findings, _ = normalize_findings([{"title": f"f{i}", "severity": "critical", "status": "fail"} for i in range(10)])
    prioritize(findings)
    score = compute_score(findings)
    assert score.value == 0
    assert score.grade == "F"
    assert "Score starts at 100" in score.explanation


def test_aggregate_counts() -> None:
    findings, _ = normalize_findings(
        [
            {"title": "a", "severity": "critical", "status": "fail", "source": "Cloudline", "category": "Net"},
            {"title": "b", "severity": "low", "status": "warn", "source": "Podscope", "category": "Reliability"},
            {"title": "c", "severity": "info", "status": "pass", "source": "Podscope"},
        ]
    )
    prioritize(findings)
    agg = aggregate(findings)
    assert agg.total_findings == 3
    assert agg.actionable_findings == 2
    assert agg.severity_counts["critical"] == 1
    assert agg.module_counts["Podscope"] == 1


def test_templates_exist_and_filter() -> None:
    assert set(TEMPLATES.keys()) == {"executive", "technical", "remediation", "compliance", "board_summary"}
    assert get_template("executive").min_severity == "medium"
    assert severity_at_least("critical", "medium") is True
    assert severity_at_least("low", "high") is False


def test_md_to_html_tables_and_lists() -> None:
    md = "## Title\n\n| A | B |\n| --- | --- |\n| critical | x |\n\n- one\n- two"
    html = md_to_html(md)
    assert "<table>" in html
    assert "badge-critical" in html
    assert "<ul>" in html


def test_render_markdown_header() -> None:
    metadata = ReportMetadata(
        report_type="technical",
        title="Title",
        project="Proj",
        organization="Org",
        environment="prod",
        audience="technical",
        generated_at="now",
        version="0.2.0",
    )
    score = compute_score([])
    agg = aggregate([])
    md = render_markdown(metadata, score, agg, [])
    assert md.startswith("# Title")
    assert "Score 100/100" in md
    assert "Org" in md
