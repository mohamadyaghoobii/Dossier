from dataclasses import dataclass

from app.schemas import (
    Aggregation,
    NormalizedFinding,
    ReportOptions,
    ReportRequest,
    Score,
    Section,
    SEVERITY_ORDER,
)
from app.services.templates import Template, severity_at_least

SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "overview": "Overview",
    "score_card": "Score Card",
    "risk_posture": "Risk Posture",
    "risk_snapshot": "Risk Snapshot",
    "top_risks": "Key Risks",
    "top_five_issues": "Top 5 Issues",
    "top_affected_areas": "Top Affected Areas",
    "remediation_priorities": "Remediation Priorities",
    "severity_table": "Severity Breakdown",
    "module_table": "Module Breakdown",
    "category_table": "Category Breakdown",
    "control_summary": "Control Summary",
    "control_groups": "Control Groups",
    "evidence_index": "Evidence Index",
    "findings": "Findings",
    "quick_wins": "Quick Wins",
    "remediation_plan": "Remediation Plan",
    "recommended_order": "Recommended Order",
    "next_actions": "Recommended Next Actions",
    "appendix": "Appendix",
}


@dataclass
class ReportContext:
    request: ReportRequest
    options: ReportOptions
    template: Template
    findings: list[NormalizedFinding]
    score: Score
    aggregation: Aggregation

    @property
    def visible(self) -> list[NormalizedFinding]:
        result = []
        for finding in self.findings:
            if not self.options.include_passed and finding.status in ("pass", "info"):
                continue
            if not severity_at_least(finding.severity, self.template.min_severity):
                continue
            result.append(finding)
        return result


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No data available._"
    line = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(cell or "-" for cell in row) + " |" for row in rows)
    return f"{line}\n{divider}\n{body}"


def _severity_emoji(severity: str) -> str:
    return {
        "critical": "🟥",
        "high": "🟧",
        "medium": "🟨",
        "low": "🟦",
        "info": "⬜",
    }.get(severity, "⬜")


def s_executive_summary(ctx: ReportContext) -> str:
    agg = ctx.aggregation
    if agg.actionable_findings == 0:
        return (
            f"{ctx.request.project} shows no actionable findings in this dataset. "
            f"The current report score is **{ctx.score.value}/100 (grade {ctx.score.grade}, {ctx.score.posture})**. "
            "Maintain existing controls and re-run the report after the next significant change."
        )
    lead = (
        f"{ctx.request.project} carries a report score of **{ctx.score.value}/100 "
        f"(grade {ctx.score.grade})** with an overall risk posture of **{ctx.score.posture}**. "
        f"The review surfaced **{agg.actionable_findings} actionable finding(s)** across "
        f"**{len(agg.module_counts)} module(s)** and **{agg.affected_assets} asset(s)**, "
        f"with the highest observed severity being **{agg.highest_severity}**."
    )
    risks = "\n".join(f"- {item.title} ({item.severity}, {item.module})" for item in agg.top_risks[:3])
    return f"{lead}\n\nLeadership should focus on the following first:\n\n{risks}"


def s_overview(ctx: ReportContext) -> str:
    agg = ctx.aggregation
    return (
        f"This {ctx.template.name.lower()} covers **{ctx.request.project}** in the "
        f"**{ctx.request.environment}** environment for **{ctx.request.organization}**. "
        f"It consolidates {agg.total_findings} finding(s) ({agg.actionable_findings} actionable) "
        f"into a single view with a score of **{ctx.score.value}/100 ({ctx.score.grade})**."
    )


def s_score_card(ctx: ReportContext) -> str:
    rows = [[item.severity, str(item.count), f"-{item.deduction:.0f}"] for item in ctx.score.breakdown]
    table = _table(["Severity", "Count", "Score impact"], rows)
    return (
        f"**Score:** {ctx.score.value}/100  \n"
        f"**Grade:** {ctx.score.grade}  \n"
        f"**Posture:** {ctx.score.posture}\n\n"
        f"{table}\n\n"
        f"_{ctx.score.explanation}_"
    )


def s_risk_posture(ctx: ReportContext) -> str:
    agg = ctx.aggregation
    counts = " · ".join(
        f"{_severity_emoji(s)} {s.title()} {agg.severity_counts.get(s, 0)}" for s in SEVERITY_ORDER
    )
    return (
        f"Overall posture is **{ctx.score.posture}** at **{ctx.score.value}/100**.\n\n"
        f"Severity distribution: {counts}."
    )


def s_risk_snapshot(ctx: ReportContext) -> str:
    agg = ctx.aggregation
    crit_high = agg.severity_counts.get("critical", 0) + agg.severity_counts.get("high", 0)
    return (
        f"**{ctx.score.value}/100** ({ctx.score.grade}) — {ctx.score.posture}.\n\n"
        f"- Critical/high issues: **{crit_high}**\n"
        f"- Affected assets: **{agg.affected_assets}**\n"
        f"- Risk trend: _baseline (no historical data yet)_"
    )


def _risk_rows(items) -> list[list[str]]:
    return [
        [str(i), item.title, item.severity, item.module, item.asset]
        for i, item in enumerate(items, start=1)
    ]


