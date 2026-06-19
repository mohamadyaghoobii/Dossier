from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_templates() -> None:
    response = client.get("/api/templates")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {"executive", "technical", "remediation", "compliance", "board_summary"}.issubset(ids)


def test_examples() -> None:
    response = client.get("/api/examples")
    assert response.status_code == 200
    assert len(response.json()) >= 8


def test_normalize_endpoint() -> None:
    payload = {
        "findings": [
            {"rule": "Open port", "level": "error", "module": "cloudline", "resource": "sg-1"},
            {"not_a_title": True},
        ]
    }
    response = client.post("/api/normalize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["dropped"] == 1
    assert data["findings"][0]["module"] == "Cloudline"
    assert data["findings"][0]["severity"] == "high"


def test_generate_report() -> None:
    payload = {
        "report_type": "technical",
        "project": "Unit Test",
        "output_format": "both",
        "findings": [
            {
                "title": "Open admin port",
                "severity": "critical",
                "source": "Cloudline",
                "asset": "sg-admin",
                "status": "fail",
                "remediation": "Restrict access.",
            }
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["aggregation"]["severity_counts"]["critical"] == 1
    assert data["score"]["value"] < 100
    assert data["markdown"]
    assert "<table" in data["html"]


def test_generate_each_report_type() -> None:
    findings = [
        {"title": "Public DB", "severity": "critical", "source": "Cloudline", "status": "fail"},
        {"title": "Broad token", "severity": "high", "source": "Gatehouse", "status": "fail"},
    ]
    for report_type in ["executive", "technical", "remediation", "compliance", "board_summary"]:
        response = client.post(
            "/api/generate",
            json={"report_type": report_type, "findings": findings, "output_format": "markdown"},
        )
        assert response.status_code == 200, report_type
        assert response.json()["sections"]


def test_ai_summarize_deterministic() -> None:
    response = client.post(
        "/api/ai/summarize",
        json={"project": "Demo", "findings": [{"title": "Public DB", "severity": "critical", "status": "fail"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["generated"] is False
    assert "Demo" in data["content"]


def test_empty_findings_score_full() -> None:
    response = client.post("/api/generate", json={"report_type": "executive", "findings": []})
    assert response.status_code == 200
    assert response.json()["score"]["value"] == 100
