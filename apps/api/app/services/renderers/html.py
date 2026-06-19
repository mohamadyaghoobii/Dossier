import re
from html import escape

from app.schemas import Aggregation, ReportMetadata, Score, Section, SEVERITY_ORDER

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+?)`")
_EMPH = re.compile(r"(?<![\*_])_([^_]+?)_(?![\*_])")


def _inline(text: str) -> str:
    out = escape(text)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _CODE.sub(r"<code>\1</code>", out)
    out = _EMPH.sub(r"<em>\1</em>", out)
    return out


def _is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _severity_class(value: str) -> str:
    token = value.strip().lower().lstrip("🟥🟧🟨🟦⬜ ").strip()
    for sev in SEVERITY_ORDER:
        if token.startswith(sev):
            return sev
    return ""


def _cell_html(cell: str) -> str:
    sev = _severity_class(cell)
    inner = _inline(cell)
    if sev:
        return f'<td><span class="badge badge-{sev}">{escape(cell.strip())}</span></td>'
    return f"<td>{inner}</td>"


def md_to_html(text: str) -> str:
    lines = text.split("\n")
    html: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            i += 1
            code: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            html.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
            continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            html.append("<hr />")
            i += 1
            continue

        if _is_table_row(line) and i + 1 < n and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()):
            headers = _split_row(line)
            i += 2
            rows = []
            while i < n and _is_table_row(lines[i]):
                rows.append(_split_row(lines[i]))
                i += 1
            head = "".join(f"<th>{_inline(h)}</th>" for h in headers)
            body = "".join("<tr>" + "".join(_cell_html(c) for c in row) + "</tr>" for row in rows)
            html.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(6, len(heading.group(1)) + 1)
            html.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("> "):
            quote = []
            while i < n and lines[i].strip().startswith("> "):
                quote.append(lines[i].strip()[2:])
                i += 1
            html.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
            continue

        if stripped.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            html.append(f"<ul>{''.join(items)}</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(f"<li>{_inline(re.sub(r'^\d+\.\s+', '', lines[i].strip()))}</li>")
                i += 1
            html.append(f"<ol>{''.join(items)}</ol>")
            continue

        html.append(f"<p>{_inline(stripped)}</p>")
        i += 1
    return "\n".join(html)


def _summary_cards(score: Score, aggregation: Aggregation) -> str:
    cards = [
        ("Score", f"{score.value}", f"Grade {score.grade}"),
        ("Posture", score.posture, "Overall risk"),
        ("Findings", str(aggregation.actionable_findings), f"{aggregation.total_findings} total"),
        ("Assets", str(aggregation.affected_assets), "Affected resources"),
    ]
    blocks = "".join(
        f'<div class="card"><span class="card-label">{escape(label)}</span>'
        f'<span class="card-value">{escape(value)}</span>'
        f'<span class="card-note">{escape(note)}</span></div>'
        for label, value, note in cards
    )
    return f'<div class="cards">{blocks}</div>'


def _severity_strip(aggregation: Aggregation) -> str:
    chips = "".join(
        f'<span class="badge badge-{sev}">{sev.title()} {aggregation.severity_counts.get(sev, 0)}</span>'
        for sev in SEVERITY_ORDER
    )
    return f'<div class="severity-strip">{chips}</div>'


def render_html(
    metadata: ReportMetadata,
    score: Score,
    aggregation: Aggregation,
    sections: list[Section],
) -> str:
    section_html = "\n".join(
        f'<section class="report-section"><h2>{escape(s.title)}</h2>{md_to_html(s.body)}</section>'
        for s in sections
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(metadata.title)}</title>
<style>
:root{{--bg:#0b1220;--panel:#111a2e;--line:#243149;--text:#e6edf7;--muted:#9fb0c9;--accent:#5ec8ff;}}
*{{box-sizing:border-box;}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:'Inter',-apple-system,'Segoe UI',Roboto,Arial,sans-serif;line-height:1.65;}}
main{{max-width:1000px;margin:0 auto;padding:48px 28px 80px;}}
header.report-header{{border:1px solid var(--line);background:linear-gradient(135deg,#13203a,#0d1729);border-radius:20px;padding:32px;margin-bottom:24px;}}
.eyebrow{{text-transform:uppercase;letter-spacing:.16em;font-size:12px;color:var(--accent);font-weight:700;margin:0 0 10px;}}
header.report-header h1{{margin:0 0 10px;font-size:30px;letter-spacing:-.02em;}}
.meta{{color:var(--muted);font-size:14px;}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0;}}
.card{{border:1px solid var(--line);background:var(--panel);border-radius:16px;padding:18px;}}
.card-label{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;}}
.card-value{{display:block;font-size:30px;font-weight:700;margin:6px 0 2px;letter-spacing:-.02em;}}
.card-note{{display:block;color:var(--muted);font-size:13px;}}
.severity-strip{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 4px;}}
.report-section{{border:1px solid var(--line);background:var(--panel);border-radius:18px;padding:24px 26px;margin:18px 0;}}
.report-section h2{{margin:0 0 14px;font-size:21px;letter-spacing:-.01em;border-bottom:1px solid var(--line);padding-bottom:12px;}}
.report-section h3{{font-size:16px;margin:20px 0 8px;color:#cfe0f7;}}
.report-section h4{{font-size:15px;margin:18px 0 6px;}}
p{{color:#d4deee;}}
ul,ol{{color:#d4deee;padding-left:22px;}}
li{{margin:6px 0;}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);}}
th{{color:var(--muted);text-transform:uppercase;font-size:11px;letter-spacing:.08em;}}
tbody tr:hover{{background:rgba(94,200,255,.05);}}
code{{background:#0a1424;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-family:'SFMono-Regular',Consolas,monospace;font-size:13px;}}
pre{{background:#070f1d;border:1px solid var(--line);border-radius:12px;padding:16px;overflow:auto;}}
pre code{{border:0;background:none;padding:0;}}
blockquote{{margin:0;padding:8px 16px;border-left:3px solid var(--accent);color:var(--muted);}}
hr{{border:0;border-top:1px solid var(--line);margin:18px 0;}}
.badge{{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid transparent;}}
.badge-critical{{background:rgba(244,63,94,.16);color:#fda4af;border-color:rgba(244,63,94,.4);}}
.badge-high{{background:rgba(249,115,22,.16);color:#fdba74;border-color:rgba(249,115,22,.4);}}
.badge-medium{{background:rgba(234,179,8,.16);color:#fde68a;border-color:rgba(234,179,8,.4);}}
.badge-low{{background:rgba(56,189,248,.16);color:#7dd3fc;border-color:rgba(56,189,248,.4);}}
.badge-info{{background:rgba(148,163,184,.16);color:#cbd5e1;border-color:rgba(148,163,184,.4);}}
@media print{{body{{background:#fff;color:#0b1220;}}.report-header,.card,.report-section{{border-color:#d8dee9;background:#fff;}}p,ul,ol,li{{color:#1f2937;}}.badge{{print-color-adjust:exact;-webkit-print-color-adjust:exact;}}}}
@media (max-width:720px){{.cards{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<main>
<header class="report-header">
<p class="eyebrow">{escape(metadata.report_type.replace('_', ' '))} report</p>
<h1>{escape(metadata.title)}</h1>
<div class="meta">{escape(metadata.organization)} · Project {escape(metadata.project)} · Environment {escape(metadata.environment)}<br/>Generated by {escape(metadata.generator)} v{escape(metadata.version)} on {escape(metadata.generated_at)}</div>
{_summary_cards(score, aggregation)}
{_severity_strip(aggregation)}
</header>
{section_html}
</main>
</body>
</html>"""
