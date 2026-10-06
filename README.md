# Agent Canary

A monorepo for behavioral security evaluation of controlled AI-agent targets.
PASS/WARN/BLOCK describes the tested behavior; it is not a universal safety proof.

| Component | Path | Present behavior |
| --- | --- | --- |
| Dashboard | `canary/` | React/Vite, server-side API proxy and GitHub OAuth |
| Evaluation backend | `cyber-redteam-foundry/` | FastAPI, LangGraph, persisted release comparisons and gates |
| GitHub Action | `action/` | Local composite action; workflow uses `./action` |
| Demo target | `demo-agent/` | Real Backboard tool-calling agent plus a separate synthetic integration fixture |
| Research pilot | `research/`, backend `evaluation/scenarios.py` | Eight versioned multi-step cases, repeated fixed paired runs and evidence |

## Local demo

Install Node 22.12+ and Python 3.11–3.13 with `uv`, then:

```bash
(cd cyber-redteam-foundry && uv sync --locked --extra test)
(cd demo-agent && uv sync --locked --extra dev)
(cd canary && npm ci)
./scripts/local-demo.sh
```

Open http://127.0.0.1:5173. In another terminal, run:

```bash
./scripts/verify-local-demo.sh
```

The demo exercises real local HTTP requests, deterministic synthetic target
regressions, the existing release comparison domain, SQLite persistence and
the dashboard proxy. It does **not** exercise the production model attack/judge
graph or claim model safety results. It needs no provider credentials and makes
no provider calls. Runtime evidence stays in ignored `.local/`.

The fixture demo and full backend suite were verified in the locked project
environment. Python Docker builds remain unverified after registry download
failures. See [the exact runtime and results](docs/VERIFICATION.md).

See [local setup and verification](docs/LOCAL_DEVELOPMENT.md),
[research implementation status](docs/RESEARCH_PLAN.md) and
[project decisions](docs/PROJECT_CONTEXT.md).

## Model-backed evaluation

Configure the backend and real target from their `.env.example` files. Keep
provider keys, `API_SECRET_KEY`, `CANARY_API_TOKEN`, OAuth credentials and session
secrets server-side. Never put credentials in `VITE_*` variables.

Run the real target from `demo-agent/` with
`PYTHONPATH=src uv run --locked uvicorn companybot.server:app --host 127.0.0.1 --port 9000`.
Use a separately deployed accepted baseline and candidate for comparisons.
Configure and explicitly accept a completed baseline for the appropriate
environment before interpreting a candidate gate.

## CI

The workflow in `.github/workflows/agent-canary.yml` checks out this monorepo
and invokes `uses: ./action`. Configure `CANARY_API_URL`,
`CANARY_PROJECT_TOKEN`, `CANARY_TARGET_VERIFICATION_TOKEN` secrets and
`CANARY_TARGET_URL`, `CANARY_BASELINE_URL` variables. Missing configuration is
a skipped assessment. A fixed URL does not automatically assess PR code;
isolated candidate deployment and its URL handoff remain planned.

Standard GitHub-maintained checkout/artifact actions remain dependencies.
Project source/deployment examples refer only to this monorepo. Required
copyright notices and upstream attribution are preserved.

## Status and attribution

The $20,000 grant request and six-month deliverables remain proposals. No
funding award, provider-cost measurement, human calibration, 200-case dataset,
or deployed research study is claimed here. Historical source-demo results
are not evidence from this checkout.
