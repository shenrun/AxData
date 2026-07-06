# API 设计

AxData 面向本地研究、局域网共享和云端发布保持同一套数据语义。Python SDK 是用户主入口：默认在本机直读 AxData 数据目录，通过 Parquet/DuckDB 查询已入库数据；也可以对支持的源接口做一次性源端直取。传入 `api_base` 时切换为远程 HTTP API 通道，读取或请求目标 AxData 服务的数据。HTTP API 是通道，不是另一套产品协议，主要服务 Web 控制台、局域网/云端共享和跨语言客户端。

## 接口风格

- 版本前缀：HTTP 稳定接口使用 `/v1`；SDK 方法名与 HTTP 通道保持同一数据语义，不要求每个便捷方法都有独立 HTTP 资源。
- 数据格式：请求默认 JSON，响应默认 JSON；大结果可选择 `arrow`、`csv` 或 `parquet`。
- 日期格式：量化接口默认使用 `YYYYMMDD`，例如 `20240102`；HTTP API 会兼容 `YYYY-MM-DD` 并在查询前转成 `YYYYMMDD`。
- 代码格式：外部统一使用 `000001.SZ`、`600000.SH`、`430047.BJ`。
- 字段选择：所有数据查询都支持 `fields`，减少传输量。
- 单个/批量参数：对代码、范围、名称这类支持批量的筛选参数，单个值传字符串，批量值传列表；页面调试和 HTTP JSON 也可用英文逗号分隔字符串。
- 分页：列表接口使用 `limit + cursor`，批量导出接口使用异步任务。
- 幂等：查询和源端直取都无写入副作用；采集和管理能力使用明确的管理端点。
- 查询边界：`query` 只读已入库的 core/factor 数据，不在查询链路临时请求第三方源。
- 直取边界：`request` 或 SDK `call` 会临时请求源端，返回 AxData 字段，默认不写入数据目录。

## 接口类型

AxData 把“读库”和“问源端”显式分开，避免普通查询不小心触发源端请求或写入。

| 类型 | SDK 入口 | HTTP 入口 | 是否请求源端 | 是否入库 | 典型用途 |
| --- | --- | --- | --- | --- | --- |
| 表查询 | `client.query("daily", ...)` | `POST /v1/query` | 否 | 否 | 读本地或远端已入库数据 |
| SDK 便捷查询 | `client.stock_basic_exchange(...)` | `POST /v1/query` | 否 | 否 | 高频稳定表的 Python 简化写法，HTTP 通道保持统一 |
| 源端直取 | `client.call("stock_codes_tdx", ...)` | `POST /v1/request/stock_codes_tdx` | 是 | 否 | 先用 TDX 代码表打通字段、解析、连接管理和源端预览 |
| 实时订阅 | 本地：`client.stream("your_stream", ...)`；远程：同方法带 `api_base` | `WS /v1/stream/your_stream` | 是 | 否 | 本地 SDK 可在进程内订阅支持的 TDX 流；远程 SDK、浏览器和跨语言客户端走 WebSocket |
| 高频源端会话 | `client.session(source="tdx" \| "tdx_ext", ...)` | 暂无远程状态会话 | 是 | 否 | 本机高频 request 复用 TDX/TDX_EXT provider adapter 和长连接池 |
| 采集入库 | CLI、`client.download(...)` 或 Collector API | `/v1/download/*`、`/v1/collector/tasks` + `/v1/collector/runs` | 是 | 是 | 显式写入 raw/staging/core/factor |
| 实时录制 | 暂未开放稳定后台任务 | 暂未开放稳定录制 API | 是 | 是 | 显式把 tick、盘口或快照流落盘；当前不是稳定用户入口 |

## 代码、交易所与接口口径

用户侧优先使用 AxData 统一代码、接口口径和字段，不直接使用上游原始列名。股票列表按接口口径分开暴露：接口名本身就是数据口径。

| 概念 | 字段或写法 | 说明 |
| --- | --- | --- |
| 股票列表（交易所） | `stock_basic_exchange` | 交易所股票列表口径，是股票主数据的默认用户入口 |
| 统一证券代码 | `instrument_id=600000.SH` | 股票主数据的唯一代码，后缀已经表达上市交易所 |
| 交易所筛选 | `exchange=SSE` | 用于按交易所过滤；`SSE`=上交所，`SZSE`=深交所，`BSE`=北交所 |
| 代码后缀 | `.SH` / `.SZ` / `.BJ` | 只出现在 `instrument_id` 里；通常分别对应 `SSE` / `SZSE` / `BSE` |
| 原始证券代码 | `symbol=600000` | 交易所原始代码，不带后缀；跨交易所调用时不如 `instrument_id` 稳妥 |

