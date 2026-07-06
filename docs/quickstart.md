# AxData 快速开始

本文介绍 AxData 的本地安装、启动和常用入口。优先推荐完整项目安装，它包含 Python SDK、CLI、API 和 Web 控制台；只在脚本或 Notebook 中使用 SDK 时，也可以直接 `pip install axdata`。Windows 使用 PowerShell 命令，macOS/Linux 使用 Bash 命令。想写新插件时，直接跳到 [plugin-development.md](plugin-development.md)。

## 0. 完整项目和 Web 控制台

运行下面一行命令即可拉取完整项目并安装本地开发环境。

Windows PowerShell：

```powershell
git clone https://github.com/electkismet/AxData.git AxData; cd AxData; powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

macOS / Linux：

```bash
git clone https://github.com/electkismet/AxData.git AxData && cd AxData && bash scripts/bootstrap.sh
```

这条命令会拉取完整项目、创建 `.venv`、安装本地 Python 包和 Web 依赖。

运行完整项目需要本机具备 3 个运行环境：Git 用来下载源码，Python 3.11+ 用来运行 SDK/API，Node.js 22.12+ 或更新 LTS 用来运行 Web 控制台。

常见环境安装方式如下。

Windows PowerShell：

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
```

macOS Homebrew：

```bash
brew install git python@3.12 node
```

Ubuntu / Debian：

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip curl ca-certificates
```

Ubuntu / Debian 自带的 `nodejs` 版本可能偏旧；如果 `node --version` 低于 `22.12`，请从 Node.js 官网、NodeSource、nvm/fnm 或系统软件源安装更新的 Node.js。

安装完成后重新打开终端，确认命令可用：

```powershell
git --version
python --version
node --version
npm --version
```

启动 API。

Windows PowerShell：

```powershell
.\.venv\Scripts\python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8666 --reload
```

macOS / Linux：

```bash
./.venv/bin/python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8666 --reload
```

启动 Web：

```powershell
npm run dev:web
```

打开 Web 控制台：

```text
http://127.0.0.1:8667
```

## 1. Python 包安装

只需要 Python SDK/CLI 时，可以直接安装 `axdata` 包：

```powershell
pip install axdata
```

如果希望放在虚拟环境里：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install axdata
```

`axdata` 会安装 AxData SDK、CLI、本地查询能力和默认数据源能力。安装后可以直接在 Python 里用 SDK，也可以用 CLI 查看本机状态；不需要先启动 API 或 Web。

```powershell
axdata doctor
axdata plugin list
```

`axdata init` 只用于提前创建本地 `data/`、`metadata/`、`cache/`、`logs/` 等目录；SDK 本地查询、源端临时请求和 Web/API 启动会按需使用默认路径。

```python
import axdata as ax

client = ax.AxDataClient()
stocks = client.stock_basic_exchange(exchange="SSE", fields=["instrument_id", "name"])
```

## 2. 源码开发说明

完整项目安装完成后，可以查看插件和本机状态：

```powershell
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata doctor
```

随项目提供的 TDX/TDX Ext 插件安装后默认可用，不需要手动启用；也可以按需禁用。普通 TDX Provider 是 `axdata.source.tdx_external`，TDX Ext 扩展行情 Provider 是 `axdata.source.tdx_ext_external`。

源码开发时可运行轻量测试和离线检查：

```powershell
.\.venv\Scripts\python -m pytest tests\test_data_collection_loop.py -q
.\.venv\Scripts\python scripts\smoke_real_sources.py --json
```

写出本地 Parquet 后，可用 DuckDB 直接查：

```powershell
@'
import duckdb

con = duckdb.connect()
rows = con.execute("""
    SELECT *
    FROM read_parquet('data/core/table=daily/**/*.parquet', hive_partitioning = true)
    LIMIT 5
""").fetchall()
print(rows)
'@ | .\.venv\Scripts\python -
```

新仓库没有本地 core Parquet 时，DuckDB 查询会提示路径不存在；先运行 Collector/Downloader 或可选真实源 smoke 写出样本后再查。

