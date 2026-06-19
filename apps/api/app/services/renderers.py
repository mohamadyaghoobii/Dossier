from html import escape
from app.schemas import Section


def render_markdown(title: str, project: str, environment: str, sections: list[Section]) -> str:
    lines = [f"# {title}", "", f"Project: {project}", f"Environment: {environment}", ""]
    for section in sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.body)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _paragraphs(text: str) -> str:
    blocks = []
    for line in text.split("\n"):
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("- "):
            blocks.append(f"<li>{escape(clean[2:])}</li>")
        else:
            blocks.append(f"<p>{escape(clean)}</p>")
    output = []
    buffer = []
    for block in blocks:
        if block.startswith("<li>"):
            buffer.append(block)
        else:
            if buffer:
                output.append("<ul>" + "".join(buffer) + "</ul>")
                buffer = []
            output.append(block)
    if buffer:
        output.append("<ul>" + "".join(buffer) + "</ul>")
    return "\n".join(output)


def render_html(title: str, project: str, environment: str, sections: list[Section]) -> str:
    section_html = "\n".join(
        f"<section><h2>{escape(section.title)}</h2>{_paragraphs(section.body)}</section>"
        for section in sections
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)}</title>
<style>
body{{margin:0;background:#0b1220;color:#e5e7eb;font-family:Inter,Arial,sans-serif;line-height:1.6}}
main{{max-width:980px;margin:0 auto;padding:48px 24px}}
header{{border:1px solid #243044;background:#111827;border-radius:24px;padding:28px;margin-bottom:24px}}
section{{border:1px solid #243044;background:#0f172a;border-radius:20px;padding:24px;margin:18px 0}}
h1{{margin:0 0 8px;font-size:34px}}
h2{{margin:0 0 16px;font-size:23px}}
p{{color:#cbd5e1}}
li{{color:#cbd5e1;margin:8px 0}}
.meta{{color:#94a3b8}}
</style>
</head>
<body>
<main>
<header><h1>{escape(title)}</h1><div class="meta">Project: {escape(project)} · Environment: {escape(environment)}</div></header>
{section_html}
</main>
</body>
</html>"""
