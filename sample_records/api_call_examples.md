# API Call Examples

These examples are reproducible judge records for the hosted MVP. Replace `http://127.0.0.1:8765` with the Railway URL and set `BITGUARD_API_KEY` to one token from `BITGUARD_API_KEYS`.

## 2026-06-24T10:00:00Z - Public Health

```bash
curl http://127.0.0.1:8765/api/health
```

Expected summary:

```json
{
  "ok": true,
  "service": "bitguard-sentinel",
  "mode": "log-audit"
}
```

## 2026-06-24T10:01:00Z - Readiness

```bash
curl http://127.0.0.1:8765/api/ready
```

Expected summary:

```json
{
  "ok": true,
  "database": {"writable": true},
  "public_market_data": {"provider": "bitget", "auto_fetch_candles": true}
}
```

## 2026-06-24T10:02:00Z - Authenticated Audit

```bash
curl -X POST http://127.0.0.1:8765/api/audit \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @samples/demo_agent_log_bundle.json
```

Expected summary:

```json
{
  "agent_id": "sentinel-demo-agent",
  "run_id": "demo-run-001",
  "summary": {
    "completed_trades": 2,
    "market_context_status": "available",
    "product_type": "USDT-FUTURES"
  }
}
```

## 2026-06-24T10:03:00Z - Authenticated Usage Records

```bash
curl http://127.0.0.1:8765/api/usage?limit=20 \
  -H "Authorization: Bearer $BITGUARD_API_KEY"
```

Expected summary:

```json
{
  "records": [
    {
      "event_type": "api.sentinel.audit",
      "agent_id": "sentinel-demo-agent",
      "run_id": "demo-run-001",
      "status": "ok"
    }
  ]
}
```

## 2026-06-24T10:04:00Z - Unauthenticated Rejection

```bash
curl -X POST http://127.0.0.1:8765/api/audit \
  -H "content-type: application/json" \
  --data-binary @samples/demo_agent_log_bundle.json
```

Expected status when `BITGUARD_REQUIRE_AUTH=1`: `401 auth_required`.
