# AxData Python SDK

PyPI 发布后，可用下面的命令安装轻量 SDK/CLI 包：

```bash
pip install axdata
```

`axdata` 会安装 AxData SDK、CLI/API 运行依赖、`axdata-core` 和默认随包提供的数据源 Provider 包。

TDX/TDX Ext source-provider 包安装后默认可用。`axdata doctor` 或 `axdata plugin list`
只用于检查本地环境，不是使用 SDK 前的强制步骤。

源码开发时，可以用 editable 模式安装本地包：

```bash
pip install -e "../../libs/axdata_core"
pip install -e "."
pip install -e "../axdata-source-tdx"
pip install -e "../axdata-source-tdx-ext"
pip install -e "../axdata-source-tencent"
pip install -e "../axdata-source-cninfo"
```

SDK 包依赖 `axdata-core[parquet]` 和本地 API 运行依赖。默认本地模式可以直接读取
Parquet/DuckDB 数据、调用本机 Provider 接口，并运行 AxData CLI 诊断；不需要先启动 HTTP 服务。

包名是 `axdata`，导入方式如下：

```python
import axdata as ax
```

## 基础用法

```python
import axdata as ax

client = ax.AxDataClient()

stocks = client.stock_basic_exchange(
    exchange="SSE",
    region="上海市",
    listing_status="listed",
    fields=["instrument_id", "name", "region", "company_full_name", "list_date"],
)

one_stock = client.stock_basic_exchange(
    instrument_id="600000.SH",
    fields=["instrument_id", "symbol", "exchange", "name", "list_date"],
)

bars = client.daily(
    ts_code="000001.SZ",
    start_date="20250101",
    end_date="20250131",
    fields=["ts_code", "trade_date", "open", "close"],
)

print(stocks.head())
print(one_stock.head())
print(bars.head())
```

查询 `stock_basic_exchange` 时，精确查一只股票建议使用 `instrument_id=600000.SH`。
按交易所筛选时使用 `exchange=SSE`、`exchange=SZSE` 或 `exchange=BSE`。
`.SH/.SZ/.BJ` 后缀属于 `instrument_id`。

SDK 是主要用户入口。默认本地模式通过 `axdata_core` 和 DuckDB 读取当前机器的 AxData
数据目录。Notebook、脚本、回测或因子研究不需要先启动本地 HTTP 服务。

```python
local = ax.AxDataClient()
snapshot = ax.AxDataClient(data_root="/data/axdata-snapshot")
```

Pass `api_base` only when the same SDK calls should go through an AxData HTTP
API channel on another process, LAN machine, or cloud service. In that mode,
the SDK reads the data directory configured on the service that `api_base`
points to:

```python
remote = ax.AxDataClient(api_base="http://192.168.1.20:8666", token="your-token")
stocks = remote.stock_basic_exchange(exchange="SZSE", fields=["instrument_id", "name", "list_date"])
```

Configuration can also come from environment variables:

```bash
export AXDATA_DATA_DIR="/data/axdata/current"
```

```python
import axdata as ax

client = ax.AxDataClient()
df = client.stock_basic_exchange(exchange="SSE", fields=["instrument_id", "name"])
```

```bash
export AXDATA_API_BASE="http://192.168.1.20:8666"
export AXDATA_TOKEN="your-token"
```

```python
import axdata as ax

remote = ax.AxDataClient()
df = remote.daily(ts_code="000001.SZ", start_date="20250101", end_date="20250131")
```

If `AXDATA_API_BASE` is set, `AxDataClient()` uses API mode. Use
`AxDataClient.local(...)` or `mode="local"` when you explicitly want local
direct reads in an environment where `AXDATA_API_BASE` is present.

Queries read data that has already been ingested into AxData. Collection is the
write path that creates raw/staging/core/factor batches. Realtime snapshots and
subscriptions are temporary by default and do not become historical data unless
a recording or collection job explicitly writes them.

## API

```python
client = ax.AxDataClient()
local = ax.AxDataClient.local(data_root="/data/axdata/current")
remote = ax.AxDataClient.api(api_base="http://192.168.1.20:8666", token=None)
```

