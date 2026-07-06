# 采集调度设计

本文说明 AxData 采集调度运行时的队列、限流、重试和写文件规则。它不是 Provider 插件协议本身，而是插件声明 `resource_group` 和 `default_limits` 之后，AxData 服务端如何统一管理采集任务。

插件模型允许插件提供 CollectorSpec。数据源 Provider 插件负责接口临时查询；Collector 插件负责把数据生产成本地资产。两者是平级插件能力：插件可以只有 Provider、Provider + legacy Collector、只有 Collector，或工具能力；只要它声明采集器，运行时都必须进入 AxData Collector Runner，由 AxData 统一管理队列、状态、日志、取消、失败退避、资源组、写入锁、质量检查和 metadata。

核心问题：采集器里的并发参数只是单个任务预算。如果多个采集任务定在同一时间触发，真实连接数会相乘，可能导致源端拥挤、超时、限流或本地写文件冲突。因此 AxData 必须有全局资源池，而不是让每个任务自己无限开并发。

## 1. 范围

本设计覆盖：

- 手动采集任务。
- 定时采集任务。
- 采集任务队列。
- 按数据源资源组限流。
- 输出目录写锁。
- 失败退避和重试。
- Web 状态展示。

不覆盖：

- 源端直取 `client.call(...)` 的所有本地直跑场景。
- 多进程绕过 AxData collector 服务直接跑脚本时的全局连接预算。
- 云端分布式任务工作进程的强一致资源租约。

当前实现只承诺在一个常驻 collector 服务进程内做到可靠全局限流。

## 1.1 当前支持能力

单机本地 Collector / Downloader 常驻调度已经可用。当前实现以
`libs/axdata_core/axdata_core/collector_scheduler.py` 为核心，提供持久任务定义、运行历史、单进程队列、
失败退避、重复运行跳过、interval/daily 触发和 API/CLI/Web 管理入口。

已落地能力：

- `CollectorTask` 保存任务定义：`task_id`、`collector_name`、`enabled`、`trigger_type`、`interval_seconds`、`daily_time`、`params`、`fields`、`formats`、`resource_group`、`downloader_profile`、`next_run_at`、`backoff_until`、最近运行状态和错误。其中 `downloader_profile` 是当前 legacy runner 的兼容字段，不是新 Collector 插件的必填身份。
- `CollectorRun` 保存运行历史：`run_id`、`task_id`、`trigger_type`、`status`、参数、输出路径、开始/结束时间、耗时、错误、跳过原因、退避时间、quality、写入 metadata 和其它 metadata。
- 本地状态文件默认位于 `metadata/collector/collector_scheduler.json`，由 `data_root` 推导；不提交 runtime metadata。
- `CollectorSchedulerService` 提供单进程队列，默认同一 `resource_group` 串行，同一 task 或同一 run signature 的 active run 会跳过为 `active_duplicate`。
- 失败后默认设置 300 秒 `backoff_until`；退避期间提交会生成 `skipped` run，`skip_reason=failure_backoff`。
- API、CLI、Web 均可查询任务和运行状态，手动运行、启用、禁用任务。

当前边界：

- 不做分布式调度、复杂 DAG、云端任务系统或跨进程强一致资源租约。
- 当前取消是状态标记；如果底层线程已经开始执行，不保证强杀源端请求或写文件过程。
- 当前 run 状态没有单独的 `waiting_resource` / `waiting_dependency`；资源等待仍表现为 `queued` 或 `running` 等待。
- Stage/progress、输出锁可视化、交易日依赖阻塞、jitter、补漏重试等属于可扩展能力；不要把设计说明理解为当前已全部实现。

## 1.2 用户流程