如果不使用 bootstrap，也可以手动安装。最小源码开发命令如下：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pip install -e libs\axdata_core
.\.venv\Scripts\python -m pip install -e packages\axdata-sdk
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tencent
.\.venv\Scripts\python -m pip install -e packages\axdata-source-cninfo
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx-ext
npm install
```

TDX 能力来自独立插件包。普通 TDX Provider 是 `axdata.source.tdx_external`，TDX Ext 扩展行情 Provider 是 `axdata.source.tdx_ext_external`；两者独立安装，安装后默认可用，也可以按需禁用。未安装或被显式禁用时，Web/CLI/API 会在 Provider 状态里显示原因。

## 3. 源码启动 API 和 Web

本节面向已经 clone 仓库并完成源码开发安装的用户。只用 `pip install axdata` 安装 SDK/CLI 时，可以跳过本节。

启动前可以先跑一次诊断；`init` 只用于提前创建本地目录，不是 SDK 或 API 的强制前置步骤：

```powershell
.\.venv\Scripts\axdata init
.\.venv\Scripts\axdata config show
.\.venv\Scripts\axdata doctor
.\.venv\Scripts\axdata status
```

`init` 会幂等创建 `data/raw`、`data/staging`、`data/core`、`data/factor`、与 data root 同级的
`metadata/collector`、`plugins/site-packages`、`cache` 和 `logs`，并在缺失时写入默认
`metadata/plugins.json`。例如 `--data-root C:\axdata\data` 会配套使用 `C:\axdata\metadata`、
`C:\axdata\plugins`、`C:\axdata\cache` 和 `C:\axdata\logs`。它不会联网、
不会自动安装第三方插件，也不会写入任何第三方源 token。

`config show` 用来确认当前 data root、metadata root、插件配置、插件 site-packages、Collector store、
API/Web 地址。`doctor` 会离线检查 Python/AxData 版本、目录是否存在且可写、DuckDB/pyarrow/pandas/FastAPI/uvicorn、
ProviderRegistry、已发现/启用/失败/冲突插件、TDX 插件是否安装启用、8666/8667 端口是否可能被占用、
最近 Collector task/run 和真实源 smoke 的可运行条件。需要脚本处理时可以加 `--json`。

启动 API：

```powershell
.\.venv\Scripts\python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8666 --reload
```

API 默认地址是 `http://127.0.0.1:8666`。另开一个终端检查：

```powershell
curl http://127.0.0.1:8666/health
curl http://127.0.0.1:8666/v1/config
curl http://127.0.0.1:8666/v1/status
curl http://127.0.0.1:8666/v1/doctor
```

启动 Web：

```powershell
npm run dev:web
```

Web 默认地址是 `http://127.0.0.1:8667`，只作为本机管理台。API 和 Web 开发时使用不同端口。API host/port、Web 本机端口可以这样覆盖：

```powershell
$env:AXDATA_API_PORT = "8766"
.\.venv\Scripts\python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8766 --reload

$env:AXDATA_WEB_PORT = "8767"
npm run dev:web
```

启动后可以在 Web 的配置页查看本地状态与诊断。该页面会调用 `/v1/status` 和 `/v1/doctor`，展示 API 状态、data/metadata/plugin 目录、已安装/已启用/禁用/失败或冲突插件数量、Collector 摘要、最近失败 run、端口和目录可写性等检查项。检查项会按 OK/WARN/ERROR/SKIP 显示；有下一步动作时会展示 `next_action` 或可复制的 `action_command`。如果 API 调用失败，页面会显示错误文本，不会白屏。

## 4. 查看插件和接口目录

CLI：

```powershell
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin installed --json
.\.venv\Scripts\axdata plugin collectors --json
```

Provider 和已安装插件的 JSON 里会包含 `status_message`、`next_action`、`action_command`，以及
`install_source`、`can_enable`、`can_disable`、`can_uninstall`、`uninstall_block_reason`。插件已安装但未启用、
manifest 不可发现、import/entry point 失败、版本不兼容或冲突时，先看这些字段再决定 enable、重装或调整 override。预装插件可以启用、禁用、逻辑卸载并重新启用；AXP 管理安装的插件可以由 AxData 物理卸载；Python 环境或 editable/development 路径发现的非预装插件需要用 `pip uninstall` 或移除开发路径。插件卸载不会删除已采集数据、metadata、用户 Task 或 run history。