因此，查询一只股票时优先传 `instrument_id=600000.SH`；批量查询某个交易所时传 `exchange=SSE`。需要新增口径时，用新的接口名显式表达。

Web 源端接口目录由 Provider manifest / Registry 的 `menu_path` 生成，Web 只做通用渲染，不把具体数据源的接口树写死在前端。目录一级按数据源组织，例如通达信、交易所、东方财富、巨潮、腾讯财经、新浪财经。通达信这类大数据源由插件在 `menu_path` 中继续声明源内分层：股票数据、指数数据、ETF 数据，再细分实时数据、短线数据、行情数据、竞价数据、财务数据、F10 数据等；其它数据源可按 `数据源 / category` 展示。搜索和详情页仍保留数据源、资产类型和业务类别。当前 `stock_codes_tdx` 公开返回字段只保留 `instrument_id`、`symbol`、`tdx_code`、`exchange`、`name`、`market`；源端特色字段按接口需要逐个加入。

通达信 7709 代码表本身主要返回市场、代码、名称和少量行情辅助字段，不直接给出完整资产类别。当前 `stock_codes_tdx` 只按 full_code 前缀筛出股票类和 CDR，并把板块归到主板、科创板、创业板、北交所或 CDR；底层分类原因只服务解析和测试，不作为公开返回字段。如需更精细分类，可引入 TDX 分类榜、板块文件或更多协议接口做交叉校验。

## 调用方式

稳定用户入口是 Python SDK。HTTP API 是远程通道；本机脚本和 Notebook 不应为了取本机数据而强依赖本地 HTTP 服务。

| 入口类别 | 访问场景 | 示例 | 读的是哪里 | 说明 |
| --- | --- | --- | --- | --- |
| Python SDK | 本地默认 | `AxDataClient()` | 当前机器的 AxData 数据目录 | 默认本地直读 Parquet/DuckDB；适合 Notebook、脚本、回测和因子研究 |
| Python SDK | 指定本地目录 | `AxDataClient(data_root="~/axdata/data")` | 指定目录里的 AxData Parquet 数据 | 用于多数据根、本地快照或测试数据集 |
| Python SDK | 远程 API | `AxDataClient(api_base="http://<AxData机器内网IP>:8666")` | `api_base` 指向的 AxData 服务 | 通过 HTTP 通道访问局域网或云端数据；方法和字段语义不变 |
| Python SDK | 源端直取 | `client.call("stock_codes_tdx", scope="all")` | 当前机器或远端服务可访问的数据源 | 临时请求源端，返回 AxData 字段，默认不入库 |
| HTTP API | 本机调试 | `POST http://127.0.0.1:8666/v1/query` | 当前这台 API 服务配置的数据目录 | 主要用于本机 Web、curl、跨语言客户端和接口调试 |
| HTTP API | 局域网/云端 | `POST http://<AxData服务地址>:8666/v1/query` | 服务端配置的数据目录或对象存储 | 其他设备不直接访问数据文件，只通过通道读取 |
| HTTP API | 源端直取 | `POST /v1/request/stock_codes_tdx` | 当前 API 服务可访问的数据源 | Web 调试、跨语言和远程源端直取通道 |
| Web 控制台 | 本机管理页面 | `http://127.0.0.1:8667` | 本机 AxData API | 查看接口说明、字段说明、数据状态、插件和采集任务；不提供远程 Web 入口 |
| CLI | 采集入库 | `axdata collector task add ...` / `axdata collector task run ...` | 写入命令配置的数据目录 | 采集是写入动作，会产生任务、运行和质量元数据；不是普通查询 |
| CLI/SDK 管理 | 源端预览 | adapter probe/debug | 不入库 | 只用于排查源是否可用，不进入 core 查询结果 |

SDK 连接选择规则：

- 未传 `api_base` 且未设置 `AXDATA_API_BASE`：使用本地模式，表查询直读 `data_root` 指向的数据目录；源端直取由本机 adapter 请求源端。
- 显式传入 `api_base` 或设置 `AXDATA_API_BASE`：使用远程模式，经 HTTP API 读取目标服务数据。
- 本地模式的 `client.stream("stock_quote_refresh_tdx", ...)` 不需要启动 AxData API 后端；它在当前 Python 进程内复用 TDX 本地 adapter 和长连接。
- 远程模式的 `client.stream(...)` 继续走 `WS /v1/stream/{stream}`，由 `api_base` 指向的服务端持有源端连接。
- 高频轮询实时快照、榜单、盘口或 TDX_EXT 扩展行情时，使用 `client.session(source="tdx" | "tdx_ext", ...)`，不要在热循环里反复创建普通 `client.call(...)` 短连接。
- 本地模式不需要 AxData HTTP token；远程模式按目标服务要求携带 AxData token。