用户可以通过 CLI、API 和 Web 管理已经存在的 CollectorSpec。`/v1/plugins/collectors` 和 CLI `plugin collectors` 由 CollectorRegistry 输出 collector catalog；旧 Provider manifest collectors 继续作为 `legacy_source=provider_manifest` 导入。默认采集目录保留 TDX 8 个核心采集器，由预装独立 collector plugin `axdata.collector.tdx` 提供，并通过 `runner_entry` 运行；交易所保留为 Source Provider 接口和本地基础数据能力，不再提供默认 CollectorSpec；`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 保留为源端接口和兼容下载入口，不再作为采集器展示。禁用或移除 Source Provider 只影响源端临时查询接口，不会影响 TDX 独立采集器。巨潮、腾讯、东方财富和新浪的预装接口保留 source_request-only 临时查询能力，不再默认生成 DownloaderProfile 或 CollectorSpec。

查看插件贡献的 collector 能力：

```powershell
.\.venv\Scripts\python -m axdata_core.cli plugin collectors --json
curl http://127.0.0.1:8666/v1/plugins/collectors
```

如果返回为空，表示当前启用的插件没有声明 CollectorSpec。创建 Collector task 需要一个真实存在的 `collector_name` 或 `collector_id`；DownloaderProfile 只能说明某个接口可批量下载，不自动等于 CollectorSpec。

创建 interval task：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task add <collector_name> `
  --task-id stock_codes_refresh `
  --trigger-type interval `
  --interval-seconds 3600 `
  --params '{\"scope\":\"all\"}' `
  --fields instrument_id,name,exchange `
  --formats parquet `
  --json
```

创建 daily task：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task add <collector_name> `
  --task-id daily_refresh `
  --trigger-type daily `
  --daily-time 18:00 `
  --json
```

