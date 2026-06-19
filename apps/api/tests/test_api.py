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
    assert len(response.json()) >= 3


def test_examples() -> None:
    response = client.get("/api/examples")
    assert response.status_code == 200
    assert len(response.json()) >= 4


def test_generate_report() -> None:
    payload = {
        "title": "Test Report",
        "project": "Unit Test",
        "environment": "test",
        "output_format": "both",
        "findings": [
            {
                "title": "Open admin port",
                "severity": "critical",
                "category": "Network Exposure",
                "source": "Cloudline",
                "target": "sg-admin",
                "description": "SSH is open to the internet.",
                "impact": "Management plane exposed.",
                "remediation": "Restrict access."
            }
        ]
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_findings"] == 1
    assert data["summary"]["severity_counts"]["critical"] == 1
    assert data["markdown"] is not None
    assert data["html"] is not None
