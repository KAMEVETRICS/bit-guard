# BitGuard Sentinel

BitGuard Sentinel is a post-trade review and order-audit dashboard for Bitget trading agents. It audits exported historical order logs, reconstructs entry/exit pairs, replays market movement around the trade window when candles are available, calculates PnL and risk, and produces a judge-friendly report without asking users to upload API keys.

The intended production data source is a locally exported Bitget read-only log bundle. For hackathon judging, the repo also includes a clearly marked demo-only agent log schema so the full audit flow can be reproduced without connecting a Bitget account.

## Requirements

- Python 3.10 or newer
- No runtime Python packages are required
- Optional: `bgc` from Bitget Agent Hub for local read-only collection

## Installation

```bash
git clone <your-public-repo-url>
cd Bitget
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional local credentials can be stored in `.env` for the local collector and optional Whale Ping intelligence layer:

```bash
copy .env.example .env
```

The dashboard does not require or receive API keys. Bitget keys stay local for read-only collection. TrueNorth and OpenRouter keys are only needed for the planned Whale Ping intelligence layer.

Key optional intelligence variables:

```text
TRUENORTH_API_KEY=
TRUENORTH_BASE_URL=
TRUENORTH_MCP_URL=
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=z-ai/glm-5.2
```

If OpenRouter publishes GLM 5.2 under a different model slug, update `OPENROUTER_MODEL` in `.env`.

## Live Deployment

Public Railway deployment:

```text
https://bit-guard-production.up.railway.app
```

Dashboard:

```text
https://bit-guard-production.up.railway.app/dashboard
```

Hosted write endpoints require a bearer token issued by the project operator.
## Access Method

Run the local dashboard and API:

```bash
python -m bitguard serve --port 8765
```

Open the landing page:

```text
http://127.0.0.1:8765
```

Open the live audit dashboard directly:

```text
http://127.0.0.1:8765/dashboard
```

API endpoints:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/usage?limit=20`
- `POST /api/audit`
- `POST /api/intelligence`
- `POST /api/redact`

`POST /api/audit` returns portfolio-level metrics, a first-class `order_audit` verdict, a `market_replay` section, and a `perception_layer` verdict. The order verdict analyzes supplied historical order/fill logs, reconstructs completed trades, detects spot versus futures logs, scores the completed trade process, and returns evidence plus iteration feedback. The market replay fetches public Bitget candles from trade timestamps when needed, while still accepting supplied candles or order-book snapshots for reproducible demos. The perception verdict analyzes optional Skill Hub snapshots plus copy-trading/whale pings to decide whether a whale/order-flow signal is opportunity, watchlist, caution, or avoid. `POST /api/intelligence` runs the same audit, optionally calls TrueNorth MCP when `TRUENORTH_MCP_URL` is configured, then asks OpenRouter/GLM for an AI Replay Coach brief when `OPENROUTER_API_KEY` is present. The brief treats trades as historical evidence, uses the candle replay as ground truth, and returns `replay_notes` plus `what_could_be_better` for agent iteration. If either service is missing, it returns a deterministic fallback brief for reproducible judging.

## Production Deployment

BitGuard is designed as a hackathon production MVP: no SaaS login, but hosted API actions can be protected with bearer tokens, requests are validated before audit logic, usage summaries are stored in SQLite, and private raw logs are not stored by default.

### Railway

1. Push this repo to a public GitHub repository.
2. Create a Railway project from the repo.
3. Railway will use `Dockerfile` and `railway.json`.
4. Add a Railway volume mounted at `/data` if you want SQLite records to persist across deploys.
5. Set the production env vars below.

| Variable | Required | Example | Notes |
| --- | --- | --- | --- |
| `BITGUARD_REQUIRE_AUTH` | Hosted yes | `1` | Requires bearer tokens on sensitive endpoints. |
| `BITGUARD_API_KEYS` | Hosted yes | `token-one,token-two` | Comma-separated API tokens for agents/judges. |
| `BITGUARD_DB_PATH` | Hosted yes | `/data/bitguard.db` | SQLite path. Local default is `data/bitguard.db`. |
| `BITGUARD_CORS_ORIGINS` | Optional | `https://your-app.up.railway.app` | Use `*` for open hackathon demos. |
| `BITGUARD_FETCH_PUBLIC_CANDLES` | Optional | `1` | Enables public Bitget candle replay fetches. |
| `BITGUARD_MAX_BODY_BYTES` | Optional | `1000000` | Request body limit for JSON uploads. |
| `BITGUARD_RATE_LIMIT_PER_MINUTE` | Optional | `60` | In-memory per IP/token rate limit. |
| `TRUENORTH_API_KEY` / `TRUENORTH_MCP_URL` | Optional |  | Enables external intelligence context. |
| `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` | Optional | `z-ai/glm-5.2` | Enables AI Replay Coach synthesis. |
| `BITGET_API_KEY` / `BITGET_SECRET_KEY` / `BITGET_PASSPHRASE` | Local optional |  | Only for local read-only collection, not dashboard uploads. |