采集、查询与实时的边界：

- 采集：从 adapter 拉取数据并写入 raw/staging/core/factor，必须在 metadata/manifest 记录 task、batch、run、时间范围、参数和质量结果。
- 查询：只读取已经入库的数据，返回稳定 AxData schema。
- 源端直取：立即请求源端并返回稳定 AxData schema，默认不写入任何数据层；普通非实时直取不启用心跳保活。
- 实时：快照、订阅和盘中流默认不入库；心跳和常驻连接只属于实时/长连接场景；需要持久化时必须显式启动实时录制或采集任务，并写入独立批次，避免临时行情污染历史事实表。

## Local Status API

本地状态诊断端点用于 Web、curl 和脚本排查当前 AxData 运行环境，不触发真实源请求，也不安装或启用插件。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/v1/status` | 本地环境诊断汇总，包含路径、依赖、插件、端口和 Collector 摘要 |
| `GET` | `/v1/doctor` | `/v1/status` 的诊断别名 |

## Plugin Management API

插件管理 API 只管理当前 AxData runtime 的插件状态，不删除用户数据。AxData Core 是数据库、插件容器、任务平台、存储、查询、API、Web 和 CLI 宿主，不是数据源，也不能通过插件管理卸载。随 AxData 提供的数据源以预装插件呈现；外部插件可来自 AXP、pip 或 editable/development 路径。

已实现端点：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/v1/plugins/providers` | 列出已发现 Provider，包含安装来源、生命周期状态、启停/卸载能力和下一步动作 |
| `GET` | `/v1/plugins/installed` | 列出 AxData 管理安装记录 |
| `GET` | `/v1/plugins/axp/export/{provider_id}` | 导出一个已发现插件的 `.axp` 安装包；`provider_id` 也可对应 collector-only 插件身份 |
| `POST` | `/v1/plugins/providers/{provider_id}/enable` | 启用 Provider |
| `POST` | `/v1/plugins/providers/{provider_id}/disable` | 禁用 Provider |
| `DELETE` | `/v1/plugins/installed/{provider_id}` | 卸载 AxData 管理或预装插件 |
| `POST` | `/v1/plugins/installed/{provider_id}/uninstall` | 卸载 AxData 管理或预装插件，支持 `disable_first=true` |

Provider payload 会返回 `install_source`、`provider_kind`、`lifecycle_status`、`can_enable`、`can_disable`、`can_uninstall`、`uninstall_mode` 和 `uninstall_block_reason`。预装源插件返回 `install_source=preinstalled`，可启用、禁用、逻辑卸载和重新启用；当前预装卸载使用 `uninstall_mode=managed_disable`，会隐藏插件贡献的 interfaces、downloaders、collectors 和 task templates，但不物理删除随包代码。AXP 管理插件可物理移除；Python 环境或 editable/development 路径发现的非预装插件需要用 `pip uninstall` 或移除开发路径。

AXP 导出接口返回 `application/octet-stream` 文件下载，只包含插件 manifest、wheel、README 和 checksum。它不导出本地 `data/`、metadata 数据库、任务历史、run history、logs、cache、API token 或第三方数据源凭据。AXP 是分发和安装单位；导入后仍由 manifest 里的 `provider`、`interfaces`、`collectors` 等字段决定进入 ProviderRegistry 还是 CollectorRegistry。

卸载任何插件都不得删除 `data/`、已采集 Parquet、metadata、用户 Task 或 Run History。已有 Task 保留为本地配置；若依赖插件被禁用、缺失或卸载，Task 的 `dependency_status` 会刷新为 `disabled`、`missing` 或 `uninstalled`，不可运行但仍可查看历史。Run History 是历史事实，插件状态变化不会回写删除既有 run。

## Collector Task API

当前单机调度使用 `/v1/collector/*` 管理 Collector task 和 run。该接口是本地管理 API，
用于 Web 控制台、CLI 和脚本自动化；它不做分布式调度或云端任务工作进程管理。

