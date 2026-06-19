import re
from typing import Protocol

from app.schemas import AIRequest, AIResponse, NormalizedFinding

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
]


def redact(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _safe_finding(finding: NormalizedFinding) -> str:
    return redact(
        f"- [{finding.severity}] {finding.title} ({finding.module} / {finding.asset}): "
        f"{finding.impact or finding.description}"
    )


class AIProvider(Protocol):
    name: str
    model: str | None

    def summarize(self, request: AIRequest, findings: list[NormalizedFinding]) -> AIResponse: ...

    def remediation_plan(self, request: AIRequest, findings: list[NormalizedFinding]) -> AIResponse: ...


class DeterministicProvider:
    name = "none"
    model = None

    def _note(self) -> str:
        return (
            "Generated deterministically without an external AI provider. "
            "Set AI_PROVIDER to enable model-assisted rewriting."
        )

    def summarize(self, request: AIRequest, findings: list[NormalizedFinding]) -> AIResponse:
        actionable = [f for f in findings if f.status in ("fail", "warn")]
        top = sorted(actionable, key=lambda f: f.priority_score, reverse=True)[:5]
        if not actionable:
            content = (
                f"{request.project} currently has no actionable risks in this dataset. "
                "Security posture is stable; continue routine monitoring."
            )
        else:
            lines = [
                f"{request.organization} reviewed {request.project} and identified "
                f"{len(actionable)} issue(s) that warrant attention.",
                "",
                "Highest priority items:",
                *[_safe_finding(f) for f in top],
                "",
                "Recommended message to leadership: prioritize the critical and high items, "
                "assign clear owners, and confirm fixes before the next production change.",
            ]
            content = "\n".join(lines)
        return AIResponse(provider=self.name, model=self.model, generated=False, content=content, note=self._note())

    def remediation_plan(self, request: AIRequest, findings: list[NormalizedFinding]) -> AIResponse:
        actionable = sorted(
            [f for f in findings if f.status in ("fail", "warn")],
            key=lambda f: f.priority_score,
            reverse=True,
        )
        if not actionable:
            content = "No remediation actions are required from the submitted findings."
            return AIResponse(provider=self.name, model=self.model, generated=False, content=content, note=self._note())
        lines = [f"Remediation roadmap for {request.project}:", ""]
        for index, finding in enumerate(actionable[:12], start=1):
            action = redact(finding.remediation or "Investigate and define a remediation step.")
            effort = "quick win" if finding.quick_win else "standard effort"
            lines.append(f"{index}. [{finding.severity}] {finding.title} — {action} ({effort})")
        return AIResponse(provider=self.name, model=self.model, generated=False, content="\n".join(lines), note=self._note())


def get_provider(provider_name: str) -> AIProvider:
    return DeterministicProvider()