API：

```powershell
curl http://127.0.0.1:8666/v1/plugins/providers
curl http://127.0.0.1:8666/v1/plugins/installed
curl http://127.0.0.1:8666/v1/plugins/collectors
curl http://127.0.0.1:8666/v1/request/interfaces
```

Web：

- Data Interfaces：查看后端 Registry 生成的接口目录、字段、参数和插件状态；目录一级按数据源组织，通达信源内再按股票数据、指数数据、ETF 数据以及实时、短线、行情、竞价、财务、F10 等类别细分。
- Tools：查看 CollectorRegistry 中的独立采集器、输出/质量契约、相关 task/template 和最近 run；DownloaderProfile 只作为兼容下载入口保留。
- Settings：查看本机访问状态、远程 SDK/API token、Provider 状态、已安装插件、Collector task/run、基础数据 / 交易日历和 TDX 服务器配置。

Web 的 Provider 状态和已安装插件卡片也会展示 `status_message`、`next_action`、`action_command`。TDX 缺失或不可用时只提示安装并启用 TDX 插件，不提供 core 兜底路径，也不会自动联网安装依赖。如果只启用了普通 TDX，source_request 目录为 core/generic 135 个接口 + 普通 TDX 90 个接口；包存在但未启用的 TDX Ext 应显示为 disabled，可点击启用；安装并启用 TDX Ext 后，扩展行情 31 个接口会以“通达信扩展行情”一级菜单出现，不混入普通通达信详情页。

## 5. 源端直取和本地查询

Python SDK 本地查询：

```python
import axdata as ax

client = ax.AxDataClient()
stocks = client.stock_basic_exchange(exchange="SSE", fields=["instrument_id", "name", "list_date"])
bars = client.daily(ts_code="000001.SZ", start_date="20240101", end_date="20240131")
```

本地查询只读已经写入 `data/core` 的 Parquet。新仓库没有自带真实行情文件时，上面的查询会提示对应 core 表还没有数据；先用 `client.call(...)` 或 Downloader/Collector 验证源端和采集链路。

源端直取：

```python
preview = client.call(
    "stock_codes_tdx",
    scope="all",
    fields=["instrument_id", "name", "exchange"],
)
```

常用 source-only 小样本也走同一入口，例如：

```python
quote = client.call("stock_realtime_snapshot_tdx", code="000001.SZ", fields=["instrument_id", "last_price", "change_pct"])
index_bars = client.call("index_kline_tdx", code="000001.SH", period="day", count=20)
etf_bars = client.call("etf_kline_tdx", code="510050.SH", period="day", count=20)
constituents = client.call("concept_constituents_tdx", concept_code="881386", count=5)
intraday = client.call("stock_intraday_today_tdx", code="000001.SZ")
recent_intraday = client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")
index_intraday = client.call("index_intraday_history_tdx", code="000001.SH", trade_date="20260617")
etf_trades = client.call("etf_trades_today_tdx", code="510050.SH")
trades = client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")
finance = client.call("stock_finance_summary_tdx", code="000001.SZ")
```

CLI 等价源端直取：

```powershell
.\.venv\Scripts\axdata request stock_realtime_snapshot_tdx `
  --param code=000001.SZ `
  --fields instrument_id,last_price,change_pct `
  --json

.\.venv\Scripts\axdata request stock_trades_history_tdx `
  --params '{\"code\":\"000001.SZ\",\"trade_date\":\"20260511\"}' `
  --fields instrument_id,trade_datetime,price,volume `
  --json

.\.venv\Scripts\axdata request index_intraday_history_tdx `
  --params '{\"code\":\"000001.SH\",\"trade_date\":\"20260617\"}' `
  --fields instrument_id,trade_time,price `
  --json

.\.venv\Scripts\axdata request etf_trades_today_tdx `
  --params '{\"code\":\"510050.SH\"}' `
  --fields instrument_id,trade_time,price `
  --json

.\.venv\Scripts\axdata request index_realtime_rank_tdx `
  --params '{\"sort\":\"change_pct\",\"count\":5}' `
  --json
```