已实现端点：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/v1/collector/tasks/templates` | 列出当前可用 task template，包含默认参数、安全边界、可用性和下一步动作 |
| `GET` | `/v1/collector/tasks/templates/{template_id}` | 查看单个 task template |
| `POST` | `/v1/collector/tasks/from-template` | 从当前可用 task template 创建 Collector task |
| `GET` | `/v1/collector/tasks` | 列出 Collector task |
| `POST` | `/v1/collector/tasks` | 创建 Collector task |
| `GET` | `/v1/collector/tasks/{task_id}` | 获取单个 task |
| `PATCH` | `/v1/collector/tasks/{task_id}` | 更新 task 配置 |
| `POST` | `/v1/collector/tasks/{task_id}/run` | 手动提交一次 run，返回 `run_id`；支持本次参数覆盖 |
| `POST` | `/v1/collector/tasks/{task_id}/backfill` | 按日期区间提交一次 backfill run |
| `POST` | `/v1/collector/tasks/{task_id}/enable` | 启用 task |
| `POST` | `/v1/collector/tasks/{task_id}/disable` | 禁用 task |
| `GET` | `/v1/collector/runs` | 列出 run history，支持 `task_id`、`status_filter`、`limit` |
| `GET` | `/v1/collector/runs/{run_id}` | 获取单个 run |
| `DELETE` | `/v1/collector/runs/{run_id}` | 删除一条已结束的 run history；只清除历史记录，不删除任务配置或已采集数据。 |
| `GET` | `/v1/collector/tasks/{task_id}/runs` | 获取单个 task 的 run history |
| `GET` | `/v1/runs` | `/v1/collector/runs` 的轻量别名 |
| `GET` | `/v1/runs/{run_id}` | `/v1/collector/runs/{run_id}` 的轻量别名 |
| `DELETE` | `/v1/runs/{run_id}` | `/v1/collector/runs/{run_id}` 的轻量别名 |
| `GET` | `/v1/tasks/{task_id}/runs` | `/v1/collector/tasks/{task_id}/runs` 的轻量别名 |
| `GET` | `/v1/collector/status` | 获取 task/run 汇总、active runs 和每个 task 最近 run |

`/v1/tasks/templates`、`/v1/tasks/from-template`、`/v1/tasks`、`/v1/tasks/{task_id}`、`/v1/tasks/{task_id}/run`、`/v1/tasks/{task_id}/backfill` 是同语义别名；run history 主路径仍是 `/v1/collector/runs`，轻量别名用于脚本和 Web run detail。

Task 创建示例：

```json
{
  "collector_name": "demo.daily.refresh",
  "task_id": "daily_refresh",
  "name": "每日行情刷新",
  "enabled": true,
  "trigger_type": "daily",
  "daily_time": "18:00",
  "params": {"start_date": "20260101"},
  "fields": ["ts_code", "trade_date", "close"],
  "formats": ["parquet"]
}
```

CLI 创建同类 task：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task add demo.daily.refresh `
  --task-id daily_refresh `
  --trigger-type daily `
  --daily-time 18:00 `
  --params '{\"start_date\":\"20260101\"}' `
  --fields ts_code,trade_date,close `
  --formats parquet `
  --json
```

运行与查看：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task run daily_refresh --wait --json
.\.venv\Scripts\python -m axdata_core.cli collector task backfill daily_refresh --start 20240101 --end 20240131 --symbol 000001.SZ --limit 20 --wait --json
.\.venv\Scripts\python -m axdata_core.cli collector run list --json
.\.venv\Scripts\python -m axdata_core.cli collector run info <run_id> --json
.\.venv\Scripts\python -m axdata_core.cli collector status --json
```

Run 状态枚举：

```text
pending / queued / running / success / failed / skipped / cancelled
```

重复运行和失败退避会生成 `skipped` run，并通过 `skip_reason` 区分，例如 `active_duplicate`、
`task_disabled`、`failure_backoff`。失败 run 会记录 `error`，需要退避时记录 `backoff_until`。
当前取消为状态标记，不保证强杀已经开始执行的底层线程。

Run history 列表是最近窗口接口，不是完整历史导出。API 默认返回最近 100 条，单次最多 500 条；CLI `collector run list` 同样有上限。`/v1/collector/status` 只返回最近窗口计数、`total_run_count`、`status_counts`、active runs 和每个 task 的 latest run，避免 run metadata 很多时状态页把完整 JSON store 序列化给前端。需要排查单次运行时使用 `GET /v1/collector/runs/{run_id}` 查看 detail。