def s_top_risks(ctx: ReportContext) -> str:
    if not ctx.aggregation.top_risks:
        return "_No prioritized risks for this dataset._"
    return _table(
        ["#", "Risk", "Severity", "Module", "Asset"],
        _risk_rows(ctx.aggregation.top_risks),
    )


def s_top_five_issues(ctx: ReportContext) -> str:
    items = ctx.aggregation.top_risks[:5]
    if not items:
        return "_No issues meet the board reporting threshold._"
    return "\n".join(f"{i}. **{item.title}** — {item.severity} ({item.module})" for i, item in enumerate(items, start=1))


def s_top_affected_areas(ctx: ReportContext) -> str:
    modules = sorted(ctx.aggregation.module_counts.items(), key=lambda kv: kv[1], reverse=True)
    if not modules:
        return "_No affected areas reported._"
    rows = [[module, str(count)] for module, count in modules]
    return _table(["Area / Module", "Findings"], rows)


def s_remediation_priorities(ctx: ReportContext) -> str:
    steps = ctx.aggregation.recommended_next_steps
    return "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))


def s_severity_table(ctx: ReportContext) -> str:
    agg = ctx.aggregation
    rows = [[_severity_emoji(s) + " " + s.title(), str(agg.severity_counts.get(s, 0))] for s in SEVERITY_ORDER]
    return _table(["Severity", "Count"], rows)


def s_module_table(ctx: ReportContext) -> str:
    rows = [[m, str(c)] for m, c in sorted(ctx.aggregation.module_counts.items(), key=lambda kv: kv[1], reverse=True)]
    return _table(["Module", "Findings"], rows)


def s_category_table(ctx: ReportContext) -> str:
    rows = [[c, str(n)] for c, n in sorted(ctx.aggregation.category_counts.items(), key=lambda kv: kv[1], reverse=True)]
    return _table(["Category", "Findings"], rows)


def _group_key(finding: NormalizedFinding, group_by: str) -> str:
    if group_by == "module":
        return finding.module
    if group_by == "category":
        return finding.category
    if group_by == "asset":
        return finding.asset
    return finding.severity


def _finding_block(finding: NormalizedFinding, ctx: ReportContext) -> str:
    lines = [
        f"#### {_severity_emoji(finding.severity)} {finding.title}",
        "",
        f"- **ID:** {finding.id}",
        f"- **Severity:** {finding.severity}  |  **Status:** {finding.status}  |  **Confidence:** {finding.confidence:.0%}",
        f"- **Module:** {finding.module}  |  **Tool:** {finding.tool}",
        f"- **Category:** {finding.category}",
        f"- **Asset:** {finding.asset}",
    ]
    if finding.file_path:
        location = finding.file_path + (f":{finding.line}" if finding.line else "")
        lines.append(f"- **Location:** {location}")
    if finding.description:
        lines.append(f"\n{finding.description}")
    if finding.impact:
        lines.append(f"\n**Impact:** {finding.impact}")
    if ctx.options.include_remediation and finding.remediation:
        lines.append(f"\n**Remediation:** {finding.remediation}")
    if ctx.options.include_evidence and finding.evidence:
        lines.append(f"\n**Evidence:**\n\n```\n{finding.evidence}\n```")
    if ctx.options.include_references and finding.references:
        refs = "\n".join(f"- {ref}" for ref in finding.references)
        lines.append(f"\n**References:**\n{refs}")
    return "\n".join(lines)


def s_findings(ctx: ReportContext) -> str:
    findings = ctx.visible
    if not findings:
        return "_No findings match the selected filters._"
    group_by = ctx.options.group_by
    groups: dict[str, list[NormalizedFinding]] = {}
    for finding in findings:
        groups.setdefault(_group_key(finding, group_by), []).append(finding)

    if group_by == "severity":
        ordered_keys = [s for s in SEVERITY_ORDER if s in groups]
    else:
        ordered_keys = sorted(groups, key=lambda k: len(groups[k]), reverse=True)

    blocks = []
    for key in ordered_keys:
        label = key.title() if group_by == "severity" else key
        blocks.append(f"### {label} ({len(groups[key])})")
        for finding in groups[key]:
            blocks.append(_finding_block(finding, ctx))
    return "\n\n".join(blocks)


def s_quick_wins(ctx: ReportContext) -> str:
    wins = [f for f in ctx.findings if f.quick_win]
    if not wins:
        return "_No quick wins detected. All remediation requires meaningful effort._"
    rows = [[f.title, f.severity, f.module, f.remediation] for f in wins[:10]]
    return _table(["Quick win", "Severity", "Module", "Fix"], rows)


def _effort(finding: NormalizedFinding) -> str:
    if finding.quick_win:
        return "S"
    if finding.severity in ("critical", "high"):
        return "M"
    return "L"