源端直取默认不写入 `raw/staging/core/factor`，也不代表接口已经加入 Collector task template。TDX 插件未安装或被显式禁用时，CLI/API/SDK 会返回可读错误并提示检查 `axdata.source.tdx_external`。

HTTP 源端直取：

```powershell
curl -X POST http://127.0.0.1:8666/v1/request/stock_codes_tdx `
  -H "Content-Type: application/json" `
  -d "{\"params\":{\"scope\":\"all\"},\"fields\":[\"instrument_id\",\"name\",\"exchange\"]}"

curl -X POST http://127.0.0.1:8666/v1/request/index_kline_tdx `
  -H "Content-Type: application/json" `
  -d "{\"params\":{\"code\":\"000001.SH\",\"period\":\"day\",\"count\":20},\"fields\":[\"instrument_id\",\"trade_time\",\"close\"]}"
```

直接用 DuckDB 查看本地 Parquet：

```powershell
@'
import duckdb

con = duckdb.connect()
rows = con.execute("""
    SELECT *
    FROM read_parquet('data/core/table=daily/**/*.parquet', hive_partitioning = true)
    LIMIT 5
""").fetchall()
print(rows)
'@ | .\.venv\Scripts\python -
```

新仓库没有本地 core Parquet 时，上面的查询会提示路径不存在；先运行 Collector/Downloader 或真实源 smoke，把样本写入 `data/core` 或指定输出目录后再查询。

采集或下载写出 Parquet 后，可以先用数据浏览命令确认本地到底有什么：

```powershell
.\.venv\Scripts\axdata data list
.\.venv\Scripts\axdata data inspect daily
.\.venv\Scripts\axdata data preview daily --limit 20
.\.venv\Scripts\axdata query daily --symbol 000001.SZ --start 20240101 --end 20240131 --limit 100
```

这些命令只读本地 metadata 和 Parquet，不请求真实源。`data list` / `data inspect` 优先读取 Collector/Downloader metadata；缺少行数、列或日期范围时只读 Parquet footer/schema metadata 补充，不为了列表展示对大文件做全量 `COUNT(*)`。目录型 Parquet 的 footer 统计有文件数和目录数上限；超过上限时会标记 metadata 受限，不返回误导性的精确行数。新增写入 metadata 时，inspect 也会显示 `write_mode`、`primary_key`、`partition_by`、`date_field`、写入前后行数和去重行数；旧 run 缺字段时为空。`preview` 和 `query` 的返回行数默认受限，并且 Data Browser 单次最多返回 100 行；大数据量下优先传 `--symbol`、`--start`、`--end` 和 `--fields`，让 DuckDB 只读取必要列和日期分区，缺匹配日期分区时直接返回空结果。需要大规模分析时，直接用 DuckDB、Python SDK 或导出任务，不在第一版 Data Browser 里做任意 SQL 编辑器。

API 等价入口：

```powershell
curl http://127.0.0.1:8666/v1/data/datasets
curl http://127.0.0.1:8666/v1/data/datasets/daily
curl "http://127.0.0.1:8666/v1/data/datasets/daily/preview?symbol=000001.SZ&start=20240101&end=20240131&limit=20"
```

Web 控制台顶部的 Data Browser 页面会展示 dataset 列表、行数、日期范围、quality 状态、字段、输出路径和小范围 preview。如果本地还没有数据，它会显示空状态；先创建并运行 Collector task，或显式运行 Downloader/真实源 smoke 后再刷新。详情区会额外展示交易日历状态、日期缺口、非交易日、K 线异常和复权异常计数；CLI 的 `axdata data inspect <dataset>` 非 JSON 输出也会显示这些高层摘要，完整字段仍在 JSON 的 `quality` 对象中。

## 6. 采集器和 Collector task

当前已经实现两类写出入口：