Task/run payload 会补充 `next_run_at`、`last_success_at`、`last_failure_at`、`last_error_summary`、
`retry_count`、`backoff_until`、`resource_group`、`queue_status`、`can_run_now`、`blocked_reason`、
`next_action` 和 `action_command`。本次 run 参数覆盖写入 `params_override`；backfill 会把日期范围写入
`metadata.backfill_range`。Run detail 还会返回 `events`、`stage_timings`、`error_category` 和
`error_summary`，用于判断失败是 provider/plugin/params/network/upstream/schema/write/quality/storage
还是 skip/backoff/resource 等类型。这些字段用于 CLI/API/Web 状态展示，不代表分布式任务系统或跨进程锁已经实现。
Downloader 写入完成后，run detail/result 还会透传 `write_mode`、`partition_by`、`primary_key`、`date_field`、
`replace_range_start/end`、`rows_before/written/after`、`duplicate_rows_dropped`、`partitions_touched`
和嵌套 `write_metadata`。这些字段描述本地 Parquet 写入语义，不新增 API 资源；旧 run 缺字段时按空值处理。

Task payload 还会返回依赖状态：`required_datasets` 表示任务运行前必须满足的系统基础数据，例如 `trade_cal`；`dependency_status=ok` 表示插件和基础数据依赖都可用，`blocked` 表示基础数据缺失或覆盖不足，`disabled` 表示依赖插件已禁用，`missing` 表示依赖插件未发现或环境损坏，`uninstalled` 表示预装插件已被当前 runtime 逻辑卸载。缺失基础数据时 payload 会带 `dependency_errors`、`next_action` 和 `action_command`，例如提示“交易日历未同步，请先同步基础数据：交易日历。”或“交易日历未覆盖 20260101-20260131，请先补全指定范围。”`blocked` / `disabled` / `missing` / `uninstalled` 的 task 可以保留、查看、修改和重新绑定，但 run now 会生成清晰失败 run，例如 `dependency_missing`、`plugin_disabled` 或 `provider_missing`，不会静默删除 task 或 run history。

Run detail 响应中的诊断字段示例：

```json
{
  "run_id": "run_20260629T010203Z_abcd1234",
  "status": "failed",
  "error_category": "storage_permission",
  "error_summary": "access is denied",
  "stage_timings": {
    "queue_wait_ms": 12,
    "params_resolve_ms": 0,
    "provider_resolve_ms": 4,
    "download_ms": null,
    "write_ms": null,
    "quality_ms": null,
    "total_ms": 37
  },
  "events": [
    {"sequence": 1, "stage": "queued", "level": "info", "message": "Collector run queued."},
    {"sequence": 2, "stage": "failed", "level": "error", "category": "storage_permission", "message": "access is denied"}
  ],
  "next_action": "检查 output_root/output_dir 是否存在、可写，以及目标文件是否被占用。",
  "action_command": "axdata collector run info run_20260629T010203Z_abcd1234 --json"
}
```

Python SDK 示例：

```python
import axdata as ax

client = ax.AxDataClient()
stocks = client.stock_basic_exchange(exchange="SSE", fields=["instrument_id", "name", "list_date"])
preview = client.call(
    "stock_codes_tdx",
    code=["000001.SZ", "600000.SH"],
)
quote = client.call(
    "stock_realtime_snapshot_tdx",
    code="000001.SZ",
    fields=["instrument_id", "last_price", "change_pct"],
)
with client.session(source="tdx", source_server_count=4, connections_per_server=2) as session:
    snapshot = session.call("stock_realtime_snapshot_tdx", code=["000001.SZ", "600000.SH"])
    rank = session.call("stock_realtime_rank_tdx", category="a_share")
with client.stream("stock_quote_refresh_tdx", code=["000001.SZ"]) as stream:
    for event in stream:
        print(event.type, event.data)
index_bars = client.call(
    "index_kline_tdx",
    code="000001.SH",
    period="day",
    count=20,
    fields=["instrument_id", "trade_time", "close"],
)
intraday = client.call("stock_intraday_today_tdx", code="000001.SZ")
recent_intraday = client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")
index_intraday = client.call("index_intraday_history_tdx", code="000001.SH", trade_date="20260617")
etf_trades = client.call("etf_trades_today_tdx", code="510050.SH")
trades = client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")
finance = client.call("stock_finance_summary_tdx", code="000001.SZ")

remote = ax.AxDataClient(api_base="http://192.168.1.20:8666")
bars = remote.daily(ts_code="000001.SZ", start_date="20240101", end_date="20240131")
with remote.stream("stock_quote_refresh_tdx", code=["000001.SZ"]) as stream:
    for event in stream:
        print(event.type, event.data)
```

CLI 源端直取示例：

