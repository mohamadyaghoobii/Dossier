from collections import Counter

from app.schemas import (
    Aggregation,
    NormalizedFinding,
    RiskItem,
    Score,
    ScoreBreakdown,
    SEVERITY_ORDER,
)

SEVERITY_POINTS = {"critical": 22.0, "high": 13.0, "medium": 6.0, "low": 2.0, "info": 0.0}
ASSET_MULTIPLIER = 0.6

ACTIONABLE_STATUSES = {"fail", "warn"}


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 55:
        return "D"
    return "F"


def _posture(score: int) -> str:
    if score >= 90:
        return "Strong"
    if score >= 75:
        return "Stable"
    if score >= 60:
        return "Elevated risk"
    if score >= 40:
        return "High risk"
    return "Critical risk"


def _actionable(findings: list[NormalizedFinding]) -> list[NormalizedFinding]:
    return [f for f in findings if f.status in ACTIONABLE_STATUSES]


def compute_score(findings: list[NormalizedFinding]) -> Score:
    actionable = _actionable(findings)
    severity_counts = Counter(f.severity for f in actionable)
    breakdown: list[ScoreBreakdown] = []
    score = 100.0
    asset_spread = len({f.asset for f in actionable})

    for severity in SEVERITY_ORDER:
        count = severity_counts.get(severity, 0)
        if not count:
            continue
        base = SEVERITY_POINTS[severity] * count
        confidence_factor = sum(
            max(0.4, f.confidence) for f in actionable if f.severity == severity
        ) / count
        deduction = base * confidence_factor
        score -= deduction
        breakdown.append(
            ScoreBreakdown(severity=severity, count=count, deduction=round(deduction, 1))
        )

    spread_penalty = min(12.0, max(0, asset_spread - 3) * ASSET_MULTIPLIER)
    score -= spread_penalty
    final = max(0, min(100, round(score)))

    if not actionable:
        explanation = "No actionable findings were submitted, so the report starts and stays at 100."
    else:
        parts = [
            f"{item.count} {item.severity} finding(s) reduced the score by {item.deduction:.0f} points"
            for item in breakdown
        ]
        explanation = (
            "Score starts at 100. "
            + "; ".join(parts)
            + f". Deductions are weighted by confidence, and {asset_spread} affected asset(s) "
            f"added a spread penalty of {spread_penalty:.0f}. Minimum score is capped at 0."
        )

    return Score(
        value=final,
        grade=_grade(final),
        posture=_posture(final),
        explanation=explanation,
        breakdown=breakdown,
    )


def _risk_item(finding: NormalizedFinding) -> RiskItem:
    return RiskItem(
        title=finding.title,
        severity=finding.severity,
        module=finding.module,
        asset=finding.asset,
        priority_score=finding.priority_score,
        reason="; ".join(finding.priority_reasons),
    )


def _next_steps(findings: list[NormalizedFinding], severity_counts: dict[str, int]) -> list[str]:
    steps: list[str] = []
    critical_high = severity_counts.get("critical", 0) + severity_counts.get("high", 0)
    if critical_high:
        steps.append(
            f"Remediate {critical_high} critical/high finding(s) before the next production change."
        )
    quick_wins = [f for f in findings if f.quick_win]
    if quick_wins:
        steps.append(
            f"Close {len(quick_wins)} quick win(s) with low-effort configuration fixes."
        )
    exposed = [f for f in findings if "internet or public exposure" in f.priority_reasons]
    if exposed:
        steps.append("Review internet-exposed assets and restrict public access.")
    secrets = [f for f in findings if "secret or credential exposure" in f.priority_reasons]
    if secrets:
        steps.append("Rotate exposed secrets and move them into a managed secret store.")
    if not steps:
        steps.append("Maintain current controls and re-run the report after the next change.")
    return steps[:5]


def aggregate(findings: list[NormalizedFinding]) -> Aggregation:
    actionable = _actionable(findings)
    severity_counts = {s: 0 for s in SEVERITY_ORDER}
    severity_counts.update(Counter(f.severity for f in actionable))
    status_counts = dict(Counter(f.status for f in findings))
    module_counts = dict(Counter(f.module for f in actionable))
    category_counts = dict(Counter(f.category for f in actionable))
    highest = next((s for s in SEVERITY_ORDER if severity_counts.get(s, 0)), "none")

    ranked = sorted(actionable, key=lambda f: f.priority_score, reverse=True)
    top_risks = [_risk_item(f) for f in ranked[:5]]
    quick_wins = [_risk_item(f) for f in ranked if f.quick_win][:5]

    return Aggregation(
        total_findings=len(findings),
        actionable_findings=len(actionable),
        severity_counts=severity_counts,
        status_counts=status_counts,
        module_counts=module_counts,
        category_counts=category_counts,
        affected_assets=len({f.asset for f in actionable}),
        highest_severity=highest,
        top_risks=top_risks,
        quick_wins=quick_wins,
        recommended_next_steps=_next_steps(findings, severity_counts),
    )