- 独立 Collector：来自 CollectorRegistry，通过 `runner_entry` 生产本地数据资产。
- 兼容 Downloader：按接口和 DownloaderProfile 立即下载；这是 legacy/显式下载入口，不是采集器 catalog 的事实源。
- 常驻 Collector task：保存任务定义，支持 manual / interval / daily、启用/禁用、run history 和状态汇总。

查看可用 CollectorSpec：

```powershell
.\.venv\Scripts\python -m axdata_core.cli plugin collectors --json
```

当前默认内置采集器包含 TDX 8 个独立 CollectorSpec：`tdx.stock_codes_tdx.snapshot`、`tdx.stock_suspensions_tdx.snapshot`、`tdx.stock_st_list_tdx.snapshot`、`tdx.stock_daily_share_tdx.snapshot`、`tdx.stock_daily_price_limit_tdx.snapshot`、`tdx.stock_kline_daily_tdx.snapshot`、`tdx.stock_limit_ladder_tdx.snapshot`、`tdx.stock_theme_strength_rank_tdx.snapshot`。`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 保留在接口页和兼容下载入口，但不再作为采集器展示。交易所保留为 Source Provider 接口和本地基础数据能力，不再提供默认 CollectorSpec。巨潮、腾讯、东方财富和新浪的预装接口仍可在接口页或 `axdata request` 中临时查询，但不再默认出现在 Collector 或 Downloader 目录里。TDX source Provider manifest 不再贡献 legacy CollectorSpec；它仍提供 TDX 源端接口和 `/v1/downloaders` 兼容入口。创建 Collector task 需要一个真实存在的 `collector_name`。

本地离线测试已经覆盖 Collector Runner 的基础链路：

```text
runner_entry 或 legacy Downloader -> CollectorRun -> Parquet 主数据 + 可选 CSV/DuckDB -> log/quality/output_paths -> DuckDB query
```

`quality` 会保留 `schema`、`primary_key`、`row_count` 三个旧状态键，并额外展示 `quality_status`、`row_count_value`、required columns 是否存在、缺失列、required 列空值计数、重复主键行数、日期/时间范围、非负数值列检查、实际/期望/额外列和字段映射。写入链路还会记录 `write_mode`、`partition_by`、`write_primary_key`、`write_date_field`、写入前后行数、去重行数和触达分区。Web/CLI/API 直接展示同一个 JSON；如果某个采集器没有日期字段或数值字段，不会因为缺这些声明而失败。

行情类质量检查会结合本地交易日历：本地已有 `trade_cal` 时，`daily`、`stock_kline_daily_tdx` 会输出交易日历覆盖、缺失交易日样本、非交易日多出样本和按证券代码的小样本覆盖摘要。采集任务层已经把 `trade_cal` 收口为系统基础依赖：日线任务运行前会先检查本地交易日历，缺失或覆盖不足时返回 `dependency_missing`，提示先同步“基础数据 / 交易日历”。日 K 线会检查 OHLC 高低关系、成交量/成交额非负。日期缺口不一定是错误，可能是停牌、未上市/退市、源端遗漏或本次只采了部分范围。

这表示框架链路可用，不表示所有真实源都已有生产级全市场 Collector。第一批核心表的当前状态是：

| core 表 | 当前源端接口 | 当前采集状态 |
| --- | --- | --- |
| `stock_basic_exchange` | `stock_codes_tdx`、`stock_basic_info_exchange` | TDX source Provider 保留兼容 DownloaderProfile，`axdata.collector.tdx` 提供独立 CollectorSpec；交易所保留 source_request/兼容 DownloaderProfile，不再提供默认采集器；如需长期全量入库，应按采集器规范补充转换任务 |
| `trade_cal` | `stock_trade_calendar_exchange` | 系统基础数据；Web 显示为“基础数据 / 交易日历”，`trade_cal_refresh` 会同步本地日历 cache，供其它采集任务运行前检查 |
| `daily` | `stock_kline_daily_tdx` | schema/query/storage 已就绪；`axdata.collector.tdx` 独立 CollectorSpec 可写显式代码小样本；如需全市场长期更新，应补充专用转换任务 |
| `adj_factor` | `stock_adj_factor_tdx` | schema/query/storage 与源端接口保留；不再作为默认采集器进入采集页；如需长期维护复权因子，应补充专用重建策略 |

创建 TDX 采集任务：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task add tdx.stock_codes_tdx.snapshot `
  --task-id stock_codes_refresh `
  --trigger-type manual `
  --params '{\"scope\":\"all\"}' `
  --fields instrument_id,symbol,tdx_code,exchange,name,market `
  --formats parquet `
  --json
```