手动提交并等待结果：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task run stock_codes_refresh --wait --json
```

查看状态：

```powershell
.\.venv\Scripts\python -m axdata_core.cli collector task list --json
.\.venv\Scripts\python -m axdata_core.cli collector run list --json
.\.venv\Scripts\python -m axdata_core.cli collector status --json
.\.venv\Scripts\python -m axdata_core.cli doctor --json
```

`collector run list` 和 `collector run info` 会展示 `status`、`started_at`、`finished_at`、`duration_ms`、
`error`、`skip_reason`、`backoff_until`、`quality`、`output_paths`、结构化 `events`、`stage_timings`、
`error_category`、`error_summary` 和 run metadata。非 JSON 输出也会把失败分类、阶段耗时、事件时间线、
跳过原因、耗时和输出路径放到摘要里，适合直接排错。task/run JSON 还会包含 `status_message`、`next_action`
和 `action_command`：disabled task 会提示 enable 命令，`failure_backoff` 会指向最近失败 run，
`active_duplicate` 会提示查看 active runs，等待资源组时会说明 `resource_group` 的占用与等待数。`doctor`
会汇总 task 数、active run、最近失败 run，并提示是否需要查看 `axdata collector run list --status failed --json`。

Run history 列表默认只返回最近记录：API 默认 100 条、单次最多 500 条，CLI `collector run list` 也限制单次窗口。`collector status` 和 `/v1/collector/status` 使用同一类最近窗口摘要，返回最近窗口计数、完整 run 总数、状态计数、active runs 和每个 task 的 latest run，不把完整历史作为状态页 payload。单个 run 的 `events` 是轻量时间线，当前保留开头事件和最近事件，避免长时间采集或频繁 progress callback 让 JSON metadata 无限制膨胀。当前 JSON store 仍适合本地单机和中等 run history；如果长期积累大量 run，应迁移到 SQLite/DuckDB metadata 或增加独立 run index，而不是把完整历史作为一个无限增长的列表接口。

API 等价入口：

- `GET /v1/collector/tasks`
- `POST /v1/collector/tasks`
- `PATCH /v1/collector/tasks/{task_id}`
- `POST /v1/collector/tasks/{task_id}/run`
- `POST /v1/collector/tasks/{task_id}/enable`
- `POST /v1/collector/tasks/{task_id}/disable`
- `GET /v1/collector/runs`
- `GET /v1/collector/runs/{run_id}`
- `GET /v1/tasks/{task_id}/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/collector/status`

Web 配置页的调度区域可以查看 task/run 状态、最近 run history、`quality`、`output_paths`、stage timings、event timeline、`status_message`、`next_action` 和 `action_command`，并执行手动运行、启用、禁用；当前 Web 支持从可用 task template 创建任务，但不提供任意手填 Collector task 的完整编辑器。

## 1.2.1 Default Collector Tasks

截至 2026-07-04，空的 Collector task store 会幂等 seed 一组产品默认任务。它们是真实
`CollectorTask`，会出现在 CLI、API 和 Web task 列表中，支持启用、禁用和手动 run now；默认均为
`enabled=false`，因此用户打开 AxData 后不会自动请求源端。

默认任务只覆盖第一稳定数据 loop：

| task_id | template_id | collector_name | schedule | resource_group | write_mode | 依赖 |
| --- | --- | --- | --- | --- | --- | --- |
| `stock_kline_daily_tdx_sample` | `stock_kline_daily_tdx` | `tdx.stock_kline_daily_tdx.snapshot` | manual，默认单只 `000001.SZ` 小样本 | `tdx.quote` | `snapshot` | `axdata.collector.tdx` + `trade_cal` |

Seed 策略：

- 只新增缺失的默认 task，不重复插入。
- 用户已修改默认 task 的 `enabled`、`params`、`trigger_type`、`interval_seconds`、`daily_time` 或 `name` 时，不覆盖这些修改。
- 模板升级时只刷新安全的显示和元数据字段，例如 `interface_name`、`expected_layer`、`schedule_hint`、`write_mode`、`partition_by`、`primary_key`、`date_field`、`required_datasets`、`dependency_status` 和 `tags`。
- 交易所基础数据不再通过默认 CollectorSpec 创建任务；交易日历缓存由“基础数据 / 交易日历”入口维护，交易所接口仍可做 source_request 临时查询。
- TDX 默认任务依赖 `axdata.collector.tdx`，不依赖 `axdata.source.tdx_external` 的启用状态；缺少或禁用 TDX 采集器插件时仍显示，但 `dependency_status` 会标记为缺失/禁用，run now 会生成失败 run，错误摘要提示“请安装/启用 TDX 采集器插件 (axdata.collector.tdx)”。
- TDX 日线任务声明系统基础数据依赖 `required_datasets=["trade_cal"]`。运行前调度器会检查本地基础交易日历，缺失时返回 `dependency_status=blocked` / `error_category=dependency_missing`，覆盖不足时提示补全指定范围。
- `stock_kline_daily_tdx_sample` 继续保持 `snapshot`，因为当前 TDX 日线轻量路径仍是源端样本口径，尚未稳定转换为 `daily.ts_code + trade_date` 事实表写入。

## 1.3 Task Template 与 Backfill

当前调度支持 task template、从模板创建核心采集任务、单次 run 参数覆盖、日期区间 backfill，以及更清晰的 task/run 状态字段。实现仍是单机单进程 Collector Scheduler，不做分布式调度、插件市场、签名或中心审核。

当前 TDX 插件贡献的模板只覆盖第一批核心闭环入口，并保持默认小样本或安全范围；交易所基础数据不再提供默认 CollectorSpec 模板：

| template_id | collector_name | 默认参数 | 说明 |
| --- | --- | --- | --- |
| `daily` | `tdx.stock_kline_daily_tdx.snapshot` | `{"code":"000001.SZ","count":800,"adjust":"none"}` | TDX 日 K 线小样本任务。 |
| `stock_kline_daily_tdx` | `tdx.stock_kline_daily_tdx.snapshot` | `{"code":"000001.SZ","count":800,"adjust":"none"}` | TDX 日 K 线显式模板。 |

TDX 模板需要 `axdata.collector.tdx` 已安装并启用；缺失时模板列表会显示 `next_action` 和 `action_command`。其中日线还需要基础数据 `trade_cal`；Web 的“基础数据 / 交易日历”入口会同步本地交易日历 cache。模板不会把 TDX core fallback 带回 core，也不会默认全市场重采。`axdata.source.tdx_external` 仍控制 TDX 源端临时查询接口和 `/v1/downloaders` 兼容入口，但不再是 TDX 默认采集任务的依赖。

CLI：

```powershell
.\.venv\Scripts\axdata collector task templates --json
.\.venv\Scripts\axdata collector task create-from-template stock_kline_daily_tdx --json
.\.venv\Scripts\axdata collector task run stock_kline_daily_tdx_sample --params '{\"count\":20}' --wait --json
.\.venv\Scripts\axdata collector task backfill stock_kline_daily_tdx_sample --start 20260101 --end 20260131 --params '{\"count\":20}' --wait --json
```

API：

- `GET /v1/collector/tasks/templates` 和别名 `GET /v1/tasks/templates`
- `POST /v1/collector/tasks/from-template` 和别名 `POST /v1/tasks/from-template`
- `POST /v1/collector/tasks/{task_id}/run` 支持 `params`、`start`、`end`、`symbol`、`limit`
- `POST /v1/collector/tasks/{task_id}/backfill` 支持必填 `start`、`end`，以及 `params`、`symbol`、`limit`

单次 run/backfill 不修改持久 task 定义。覆盖参数会记录在 `CollectorRun.params_override`，最终运行参数记录在 `CollectorRun.params`；backfill 还会在 `metadata.run_mode=backfill` 和 `metadata.backfill_range` 里记录日期范围。调度层只校验日期格式和区间顺序，具体源端是否支持 `start_date/end_date/code/limit/count` 由 Collector/Downloader 执行时校验。backfill 记录范围不等于自动去重；是否避免重复写入取决于 DownloaderProfile 的 `write_mode`、`primary_key`、`partition_by` 和 `date_field`。当前默认 `stock_kline_daily_tdx` 仍保持快照写出。

task/run JSON 现在还会透传：

- `last_failure_at`
- `last_error_summary`
- `queue_status`
- `can_run_now`
- `blocked_reason`
- `params_override`
- `events`
- `stage_timings`
- `error_category`
- `error_summary`
- `write_mode`
- `partition_by`
- `primary_key`
- `date_field`
- `replace_range_start` / `replace_range_end`
- `rows_before` / `rows_written` / `rows_after`
- `duplicate_rows_dropped`
- `partitions_touched`

这些字段兼容旧 metadata：缺字段时读取为 `null`、空列表、空 timing 或默认 ready 状态。Web 的 Scheduler 页面现在可以查看模板、从可用模板创建任务、查看 next run / 最近成功 / 最近失败 / backoff / blocked reason，并提交小范围 backfill。API 失败时仍显示错误文本，不白屏。

## 1.4 Run 诊断信息

Collector run detail 已有结构化诊断能力。该能力只增强当前单机 Collector Scheduler 和 Downloader run metadata，不重写调度器，不做分布式任务工作进程，也不改变 Provider 插件安装/启用边界。

每个新 run 会持久化：

| 字段 | 说明 |
| --- | --- |
| `events` | 轻量事件时间线，包含 `sequence/event_id/timestamp/stage/level/message/category/details`。事件不存大 payload，不记录 token、secret、password、authorization 或 api_key。 |
| `stage_timings` | 阶段耗时，当前字段为 `queue_wait_ms`、`params_resolve_ms`、`provider_resolve_ms`、`download_ms`、`write_ms`、`quality_ms`、`total_ms`；未跑到的阶段为 `null`。 |
| `error_category` | 失败或跳过分类。成功但质量检查为 blocking error 时会标为 `quality_failed`。 |
| `error_summary` | 适合列表和终端展示的短错误摘要。完整上下文仍看 `error`、`quality`、`events` 和 `metadata`。 |
| `next_action` / `action_command` | 根据状态和错误分类给出的下一步动作。 |

`stage` 包括 `queued`、`started`、`params_resolved`、`request_planned`、`downloaded`、`written`、`quality_checked`、`metadata_recorded`、`finished`、`skipped`、`failed`。Downloader 返回的 `duration_breakdown_ms` 会映射到 Collector run 的 `download/write/quality` timing；失败时仍保存已经知道的排队和总耗时。

错误分类包括：

```text
provider_missing / plugin_disabled / plugin_failed / dependency_missing /
invalid_params / network_error / upstream_empty / upstream_error /
schema_mismatch / quality_failed / write_failed / storage_missing /
storage_permission / duplicate_skipped / backoff_blocked / resource_waiting /
unknown
```

分类是保守启发式：已知异常类型和关键字会尽量归入具体类别，无法可靠判断时使用 `unknown`。默认测试只使用离线异常样例覆盖分类，不请求真实网络。

## 2. 术语

| 名称 | 含义 |
| --- | --- |
| Job | 用户创建的一次采集任务定义，例如每日 18:00 采集最新股票列表 |
| Run | Job 的一次实际运行，例如 2026-06-22 18:00 这次运行 |
| Stage | Run 执行阶段，例如拉股票池、拉快照、清洗、写文件 |
| Resource Group | 源端资源组，例如 `tdx.quote`、`tdx.f10`、`tencent.http` |
| Budget | 单个 Run 希望使用的资源预算 |
| Limit | 全局资源池允许同时使用的资源上限 |
| Lease | Run 从资源池拿到的临时资源占用 |

## 3. 核心原则

同一时间触发不等于同一时间开跑。

正确流程：

```text
timer/manual trigger -> enqueue run -> resource manager grants lease -> execute -> release lease
```

如果 10 个任务都设置为 18:00：

- 18:00 时它们都进入队列。
- Collector 按资源组和优先级决定谁先跑。
- 没拿到资源的任务保持 `queued`，并可在 metadata 中记录资源等待信息；更细的 `waiting_resource` 状态可作为扩展能力。
- 不允许 10 个任务各自按页面配置直接开满并发。

## 3.1 插件采集器契约

插件可以声明采集器，但不能绕过 AxData 调度器自行长期运行。新 CollectorSpec 至少应表达：

| 字段 | 说明 |
| --- | --- |
| `collector_id` / `name` | 采集器系统 ID；`name` 是旧字段别名 |
| `display_name_zh` | 展示名 |
| `collector_plugin_id` | 贡献该采集器的插件 ID |
| `dataset_id` | 采集输出的数据集 ID |
| `asset_class` / `category` | 资产类别和业务分类 |
| `runner_entry` | Collector Runner 调用的 Python 入口 |
| `resource_group` | 默认资源组 |
| `default_params` | 默认采集参数 |
| `config_schema` | 用户可配置参数和本地配置提示 |
| `default_schedule` | 默认调度建议，用户可覆盖 |
| `output` | 输出层、格式、写入模式和路径建议 |
| `quality` | required columns、主键、日期字段、数值约束等质量契约 |
| `lifecycle_status` | experimental、stable、deprecated 等生命周期状态 |
| `interfaces` | deprecated；旧 Provider manifest 兼容字段 |
| `required_interfaces` | deprecated；旧 Provider manifest 兼容字段 |
| `downloader_profile` | deprecated；旧 Provider manifest 兼容字段 |

允许的插件形态：

- Provider 插件不带采集器。
- Provider 插件同时带 legacy collectors，作为兼容路径。
- Collector 插件只带采集器，不提供 Provider，也不伪造 Provider 身份。
- 同一个包同时提供 Provider 和独立 Collector 时，也必须把 `interface_name`、`collector_id` 和 `dataset_id` 分开命名。

运行规则：

- 插件只声明采集能力，不直接开后台线程。
- 手动、定时、Web、API 启动的采集都进入 AxData 队列。
- Collector Runner 通过 `runner_entry` 执行新采集器，统一记录 run、stage、日志、输出文件和质量结果。
- 新采集器不得通过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或旧 DownloaderProfile -> Adapter 链路套接口采集；它可以自带取数逻辑、读取本地文件或使用自己的上游客户端。
- 旧 Provider manifest collectors 可以继续经 `interfaces` / `downloader_profile` / `run_downloader()` 路径执行，但必须在 catalog 和 UI 中标记为 legacy，不得包装成最终形态。
- 写入 raw/staging/core/factor 必须通过 AxData Writer 和 metadata 体系。
- 卸载或禁用插件时，AxData 应能识别该插件贡献的采集器并从可用列表移除。
- 插件卸载不删除用户创建的 CollectorTask 或 Run History。插件贡献的 CollectorSpec 和 task template 会随插件禁用/卸载从可用能力中消失；已有 Task 保留为本地配置，`dependency_status` 刷新为 `disabled`、`missing` 或 `uninstalled`，run now 会生成清晰的失败 run（例如 `plugin_disabled`、`collector_missing` 或 legacy `provider_missing`），而不是崩溃或静默删除历史。
- Run History 是历史事实，只记录当时的任务、参数、输出、质量和错误；插件卸载、重装或禁用都不回写删除既有 run。

## 4. Resource Group

Provider 的 DownloaderProfile 和独立 CollectorSpec 都可以声明资源组。旧下载 profile 继续通过接口下载路径提供资源组；新采集器应直接在 CollectorSpec 中声明 `resource_group`，由 Collector Runner 按同一资源池限流。

```json
{
  "resource_group": "tdx.quote",
  "default_limits": {
    "max_active_jobs": 1,
    "max_connections_total": 8,
    "request_interval_ms": 0
  }
}
```

资源组命名建议：

```text
{source_code}.{resource_type}
```

示例：

| 资源组 | 用途 |
| --- | --- |
| `tdx.quote` | TDX 7709 普通行情 |
| `tdx.f10` | TDX F10 题材、资料、公告类 |
| `tdx.ext` | TDX 拓展行情 |
| `tencent.http` | 腾讯财经公开 HTTP |
| `cninfo.http` | 巨潮公开 HTTP |

同一个上游连接预算内的接口必须共用资源组。不要为了每个接口单独建资源组，否则全局调度无法防止源端拥挤。

## 5. Limits

资源组限制分两层：

| 层级 | 来源 | 作用 |
| --- | --- | --- |
| Plugin default | CollectorSpec 或 DownloaderProfile | 插件作者建议 |
| Local override | 用户或管理员配置 | 当前机器实际执行上限 |

最终执行以 local override 为准；没有 override 时使用 Provider default。

建议限制字段：

| 字段 | 说明 |
| --- | --- |
| `max_active_jobs` | 同一资源组同时运行的 Run 数 |
| `max_connections_total` | 同一资源组总连接数 |
| `max_requests_per_second` | 每秒请求数上限，可选 |
| `request_interval_ms` | 请求间隔，可选 |
| `max_retries` | 默认重试次数 |
| `backoff_base_ms` | 退避基准 |
| `backoff_max_ms` | 最大退避 |

TDX 这类长连接源更关注连接数；HTTP 源更关注请求频率和退避。

## 6. Budgets

单个任务可以有自己的执行预算，例如：

```json
{
  "server_count": 4,
  "connections_per_server": 2,
  "batch_size": 80
}
```

任务预算不能突破资源组全局限制。如果任务预算需要 8 条连接，但资源组当前只剩 4 条连接，调度器可以：

- 等待足够资源。
- 降级为可用资源运行，前提是 profile 声明支持降级。
- 保持 `queued` 并记录资源等待信息；更细的 `waiting_resource` 状态可作为扩展能力。

是否允许降级由 DownloaderProfile 声明：

| 字段 | 含义 |
| --- | --- |
| `allow_degraded_budget` | 资源不足时是否允许少量资源运行 |
| `min_connections_total` | 降级运行所需最小连接数 |

没有声明时，默认等待足够资源。

## 7. 队列策略

Run 状态：

| 状态 | 含义 |
| --- | --- |
| `pending` | 已创建，未到触发时间 |
| `queued` | 已到触发时间，等待调度 |
| `running` | 正在执行 |
| `success` | 成功 |
| `failed` | 失败 |
| `skipped` | 因已有成功结果或规则跳过 |
| `cancelled` | 被取消 |

可以扩展 `waiting_resource`、`waiting_dependency` 等更细状态。当前为了保持 API/CLI/Web 返回结构稳定，
只使用上表七个状态；资源组等待和依赖等待通过 metadata/message 或跳过原因表达。

优先级建议：

1. 用户手动触发的任务高于普通定时任务。
2. 修复任务高于普通增量任务。
3. 同优先级按触发时间排序。
4. 同源同接口可增加 jitter，避免整点同时打源端。

手动任务可以插队，但仍受资源组限制。

## 8. 重复运行策略

同一接口、同一参数、同一数据日期、同一输出目录，如果当天已经成功：

- 默认提示用户已有结果。
- 自动任务默认 `skipped`。
- 手动任务可以选择覆盖、另存或跳过。

文件名有时间戳时，也需要记录逻辑数据日期，避免仅凭文件名判断是否重复。

## 9. 阶段模型

一个 Run 可以拆成多个 Stage：

```text
prepare -> source_fetch -> normalize -> write -> quality -> finalize
```

每个 Stage 记录：

- 开始时间。
- 结束时间。
- 耗时。
- 处理数量。
- 错误数量。
- 资源占用。

Web 进度应展示各阶段耗时，让用户知道慢在源端、清洗还是写文件。

对多阶段接口，例如“先拉股票池，再批量拉快照”：

- 股票池阶段可以使用自己的小预算。
- 快照阶段可以使用另一个预算。
- 两个阶段可以共享同一资源组，也可以声明不同资源组。
- UI 说明应写清阶段差异，不要只显示一个模糊并发数。

## 10. 进度模型

进度字段：

| 字段 | 说明 |
| --- | --- |
| `total_units` | 总工作量，例如总股票数、总页数、总请求数 |
| `completed_units` | 已完成工作量 |
| `failed_units` | 失败工作量 |
| `current_stage` | 当前阶段 |
| `stage_elapsed_ms` | 当前阶段耗时 |
| `elapsed_ms` | 总耗时 |
| `eta_ms` | 预计剩余时间，可为空 |
| `throughput` | 近期速度 |

ETA 原则：

- 只有在 `total_units` 已知且已完成足够样本后才显示。
- 样本太少时显示“计算中”，不要给假精确。
- 源端波动很大时，可以显示区间，例如 `约 20-40 秒`。
- 比起不准的 ETA，更重要的是展示 `completed/total` 和各阶段耗时。

## 11. Retry And Backoff

失败类型：

| 类型 | 策略 |
| --- | --- |
| 参数错误 | 不重试，直接失败 |
| 上游限流 | 指数退避后重试 |
| 上游超时 | 重试 |
| 单个标的失败 | 记录 failed unit，按 profile 决定是否补漏 |
| 写文件失败 | 不重试或有限重试，保护数据一致性 |

退避建议：

```text
sleep = min(backoff_max_ms, backoff_base_ms * 2 ** retry_count) + jitter
```

补漏策略应由 profile 声明。例如 F10 题材可以先用 6 个执行单元拉取，漏了再用 6 个执行单元补漏；如果没漏，不进入补漏阶段。

## 12. Output Locks

同一输出目标必须加锁。锁粒度建议：

```text
data_root + provider_id + interface_name + output_format + logical_data_date
```

写文件原则：

- 先写临时文件。
- 写完校验后原子 rename。
- manifest 最后写。
- 如果失败，不留下看起来成功的最终文件。

锁只保证同一 collector 进程或同一机器上的文件写冲突。跨机器共享存储的强锁属于云端部署能力，当前不承诺。

## 13. 单进程边界

全局并发保证只在单个常驻 collector 服务进程内成立。

明确不承诺：

- 两个 Python 脚本绕过 collector 同时跑，还能共享连接预算。
- 两台机器同时写同一个共享目录，还能靠本地文件锁完全协调。
- SQLite 或文件锁能提供分布式强一致 lease。

可以做 best-effort：

- 同机输出目录文件锁。
- 临时文件 + 原子 rename。
- 启动时扫描残留 running 状态并标记 interrupted。

但文档和 UI 不应把 best-effort 描述成硬保证。

## 14. Manual Runs

手动采集：

- 可以比普通定时任务优先。
- 必须显示排队原因。
- 必须受资源组全局限制。
- 用户可以取消 queued 或 running run。
- running 取消应尽量释放连接和文件锁。

如果手动任务和自动任务使用同一输出目标：

- 自动任务已在跑时，手动任务默认等待或提示。
- 手动任务已在跑时，自动任务默认 skipped 或 queued，按配置决定。

手动运行通过 `POST /v1/collector/tasks/{task_id}/run` 或
`axdata collector task run <task_id>` 提交。提交成功会立刻返回 `run_id`，实际执行在线程池中异步完成；
同一 task 或同一 run signature 已 active 时，新 run 会记录为 `skipped`，`skip_reason=active_duplicate`。

## 15. Scheduled Runs

定时采集：

- 保存前应检查所需基础依赖是否可用，例如交易日历。
- 到点后只创建 Run 并入队。
- 如果错过触发时间，启动时可以补创建缺失 Run。
- 可以增加随机 jitter，避免多个任务同一秒请求源端。

交易日逻辑：

- 需要交易日判断的任务应读取本地交易日历缓存。
- 如果日历缺失，可通过 metadata/message 或错误文本表达；更细的 `waiting_dependency` 状态或保存配置提示可作为扩展能力。
- 日历更新本身是独立任务，也应进队列，但通常资源组不同。

当前支持 `manual`、`interval` 和 `daily`。`interval` 使用 `interval_seconds` 计算下一次触发，
`daily` 使用本地 `HH:MM` 字符串计算下一次触发；服务启动后后台 loop 按固定 tick 检查 due task。
启动时不会自动补跑所有错过的历史触发，也不内置复杂 cron 或高级时区规则。

## 16. Web Status

Web 应展示：

- 当前状态。
- 当前阶段。
- 进度百分比。
- 已完成/总数。
- 当前资源组。
- 占用连接数。
- 排队原因。
- 源端耗时、清洗耗时、写文件耗时。
- 最近错误。
- 输出文件。

示例文案：

```text
等待中：tdx.quote 资源组已占用 8/8 连接，前面还有 2 个任务。
运行中：快照阶段，已完成 3200/5350，tdx.quote 占用 8/8 连接。
写文件：源端 5.2s，清洗 0.4s，写入 0.2s。
```

不要只显示“采集中”，用户无法判断是卡住、排队还是慢。

## 17. Metrics

每次 Run 至少记录：

- `run_id`
- `job_id`
- `collector_id` / `collector_name`
- `collector_plugin_id`
- `dataset_id`
- `provider_id` / `interface_name`（legacy 路径可选）
- `resource_group`
- `trigger_type`
- `status`
- `started_at`
- `finished_at`
- `elapsed_ms`
- `source_elapsed_ms`
- `normalize_elapsed_ms`
- `write_elapsed_ms`
- `rows_written`
- `rows_before`
- `rows_after`
- `duplicate_rows_dropped`
- `partitions_touched`
- `requests_total`
- `requests_failed`
- `retry_count`
- `output_files`

这些指标用于 Web 展示、日志排查和优化默认并发。

## 18. 当前支持能力

独立采集器体系的本地单机主路径已经落地：

1. `CollectorSpec` 已支持 `collector_id` / `collector_plugin_id` / `dataset_id` / `runner_entry` / `output` / `quality` 等独立采集器字段，并保留 `interfaces`、`required_interfaces`、`downloader_profile` 为 deprecated 兼容字段。
2. `CollectorRegistry` 已成为 `/v1/plugins/collectors`、CLI `plugin collectors` 和 Web 采集页的采集器 catalog 事实源；旧 Provider manifest collectors 只作为 `legacy_source=provider_manifest` 导入。
3. 新 `runner_entry` 路径已接入 Collector Runner、Writer、Quality、Metadata 和 Run History；新 runner 不经过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或 DownloaderProfile -> Adapter 链路。
4. 默认 collector catalog 当前为 8 个 independent / non-legacy collectors，均由 `axdata.collector.tdx` 提供；交易所保留为 Source Provider 接口和本地基础数据能力，不再提供默认 CollectorSpec；`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 保留为源端接口和兼容下载入口，不再作为采集器展示。巨潮、腾讯、东方财富和新浪仍保留 source_request 接口，但默认不提供采集器。
5. Web 采集页已改成“采集插件 / 采集任务”视角：侧栏一级按采集插件分组，插件下展示各自采集任务；接口页只提示“相关采集器”，不再把接口本身描述为采集器。

需要继续加强的是长期采集能力，而不是把旧接口路径重新当成采集器主线：资源组 jitter、补漏策略、跨进程/云端资源租约、更多资产的独立 Collector plugin、TDX 日线全市场 raw/staging -> core 转换和长期真实源小样本检查。