Readiness check:

```bash
curl https://your-app.up.railway.app/api/ready
```

Authenticated audit call:

```bash
curl -X POST https://your-app.up.railway.app/api/audit \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @samples/demo_agent_log_bundle.json
```

OpenAPI-style docs live at `docs/openapi.json`; production notes live at `docs/PRODUCTION.md`.


## Agent Connection

Agents connect to BitGuard in three practical ways.

### 1. File-based CLI

Use this when an agent can write a JSON evidence bundle after a run. The agent writes orders, fills, positions, optional decisions, optional Skill Hub snapshots, and optional whale/copy-trading pings to disk, then calls the CLI:

```bash
bitguard audit exports/agent-log-bundle.json --out outputs/audit_report.json
bitguard intelligence exports/agent-log-bundle.json --out outputs/intelligence_report.json
```

No private Bitget key is sent to BitGuard. If candles are missing, BitGuard can fetch public Bitget candles from the submitted symbol and timestamps.

### 2. Local HTTP API

Use this when an agent can POST JSON to a local or deployed service:

```bash
bitguard serve --port 8765
curl -X POST http://127.0.0.1:8765/api/audit \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @exports/agent-log-bundle.json
curl -X POST http://127.0.0.1:8765/api/intelligence \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @exports/agent-log-bundle.json
```

`/api/audit` returns deterministic replay, PnL, risk, and pattern-library output. `/api/intelligence` returns the same audit plus the replay coach brief.

### 3. Local Bitget collector

Use this when the trader wants BitGuard to collect their read-only Bitget logs locally before auditing:

```bash
bitguard collect-bitget --agent-id my-agent --out exports/bitget-log-bundle.json
bitguard audit exports/bitget-log-bundle.json --out outputs/audit_report.json
```

The collector uses `bgc --read-only`. API keys stay on the user's machine and are not written to the exported bundle.

To print a machine-readable connection guide for agent developers:

```bash
bitguard connect --port 8765
```

Minimum bundle shape:

```json
{
  "source": "demo-agent-log-schema",
  "agent_id": "my-agent",
  "run_id": "run-001",
  "orders": [],
  "fills": [
    {"symbol": "BTCUSDT", "side": "buy", "price": 65000, "quantity": 0.01, "timestamp": "2026-06-20T10:00:00Z"},
    {"symbol": "BTCUSDT", "side": "sell", "price": 65300, "quantity": 0.01, "timestamp": "2026-06-20T11:00:00Z"}
  ],
  "positions": [],
  "agent_decisions": [],
  "skill_hub": {},
  "copy_trading_pings": []
}
```
## Data Sources

### Bitget Read-Only Export

BitGuard does not collect private Bitget API keys in the dashboard. Traders or agents query their own Bitget read-only endpoints locally, then submit the exported JSON bundle. This repo includes an optional local collector helper that can produce that bundle with `bgc --read-only`; API keys stay on the user machine.

```bash
python -m bitguard collect-bitget --out exports/bitget-log-bundle.json --agent-id my-agent
```

The resulting bundle can be audited locally or uploaded to a hosted Sentinel instance. The collector also attempts optional read-only copy-trading sections (`copy_trading_traders`, `copy_trading_orders`, and `copy_trading_positions`) for the planned Whale Ping module. If Bitget credentials or permissions do not expose those sections, the collector records the error without blocking the core order audit.

### Market Replay

For completed trades, Sentinel can compare entry/exit prices with chart movement around the same period. In production, the API can fetch public Bitget candles automatically from the submitted symbol and entry/exit timestamps. Bundles may also include a `market_context.candles` object keyed by symbol, or similar snapshots generated by the agent/exporter, for offline demos and judge-reproducible fixtures.

