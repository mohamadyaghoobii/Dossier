import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EXAMPLE_DIR = ROOT / "examples"

EXAMPLES = {
    "findings-sample": "Mixed analyzer findings with critical, high, medium, and low risk.",
    "mixed-results": "Compact OpsDeck-style result bundle from multiple modules.",
    "executive-summary-input": "Small production-focused executive report input.",
    "empty-findings": "Clean project sample with no findings."
}


def load_examples() -> list[dict[str, Any]]:
    results = []
    for item_id, description in EXAMPLES.items():
        path = EXAMPLE_DIR / f"{item_id}.json"
        content = json.loads(path.read_text(encoding="utf-8"))
        results.append({"id": item_id, "name": item_id.replace("-", " ").title(), "description": description, "content": content})
    return results


TEMPLATES = [
    {
        "id": "executive-risk-brief",
        "name": "Executive Risk Brief",
        "audience": "executive",
        "description": "Short leadership-focused summary with score, top risks, and business impact.",
        "sections": ["Executive Summary", "Risk Snapshot", "Top Priorities", "Next Steps"]
    },
    {
        "id": "technical-remediation-plan",
        "name": "Technical Remediation Plan",
        "audience": "technical",
        "description": "Detailed remediation report grouped by severity, category, source, and target.",
        "sections": ["Technical Summary", "Finding Details", "Remediation Roadmap", "Appendix"]
    },
    {
        "id": "stakeholder-pack",
        "name": "Stakeholder Pack",
        "audience": "mixed",
        "description": "Balanced report for engineering, security, and management review.",
        "sections": ["Executive Summary", "Technical Details", "Roadmap", "Ownership"]
    }
]