也可以从当前可用模板创建核心任务。模板只使用安全默认参数，不会一键全市场重采：

```powershell
.\.venv\Scripts\axdata collector task templates
.\.venv\Scripts\axdata collector task create-from-template daily --json
```

`daily` 和 `stock_kline_daily_tdx` 模板需要 TDX 采集器插件 `axdata.collector.tdx` 已安装并启用；缺失时模板列表会显示下一步命令。它们还声明 `required_datasets=["trade_cal"]`，因此建议先在 Web 中同步“基础数据 / 交易日历”。TDX 日线默认 `code=000001.SZ,count=800,adjust=none`。

空的 Collector task store 会自动 seed 一个默认可见任务：`stock_kline_daily_tdx_sample`。它默认禁用，不会自动联网采集；用户可以在 CLI/API/Web 中查看、启用、禁用或手动运行。缺少或禁用 TDX 采集器插件时，该默认任务仍显示，但运行会提示“请安装/启用 TDX 采集器插件 (axdata.collector.tdx)”。缺少交易日历时，TDX 日线任务会提示“交易日历未同步，请先同步基础数据：交易日历。”`stock_kline_daily_tdx_sample` 仍使用 `snapshot`，因为当前日线轻量路径还没有稳定转换为正式 `daily.trade_date` 写入。

手动运行并等待结果：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task run stock_kline_daily_tdx_sample --wait --json
```

手动 run 可以只覆盖本次参数，不修改 task 定义：

```powershell
.\.venv\Scripts\axdata collector task run daily_sample_tdx `
  --symbol 000001.SZ `
  --limit 20 `
  --wait `
  --json
```

这里的 `daily_sample_tdx` 是上面 `collector task create-from-template daily` 创建出的任务 id。若你没有创建模板任务，也可以直接运行默认可见的 `stock_kline_daily_tdx_sample`；TDX 采集器插件缺少或禁用时会生成失败 run，并提示安装/启用 `axdata.collector.tdx`。

按日期区间补采：

```powershell
.\.venv\Scripts\axdata collector task backfill daily_sample_tdx `
  --start 20240101 `
  --end 20240131 `
  --symbol 000001.SZ `
  --limit 20 `
  --wait `
  --json
```

查看任务、运行历史和汇总：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task list --json
.\.venv\Scripts\python -m axdata_core.cli collector run list --json
.\.venv\Scripts\python -m axdata_core.cli collector run info <run_id> --json
.\.venv\Scripts\python -m axdata_core.cli collector status --json
```

API 创建任务：

```powershell
curl -X POST http://127.0.0.1:8666/v1/collector/tasks `
  -H "Content-Type: application/json" `
  -d "{\"collector_name\":\"tdx.stock_codes_tdx.snapshot\",\"task_id\":\"stock_codes_refresh\",\"trigger_type\":\"manual\",\"params\":{\"scope\":\"all\"},\"fields\":[\"instrument_id\",\"symbol\",\"tdx_code\",\"exchange\",\"name\",\"market\"],\"formats\":[\"parquet\"]}"
```

API 手动运行并查看状态：

```powershell
curl -X POST http://127.0.0.1:8666/v1/collector/tasks/stock_codes_refresh/run `
  -H "Content-Type: application/json" `
  -d "{}"

curl http://127.0.0.1:8666/v1/collector/status
curl http://127.0.0.1:8666/v1/collector/runs
curl http://127.0.0.1:8666/v1/collector/runs/<run_id>
curl http://127.0.0.1:8666/v1/tasks/trade_cal_refresh/runs
```

