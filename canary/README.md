# Agent Canary dashboard

React/TypeScript/Vite dashboard inside the Agent Canary monorepo.

```bash
npm ci
cp .env.example .env.local
# Local only: AUTH_REQUIRED=false
# Set CANARY_API_URL=http://127.0.0.1:8001 and CANARY_API_TOKEN to backend API_SECRET_KEY.
npm run dev
npm run build
npm run lint
npm run test:api
```

Both Vite and the Node static server use the deployed server-side API/auth
handlers. The browser calls same-origin `/api`, and the backend bearer token
stays in the server process. SSE responses stream through the proxy.
`npm run dev` binds to loopback. Production cannot bypass GitHub OAuth through
`AUTH_REQUIRED=false` or `CANARY_DEV_BYPASS`.

For Vercel set the deployment root to `canary/`. Set `CANARY_API_URL`,
`CANARY_API_TOKEN`, OAuth client credentials, `GITHUB_ALLOWED_LOGINS`,
`SESSION_SECRET` (32+ characters), `APP_URL` and redirect URI on the server.
Never expose secrets in `VITE_*` variables. The example allowlist uses
`stevemensah333-rgb`.

The Docker image builds with Node 22 and serves built assets with the Node
server at port 8000. Its default production environment requires OAuth.
The root Compose override is a loopback-only local demo with explicit local
identity; do not use that override for hosting. `nginx.conf` is a legacy
configuration and is no longer the Docker runtime.

See [monorepo setup](../docs/LOCAL_DEVELOPMENT.md) and
[research status](../docs/RESEARCH_PLAN.md).