Available methods:

- `client.query(api_name, fields=None, **params)`
- `client.daily(fields=None, **params)`
- `client.adj_factor(fields=None, **params)`
- `client.trade_cal(fields=None, **params)`
- `client.stock_basic_exchange(fields=None, **params)`
- `client.call(interface, fields=None, options=None, **params)` for temporary source requests such as `stock_codes_tdx`, `stock_realtime_snapshot_tdx`, `index_kline_tdx`, `stock_intraday_today_tdx`, `stock_intraday_recent_history_tdx`, `index_intraday_history_tdx`, `etf_trades_today_tdx`, and `stock_finance_summary_tdx`
- `client.stream(stream, fields=None, **params)` for realtime streams. Without `api_base`, supported TDX streams run locally in-process; with `api_base`, they use the remote WebSocket API.
- `client.session(source="tdx" | "tdx_ext", **options)` for high-frequency local TDX/TDX_EXT source requests that should reuse local provider adapters and long-connection pools.
- `ax.pro_api(...)`
- `ax.download(...)`
- `ax.get(...)`

In local mode, query methods read Parquet data through `axdata_core` and do not
need a running AxData HTTP service. In API mode, all query methods, including
`stock_basic_exchange()`, `daily()`, `adj_factor()`, and `trade_cal()`, post to `/v1/query`;
source requests through `call(...)` post to `/v1/request/{interface}`. Registered
TDX source previews include quote snapshots, ranking pages, order books, index
and ETF K-line samples, intraday/trade-detail samples, finance snapshots, and
concept constituents. These calls default to
`persist=false`: they do not write raw/staging/core/factor data and do not imply
that the interface has a Collector task template.

```python
quote = client.call(
    "stock_realtime_snapshot_tdx",
    code="000001.SZ",
    fields=["instrument_id", "last_price", "change_pct"],
)
index_bars = client.call("index_kline_tdx", code="000001.SH", period="day", count=20)
etf_bars = client.call("etf_kline_tdx", code="510050.SH", period="day", count=20)
intraday = client.call("stock_intraday_today_tdx", code="000001.SZ")
recent_intraday = client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")
index_intraday = client.call("index_intraday_history_tdx", code="000001.SH", trade_date="20260617")
etf_trades = client.call("etf_trades_today_tdx", code="510050.SH")
trades = client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")
finance = client.call("stock_finance_summary_tdx", code="000001.SZ")
```

For high-frequency polling, keep a local source session open instead of looping
plain `client.call(...)`:

```python
with client.session(source="tdx", source_server_count=4, connections_per_server=2) as session:
    snapshot = session.call("stock_realtime_snapshot_tdx", code=["000001.SZ", "600000.SH"])
    rank = session.call("stock_realtime_rank_tdx", category="a_share")
```

Realtime streams follow the same local/remote boundary:

```python
local = ax.AxDataClient()
with local.stream("stock_quote_refresh_tdx", code=["000001.SZ"]) as stream:
    for event in stream:
        print(event.type, event.data)

remote = ax.AxDataClient(api_base="http://192.168.1.20:8666", token="your-token")
with remote.stream("stock_quote_refresh_tdx", code=["000001.SZ"]) as stream:
    for event in stream:
        print(event.type, event.data)
```

The `code` parameter can be a single string, a list, or a comma-separated string.
Source-only K-line and ranking previews use bounded defaults; pass `count`
explicitly when you need a larger sample. Intraday, trade-detail, auction,
finance, index, and ETF examples remain temporary source requests, not Collector
task templates.
Token values are sent as
`Authorization: Bearer ...`.
All query methods return a `pandas.DataFrame`.
The SDK returns `pandas.DataFrame` objects from query and source-request calls.

The old `stock_basic()` method name may remain as a migration alias for
`stock_basic_exchange()`, but new notebooks and applications should use the
explicit interface name.

`download(...)` and `get(...)` are local cache style placeholders for now. They
raise `NotImplementedError` until the cache workflow is implemented.