```powershell
.\.venv\Scripts\axdata request stock_realtime_snapshot_tdx `
  --param code=000001.SZ `
  --fields instrument_id,last_price,change_pct `
  --json

.\.venv\Scripts\axdata request stock_intraday_history_tdx `
  --params '{\"code\":\"000001.SZ\",\"trade_date\":\"20260519\"}' `
  --fields instrument_id,trade_time,price `
  --json

.\.venv\Scripts\axdata request index_intraday_history_tdx `
  --params '{\"code\":\"000001.SH\",\"trade_date\":\"20260617\"}' `
  --fields instrument_id,trade_time,price `
  --json

.\.venv\Scripts\axdata request etf_trades_today_tdx `
  --params '{\"code\":\"510050.SH\"}' `
  --fields instrument_id,trade_time,price `
  --json

.\.venv\Scripts\axdata request etf_realtime_rank_tdx `
  --params '{\"sort\":\"change_pct\",\"count\":5}' `
  --json
```

这些调用都是 `source_request`：默认 `persist=false`，只做临时源端小样本查询，不写入 `raw/staging/core/factor`，也不会自动创建 Collector task 或 task template。当前已补齐调用体验的 source-only 小样本包括第一批的实时快照、榜单、盘口、指数/ETF K 线和概念成分，第二批的股票分时、逐笔、竞价、财务摘要和指数/ETF 榜单，以及第三批的近期分时、副图、历史竞价、指数分时和 ETF 分时/成交明细接口。TDX Provider 禁用或缺失时，API/CLI/SDK 错误会提示检查 `axdata.source.tdx_external`。

## 响应包络

成功响应：

```json
{
  "data": [
    {
      "ts_code": "000001.SZ",
      "trade_date": "20240102",
      "open": 9.39,
      "close": 9.21
    }
  ],
  "schema": [
    {"name": "ts_code", "type": "string"},
    {"name": "trade_date", "type": "date"},
    {"name": "open", "type": "double"},
    {"name": "close", "type": "double"}
  ],
  "meta": {
    "request_id": "req_01J00000000000000000000000",
    "table": "daily",
    "count": 1,
    "next_cursor": null,
    "data_version": "core.daily.v1"
  }
}
```

## 通用查询接口

`POST /v1/query`

请求：

```json
{
  "table": "daily",
  "fields": ["ts_code", "trade_date", "open", "high", "low", "close"],
  "filters": {
    "ts_code": "000001.SZ"
  },
  "start_date": "20240101",
  "end_date": "20240131",
  "limit": 1000,
  "params": {}
}
```

响应：

```json
{
  "data": [
    {
      "ts_code": "000001.SZ",
      "trade_date": "20240102",
      "open": 9.39,
      "high": 9.42,
      "low": 9.15,
      "close": 9.21
    }
  ],
  "schema": [
    {"name": "ts_code", "type": "string"},
    {"name": "trade_date", "type": "date"},
    {"name": "open", "type": "double"},
    {"name": "high", "type": "double"},
    {"name": "low", "type": "double"},
    {"name": "close", "type": "double"}
  ],
  "meta": {
    "request_id": "req_01J00000000000000000000001",
    "table": "daily",
    "count": 1,
    "next_cursor": null
  }
}
```

当前实现支持 `filters` 精确匹配和 `start_date/end_date` 日期范围。扩展查询可继续增加 `where` 操作：

| 操作 | 示例 | 说明 |
| --- | --- | --- |
| `eq` | `{"ts_code": {"eq": "000001.SZ"}}` | 等于 |
| `in` | `{"ts_code": {"in": ["000001.SZ", "600000.SH"]}}` | 列表匹配 |
| `between` | `{"trade_date": {"between": ["20240101", "20240131"]}}` | 闭区间 |
| `gte` / `lte` | `{"trade_date": {"gte": "20240101"}}` | 单侧范围 |
| `is_null` | `{"delist_date": {"is_null": true}}` | 空值判断 |

## 本地数据浏览接口

Data Browser 接口用于回答“本机已经采集了哪些数据”，只读本地 metadata 和 Parquet，不请求源端，也不执行任意 SQL。当前优先从最近 `CollectorRun.output_paths`、`CollectorRun.quality`、写入 metadata 和 Downloader `logs/*.json` 发现 dataset；缺失时补充检查已知 core 表路径。列表和详情只返回已有本地数据实例的 dataset：单纯来自插件 manifest、CollectorSpec、`queryable=true` 或预期 `storage_path` 的声明，不能出现在 `/v1/data/datasets`。列表和详情优先使用 run/downloader metadata；metadata 不足时只读 Parquet footer/schema metadata 补行数和列，不对大 Parquet 做 `COUNT(*)`。目录型 Parquet 的 footer 统计有文件数和目录数上限；超过上限时响应 metadata 会标记统计受限，并避免返回误导性的精确行数。