The replay output feeds both the Pattern Library and the AI Replay Coach in `/api/intelligence`. TrueNorth/OpenRouter can add external market-structure interpretation, but the coach still anchors on Sentinel's deterministic replay facts: entry/exit movement, favorable/adverse excursion, entry quality, exit quality, and the completed-trade verdict.

```json
{
  "product_type": "USDT-FUTURES",
  "market_context": {
    "source": "agent-export",
    "fetch_status": "supplied",
    "candles": {
      "BTCUSDT": [
        {"timestamp": "2026-06-22T09:00:00Z", "open": 64900, "high": 65200, "low": 64800, "close": 65000, "volume": 1200}
      ]
    }
  }
}
```


### Pattern Library

Inspired by Pacifica-style pattern intelligence, every audit now emits a `pattern_library` section. It converts completed trade replay into reusable agent behavior cards: observed setups, risk patterns, sample size, win rate, average PnL, symbols, conditions, and the recommended next action. Patterns are marked `observed` or `risk` unless enough samples exist to honestly call them `verified`.

This gives judges a clearer product loop: upload agent logs, replay the trade, extract behavior patterns, then use the AI Replay Coach to explain what should change before the next strategy iteration.
### Skill Hub Perception Layer

Agents can include optional Skill Hub snapshots in the submitted JSON bundle. The dashboard does not call analyst tools with user secrets; it audits the evidence the agent already exported.

```json
{
  "skill_hub": {
    "macro_analyst": {"stance": "mixed headwind", "summary": "Macro backdrop is mixed."},
    "market_intel": {"stance": "whale accumulation bullish", "summary": "Top-trader proxies show accumulation."},
    "news_briefing": {"stance": "event risk", "summary": "Fresh headlines add catalyst risk."},
    "sentiment_analyst": {"stance": "crowded longs funding elevated", "summary": "Longs are crowded."},
    "technical_analysis": {"stance": "bullish trend near resistance", "summary": "Breakout confirmation is needed."}
  },
  "copy_trading_pings": [
    {
      "source": "copy_trading",
      "symbol": "BTCUSDT",
      "direction": "long",
      "notional_usdt": 4200,
      "followers": 1860,
      "leader_drawdown_pct": 12.4,
      "summary": "A highly followed copy-trading leader is net long BTC."
    }
  ]
}
```

This powers the Whale Pings tab and the `perception_layer` output in audit reports.

### Demo Agent Log Schema

For hackathon judging and local reproduction, this repo includes:

```text
samples/demo_agent_log_bundle.json
```

This file is simulated demo data. It is not live Bitget account data.

## Usage Examples

Audit the demo bundle:

```bash
python -m bitguard audit samples/demo_agent_log_bundle.json --out outputs/audit_report.json
```

Redact a bundle before sharing:

```bash
python -m bitguard redact samples/demo_agent_log_bundle.json --out outputs/redacted_bundle.json
```

Generate an AI replay coach report:

```bash
python -m bitguard intelligence samples/demo_agent_log_bundle.json --out outputs/intelligence_report.json
```

Print agent connection options:

```bash
python -m bitguard connect --port 8765
```

Generate reproducible judge records:

```bash
python -m bitguard demo
```

This writes:

- `sample_records/audit_report.json`
- `sample_records/intelligence_report.json`
- `sample_records/redacted_demo_bundle.json`
- `sample_records/usage_records.jsonl`
- `sample_records/api_call_examples.md`

## Audit Output

Sentinel reports:

- Entry and exit reconstruction
- Spot versus futures detection
- Candle-based market replay around completed trades
- Realized PnL
- Win rate and profit factor
- Max drawdown
- Open position concentration
- Leverage exposure
- Funding-rate bleed
- Overtrading signals
- Missing stop-loss decisions
- Composite risk score and health grade
- Skill Hub perception verdict for whale/copy-trading pings

## Verification

Run tests:

```bash
python -m unittest discover -s tests
```

Run the full sample flow:

```bash
python -m bitguard demo
```

## Current Scope

- No live order execution.
- No full SaaS login or team account system.
- Hosted API actions use bearer-token auth.
- No hosted API key collection.
- Bitget API collection is local-only and read-only.
- Demo schema is explicitly non-live and exists only for reproducibility.



