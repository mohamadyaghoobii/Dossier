# Dossier

Dossier is a DevSecOps report generator that turns analyzer findings into stakeholder-ready reports. It is designed to sit beside tools such as OpsDeck, Podscope, Dockyard, Gatehouse, Stacklint, Tracepack, Signalbook, and Cloudline.

![Dossier dashboard](docs/images/dossier-dashboard.svg)

## What Dossier does

Dossier accepts normalized findings from security, DevOps, cloud, Kubernetes, CI/CD, IaC, dependency, and observability analyzers. It builds a consistent report bundle with risk scoring, executive summaries, technical findings, remediation planning, and exportable Markdown or HTML.

It is not a vulnerability scanner. It is the reporting layer that converts analysis output into a format that engineers, managers, and stakeholders can actually use.

## Why it exists

DevSecOps tools often produce useful findings but weak reporting. Engineering teams need a reliable way to convert findings into:

- Executive summaries
- Technical remediation plans
- Sprint-ready fix lists
- Stakeholder status updates
- Markdown reports for repositories and wikis
- HTML reports for sharing and archiving
- A stable output contract that a central platform can ingest

Dossier provides that reporting workbench.

## Architecture

![Dossier flow](docs/images/dossier-flow.svg)

```text
Analyzer JSON
  -> Dossier API
  -> Finding normalization
  -> Risk scoring
  -> Report sections
  -> Markdown and HTML exports
  -> OpsDeck integration later
```

## Repository structure

```text
dossier
├── apps/api
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── services
│   │   └── schemas.py
│   ├── tests
│   ├── Dockerfile
│   └── requirements.txt
├── apps/web
│   ├── app
│   ├── components
│   ├── lib
│   ├── Dockerfile
│   └── package.json
├── docs/images
├── examples
├── docker-compose.yml
└── .env.example
```

## Current features

- FastAPI backend
- Next.js frontend
- Markdown and HTML output
- Severity scoring
- Grade calculation
- Severity, category, and source distributions
- Executive summary generation
- Technical details section
- Remediation roadmap section
- Example inputs
- Local SVG diagrams
- Docker Compose setup
- Backend endpoint tests

## Supported finding input

Dossier expects findings in a simple JSON structure:

```json
{
  "project": "MetaSec DevSecOps Suite",
  "environment": "production",
  "findings": [
    {
      "title": "Public administrative port exposed",
      "severity": "critical",
      "category": "Network Exposure",
      "source": "Cloudline",
      "target": "aws_security_group.web_admin",
      "description": "SSH is open to the internet on a production-facing security group.",
      "impact": "Attackers can attempt brute-force or exploit management services.",
      "remediation": "Restrict administrative access to VPN, bastion, or approved office ranges.",
      "status": "open"
    }
  ]
}
```

Severity values:

```text
critical, high, medium, low, info
```

## Scoring model

Dossier starts each report at 100 and subtracts points based on severity:

```text
critical: -22
high:     -14
medium:   -8
low:      -3
info:      0
```

Grades:

```text
A: 90-100
B: 80-89
C: 70-79
D: 55-69
F: 0-54
```

## API endpoints

```text
GET  /health
GET  /ready
GET  /api/templates
GET  /api/examples
POST /api/generate
```

## Example API usage

```bash
curl -s http://localhost:8000/api/examples
```

```bash
curl -s -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d @examples/findings-sample.json
```

## Quick start with Docker Compose

```bash
docker compose up --build
```

Services:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
```

## Backend manual setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
cd apps\api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend manual setup

```bash
cd apps/web
npm install
npm run dev
```

## Tests

Backend:

```bash
cd apps/api
pytest
```

Frontend:

```bash
cd apps/web
npm install
npm run typecheck
npm run build
```

## Environment variables

```text
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
AI_PROVIDER=none
```

## Integration plan with OpsDeck

Dossier is intended to become the reporting module inside the final integrated platform.

Planned integration contract:

- Accept findings from all analyzer modules
- Preserve source module names
- Return stable report metadata
- Return normalized severity counts
- Return Markdown and HTML exports
- Later support PDF generation
- Later support saved report history
- Later support ticket export and PR comments

## Roadmap

- Add richer report templates
- Add PDF export
- Add DOCX export
- Add report history and persistence
- Add user-defined templates
- Add Jinja-style template rendering
- Add Playwright E2E tests
- Add AI-assisted executive summary generation
- Add Jira/GitHub issue export
- Add OpsDeck ingestion contract
- Add report comparison between runs

## Security notes

- Do not submit real secrets in report inputs.
- If findings contain secret evidence, redact it before sending to Dossier.
- AI integration is disabled by default.
- Future AI features should never receive unredacted sensitive evidence.
- HTML output is generated from escaped text sections.

## Contribution notes

This project is intentionally small and modular. Keep Dossier focused on reporting, exports, templates, and stakeholder communication. Scanner logic belongs in the analyzer modules.
