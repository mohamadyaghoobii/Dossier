import hashlib
from typing import Any

from app.schemas import NormalizedFinding, Severity, Status

SEVERITY_ALIASES: dict[str, Severity] = {
    "critical": "critical",
    "crit": "critical",
    "blocker": "critical",
    "severe": "critical",
    "high": "high",
    "error": "high",
    "danger": "high",
    "important": "high",
    "medium": "medium",
    "moderate": "medium",
    "warning": "medium",
    "warn": "medium",
    "low": "low",
    "minor": "low",
    "info": "info",
    "informational": "info",
    "note": "info",
    "unknown": "info",
    "none": "info",
}

STATUS_ALIASES: dict[str, Status] = {
    "fail": "fail",
    "failed": "fail",
    "failure": "fail",
    "open": "fail",
    "alert": "fail",
    "error": "fail",
    "warn": "warn",
    "warning": "warn",
    "review": "warn",
    "pass": "pass",
    "passed": "pass",
    "ok": "pass",
    "success": "pass",
    "resolved": "pass",
    "info": "info",
    "informational": "info",
    "accepted": "accepted",
    "risk_accepted": "accepted",
    "wontfix": "accepted",
    "mitigated": "mitigated",
    "compensating": "mitigated",
    "suppressed": "mitigated",
}

MODULE_ALIASES = {
    "podscope": "Podscope",
    "dockyard": "Dockyard",
    "gatehouse": "Gatehouse",
    "stacklint": "Stacklint",
    "tracepack": "Tracepack",
    "signalbook": "Signalbook",
    "cloudline": "Cloudline",
    "opsdeck": "OpsDeck",
}

TITLE_KEYS = ["title", "name", "rule", "rule_name", "check", "check_name", "message", "summary"]
SEVERITY_KEYS = ["severity", "level", "risk", "priority", "criticality"]
STATUS_KEYS = ["status", "result", "state", "outcome"]
CATEGORY_KEYS = ["category", "group", "class", "type", "kind", "domain"]
MODULE_KEYS = ["module", "source", "source_module", "scanner", "engine", "product"]
TOOL_KEYS = ["tool", "tool_name", "analyzer", "checker"]
ASSET_KEYS = ["asset", "resource", "target", "object", "component", "service"]
FILE_KEYS = ["file", "file_path", "path", "filepath", "location"]
LINE_KEYS = ["line", "line_number", "lineno", "start_line"]
DESCRIPTION_KEYS = ["description", "detail", "details", "body", "message", "explanation"]
IMPACT_KEYS = ["impact", "consequence", "risk_description", "business_impact"]
REMEDIATION_KEYS = ["remediation", "fix", "recommendation", "solution", "advice", "mitigation"]
EVIDENCE_KEYS = ["evidence", "proof", "snippet", "context", "raw"]
REFERENCE_KEYS = ["references", "refs", "links", "urls", "see_also"]
CONFIDENCE_KEYS = ["confidence", "certainty"]
CREATED_KEYS = ["created_at", "created", "timestamp", "detected_at", "first_seen", "date"]
PROJECT_KEYS = ["project", "project_name", "repo", "repository", "application", "app"]


def _first(raw: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
        lowered = {str(k).lower(): v for k, v in raw.items()}
        if key in lowered and lowered[key] not in (None, ""):
            return lowered[key]
    return None


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value).strip()


def normalize_severity(value: Any) -> Severity:
    text = _as_text(value).lower()
    if text in SEVERITY_ALIASES:
        return SEVERITY_ALIASES[text]
    if text.isdigit():
        number = int(text)
        if number >= 9:
            return "critical"
        if number >= 7:
            return "high"
        if number >= 4:
            return "medium"
        if number >= 1:
            return "low"
    return "info"


def normalize_status(value: Any, severity: Severity) -> Status:
    text = _as_text(value).lower()
    if text in STATUS_ALIASES:
        return STATUS_ALIASES[text]
    if severity == "info":
        return "info"
    return "fail"


def normalize_module(value: Any) -> str:
    text = _as_text(value)
    return MODULE_ALIASES.get(text.lower(), text or "unknown")


def _references(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value)]


def _confidence(value: Any) -> float:
    if value is None:
        return 1.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        text = _as_text(value).lower()
        return {"high": 0.95, "medium": 0.7, "low": 0.4}.get(text, 1.0)
    if number > 1:
        number = number / 100 if number <= 100 else 1.0
    return max(0.0, min(1.0, number))


def _line(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _make_id(raw: dict[str, Any], title: str, module: str, asset: str) -> str:
    existing = _first(raw, ["id", "finding_id", "uid", "ref_id"])
    if existing:
        return str(existing)
    digest = hashlib.sha1(f"{module}|{title}|{asset}".encode("utf-8")).hexdigest()
    return f"DSR-{digest[:8].upper()}"


def normalize_finding(raw: dict[str, Any], default_project: str | None = None) -> NormalizedFinding | None:
    if not isinstance(raw, dict):
        return None
    title = _as_text(_first(raw, TITLE_KEYS))
    if not title:
        return None
    severity = normalize_severity(_first(raw, SEVERITY_KEYS))
    status = normalize_status(_first(raw, STATUS_KEYS), severity)
    module = normalize_module(_first(raw, MODULE_KEYS))
    tool = _as_text(_first(raw, TOOL_KEYS)) or (module if module != "unknown" else "manual")
    asset = _as_text(_first(raw, ASSET_KEYS)) or "unspecified"
    project = _as_text(_first(raw, PROJECT_KEYS)) or default_project
    metadata = {k: v for k, v in raw.items() if isinstance(k, str) and k.startswith("meta_")}
    extra_metadata = raw.get("metadata")
    if isinstance(extra_metadata, dict):
        metadata = {**extra_metadata, **metadata}

    return NormalizedFinding(
        id=_make_id(raw, title, module, asset),
        title=title,
        severity=severity,
        status=status,
        category=_as_text(_first(raw, CATEGORY_KEYS)) or "General",
        module=module,
        tool=tool,
        project=project or None,
        asset=asset,
        file_path=_as_text(_first(raw, FILE_KEYS)) or None,
        line=_line(_first(raw, LINE_KEYS)),
        description=_as_text(_first(raw, DESCRIPTION_KEYS)),
        impact=_as_text(_first(raw, IMPACT_KEYS)),
        remediation=_as_text(_first(raw, REMEDIATION_KEYS)),
        evidence=_as_text(_first(raw, EVIDENCE_KEYS)) or None,
        references=_references(_first(raw, REFERENCE_KEYS)),
        confidence=_confidence(_first(raw, CONFIDENCE_KEYS)),
        created_at=_as_text(_first(raw, CREATED_KEYS)) or None,
        tags=[str(tag) for tag in raw.get("tags", []) if str(tag)] if isinstance(raw.get("tags"), list) else [],
        metadata=metadata,
    )


def normalize_findings(raw_findings: list[dict[str, Any]], default_project: str | None = None) -> tuple[list[NormalizedFinding], int]:
    normalized: list[NormalizedFinding] = []
    dropped = 0
    for raw in raw_findings:
        finding = normalize_finding(raw, default_project)
        if finding is None:
            dropped += 1
            continue
        normalized.append(finding)
    return normalized, dropped


def extract_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("findings", "results", "issues", "items", "checks"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []
