# 数据分层设计

AxData 使用 `raw -> staging -> core -> factor` 四层数据模型。每一层都保存为 Parquet 文件，DuckDB 负责本地查询、视图和轻量缓存。Python SDK 默认在本机通过这一层直接读取已入库数据；HTTP API 是远程访问同一数据语义的通道。

源端直取不属于数据分层。它是 SDK/API 对源接口的一次性请求：按 AxData 字段返回结果，默认不写入 `raw`、`staging`、`core` 或 `factor`。新增源接口时，应先定义接口目录、参数、字段和解析，再决定是否设计采集入库路径。

当前默认采集能力由预装的 TDX Collector 插件提供，覆盖少量稳定示例和基础闭环。Collector 通过 `runner_entry` 产出 records，再由 AxData Writer 写出 Parquet，并记录 `CollectorRun`、`output_paths`、`row_count`、`quality` 和 metadata log。交易所、巨潮、腾讯、东方财富、新浪财经等预装源接口主要作为 source_request-only 接口使用：可以在接口页、SDK 或 CLI 中临时查询，但默认不写入本地数据层。需要长期入库的接口，应按采集器插件规范单独声明 CollectorSpec 和写入契约。

兼容 DownloaderProfile 继续服务显式下载入口 `/v1/downloaders`，但它不是新采集器的推荐形态。新采集器应进入 Collector Runner，并由 AxData 统一处理队列、状态、日志、Writer、Quality 和 metadata；不要通过 `/v1/request`、SDK `call`、ProviderRegistry route 或旧 DownloaderProfile 链路套接口采集。可选脚本 `scripts/smoke_real_sources.py` 用于真实源小样本检查，默认不进入普通测试流程，也不代表所有真实源都已经具备全市场长期采集能力。

## 分层总览

| 层级 | 目的 | 是否面向用户 | 是否可重建 | 典型粒度 |
| --- | --- | --- | --- | --- |
| raw | 保存上游接口原始快照 | 否 | 否，作为追溯依据保留 | adapter + interface + batch |
| staging | 源数据标准化和清洗 | 否 | 是，可从 raw 重建 | source + table + date |
| core | AxData 统一事实表和主数据 | 是 | 是，可从 staging 重建 | table + business key |
| factor | 因子、特征和研究数据集 | 是 | 是，可从 core 重建 | factor_set + date |

| 临时路径 | 目的 | 是否面向用户 | 是否可重建 | 典型粒度 |
| --- | --- | --- | --- | --- |
| source_request | 源端直取、接口调试、实时快照 | 是 | 否，不落盘 | interface + params |

## raw 层

raw 层保存上游返回结果的最小改动版本，用于追溯、回放和问题定位。

职责：

- 保存上游接口响应中的字段、顺序、原始类型和源侧空值。
- 记录 adapter、interface、params、fields、request_id、batch_id、run_id、ingested_at。
- 不做业务清洗，不改字段名，不做跨接口合并。
- 支持重放同一个采集批次生成 staging。

建议路径：

```text
data/raw/adapter=tushare/interface=daily/ingest_date=2026-06-07/batch_id=.../*.parquet
data/raw/adapter=exchange/interface=stock_basic_exchange/ingest_date=2026-06-07/batch_id=.../*.parquet
```

raw 层可以保留少量 JSON 元数据文件，但表格响应优先落 Parquet，便于统一读取。

## staging 层

staging 层把上游数据转换为 AxData 中间规范，但仍保留 adapter/interface 维度。

职责：

- 字段名转换为 snake_case。
- 日期转换为 `date` 或 `timestamp`。
- 代码转换为 AxData 统一代码格式。
- 数值单位转换到 AxData 标准单位。
- 去除同一 source、同一批次内的重复记录。
- 标记源侧缺失、异常、停牌、退市等状态。

建议路径：

```text
data/staging/adapter=tushare/table=daily/parquet/20260605.parquet
data/staging/adapter=exchange/table=stock_basic_exchange/exchange=SSE/*.parquet
```

staging 层仍允许 adapter-specific 字段，但这些字段只服务采集转换、追溯和调试，不进入常规用户 schema。

## core 层

core 层是 AxData 的稳定数据产品层。Python SDK 本地模式和 HTTP API 默认从 core 层读取。

职责：

- 输出稳定用户 schema，不暴露上游字段差异。
- 按接口口径分别生成用户表，例如 `stock_basic_exchange`；新增口径应使用独立表名，查询层保持口径分离。
- 提供稳定主键、唯一约束、字段单位和字段语义。
- 只保存可解释的基础数据，不保存实验性因子。
- 不用 provider 原始字段替代 core 字段；例如 `daily` 使用 `ts_code + trade_date` 和 `vol`，TDX 源端 `instrument_id + trade_time + volume` 需要在 staging/转换或 profile mapping 中显式映射。

建议路径：

```text
data/core/table=stock_basic_exchange/*.parquet
data/core/table=trade_cal/exchange=SSE/*.parquet
data/core/table=daily/parquet/20260605.parquet
data/core/table=adj_factor/parquet/20260605.parquet
```

核心表写入策略：

- 小表如 `stock_basic_exchange` 可整表重写，也可在稳定主键明确后按 `instrument_id` upsert。
- 日历表可按 `exchange` 和年度分区覆盖，或按 `cal_date` 范围替换。
- 行情和复权表按 `trade_date` 分区，便于按日期增量更新、补采和全市场扫描。
- 当前轻量 Downloader 已在 run log/CollectorRun 中记录写入 metadata；稳定 manifest/index 可继续扩展，不在当前存储架构中重写。

本地写入模式：

| write_mode | 语义 | 适用层级 | 必需声明 | 当前落地状态 |
| --- | --- | --- | --- | --- |
| `append` | 追加新文件，不做去重；同名文件已存在时写入带序号的新文件。 | raw、snapshot、追溯留痕 | 无；可声明 `primary_key` 供 quality 使用 | `DownloadWriter` 支持 |
| `snapshot` | 保留一次运行快照，用原子替换写出目标文件；这是兼容旧 profile 的默认模式。 | snapshot、source-only、小样本 smoke、小表快照 | 无 | 默认支持 |
| `overwrite_partition` | 只删除并重写本次数据触达的分区 Parquet 文件，其它分区不动。 | staging、core、factor 的分区表 | `partition_by` | `DownloadWriter` 支持 |
| `replace_range` | 按 `date_field` 的闭区间移除旧行，再写入本次数据。 | core/factor 的日期补采、修复采集 | `date_field`；可选 `replace_range_start/end` | `DownloadWriter` 支持 |
| `upsert_by_key` | 读取既有 Parquet，与本次数据合并，按 `primary_key` 保留最后一条，避免同 key 重跑重复。 | core/factor 稳定事实表、小批量分区样本 | `primary_key`；分区表建议同时声明 `partition_by` | `DownloadWriter` 支持 |

写入声明来自独立 CollectorSpec 的 `output` / runner 返回 metadata，或 legacy DownloaderProfile / Provider manifest 的 `output`：

- `write_mode` 缺省为 `snapshot`，旧 profile 不需要迁移。
- `primary_key` 是 `upsert_by_key` 的硬要求；缺失时写入会失败并返回可读错误。
- `partition_by` 是 `overwrite_partition` 的硬要求；按日期分区的 Parquet output path 表示格式目录，例如 `.../parquet`，目录下按 `YYYYMMDD.parquet` 一天一个文件写入；旧的 `trade_date=YYYYMMDD/*.parquet` 目录仍可读取。
- `date_field` 是 `replace_range` 的硬要求；没有日期字段的接口不能声明 range 替换。
- `replace_range_start` / `replace_range_end` 当前来自执行层可选传入；未传时用本次 frame 的日期最小/最大值。

写入 metadata 会随 run/output 保存，并在 CLI/API/Data Browser 透传：

