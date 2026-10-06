# CompanyAgent — Agent Canary demo target

This target lives inside [Agent Canary](../README.md). Its real FastAPI server
uses LangChain tools and Backboard. It offers `/health`, `/info`, and `/chat`.
The runtime does not replace missing provider credentials with fixture results.

```bash
uv sync --locked --extra dev
cp .env.example .env
# Configure BACKBOARD_API_KEY server-side.
PYTHONPATH=src uv run --locked uvicorn companybot.server:app --host 127.0.0.1 --port 9000
uv run --locked --extra dev pytest -q
```

`security.py` provides employee lookup with sensitive-field redaction,
restricted arithmetic, document credential redaction and safe system metadata.
The employee/document data is synthetic. The current server does not enforce
target API-key authentication or rate limiting; do not infer those features
from configuration names or older demo descriptions.

`companybot.fixture:app` is an explicitly separate deterministic integration
server. `/baseline/chat`, `/regressed/chat`, and `/fixed/chat` exercise synthetic
failure markers and tool policy. Its chat grammar is fixture-specific, and it
cannot measure real model behavior. See [local demo](../docs/LOCAL_DEVELOPMENT.md).

Docker build context is `demo-agent/`. Railway must set its service root to
`demo-agent/` so `railway.json` and `Dockerfile` resolve within this monorepo.
Cloud deployment, HTTPS, isolated PR targets and provider-backed paired pilots
have not been verified in this checkout. The root workflow tests a configured
endpoint; it does not deploy this directory automatically.

The MIT copyright and permission notice remains in [LICENSE](LICENSE).
