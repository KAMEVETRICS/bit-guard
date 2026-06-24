# Production Notes

BitGuard Sentinel is production-ready for a hackathon-hosted MVP: token-protected API actions, SQLite usage records, schema validation, request limits, and a Railway deployment path. It is not a full SaaS login product.

## Railway Deployment

1. Push this repository to a public GitHub repo.
2. Create a new Railway project from the repo.
3. Railway will use `Dockerfile` and `railway.json`.
4. Add a volume mounted at `/data` if you want usage records to survive redeploys.
5. Set these environment variables:

```text
BITGUARD_REQUIRE_AUTH=1
BITGUARD_API_KEYS=replace-with-long-random-token
BITGUARD_DB_PATH=/data/bitguard.db
BITGUARD_CORS_ORIGINS=https://your-railway-domain.up.railway.app
BITGUARD_FETCH_PUBLIC_CANDLES=1
```

Optional intelligence and collector variables remain local or optional:

```text
TRUENORTH_API_KEY=
TRUENORTH_MCP_URL=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=z-ai/glm-5.2
BITGET_API_KEY=
BITGET_SECRET_KEY=
BITGET_PASSPHRASE=
```

## Runtime Checks

Public checks:

```bash
curl https://your-app.up.railway.app/api/health
curl https://your-app.up.railway.app/api/ready
```

Authenticated audit:

```bash
curl -X POST https://your-app.up.railway.app/api/audit \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @samples/demo_agent_log_bundle.json
```

Unauthenticated POSTs should return `401` when `BITGUARD_REQUIRE_AUTH=1`.

## Stored Data

SQLite stores summary records only:

- `usage_records`: timestamp, event type, agent id, run id, source, status, summary JSON.
- `audit_runs`: request id, agent id, run id, audit summary JSON, pattern summary JSON, created timestamp.

Raw private order logs are not stored by the hosted API.

## Operational Limits

- Auth is bearer-token based, not user login.
- Rate limiting is in-memory per process.
- SQLite is suitable for judging/demo use, not high-volume multi-tenant SaaS.
- Public Bitget candles are fetched from submitted symbols and timestamps; private Bitget account reads should happen locally through the collector.
