from collections import Counter

from app.schemas import NormalizedFinding

SEVERITY_WEIGHT = {"critical": 100.0, "high": 70.0, "medium": 40.0, "low": 15.0, "info": 5.0}

EXPOSURE_TERMS = ("public", "internet", "exposed", "0.0.0.0", "external", "unauthenticated", "anonymous")
SECRET_TERMS = ("secret", "token", "credential", "password", "api key", "api-key", "private key")
IAM_TERMS = ("iam", "admin", "privilege", "root", "wildcard", "permission", "policy", "rbac")
PRODUCTION_TERMS = ("prod", "production")
QUICK_WIN_TERMS = (
    "enable",
    "set ",
    "add ",
    "disable",
    "restrict",
    "rotate",
    "update",
    "remove",
    "configure",
    "define",
)


def _haystack(finding: NormalizedFinding) -> str:
    return " ".join(
        part.lower()
        for part in (
            finding.title,
            finding.category,
            finding.asset,
            finding.description,
            finding.impact,
            " ".join(finding.tags),
            str(finding.metadata),
        )
        if part
    )


def _is_quick_win(finding: NormalizedFinding) -> bool:
    if finding.severity in ("critical",):
        return False
    text = finding.remediation.lower().strip()
    if not text:
        return False
    if len(text) > 160:
        return False
    return text.startswith(QUICK_WIN_TERMS) or any(term in text for term in QUICK_WIN_TERMS)


def prioritize(findings: list[NormalizedFinding]) -> list[NormalizedFinding]:
    asset_counts = Counter(finding.title for finding in findings)
    for finding in findings:
        score = SEVERITY_WEIGHT.get(finding.severity, 5.0)
        reasons: list[str] = [f"{finding.severity} severity"]
        haystack = _haystack(finding)

        if any(term in haystack for term in EXPOSURE_TERMS):
            score += 35.0
            reasons.append("internet or public exposure")
        if any(term in haystack for term in SECRET_TERMS):
            score += 30.0
            reasons.append("secret or credential exposure")
        if any(term in haystack for term in IAM_TERMS):
            score += 20.0
            reasons.append("identity or privilege risk")
        if any(term in haystack for term in PRODUCTION_TERMS):
            score += 18.0
            reasons.append("production environment")

        repeats = asset_counts[finding.title]
        if repeats > 1:
            score += min(25.0, repeats * 5.0)
            reasons.append(f"repeated across {repeats} assets")

        score *= max(0.4, finding.confidence)
        if finding.status in ("accepted", "mitigated", "pass"):
            score *= 0.3
            reasons.append(f"status {finding.status}")

        finding.priority_score = round(score, 1)
        finding.priority_reasons = reasons
        finding.quick_win = _is_quick_win(finding)
    findings.sort(key=lambda item: item.priority_score, reverse=True)
    return findings