| 字段 | 说明 |
| --- | --- |
| `write_mode` | 实际使用的写入模式。 |
| `partition_by` | 分区字段列表。 |
| `primary_key` | 写入去重使用的主键；quality 旧键 `primary_key` 仍保留为检查状态，写入主键在 quality 中使用 `write_primary_key`。 |
| `date_field` | range 替换和日期展示使用的日期/时间字段。 |
| `replace_range_start` / `replace_range_end` | 本次替换的日期闭区间；非 range 模式为空。 |
| `rows_before` / `rows_written` / `rows_after` | 本次写入前、输入、写入后行数；能低风险获得时记录。 |
| `duplicate_rows_dropped` | `upsert_by_key` 合并时因重复 key 丢弃的行数。 |
| `partitions_touched` | 本次触达的分区标签，例如 `trade_date=20260618`。 |
| `write_metadata.formats` | 按输出格式记录的写入 metadata；Parquet 是主数据格式，CSV/DuckDB 是额外导出或查询缓存；旧 JSONL 仅作为兼容下载格式保留。 |

核心表推荐策略：

| 表或接口 | 推荐策略 | 当前代码状态 |
| --- | --- | --- |
| `trade_cal` | `overwrite_partition` by `exchange` + year，或 `replace_range` by `cal_date`。 | 策略声明；现有轻量 profile 仍保持快照写出。 |
| `stock_basic_exchange` | `snapshot + latest` 整表重建，或稳定后 `upsert_by_key instrument_id`。 | 策略声明；现有轻量 profile 仍保持快照写出。 |
| `daily` | `replace_range` 或 `upsert_by_key ts_code + trade_date`，并按 `trade_date` 分区。 | 策略声明；`stock_kline_daily_tdx` 还未转换成稳定 `daily.trade_date` 写入。 |
| `adj_factor` | `upsert_by_key ts_code + trade_date`；发生修订时也可用 `replace_range`。 | schema 和源端接口保留；当前不作为默认采集器。 |
| `stock_kline_daily_tdx` | 源端样本建议 `upsert_by_key instrument_id + trade_time + period`；正式 `daily` 前需映射为 `ts_code + trade_date`。 | 策略声明；当前代码保持 `snapshot`，避免在缺稳定 `trade_date` 字段时错误去重。 |

当前核心表映射与缺口：

| core 表 | 当前源端接口 | 当前入库状态 |
| --- | --- | --- |
| `stock_basic_exchange` | `stock_codes_tdx`、`stock_basic_info_exchange` | `stock_codes_tdx` 有 TDX 兼容 DownloaderProfile 和 `axdata.collector.tdx` 独立 CollectorSpec；`stock_basic_info_exchange` 保留为交易所源端接口和兼容 DownloaderProfile，不再提供默认采集器；生产级 core latest/history 转换仍需补齐 |
| `trade_cal` | `stock_trade_calendar_exchange` | 已产品化为系统基础数据：Web 展示为“基础数据 / 交易日历”，`trade_cal_refresh` 会同步本地交易日历 cache；`stock_trade_calendar_exchange` 保留为交易所源端接口和兼容 DownloaderProfile，不再提供默认采集器 |
| `daily` | `stock_kline_daily_tdx` | schema、partitioned storage 和 DuckDB query 已验证；TDX independent CollectorSpec 可写显式代码小样本；生产级全市场 core 转换仍需补齐 |
| `adj_factor` | `stock_adj_factor_tdx` | schema 和源端接口保留；不再作为默认采集器进入采集页，生产级复权因子重建策略仍需补齐 |

第一批 source-only / raw / snapshot 接口当前写入层建议：

| 接口 | 输出层 | 说明 |
| --- | --- | --- |
| `stock_historical_list_exchange` | snapshot | 某一日期或日期范围的股票池快照，默认不作为稳定 core 表。 |
| `cninfo_announcements`、`cninfo_announcement_detail` | raw | 当前是 source_request-only；公告元信息和 PDF 元信息保留源端口径，默认不通过 Downloader/Collector 写入。 |
| `tencent_realtime_snapshot` | snapshot | 当前是 source_request-only；实时快照默认不污染历史事实表，持久化应由独立录制或快照采集器实现。 |
| `eastmoney_dragon_tiger_daily`、`eastmoney_margin_trading`、`eastmoney_research_reports` | raw | 当前是 source_request-only；公开 HTTP 源端口径，如需入库应设计独立专题采集器。 |
| `stock_financial_report_sina` | raw | 当前是 source_request-only；新浪财经 JSON 财报源端口径，如需入库应先确认稳定财务表口径。 |

可选真实源小样本检查的当前分类：

