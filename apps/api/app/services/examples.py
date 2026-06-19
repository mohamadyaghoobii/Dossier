import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EXAMPLE_DIR = ROOT / "examples"

EXAMPLES = [
    ("mixed-results", "Mixed Results", "OpsDeck", "Multi-module bundle spanning seven analyzers."),
    ("findings-sample", "Findings Sample", "OpsDeck", "Representative findings across critical to low risk."),
    ("executive-summary-input", "Executive Input", "OpsDeck", "Production-focused input for an executive brief."),
    ("technical-report-input", "Technical Input", "OpsDeck", "Detailed input for a full technical report."),
    ("remediation-plan-input", "Remediation Input", "OpsDeck", "Backlog-style input for a remediation plan."),
    ("podscope-results", "Podscope", "Podscope", "Kubernetes manifest review findings."),
    ("dockyard-results", "Dockyard", "Dockyard", "Dockerfile and container build findings."),
    ("gatehouse-results", "Gatehouse", "Gatehouse", "CI/CD pipeline review findings."),
    ("stacklint-results", "Stacklint", "Stacklint", "Infrastructure-as-Code review findings."),
    ("tracepack-results", "Tracepack", "Tracepack", "Secrets, SBOM, and dependency findings."),
    ("signalbook-results", "Signalbook", "Signalbook", "Observability and incident readiness findings."),
    ("cloudline-results", "Cloudline", "Cloudline", "Cloud posture review findings."),
    ("empty-findings", "Empty Findings", "OpsDeck", "Clean project with no findings."),
]


def load_examples() -> list[dict[str, Any]]:
    results = []
    for item_id, name, module, description in EXAMPLES:
        path = EXAMPLE_DIR / f"{item_id}.json"
        if not path.exists():
            continue
        content = json.loads(path.read_text(encoding="utf-8"))
        results.append(
            {"id": item_id, "name": name, "module": module, "description": description, "content": content}
        )
    return results
