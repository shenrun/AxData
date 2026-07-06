# AxData HTTP API

FastAPI channel for AxData table discovery and query endpoints. The Python SDK
is the primary user entry: it reads local data directly by default, and uses
this HTTP API when `api_base` points to a local, LAN, or cloud AxData service.

## Install

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pip install -e libs\axdata_core
```

If `axdata_core` is not installed as a package yet, the API will also try to
import it from `libs/axdata_core` when started from this repository.

## Start

```powershell
npm run dev:api
```

By default the API listens on `http://127.0.0.1:8666`. If the port is occupied:

```powershell
$env:AXDATA_API_HOST = "127.0.0.1"
$env:AXDATA_API_PORT = "8766"
npm run dev:api
```

OpenAPI docs are available at:

```text
http://127.0.0.1:8666/docs
```

## Authentication

Authentication is optional for local development. If no token is configured,
endpoints are open.

For a single environment token:

```powershell
$env:AXDATA_API_TOKEN = "change-me"
npm run dev:api
```

For multiple remote SDK/API clients, create one token per research machine,
notebook, script, or server task from the local web console or API. Named tokens are stored in the local
`metadata/api_tokens.json` registry and are hidden by default in the web console:

```powershell
curl -X POST http://127.0.0.1:8666/v1/auth/tokens `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"notebook-laptop\"}"
```

Local `127.0.0.1` access does not require a token by default. Remote SDK/API listeners
or `AXDATA_API_AUTH_REQUIRED=true` require a valid token. Call endpoints with
either:

```powershell
curl -H "Authorization: Bearer change-me" http://127.0.0.1:8666/health
curl "http://127.0.0.1:8666/health?token=change-me"
```

List and delete named tokens with:

```powershell
curl -H "Authorization: Bearer change-me" http://127.0.0.1:8666/v1/auth/tokens
curl -X DELETE -H "Authorization: Bearer change-me" http://127.0.0.1:8666/v1/auth/tokens/<token_id>
```

The web console is a local management UI on `127.0.0.1:8667`.
Other machines should usually access AxData through the SDK/API on port `8666`
instead of opening the web console remotely. The web port can be customized
with `AXDATA_WEB_PORT`, but the web host remains local loopback.

## Routes

- `GET /health`
- `GET /v1/config`
- `GET /v1/tables`
- `GET /v1/tables/{table}`
- `POST /v1/query`
- `GET /v1/request/interfaces`
- `POST /v1/request/{interface_name}`
- `GET /v1/auth/tokens`
- `POST /v1/auth/tokens`
- `DELETE /v1/auth/tokens/{token_id}`
- `WS /v1/stream/stock_quote_refresh_tdx`

Data returned by `axdata_core` is converted to JSON. Pandas DataFrames are
returned as record arrays.

## Query Example

The HTTP API is useful for the web console, curl, non-Python clients, and
remote access. It reads data that has already been ingested into the service's
configured data directory.

```bash
curl -X POST "http://127.0.0.1:8666/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"table":"stock_basic_exchange","fields":["instrument_id","symbol","exchange","name","list_date"],"params":{"instrument_id":"600000.SH"},"limit":1000}'

curl -X POST "http://127.0.0.1:8666/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"table":"daily","fields":["ts_code","trade_date","close"],"params":{"ts_code":"000001.SZ","start_date":"20240101","end_date":"20240131"},"limit":1000}'
```

`POST /v1/query` uses the same parameter semantics as the SDK API backend:

- `fields`: selected AxData fields, as a list or comma-separated string.
- `columns`: alias for `fields`.
- `filters`: explicit exact-match filters. `null` values are ignored.
- `params`: SDK-style parameters. `start`, `start_date`, `end`, and `end_date`
  become date ranges; other non-null values are merged into exact-match
  filters.
- `start` / `start_date`: start of the table date field range. `YYYY-MM-DD`
  is accepted and normalized to `YYYYMMDD`.
- `end` / `end_date`: end of the table date field range. `YYYY-MM-DD` is
  accepted and normalized to `YYYYMMDD`.
- `limit`: maximum rows. Omit it for the default limit; use `null` only for
  trusted local or internal calls that intentionally need no limit.

Example:

```bash
curl -X POST "http://127.0.0.1:8666/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "daily",
    "fields": ["ts_code", "trade_date", "close"],
    "params": {
      "ts_code": "000001.SZ",
      "start_date": "2024-01-02",
      "end_date": "2024-01-31"
    },
    "limit": 1000
  }'