已实现端点：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/v1/data/datasets` | 列出本地 dataset，包含 interface、provider/source、layer、output_paths、row_count、日期范围、columns、quality、write metadata、latest_run。 |
| `GET` | `/v1/data/datasets/{dataset}` | 查看单个 dataset 的 metadata、quality、写入策略、字段和输出路径。 |
| `GET` | `/v1/data/datasets/{dataset}/preview` | 对 dataset 的 Parquet 输出做小范围预览查询。 |
| `DELETE` | `/v1/data/datasets/{dataset}` | 删除该 dataset 在 AxData 数据根目录下的本地数据集目录、相关运行记录和日志引用；不删除 Collector 任务配置。 |

Preview 参数：

| 参数 | 说明 |
| --- | --- |
| `fields` | 逗号分隔字段列表。 |
| `symbol` | 自动匹配 `ts_code`、`instrument_id`、`symbol` 或 `code` 中存在的字段。 |
| `start` / `end` | 日期范围，兼容 `YYYYMMDD` 和 `YYYY-MM-DD`。 |
| `filter` | `key=value` 精确过滤，可重复；也可传 JSON object 字符串。 |
| `limit` | 默认 3，最大 100；超过上限会被截断到 100。 |

示例：

```powershell
curl http://127.0.0.1:8666/v1/data/datasets
curl http://127.0.0.1:8666/v1/data/datasets/daily
curl "http://127.0.0.1:8666/v1/data/datasets/daily/preview?symbol=000001.SZ&start=20240101&end=20240131&limit=20"
```

缺数据时返回空列表和空状态说明；run metadata 指向的文件不存在时，inspect 会显示 `missing_paths`，preview 会返回可读错误，提示重新采集或检查 run metadata。

Dataset list/detail 会在有记录时返回 `write_mode`、`partition_by`、`primary_key`、`date_field`、
`replace_range_start`、`replace_range_end`、`rows_before`、`rows_written`、`rows_after`、
`duplicate_rows_dropped` 和 `partitions_touched`。这些字段兼容旧 metadata：缺失时为 `null` 或空数组。

Preview/query 始终带 limit，Data Browser 单次最多返回 100 行。目录型 dataset 如果存在 `YYYYMMDD.parquet` 日期文件或旧的 `trade_date=...` 日期分区，preview 会按 `start/end` 裁剪到匹配文件/分区；core 表如果按 schema 日期字段拆文件，`start/end` 也会尽量裁剪到匹配路径。没有匹配日期文件或分区时返回空结果而不是回退扫描全表。

## 常用表查询示例

日行情、交易日历、股票列表这类已入库数据都通过 `POST /v1/query` 读取。SDK 里的
`daily()`、`trade_cal()`、`stock_basic_exchange()` 只是 Python 便捷方法，远程模式也会发送到同一个 HTTP 入口。

日行情请求：

```json
{
  "table": "daily",
  "fields": ["ts_code", "trade_date", "open", "close", "vol", "amount"],
  "params": {
    "ts_code": "000001.SZ",
    "start_date": "20240101",
    "end_date": "20240131"
  },
  "limit": 1000
}
```

响应：

```json
{
  "data": [
    {
      "ts_code": "000001.SZ",
      "trade_date": "20240102",
      "open": 9.39,
      "close": 9.21,
      "vol": 412345.67,
      "amount": 381234.56
    }
  ],
  "schema": [
    {"name": "ts_code", "type": "string"},
    {"name": "trade_date", "type": "date"},
    {"name": "open", "type": "double"},
    {"name": "close", "type": "double"},
    {"name": "vol", "type": "double"},
    {"name": "amount", "type": "double"}
  ],
  "meta": {
    "request_id": "req_01J00000000000000000000002",
    "table": "daily",
    "count": 1,
    "adjust": "none"
  }
}
```

复权参数：

- `adjust=none`：默认，返回未复权价格。
- `adjust=qfq`：前复权视图，由 `daily + adj_factor` 计算。
- `adjust=hfq`：后复权视图，由 `daily + adj_factor` 计算。

交易日历请求：

```json
{
  "table": "trade_cal",
  "fields": ["exchange", "cal_date", "is_open", "pretrade_date"],
  "params": {
    "exchange": "SSE",
    "start_date": "20240101",
    "end_date": "20240110"
  },
  "limit": 1000
}
```

响应：

```json
{
  "data": [
    {
      "exchange": "SSE",
      "cal_date": "20240102",
      "is_open": true,
      "pretrade_date": "2023-12-29"
    }
  ],
  "schema": [
    {"name": "exchange", "type": "string"},
    {"name": "cal_date", "type": "date"},
    {"name": "is_open", "type": "boolean"},
    {"name": "pretrade_date", "type": "date"}
  ],
  "meta": {
    "request_id": "req_01J00000000000000000000003",
    "table": "trade_cal",
    "count": 1
  }
}
```

## AxData 字段契约

AxData 可以借鉴 Tushare/RQData 这类平台的调用手感，例如统一入口、参数字典和 `fields` 字段选择，但 core/API 字段名是 AxData 自己的稳定契约，不暴露交易所原始列名，也不承诺兼容任何第三方平台字段名。

以 `stock_basic_exchange` 为例，用户侧使用：

```json
{
  "table": "stock_basic_exchange",
  "fields": ["instrument_id", "name", "industry", "list_date"],
  "params": {"exchange": "SZSE"},
  "limit": 1000
}
```

不使用 `agdm`、`A_STOCK_CODE`、`list_status` 等上游或第三方字段名。上游原始字段只保留在 raw/staging 和采集 manifest 中，由采集与转换层整理为对应接口的 AxData schema。

## Token 策略

AxData token 与第三方数据源 token 分离。

本地模式：

- 默认只监听 `127.0.0.1`。
- 开发环境可允许无 token 访问。
- 如果设置 `AXDATA_API_TOKEN`，所有 HTTP 请求必须携带 `Authorization: Bearer <token>`。
- 也可以在 Web 控制台或 `/v1/auth/tokens` 创建多个命名 token；token 保存在本机 `metadata/api_tokens.json`，Web 默认隐藏、点击显示。默认监听 `127.0.0.1` 时本机访问不需要 token；远程监听或显式强制鉴权时，API 进入 token 鉴权模式。Web 控制台只作为本机管理台，不提供远程 Web 入口；远程设备应使用 SDK/API 和 token。

局域网模式：

- 必须开启 AxData token。
- token 只代表 AxData 用户或应用，不代表 Tushare、RQData 等第三方账号。
- 当前实现支持多个命名 token、最近使用时间和删除，适合一台设备或一个脚本一个 token。
- 可继续扩展 `data:read`、`metadata:read`、`admin:write` 等作用域，并增加过期时间和更细访问记录。

云端模式：

- 使用短期 access token 和可轮换 refresh token。
- 支持服务账号、用户账号、访问日志、IP 限制和速率限制。
- 第三方源凭据由对应 Provider 和部署环境自行处理；AxData API 不托管、不注入、不代理源凭据，且源凭据不得进入请求、响应、日志或导出文件。

## 错误格式

错误响应统一使用：

```json
{
  "error": {
    "code": "invalid_request",
    "message": "start_date must be before or equal to end_date",
    "details": {
      "field": "start_date",
      "start_date": "20240201",
      "end_date": "20240101"
    }
  },
  "meta": {
    "request_id": "req_01J00000000000000000000004",
    "trace_id": "trace_01J00000000000000000000005"
  }
}
```

错误码：

| HTTP 状态 | code | 场景 |
| --- | --- | --- |
| 400 | `invalid_request` | 参数格式错误、日期范围错误、字段不存在 |
| 401 | `unauthorized` | 缺失 token 或 token 无效 |
| 403 | `forbidden` | token 无对应作用域 |
| 404 | `not_found` | 表、字段、标的或分区不存在 |
| 409 | `schema_conflict` | 请求字段与 schema 版本冲突 |
| 422 | `data_not_ready` | 数据尚未采集或质量检查未通过 |
| 429 | `rate_limited` | 超过 AxData 限流 |
| 502 | `upstream_unavailable` | 源数据服务不可用 |
| 500 | `internal_error` | 未分类服务端错误 |

## 版本与兼容

- `/v1` 中字段只做向后兼容新增。
- 字段语义、单位或类型改变必须进入新字段或新版本。
- 响应 `meta.data_version` 标明数据表版本，不等同于 API 版本。
- Python SDK 只暴露稳定表名、字段名和方法名；本地直读实现不得把 DuckDB 实现细节泄露为用户契约。
- 旧 `stock_basic` 名称在兼容期作为 `stock_basic_exchange` 的别名保留；新代码和文档应使用 `stock_basic_exchange`。
