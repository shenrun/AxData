# AxData

AxData 是一个开源量化数据库框架，面向个人量化研究、本地数据管理和数据源插件开发。

这个 PyPI 包提供统一的 Python 安装入口，包含：

- Python SDK
- AxData CLI
- 核心框架
- 默认随包的数据源 Provider 模块

安装后可以在本地直接使用 SDK 和 CLI；不需要先启动 HTTP 服务。需要 Web 控制台、源码开发或二次扩展时，建议按项目文档使用完整项目安装方式。

项目文档：<https://electkismet.github.io/AxData/>

## 安装

```bash
pip install axdata
```

## 基础用法

```python
import axdata as ax

client = ax.AxDataClient()

stocks = client.stock_basic_exchange(
    exchange="SSE",
    fields=["instrument_id", "name", "region", "list_date"],
)

bars = client.daily(
    ts_code="000001.SZ",
    start_date="20250101",
    end_date="20250131",
    fields=["ts_code", "trade_date", "open", "close"],
)

print(stocks.head())
print(bars.head())
```

默认情况下，`AxDataClient()` 使用本地模式，直接读取当前机器上的 AxData 数据目录。Notebook、脚本、回测或因子研究不需要先启动本地 HTTP 服务。

```python
local = ax.AxDataClient()
snapshot = ax.AxDataClient(data_root="/data/axdata-snapshot")
```

只有当 SDK 需要访问另一台机器、另一个进程或服务器上的 AxData HTTP API 时，才需要传入 `api_base`：

```python
remote = ax.AxDataClient(api_base="http://192.168.1.20:8666", token="your-token")
stocks = remote.stock_basic_exchange(exchange="SZSE", fields=["instrument_id", "name", "list_date"])
```

也可以通过环境变量指定数据目录或 API 地址：

```bash
export AXDATA_DATA_DIR="/data/axdata/current"
export AXDATA_API_BASE="http://192.168.1.20:8666"
export AXDATA_TOKEN="your-token"
```

如果设置了 `AXDATA_API_BASE`，`AxDataClient()` 会默认使用 API 模式。需要在这种环境里强制使用本地模式时，可以使用 `AxDataClient.local(...)` 或 `mode="local"`。

## 数据源请求

`client.call(...)` 用于临时请求数据源接口，默认不写入本地数据目录：

```python
quote = client.call(
    "stock_realtime_snapshot_tdx",
    code="000001.SZ",
    fields=["instrument_id", "last_price", "change_pct"],
)

finance = client.call("stock_finance_summary_tdx", code="000001.SZ")
```

数据源请求和采集入库是两层能力：

- Source Provider 负责临时请求源端接口。
- Collector 负责把数据写成本地 Parquet/DuckDB 可查询资产。

因此，能通过 `client.call(...)` 请求的接口，不等于已经有对应的长期入库采集任务。

## 常用入口

```python
client = ax.AxDataClient()
local = ax.AxDataClient.local(data_root="/data/axdata/current")
remote = ax.AxDataClient.api(api_base="http://192.168.1.20:8666", token=None)
```

常用方法：

- `client.query(api_name, fields=None, **params)`
- `client.daily(fields=None, **params)`
- `client.adj_factor(fields=None, **params)`
- `client.trade_cal(fields=None, **params)`
- `client.stock_basic_exchange(fields=None, **params)`
- `client.call(interface, fields=None, options=None, **params)`
- `client.stream(stream, fields=None, **params)`
- `client.session(source="tdx" | "tdx_ext", **options)`
- `ax.pro_api(...)`
- `ax.download(...)`
- `ax.get(...)`

所有查询和数据源请求默认返回 `pandas.DataFrame`。

## 完整项目

如果需要 Web 控制台、接口文档、插件管理页面、API 服务和源码开发环境，请使用完整项目安装方式：

```bash
git clone https://github.com/electkismet/AxData.git AxData
```

完整安装说明见项目文档：

<https://electkismet.github.io/AxData/>

## 使用声明

本项目仅是一个开源量化数据库框架，数据接口部分基于互联网公开信息搜集整理。项目不提供商业数据服务，也不代表任何第三方数据源、网站或开源项目的授权。

通过本项目访问或获取第三方数据时，用户需自行遵守相关法律法规、数据源条款、网站规则和服务协议。