输出路径会出现在 run 的 `output_paths` 字段中。失败信息在 `error`，跳过原因在 `skip_reason`，失败退避时间在 `backoff_until`。
task/run JSON 也会包含 `status_message`、`next_action`、`action_command`，用于提示 disabled、duplicate skip、
failure backoff、资源组等待和失败 run 的下一步排查命令。
任务状态还会显示 `next_run_at`、`last_success_at`、`last_failure_at`、`last_error_summary`、`retry_count`、
`queue_status`、`can_run_now`、`blocked_reason` 和本次 run 的 `params_override`。backfill run 会在
`metadata.backfill_range` 中记录 `start/end`。
新 run 还会记录 `events`、`stage_timings`、`error_category` 和 `error_summary`。`events` 是轻量时间线，
可看到 run 是否停在 queued、provider/profile 解析、下载、写文件、质量检查或 metadata 记录；`stage_timings`
会显示排队、Provider 解析、下载、写入、质量检查和总耗时，未执行阶段为 `null`；`error_category`
会把常见失败归为 `provider_missing`、`plugin_disabled`、`invalid_params`、`network_error`、`upstream_empty`、
`upstream_error`、`schema_mismatch`、`write_failed`、`storage_permission`、`quality_failed`、`backoff_blocked`
等类别，不能可靠判断时为 `unknown`。失败后先看 `collector run info <run_id> --json` 里的分类、事件和下一步动作，再决定改参数、启用插件、检查网络或修复输出目录。
`quality_status=ok` 表示本次 profile/schema 声明的基础检查通过；`warn` 表示有非阻塞提示，例如空结果或额外列；`error` 表示 required columns、主键或声明的数值范围有 blocking 问题。

Web 配置页的调度区域会展示同样的信息：task 模板、task 状态、trigger、resource_group、enabled/disabled、最近 run、run history、错误分类/摘要、stage timings、event timeline、`quality`、`output_paths` 和下一步动作。状态汇总使用最近窗口，同时返回完整 run 总数和状态计数；排查单次运行时进入 run detail。可以从可用模板创建任务，也可以对已有 task 提交手动运行或小范围 backfill；长路径和长命令会自动换行。

## 7. 真实源小样本检查

普通开发和 CI 的默认测试不请求真实网络。真实源小样本检查放在独立脚本里，必须显式启用：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --json
# 默认只输出 4 个核心表 skip，不请求网络。

.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

Web 配置页只展示真实源小样本检查的状态和推荐命令，不会自动运行真实网络检查。需要覆盖当前三项核心小样本时，在命令行显式运行：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --interfaces stock_basic_exchange trade_cal daily `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

脚本当前示例覆盖三项核心小样本路径：

| core 表 | 源端接口 | 当前链路 |
| --- | --- | --- |
| `stock_basic_exchange` | `stock_basic_info_exchange` | 交易所源端取数小样本，写 core Parquet，再用 DuckDB 读回 |
| `trade_cal` | `stock_trade_calendar_exchange` | 交易所源端取数日期范围，写 core Parquet，再用 DuckDB 读回 |
| `daily` | `stock_kline_daily_tdx` | 需要 TDX 插件；当前是显式小样本 smoke/core profile 路径，不是 core 兜底，也不是生产级全市场日线任务 |

第一批 source-only 接口不会进入默认目标。需要联网检查时必须显式指定接口名，例如：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --interfaces tencent_realtime_snapshot `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

source-only 目标用于联网小样本检查，主路径仍以 Parquet 写出并用 DuckDB 读回；CSV/DuckDB 可以作为额外导出或缓存。旧 JSONL 只属于兼容下载/调试输出，不作为采集页主路径展示。当前可显式选择的第一批接口包括 `stock_historical_list_exchange`、`cninfo_announcements`、`cninfo_announcement_detail`、`tencent_realtime_snapshot`、`eastmoney_dragon_tiger_daily`、`eastmoney_margin_trading`、`eastmoney_research_reports` 和 `stock_financial_report_sina`；其中公告详情需要传入可访问的 `--announcement-url`。

如果要检查 TDX 两项，先安装插件包；随项目提供的 TDX 包安装后默认可用：

```powershell
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

只跑 `daily` 和 `adj_factor`：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --interfaces daily adj_factor `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