```

For `stock_basic_exchange`, use `instrument_id=600000.SH` when querying one
stock. Use `exchange=SSE`, `exchange=SZSE`, or `exchange=BSE` when filtering by
exchange. The `.SH/.SZ/.BJ` suffix belongs to `instrument_id`. SDK convenience
methods such as `stock_basic_exchange()` and `daily()` still exist, but in API
mode they post to `/v1/query` instead of using dedicated GET routes.

`GET /v1/request/interfaces` currently exposes TDX source preview interfaces:

- `stock_codes_tdx`: TDX 7709 latest stock list preview. It accepts `name`,
  `code`, `scope`, and optional `fields`. If `fields` is omitted, the response
  uses the public interface fields.
- `stock_st_list_tdx`: TDX 7709 latest ST stock list preview. It scans the
  current stock universe and returns stocks whose current short name starts
  with `ST` or `*ST`.
- `stock_suspensions_tdx`: TDX 7709 latest suspension list preview. It scans
  the current stock universe and returns the stocks currently reported as
  suspended. The public fields match the stock-list identifier fields.
- `stock_realtime_rank_tdx`: TDX 7709 realtime ranking preview. It accepts
  `category`, `sort`, `count`, `ascending`, and optional `filters`.
  By default it returns the first 80 current quote rows with a one-based rank;
  pass `count="all"` to request the complete current ranking.
- `stock_realtime_snapshot_tdx`: TDX 7709 realtime quote snapshot preview. It
  accepts `code` and returns one row per security with price, volume, turnover,
  inside/outside volume, best bid/ask, parsed intraday snapshot indicators, and
  calculated fields such as opening/high/low change percentage, average price,
  inside/outside ratio, opening amount ratio, drawdown/attack percentage, and
  locked amount.
- `stock_order_book_tdx`: TDX 7709 current five-level order-book preview. It
  accepts `code` and returns one row per level with bid/ask prices and volumes.
- `stock_intraday_today_tdx`: TDX 7709 current-day intraday preview. It accepts
  `code` and returns minute price points, intraday average price, and minute
  volume for the current trading day. It is separate from K-line interfaces and
  does not return OHLC fields.
- `stock_intraday_history_tdx`: TDX 7709 historical intraday preview. It
  accepts `code` and `trade_date`, and returns minute price points, minute
  volume, and previous close for the selected trading date. It is separate from
  K-line interfaces and does not return OHLC fields.
- `stock_intraday_recent_history_tdx`: TDX 7709 recent historical intraday
  preview. It accepts `code` and `trade_date`, and returns recent-date minute
  price points, intraday average price, minute volume, previous close, and open
  price.
- `stock_trades_today_tdx`: TDX 7709 current-day trade-detail preview. It
  accepts `code` and returns current trading-day trade-detail rows. TDX
  pagination is handled inside AxData.
- `stock_trades_history_tdx`: TDX 7709 historical trade-detail preview. It
  accepts `code` and `trade_date`, and returns trade price, volume, order count,
  and direction for the selected trading date. TDX pagination is handled inside
  AxData.
- `stock_kline_*_tdx`: TDX 7709 K-line previews, including second, minute,
  custom-minute, daily, custom-day, weekly, monthly, quarterly, and yearly
  periods. They return AxData-normalized OHLCV rows. `code` accepts one
  security, a list, or a comma-separated string; K-line calls default to full
  history, and batch requests are merged into one result table by AxData.

Example:

```bash
curl -X POST "http://127.0.0.1:8666/v1/request/stock_codes_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"scope":"all"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_suspensions_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"scope":"all"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_st_list_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"scope":"all"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_realtime_rank_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"category":"a_share","sort":"change_pct","count":80},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_realtime_rank_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"category":"a_share","sort":"change_pct","count":"all"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_realtime_snapshot_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_order_book_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_today_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ"},"fields":["instrument_id","time_label","price","avg_price","volume"],"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_history_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ","trade_date":"20260519"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_recent_history_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ","trade_date":"20260519"},"fields":["instrument_id","time_label","price","avg_price","open_price"],"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_trades_today_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_trades_history_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":"000001.SZ","trade_date":"20260511"},"persist":false}'

curl -X POST "http://127.0.0.1:8666/v1/request/stock_kline_second_tdx" \
  -H "Content-Type: application/json" \
  -d '{"params":{"code":["000001.SZ","600000.SH"],"seconds":5},"persist":false}'
```

Source requests are previews and keep `persist=false`; they do not write
raw/staging/core/factor data.

Realtime streams use WebSocket and also do not write raw/staging/core/factor
data by default. The first TDX stream is `stock_quote_refresh_tdx`: clients
subscribe with a code list, receive an initial `snapshot`, and then receive
periodic `update` events with the latest quote rows. The initial snapshot uses
the realtime snapshot request path, and later updates use the TDX quote refresh
request path.

```json
{
  "op": "subscribe",
  "params": {
    "code": ["000001.SZ", "600000.SH"],
    "fields": ["instrument_id", "last_price", "change_pct", "volume", "amount"],
    "interval_ms": 3000,
    "initial_snapshot": true
  }
}
```

TDX connection details are managed at the adapter/transport layer rather than
inside every business interface:

- `AXDATA_TDX_HOSTS`: comma-separated `host:7709` list. Empty means the built-in
  host pool.
- `AXDATA_TDX_POOL_SIZE`: connection pool size, default `1`.
- `AXDATA_TDX_KLINE_HOST_COUNT`: K-line batch host count, default `2`.
- `AXDATA_TDX_KLINE_POOL_SIZE`: K-line batch connections per host, default `4`.
- `AXDATA_TDX_HEARTBEAT_INTERVAL`: heartbeat interval in seconds. Source
  previews default to `0`/disabled; set a positive number only for realtime or
  long-lived clients that need keepalive.
- `AXDATA_TDX_PROBE_HOSTS`: set to `true`, `1`, or `yes` to sort hosts by TCP
  latency before use.
- `AXDATA_TDX_TIMEOUT`: socket/request timeout in seconds, default `8.0`.

Local and LAN calls are the same HTTP API; only the host changes. The API reads
data from the machine where the AxData service is running.

```bash
curl -X POST "http://192.168.1.20:8666/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"table":"stock_basic_exchange","fields":["instrument_id","name","list_date"],"params":{"exchange":"SZSE"},"limit":1000}'
```

The API reads core Parquet tables from `AXDATA_DATA_DIR`, defaulting to the
repository `data/` directory.

Collection jobs are the write path for historical data. Source probes,
debug previews, realtime snapshots, and subscriptions do not enter historical
tables unless an explicit collection or recording job writes a batch.