def s_remediation_plan(ctx: ReportContext) -> str:
    findings = [f for f in ctx.findings if f.status in ("fail", "warn")]
    if not findings:
        return "_No remediation actions required from this dataset._"
    buckets = {
        "Immediate (this week)": [f for f in findings if f.severity in ("critical", "high")],
        "Next sprint": [f for f in findings if f.severity == "medium"],
        "Backlog": [f for f in findings if f.severity in ("low", "info")],
    }
    blocks = []
    for name, items in buckets.items():
        blocks.append(f"### {name}")
        if not items:
            blocks.append("_No items._")
            continue
        rows = [
            [
                f.title,
                f.severity,
                f.module,
                "_unassigned_",
                _effort(f),
                f.remediation or "Define an owner and remediation step.",
            ]
            for f in items[:12]
        ]
        blocks.append(_table(["Task", "Severity", "Module", "Owner", "Effort", "Action"], rows))
    return "\n\n".join(blocks)


def s_recommended_order(ctx: ReportContext) -> str:
    ranked = sorted(ctx.findings, key=lambda f: f.priority_score, reverse=True)[:10]
    if not ranked:
        return "_No prioritized order available._"
    return "\n".join(
        f"{i}. **{f.title}** ({f.severity}, priority {f.priority_score:.0f}) — {f.priority_reasons[0] if f.priority_reasons else ''}"
        for i, f in enumerate(ranked, start=1)
    )


def s_next_actions(ctx: ReportContext) -> str:
    return "\n".join(f"{i}. {step}" for i, step in enumerate(ctx.aggregation.recommended_next_steps, start=1))


def s_control_summary(ctx: ReportContext) -> str:
    status = ctx.aggregation.status_counts
    rows = [
        ["Pass", str(status.get("pass", 0))],
        ["Fail", str(status.get("fail", 0))],
        ["Warn", str(status.get("warn", 0))],
        ["Accepted", str(status.get("accepted", 0))],
        ["Mitigated", str(status.get("mitigated", 0))],
        ["Info", str(status.get("info", 0))],
    ]
    return _table(["Control state", "Count"], rows)


def s_control_groups(ctx: ReportContext) -> str:
    groups: dict[str, list[NormalizedFinding]] = {}
    for finding in ctx.findings:
        groups.setdefault(finding.category, []).append(finding)
    if not groups:
        return "_No controls evaluated._"
    blocks = []
    for category in sorted(groups):
        items = groups[category]
        fails = sum(1 for f in items if f.status in ("fail", "warn"))
        verdict = "FAIL" if fails else "PASS"
        blocks.append(f"### {category} — {verdict}")
        rows = [[f.title, f.status, f.asset] for f in items]
        blocks.append(_table(["Control", "Status", "Asset"], rows))
    return "\n\n".join(blocks)


def s_evidence_index(ctx: ReportContext) -> str:
    if not ctx.options.include_evidence:
        return "_Evidence inclusion disabled for this report._"
    rows = [[f.id, f.title, f.asset] for f in ctx.findings if f.evidence]
    if not rows:
        return "_No evidence attached to findings._"
    return _table(["Finding ID", "Title", "Asset"], rows)


def s_appendix(ctx: ReportContext) -> str:
    if not ctx.options.include_appendix:
        return "_Appendix disabled._"
    agg = ctx.aggregation
    return (
        "**Input summary**\n\n"
        f"- Findings received: {agg.total_findings}\n"
        f"- Actionable findings: {agg.actionable_findings}\n"
        f"- Modules: {', '.join(sorted(agg.module_counts)) or 'none'}\n"
        f"- Categories: {', '.join(sorted(agg.category_counts)) or 'none'}\n"
        f"- Affected assets: {agg.affected_assets}\n\n"
        "**Severity model**\n\n"
        "Scores start at 100 and decrease based on severity, confidence, and asset spread. "
        "Grades: A 90-100, B 80-89, C 70-79, D 55-69, F below 55."
    )


BUILDERS = {
    "executive_summary": s_executive_summary,
    "overview": s_overview,
    "score_card": s_score_card,
    "risk_posture": s_risk_posture,
    "risk_snapshot": s_risk_snapshot,
    "top_risks": s_top_risks,
    "top_five_issues": s_top_five_issues,
    "top_affected_areas": s_top_affected_areas,
    "remediation_priorities": s_remediation_priorities,
    "severity_table": s_severity_table,
    "module_table": s_module_table,
    "category_table": s_category_table,
    "findings": s_findings,
    "quick_wins": s_quick_wins,
    "remediation_plan": s_remediation_plan,
    "recommended_order": s_recommended_order,
    "next_actions": s_next_actions,
    "control_summary": s_control_summary,
    "control_groups": s_control_groups,
    "evidence_index": s_evidence_index,
    "appendix": s_appendix,
}


def build_sections(ctx: ReportContext) -> list[Section]:
    sections: list[Section] = []
    for section_id in ctx.template.sections:
        builder = BUILDERS.get(section_id)
        if not builder:
            continue
        body = builder(ctx)
        sections.append(
            Section(id=section_id, title=SECTION_TITLES.get(section_id, section_id.title()), body=body)
        )
    if ctx.request.notes:
        sections.append(Section(id="analyst_notes", title="Analyst Notes", body=ctx.request.notes))
    return sections