| core 表 | 检查状态 | 说明 |
| --- | --- | --- |
| `stock_basic_exchange` | 可通过交易所内置源直取小样本检查 | 写入指定输出目录下的 core Parquet 和 metadata，DuckDB 可读回；Registry 只显示对应源端接口/兼容 DownloaderProfile，不再显示交易所 CollectorSpec |
| `trade_cal` | 可通过交易所内置源直取小样本检查 | 交易所返回的是日期范围样本；写入 core 分区后查询；Registry 只显示对应源端接口/兼容 DownloaderProfile，不再显示交易所 CollectorSpec |
| `daily` | 需要 TDX 插件可用 | 当前通过 `stock_kline_daily_tdx` 源端直取或 TDX 轻量 profile 写小样本 core 分区；不是 core 内置兜底，也不是生产级全市场日线任务 |
| `adj_factor` | 需要 TDX source 插件可用 | 当前可通过 `stock_adj_factor_tdx` 源端直取或兼容下载入口做小样本检查；不再作为默认采集器进入采集页，也不是生产级复权因子任务 |

第一批 source-only 真实源检查不是默认目标，必须显式选择，例如：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --interfaces tencent_realtime_snapshot `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

## factor 层

factor 层保存从 core 层派生的因子、标签、训练特征和研究数据集。

职责：

- 明确因子名称、版本、计算窗口、依赖表、代码版本和参数。
- 保证点时正确，不能使用未来数据。
- 支持宽表和长表两种形态：宽表适合批量训练，长表适合因子目录和动态选择。
- 保存质量指标，例如缺失率、极值裁剪比例、覆盖标的数。

建议路径：

```text
data/factor/factor_set=alpha_basic/version=1/trade_date=2026-06-05/*.parquet
data/factor/factor_set=labels/version=1/trade_date=2026-06-05/*.parquet
```

初期建议使用宽表：

```text
ts_code, trade_date, factor_mom_20, factor_vol_20, factor_turnover_20, ...
```

当因子数量快速增长后，再增加长表或因子 catalog：

```text
ts_code, trade_date, factor_name, factor_value, factor_version
```

## Parquet 与 DuckDB 分工

Parquet 是长期存储：

- 作为数据真相来源。
- 适合列式压缩、批量扫描、跨语言读取和对象存储迁移。
- 通过按日期拆文件或目录分区表达常用过滤条件；核心日频表优先使用 `YYYYMMDD.parquet` 一天一个文件。
- 文件可直接被 Python、DuckDB、Polars、Spark、Arrow 读取。

DuckDB 是查询执行层：

- 读取 Parquet 外部表或视图。
- 执行本地 SQL、join、聚合和导出。
- 保存 catalog、视图定义、临时表和可重建缓存。
- 为 Python SDK 本地直读、HTTP API、Notebook 和回测提供一致查询语义。

DuckDB 不应成为唯一数据真相来源。`catalog.duckdb` 损坏时，系统必须能根据 Parquet、manifest 和 schema 文件重建。

## 目录与视图约定

推荐在 DuckDB 中为每层建立 schema：

```sql
CREATE SCHEMA raw;
CREATE SCHEMA staging;
CREATE SCHEMA core;
CREATE SCHEMA factor;
```

核心视图示例：

```sql
CREATE OR REPLACE VIEW core.daily AS
SELECT *
FROM read_parquet('data/core/table=daily/**/*.parquet', union_by_name = true);
```

SDK 和 HTTP API 的普通查询只访问 `core.*` 和 `factor.*`。管理员和调试命令可以访问 `raw.*`、`staging.*` 与元数据表。源端直取接口不查询 DuckDB，而是走 Source Request Gateway 请求源端并临时返回。

## 入库边界与实时数据

采集是 AxData 的写入动作。任何称为采集的流程都必须产生任务、批次和运行元数据，并按分层规则写入 raw、staging，再进入 core 或 factor。

- 历史采集、增量采集、修复采集和录制任务都应写入 task/batch/run、lineage、质量结果和可重放参数。
- 查询不是采集：SDK 和 HTTP API 查询只读已入库数据，不在查询链路临时请求第三方源。
- 源端直取不是采集：`request`、`client.call(...)`、adapter probe/debug 可直接请求源端，但默认只返回临时结果，不写入 raw、staging、core 或 factor。
- 实时行情默认不入库：快照、订阅和盘中流是临时数据流或内存态视图；如需持久化，必须显式启动 realtime recording 或 collection job，并使用独立 task/batch/run 元数据记录时间窗口和录制参数。

实时录制进入历史层时，应避免污染日线事实表：

- 原始 tick、盘口或快照先写入 raw/staging 对应实时源目录。
- 派生出的分钟线或日线必须经过质量检查和时间窗口确认后再进入 core。
- 未完成收盘确认的盘中数据不得覆盖 `daily` 的正式收盘行情。

## 数据质量约束

通用约束：

- 主键不能为空。
- 日期必须为有效交易日，除非表本身是日历表。
- 同一主键在 core 层只能出现一条记录。
- `open/high/low/close` 不能为负；`high >= low`。
- 成交量和成交额不能为负。
- `adj_factor > 0`。
- core 层字段单位必须与 schema 文档一致。

当前已落地的 Downloader/Collector 基础质量检查：

| 检查 | 说明 |
| --- | --- |
| `row_count` / `row_count_value` | 空结果给 warning；实际行数进入 metadata。 |
| required columns | 检查 profile/schema 声明的 required columns 是否存在。 |
| null counts | 统计 required columns 的空值行数。 |
| duplicate key | 按主键统计重复影响行数。 |
| date range | 按声明的 `date_field` 或 `datetime_field` 记录最小/最大值。 |
| calendar alignment | 对行情/复权类数据按本地 `trade_cal` 检查交易日缺口和非交易日多出；任务声明 `required_datasets=["trade_cal"]` 时，调度器会在运行前先检查本地交易日历基础数据。 |
| date gaps | 输出缺失交易日数量、样本和按证券代码的小样本覆盖摘要。 |
| numeric positive | 对价格、成交量、成交额、复权因子等声明列检查负数；列不存在时 warning，不强行失败无此字段的接口。 |
| OHLC rules | 对 `open/high/low/close` 检查 `high >= low/open/close` 和 `low <= open/close`。 |
| adjustment factor | 对 `adj_factor` 检查严格大于 0。 |
| schema columns | 记录实际列、期望列和 unexpected columns。 |
| field mappings | 记录源端字段到 core 字段的兼容映射，例如 TDX 日线 `volume -> vol`。 |

质量结果随 Downloader run log 和 CollectorRun 保存，并可通过 CLI/API/Web 的 task/run JSON 查看；稳定 manifest 目录可继续扩展写入：

```text
metadata/quality/table=daily/run_id=.../*.json
```

质量状态分为三类：

- `ok`：声明检查均通过。
- `warn`：允许写入但记录问题，例如空结果、unexpected columns、可选数值列缺失、交易日缺口。日期缺口可能来自停牌、未上市/退市、源端遗漏或采集范围不完整。对于已经声明 `trade_cal` 基础依赖的采集任务，缺少本地交易日历会在运行前被阻止，而不是等到质量检查阶段才给 warning。
- `error`：blocking 问题，例如 required columns 缺失、required columns 有空值、主键重复、声明的非负数值列出现负数、非交易日出现行情数据、OHLC 关系异常或 `adj_factor <= 0`。当前轻量 Downloader 仍会把小样本写出，生产级 core 转换任务应据此决定是否阻止覆盖正式 core 分区。

## 本地 Dataset 发现与预览

第一版 Data Browser 不盲扫全盘，也不把 DuckDB 暴露成任意 SQL 编辑器。发现顺序如下：

1. 读取 `metadata/collector/collector_scheduler.json` 中最近的 `CollectorRun`，优先使用 `output_paths`、`quality`、`provider_id`、`downloader_profile`、`result.download_result`、`started_at/finished_at`；当前 discovery 只取最近窗口，避免 run metadata 很多时列表接口返回不可控历史。
2. 在已知 data root 下的 raw/staging/core/factor/snapshots 输出目录里读取最近的 Downloader `logs/*.json`，用于发现绕过 Collector task 的单次 Downloader 输出。
3. 检查已知 core 表路径，例如 `data/core/daily.parquet` 或 `data/core/table=daily/**/*.parquet`，补充没有 run metadata 的本地 core 数据。
4. 如果 run/downloader metadata 已经提供 `row_count`、`schema_columns` 和 `date_range`，列表和详情不再枚举 Parquet 数据文件；缺失时只读 Parquet footer/schema metadata 补行数、列和分区日期范围。目录型 Parquet 只在文件数和目录数上限内读取 footer；超过上限时会标记 `metadata.parquet_stats_limited=true`，优先返回列和分区日期范围，不伪造精确 `row_count`。preview 才通过 DuckDB 读取 Parquet，并始终带 limit。

dataset metadata 暴露字段：

| 字段 | 说明 |
| --- | --- |
| `dataset` / `interface_name` | 本地 dataset 名称和采集接口名。 |
| `provider` / `source` | 来自 CollectorRun、Provider 或 downloader source_meta。 |
| `layer` | raw、staging、core、factor 或 snapshot。 |
| `output_paths` | parquet/csv/duckdb/log 等输出路径；preview 只读 parquet。旧 JSONL 路径仅来自兼容下载历史。 |
| `row_count` | 优先取 quality/run 记录，缺失时用 Parquet footer metadata 补。 |
| `date_min/date_max` | 优先取 `quality.date_range`，缺失时按日期字段补。 |
| `columns` | 优先取 quality/schema columns，缺失时用 Parquet footer/schema metadata 补。 |
| `quality_status`、`quality_warnings/errors` | 写出质量摘要。 |
| `write_mode`、`partition_by`、`primary_key`、`date_field` | 写入策略摘要；旧 metadata 缺失时为空。 |
| `rows_before`、`rows_written`、`rows_after` | 写入前、本次输入和写入后行数；只在 writer 可低风险获得时填充。 |
| `duplicate_rows_dropped`、`partitions_touched` | upsert 去重行数和本次触达的分区标签。 |
| `latest_run_id`、`latest_run_status`、`updated_at` | 最近 run 和更新时间。 |
| `missing_paths` | run metadata 指向但当前不存在的文件路径。 |

CLI/API/Web 的 Data Browser preview/query 默认限制返回行数，单次最多 100 行。Data Browser preview 对目录型 Parquet 如果识别到 `YYYYMMDD.parquet` 日期文件或旧的 `trade_date=...` 日期分区，会按 `start/end` 裁剪到匹配文件/分区；没有匹配日期文件或分区时返回空结果，不回退扫描整棵目录。core `query_table()` 会按字段投影和过滤条件构造 DuckDB 查询；当 core 表按 schema 日期字段拆文件，并传入 `start/end` 时，也会优先裁剪到匹配日期路径。它们只用于确认数据是否存在、字段是否正确和抽样查看；批量分析仍应使用本地 DuckDB、Python SDK 或导出任务。

当前 JSON metadata store 适合本地单机和中等规模 run history。Collector run 列表默认只返回最近记录，API/CLI 会限制单次列表窗口；status 摘要只返回最近窗口、总数、状态计数、active runs 和每个 task 的 latest run；run detail 仍可按 `run_id` 查看完整记录。如果 run metadata 明显增长，应升级到 SQLite/DuckDB metadata 或增加 manifest/index，而不是把所有历史 run 放进一个无限增长的列表响应。

## 更新与重算策略

- 全量初始化：按表和历史日期分片写入 raw，再逐层构建。
- 日常增量：交易日收盘后采集 `daily`，交易日前后更新 `trade_cal`；`adj_factor` 更适合作为派生/重建能力按需生成，不作为默认高频采集任务。core/factor 层优先使用 `overwrite_partition`、`replace_range` 或 `upsert_by_key` 避免同一逻辑数据重复膨胀。
- 主数据修复：`stock_basic_exchange` 可按口径整表刷新，并与历史版本比较；稳定主键路径可演进为 `upsert_by_key instrument_id`。
- 数据修订：源数据变更时新增批次并重建受影响分区，不直接覆盖 raw；raw 层保留 `append`/追溯快照，core 层使用明确分区或主键语义。
- 因子重算：当 core 数据修订、因子代码变更或参数变更时，生成新的 factor version。