`--enable-provider` 仍可用于临时覆盖 smoke 输出目录里的插件配置，但不会安装 Python 包；如果当前 `.venv` 没有 `axdata-source-tdx` entry point，TDX 两项仍会 skip 并提示安装。editable 本地开发安装和 wheel / `.axp` 安装都通过同一套 Registry 发现逻辑。

输出目录中可以直接查看：

```text
data/core/table=<table>/.../*.parquet
snapshots/<run_id>/<interface>/parquet/*.parquet
snapshots/<run_id>/<interface>/csv/*.csv
snapshots/<run_id>/<interface>/duckdb/*.duckdb
metadata/real_source_smoke/<run_id>/summary.json
```

`pass` 表示真实源返回小样本、写出 Parquet、质量检查通过且 DuckDB 能读回；`skip` 会区分未安装、已安装但未启用、已发现但状态异常或未显式运行；`fail` 表示真实网络、上游、参数或限流等问题。真实源小样本检查是可选流程，不进入默认 `pytest -q` 的联网路径。

可选 pytest 入口默认跳过：

```powershell
.\.venv\Scripts\python -m pytest tests\test_real_source_smoke.py -q
# 默认：离线 dry-skip 测试通过，真实源测试 skipped。

$env:AXDATA_RUN_REAL_SMOKE = "1"
.\.venv\Scripts\python -m pytest tests\test_real_source_smoke.py -q
```

## 8. AXP 本地插件安装

`.axp` 是本地安装信封，不是信任信封。它可以包含 Provider wheel、manifest、README、LICENSE、checksum 和依赖 wheels。

开发自己的插件前先读 [plugin-development.md](plugin-development.md)。AxData 只把带有 `axdata-provider.json` 或 `axdata-plugin.json` manifest 的 Python 包识别为 AxData 插件；缺少 manifest 的 entry point 会进入 `doctor/status` 诊断，不会出现在普通插件列表或插件统计里。

本地开发随项目提供的 TDX 插件时，最短路径是 editable 安装插件包并检查状态：

```powershell
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata doctor
```

预览：

```powershell
.\.venv\Scripts\axdata plugin axp-preview C:\path\to\plugin.axp --json
```

离线安装，默认不启用：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\plugin.axp --json
```

允许联网安装缺失依赖：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\plugin.axp --allow-online-deps --json
```

安装后启用或禁用：

```powershell
.\.venv\Scripts\axdata plugin enable axdata.source.example
.\.venv\Scripts\axdata plugin disable axdata.source.example
.\.venv\Scripts\axdata doctor
.\.venv\Scripts\axdata status
```

AXP checksum 只用于完整性和打包一致性检查，不证明作者身份、不证明代码安全、不授予内置权限。AxData 不做插件市场、中心审核或签名验签。默认安装只使用包内 dependency wheels 和当前 AxData 插件运行环境；缺 required dependency、版本不满足或冲突时会拒绝安装并给出提示。只有显式传入 `--allow-online-deps` 时，才允许 pip 从当前环境配置的索引安装缺失依赖。

## 9. 使用边界

- Web 可以查看和管理已有 Collector task/run，并可从当前可用 task template 创建任务；任意手填 Collector task 的完整编辑器仍未提供。
- Web 可以查看 status/doctor、插件 guidance、Collector task/run guidance 和真实源 smoke 命令行指引，但不会自动触发真实网络 smoke。
- Collector 调度是单机本地调度，不做分布式调度、复杂 DAG 或云端任务系统。
- 取消 run 当前是状态标记，不保证强杀已经开始的源端请求或写文件。
- `client.call(...)` 和 `/v1/request/*` 默认只做源端直取，不入库。
- 普通查询只读已经写入 AxData 的 Parquet 数据。
- 离线小样本闭环测试不等于真实源全市场采集已稳定；真实源可用性和 core 转换需要逐项检查。
- `scripts/smoke_real_sources.py` 只做可选真实源小样本检查；它写入用户指定输出目录或临时目录，不提交运行产物。
- `data/`、`metadata/plugins.json`、`metadata/*.db`、`metadata/*.sqlite`、`cache/` 和 `logs/` 都是本地运行产物，不提交到仓库。
