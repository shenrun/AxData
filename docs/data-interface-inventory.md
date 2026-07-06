# 数据接口资产一览（维护者参考）

本文记录 AxData 接口资产、默认采集能力和兼容下载能力，主要服务维护者盘点和发布前检查。矩阵中的“闭环”只表示接口已经进入 Registry、source_request、Downloader/Collector 声明、文件写出和离线测试链路；不等于全市场长期采集、raw/staging -> core 转换或真实源长期稳定性已经完成。真实源小样本检查默认不联网，只有显式 `--run` 才请求上游。

## 当前接口口径

当前 source_request 合并目录为 256 个接口：TDX 普通行情 90 个、TDX Ext 31 个、core/generic 135 个。`stock_quote_refresh_tdx` 是 `/v1/stream/stock_quote_refresh_tdx` 实时流，不属于 source_request catalog；Web 接口页如包含该静态流条目，页面条目数可能为 257。下方带日期的历史章节保留当时背景，接口数量以本节口径为准。

## 状态定义

| 状态 | 含义 |
| --- | --- |
| complete | 已有底层实现，manifest/catalog 可见，source_request 可路由，有 schema 字段说明，有 DownloaderProfile/CollectorSpec，可写 Parquet 主数据，并可选 CSV 导出或 DuckDB 查询缓存；离线测试覆盖写出与 DuckDB 读回或等价链路，并声明基础 quality contract。 |
| source_request-only | 已有底层实现、catalog、source_request 路由、参数字段和样例，但默认不提供 DownloaderProfile/CollectorSpec；适合临时查询，或由独立采集器插件重新设计入库。 |
| partial | 已有主要能力，但某些包 manifest、生产级 core 转换、真实源 smoke 或 CollectorSpec 尚未同步。 |
| adapter-only | 已有源端实现和 catalog/source_request，但还没有采集 profile 或入库链路。 |
| documented-only | 文档设计存在，代码未落地。 |
| blocked | 受 token、上游权限、缺插件、缺网络或其它外部条件阻塞。 |

## 当前默认采集口径

以下 6 个非核心预装源默认采集能力不再进入采集目录：`cninfo.cninfo_announcements.snapshot`、`cninfo.cninfo_announcement_detail.snapshot`、`tencent.tencent_realtime_snapshot.snapshot`、`eastmoney.eastmoney_dragon_tiger_daily.snapshot`、`eastmoney.eastmoney_margin_trading.snapshot`、`eastmoney.eastmoney_research_reports.snapshot`。这些接口对应的 Provider、InterfaceSpec、Adapter 和 `/v1/request/*` 临时查询能力仍保留；`collection.supported=false`，不再出现在 `/v1/plugins/collectors` 或 `/v1/downloaders`。

交易所 3 个核心能力保留为 Source Provider 接口、source_request 临时查询和兼容 DownloaderProfile，不再作为默认 CollectorSpec 进入 CollectorRegistry。`axdata.source.exchange` 禁用或移除后，交易所源端接口路由会消失；采集页不会保留独立交易所采集器。交易所 3 个 DownloaderProfile 保留，供 `/v1/downloaders` 和旧显式下载入口兼容。

TDX 核心采集器由预装独立 collector plugin `axdata.collector.tdx` 提供。当前采集页保留 8 个 TDX 独立采集器：`tdx.stock_codes_tdx.snapshot`、`tdx.stock_suspensions_tdx.snapshot`、`tdx.stock_st_list_tdx.snapshot`、`tdx.stock_daily_share_tdx.snapshot`、`tdx.stock_daily_price_limit_tdx.snapshot`、`tdx.stock_kline_daily_tdx.snapshot`、`tdx.stock_limit_ladder_tdx.snapshot`、`tdx.stock_theme_strength_rank_tdx.snapshot`。`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 保留为源端接口和兼容 DownloaderProfile，但不再作为采集器展示。这些采集器使用 `axdata_source_tdx.collectors:run_tdx_collector` 作为 `runner_entry`，直接调用 TDX provider package adapter/request 逻辑，不通过 `/v1/request`、SDK、ProviderRegistry route 或 DownloaderProfile 采集。TDX DownloaderProfile 仍保留，供 `/v1/downloaders` 和旧显式下载入口兼容。日线仍是显式代码小样本写入路径，不代表全市场 raw/staging -> core 转换已经完成。

当前默认采集口径：

| 指标 | 结果 | 说明 |
| --- | ---: | --- |
| 预装源接口 | 9 | 交易所 3、巨潮 2、腾讯 1、东方财富 3，全部仍是 source_request 接口。 |
| 预装源 DownloaderProfile | 3 | 仅交易所 `stock_trade_calendar_exchange`、`stock_historical_list_exchange`、`stock_basic_info_exchange`，作为显式下载兼容入口保留。 |
| 预装源 legacy CollectorSpec | 0 | 交易所 Provider manifest 不再声明 legacy collector；巨潮、腾讯、东方财富、新浪也没有默认 collector。 |
| 内置独立 CollectorSpec | 8 | `axdata.collector.tdx` 提供 TDX 核心 8 个；交易所和复权因子不再提供默认 CollectorSpec。 |
| 有兼容下载信息的核心接口 | 13 | 交易所 3 + TDX 普通行情 10；这些接口可用于显式下载兼容入口，但采集器身份以 CollectorRegistry 的 CollectorSpec 为准。 |
| 默认 CollectorSpec | 8 | TDX 独立采集器 8；TDX Ext 仍为 0。 |
| 启用 TDX source 后 CollectorSpec | 8 | TDX source Provider manifest 不再贡献 collectors；启用 source 只影响源端接口和 `/v1/downloaders` 兼容入口。 |

## 历史兼容记录

以下记录用于解释旧 Provider manifest collectors 的兼容背景；不要把本节的 20 个 legacy CollectorSpec 和 ProviderRegistry catalog 口径当作当前状态。当前状态以上方“当前默认采集口径”为准。

旧口径中，Source Provider Registry 曾同时承担接口和采集器目录。现在的产品边界是：Source Provider Registry 管接口临时查询；Collector Registry 管采集器插件和本地资产生产。接口 ID、采集器 ID、数据集 ID 必须独立；采集器可以和接口显示同一个中文名，但系统 ID 不得混用。

旧口径运行态：

| 指标 | 结果 | 说明 |
| --- | ---: | --- |
| Provider 插件 | 7 | `/v1/plugins/providers` 返回交易所、巨潮、腾讯、东方财富、新浪、TDX、TDX Ext。 |
| 接口 | 131 | 预装源插件 10 + TDX 普通行情 90 + TDX Ext 31。 |
| DownloaderProfile | 20 | 预装源插件 10 + TDX 普通行情 10。 |
| CollectorSpec | 20 | `/v1/plugins/collectors` 返回 `meta.catalog_source=axdata_core.provider_registry`。 |

当前 20 个 CollectorSpec 全部是 legacy provider-manifest / downloader-profile 形态，不是独立 collector plugin：

| 来源 | 数量 | 生成位置 | 特征 |
| --- | ---: | --- | --- |
| 预装源轻量 collector | 10 | `libs/axdata_core/axdata_core/builtin_providers.py::_generic_builtin_collector_spec()` | 每个 collector 对应一个 interface 和一个 `.snapshot` DownloaderProfile。 |
| TDX 普通行情轻量 collector | 10 | `packages/axdata-source-tdx/.../axdata-provider.json` 与 `collectors.py` | 每个 collector 声明 `interfaces`、`required_interfaces` 和 `downloader_profile`。 |
| TDX Ext | 0 | `packages/axdata-source-tdx-ext` | 只有 31 个 source_request 接口，尚无 downloader/collector。 |

代码依赖链：

- `CollectorSpec` 当前定义在 `libs/axdata_core/axdata_core/plugins.py`，主字段仍是 `name`、`interfaces`、`downloader_profile`、`required_interfaces`、`resource_group`、`output`。
- `ProviderRegistrySnapshot.collectors` 和 `ProviderRegistry._rebuild_collectors()` 仍从 Provider manifest 合并 collectors。
- `provider_catalog.list_registry_collector_dicts()` 把 ProviderRegistry collectors 投影给 CLI/API。
- API `/v1/plugins/collectors` 在 `apps/api/plugin_routes.py` 中调用 `list_registry_collector_dicts()`，因此 catalog source 仍是 `axdata_core.provider_registry`。
- CLI `axdata plugin collectors` 也调用 `provider_catalog.list_registry_collector_dicts()`。
- `collector_runner.py` 从 ProviderRegistry 解析 collector，再解析 `downloader_profile` 或单个 interface，最后调用 `run_downloader()`；这正是 legacy 路径。
- Web 左侧“采集”页当前仍从 `/v1/downloaders` 得到可采集 `interface_name` 列表并按接口展示；配置页已有 Collector task/template 面板，但采集页产品语义仍在过渡。

兼容要求：

- 新增 CollectorRegistry 作为采集器 catalog 事实源，支持 `axdata-plugin.json` collector-only 插件。
- 旧 Provider manifest collectors 继续导入，但必须标记 `legacy_source=provider_manifest`。
- `/v1/plugins/collectors`、CLI `plugin collectors`、task template 可用性和 Web 采集页应逐步改为读取 CollectorRegistry。
- 新 CollectorSpec 至少支持 `collector_id`/`name`、`collector_plugin_id`、`dataset_id`、`asset_class`、`category`、`default_params`、`config_schema`、`default_schedule`、`output`、`quality`、`runner_entry`、`resource_group`、`lifecycle_status`。
- `interfaces`、`required_interfaces`、`downloader_profile` 保留为 deprecated 兼容字段；新采集器不得通过 `/v1/request`、SDK `call`、ProviderRegistry route 或旧 DownloaderProfile 链路套接口采集。

## 第一批预装源插件接口

以下为交易所、巨潮、腾讯、东方财富、新浪财经这些随 AxData 提供的预装源插件中已经封装的源端接口。选择原因：已有 adapter/catalog，实现不依赖新增数据源；默认离线测试可覆盖；字段结构相对稳定；能复用通用 Downloader/Collector 小批量快照路径。它们按预装插件管理，不是不可卸载的 Core 内置数据源。

| interface_name | 中文说明 | 数据源/provider | 底层实现 | manifest/catalog | source_request | schema字段 | Collector/Downloader | Parquet/CSV/DuckDB | DuckDB | 离线测试 | 真实源 smoke | 状态 | 优先级 | 缺口说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stock_trade_calendar_exchange` | 交易日历 | `axdata.source.exchange` | 交易所 adapter | 预装源接口 catalog | 精确路由；禁用 source 后接口不可调 | catalog 字段；core `trade_cal` schema | 兼容 DownloaderProfile `stock_trade_calendar_exchange.snapshot`；无默认 CollectorSpec | 支持显式下载兼容 | source/smoke 可写临时 core 样本 | manifest/catalog/downloader/source_request 测试 | 默认 dry skip；核心 smoke 可显式运行 | complete | P0 | 默认采集器已下线；交易日历缓存由基础数据入口维护。 |
| `stock_historical_list_exchange` | 历史股票列表 | `axdata.source.exchange` | 交易所 adapter | 预装源接口 catalog | 精确路由；禁用 source 后接口不可调 | catalog 字段 | 兼容 DownloaderProfile `stock_historical_list_exchange.snapshot`；无默认 CollectorSpec | 支持显式下载兼容 | source snapshot 可 DuckDB 读回 | manifest/catalog/downloader/source_request 测试 | 可显式 `--interfaces stock_historical_list_exchange` | complete | P1 | 默认不映射为稳定 core 表；默认不生成采集任务。 |
| `stock_basic_info_exchange` | 股票基础信息 | `axdata.source.exchange` | 交易所 adapter | 预装源接口 catalog | 精确路由；禁用 source 后接口不可调 | catalog 字段；core `stock_basic_exchange` schema | 兼容 DownloaderProfile `stock_basic_info_exchange.snapshot`；无默认 CollectorSpec | 支持显式下载兼容 | source/smoke 可写临时 core 样本 | manifest/catalog/downloader/source_request 测试 | 默认 dry skip；核心 smoke 可显式运行 | complete | P0 | 默认采集器已下线；全市场 core latest/history 重建策略仍需补生产任务。 |
| `cninfo_announcements` | 公告列表 | `axdata.source.cninfo` | 巨潮 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces cninfo_announcements` 做 source-only smoke | source_request-only | P1 | PDF 正文解析不在本接口范围内；如需归档应由独立公告采集器重新设计。 |
| `cninfo_announcement_detail` | 公告 PDF 元信息 | `axdata.source.cninfo` | 巨潮 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces cninfo_announcement_detail` 做 source-only smoke | source_request-only | P2 | 依赖具体 PDF URL；不解析正文；默认不生成采集任务。 |
| `tencent_realtime_snapshot` | 实时快照 | `axdata.source.tencent` | 腾讯 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces tencent_realtime_snapshot` 做 source-only smoke | source_request-only | P1 | 实时快照默认不进入历史 core；持久化应由独立录制/快照采集器实现。 |
| `eastmoney_dragon_tiger_daily` | 龙虎榜每日汇总 | `axdata.source.eastmoney` | 东方财富 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces eastmoney_dragon_tiger_daily` 做 source-only 小样本检查 | source_request-only | P1 | 日期无记录时可能返回空；如需入库应先定义专题数据集。 |
| `eastmoney_margin_trading` | 融资融券明细 | `axdata.source.eastmoney` | 东方财富 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces eastmoney_margin_trading` 做 source-only 小样本检查 | source_request-only | P1 | 默认不映射为稳定 core 表；默认不生成采集任务。 |
| `eastmoney_research_reports` | 个股研报列表 | `axdata.source.eastmoney` | 东方财富 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces eastmoney_research_reports` 做 source-only smoke | source_request-only | P2 | 只返回研报元信息；不抓取附件正文；默认不生成采集任务。 |
| `stock_financial_report_sina` | JSON 财务报表 | `axdata.source.sina` | 新浪财经 adapter | 预装插件 manifest、Registry catalog | 精确路由 | catalog 字段 | 无；source_request-only | 不通过默认 Downloader 写出 | 不接默认写出 | manifest/catalog/source_request 测试 | 可显式 `--interfaces stock_financial_report_sina` 做 source-only smoke | source_request-only | P1 | JSON 财报源端口径，字段更完整；默认不生成采集任务。 |

## 其它已有接口资产

| 接口族 | 中文说明 | 数据源/provider | 底层实现 | manifest/catalog | source_request | schema字段 | Collector/Downloader | Parquet/CSV/DuckDB | DuckDB | 离线测试 | 真实源 smoke | 状态 | 优先级 | 缺口说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TDX 普通行情 90 个接口 | 股票、指数、ETF、K 线、F10、短线等 | `axdata.source.tdx_external` + `axdata.collector.tdx` | 外部 TDX 包 adapter | 外部包 manifest 90 接口；TDX 8 个独立 collector catalog | source 插件可用后精确路由；TDX 独立采集器不依赖 source Provider 启用状态 | 插件 catalog 字段；`daily`/`adj_factor` core schema 已有 | 10 个 DownloaderProfile；8 个 independent CollectorSpec：`stock_codes_tdx`、`stock_suspensions_tdx`、`stock_st_list_tdx`、`stock_daily_share_tdx`、`stock_daily_price_limit_tdx`、`stock_kline_daily_tdx`、`stock_limit_ladder_tdx`、`stock_theme_strength_rank_tdx`；`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 仅保留源端接口/兼容下载；0 个 legacy Provider-manifest CollectorSpec | Parquet 主数据；CSV/DuckDB 可选；兼容下载仍支持旧格式 | 已有 downloader 写出测试和核心离线闭环；TDX runner_entry 离线测试覆盖；日线离线样例写出后可读回；profile 和 independent spec 已声明 required/date/numeric/field mapping quality contract | 包级、路由、downloader、collector、离线 collection 测试 | `daily` 可显式小样本检查；TDX 真实请求需插件可用且连接可用 | partial | P0/P1 | TDX 日线仍保留源端 `instrument_id/trade_time/volume` 并通过 mapping 对齐 `daily.ts_code/trade_date/vol`；复权因子接口和 schema 保留，但不再作为采集器；全市场 raw/staging -> core 转换仍未完成。 |
| TDX Ext 31 个接口 | 期货、期权、基金、债券、外汇、宏观扩展行情 | `axdata.source.tdx_ext_external` | 外部 TDX Ext 包 adapter/cache | 外部包 manifest 31 接口 | 启用插件后精确路由 | 插件 catalog 字段 | DownloaderProfile 0，CollectorSpec 0 | 未接统一写出 | 未接 | 包级 catalog/route/import 边界测试 | 无默认目标 | adapter-only | P2 | 先保持源端预览，再按资产优先级补 profile。 |
| 外部 Tencent 包 | 腾讯实时快照 | `axdata.source.tencent_external` | 外部 Tencent adapter | 外部包 manifest 1 接口 | 启用并处理冲突后可路由 | 插件 catalog 字段 | DownloaderProfile 0，CollectorSpec 0 | 未同步 | 未同步 | 包级 discovery/call/check 测试 | 无默认目标 | partial | P2 | 预装 Tencent 插件已补轻量闭环，外部包 manifest 尚未同步 downloader/collector。 |
| 外部 Cninfo 包 | 巨潮公告列表/PDF 元信息 | `axdata.source.cninfo_external` | 外部 Cninfo adapter | 外部包 manifest 2 接口 | 启用并处理冲突后可路由 | 插件 catalog 字段 | DownloaderProfile 0，CollectorSpec 0 | 未同步 | 未同步 | 包级 discovery/call/check 测试 | 无默认目标 | partial | P2 | 预装 Cninfo 插件已补轻量闭环，外部包 manifest 尚未同步 downloader/collector。 |
| 核心四表本地数据链路 | `stock_basic_exchange`、`trade_cal`、`daily`、`adj_factor` | 本地 Parquet/DuckDB | storage/query/schema | schema/query catalog | 查询不触源 | core schema | 离线 Collector/Downloader 基础链路 | 支持 | 已验证 | `tests/test_data_collection_loop.py` | 四表可显式小样本检查 | partial | P0 | 真实源全市场 raw/staging -> core 生产转换仍需逐项补齐。 |

## 第二批 TDX 普通行情接口

本节选择 TDX 普通行情中已经有源端实现、字段结构稳定且能离线测试的 P0 核心表相关接口。默认参数均为单只 `000001.SZ` 小样本，避免 Downloader/Collector catalog 被查看或调度时隐式展开全市场请求。TDX source provider manifest 当前为 90 interfaces / 10 downloaders / 0 collectors；8 个 TDX 核心采集器由 `axdata.collector.tdx` 独立 collector plugin 提供，`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 仅保留源端接口/兼容 DownloaderProfile。

| interface_name | 中文说明 | 数据源/provider | 闭环状态 | 默认参数 | 输出层 | 主键 | 离线测试 | 仍待完成 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stock_kline_daily_tdx` | 股票日 K 线 | `axdata.source.tdx_external` + `axdata.collector.tdx` | manifest/catalog/source_request/DownloaderProfile/independent CollectorSpec/Parquet/CSV/DuckDB 已接入；quality contract 已声明 required columns、datetime range、非负数值列和 `instrument_id/trade_time/volume` 到 `ts_code/trade_date/vol` 的映射 | `code=000001.SZ`、`count=800`、`adjust=none` | core sample | `instrument_id + trade_time + period` | profile 注册、离线写出、DuckDB 读回、runner_entry、quality metadata | 全市场日线任务、raw/staging -> core `daily` 转换和真实源长期小样本检查 |
| `stock_adj_factor_tdx` | 复权因子 | `axdata.source.tdx_external` | manifest/catalog/source_request/兼容 DownloaderProfile 已接入；不再声明 independent CollectorSpec，也不再进入采集页 | `code=000001.SZ`、`adjust=qfq` | source/compat sample | `ts_code + trade_date` | profile 注册、源端请求和兼容下载测试 | 复权因子重建策略和真实源长期小样本检查 |

## 第三批接口补齐候选盘点

本节记录接口补齐候选，不新增接口、不新增 DownloaderProfile/CollectorSpec。当时的 Web/runtime 口径只覆盖普通 TDX 与预装源插件，未把 TDX Ext 扩展行情计入默认目录；当前发布口径以 `axdata` 安装后的 Provider Registry 为准，随项目提供的 TDX 与 TDX Ext 插件安装后默认可用。其中 `collection.supported=true` 仅表示接口页可显示兼容下载信息，不等于采集器数量。实际采集器 catalog 为 TDX 8 个独立采集器。产品决策仍是采集器少而稳，更多接口先作为 source_request/query preview 暴露。

## Source Request 可调用性里程碑统计 2026-06-29

本节为 `source-request-callability-ready` 当时的收口统计，口径以阶段测试时的 Provider Registry、`docs/data-interface-inventory.md` 分类和离线测试为准。当时的 runtime catalog 校验使用临时插件配置只启用 `axdata.source.tdx_external`，不读取本机运行态 `metadata/plugins.json`，也不把 TDX Ext 31 个接口计入默认 100 个接口口径；当前发布口径以 `axdata` 安装后的实际目录为准。

| 指标 | 数量 | 口径说明 |
| --- | ---: | --- |
| catalog 接口总数 | 100 | `list_registry_interface_dicts()` 默认 runtime 口径；全部 `request_mode=source_request`。 |
| TDX 普通行情 catalog 接口 | 90 | 来自 `axdata.source.tdx_external`；真实调用需要插件可用和可用 TDX 连接。 |
| 预装源插件 catalog 接口 | 9 | 交易所 3、巨潮 2、东方财富 3、腾讯 1。 |
| source_request 路由可用接口 | 100 | TDX enabled 临时配置下 100 个接口均为 `plugin_status=enabled`；这表示可通过 source_request 路由请求源端，不表示都已纳入小样本文档增强或采集。 |
| 三批已增强 source-only 小样本接口 | 26 | 第一批 8、第二批 10、第三批 8；全部是临时调用，不写入数据层。 |
| query_only 候选 | 4 | F10/财务/信息流口径尚未收敛，继续保持查询或目录预览，不新增采集器。 |
| callability_candidate 剩余 | 0 | 上一阶段 8 个候选已全部在第三批移入 source_request callable 状态。 |
| future_collectable 候选 | 8 | 以后可能补 profile、转换策略或生产验证，但本里程碑不扩采集器或 task template。 |
| 有兼容 DownloaderProfile 的接口 | 13 | 预装交易所 3、TDX 10；`collection.supported=true` 只表示存在显式下载兼容信息，不等于 CollectorSpec 或 scheduled task。巨潮、腾讯、东方财富、新浪 7 个预装接口为 source_request-only。 |
| CollectorSpec | 8 | TDX independent 8；交易所、复权因子和非核心 7 个预装源默认 CollectorSpec 均已下线。 |

TDX 被显式禁用时，普通 TDX 接口仍可作为不可用目录项保留，标记 `plugin_status=disabled`、`enabled=false`，并给出 `axdata plugin enable axdata.source.tdx_external`。其中预装交易所接口为 `collection.supported=true`；巨潮、腾讯、东方财富等 source-only 接口为 `collection.supported=false`。`stock_kline_daily_tdx`、`stock_adj_factor_tdx` 等已有 profile 的 TDX 接口只表示“插件可用后可显式下载/源端请求”，不表示接口本身就是采集器。默认采集器 catalog 只包含 `axdata.collector.tdx` 提供的 TDX 8 个采集器，可通过禁用 `axdata.collector.tdx` 独立隐藏。

## Source Request 可调用性增强第一批 2026-06-29

本节选择 8 个已有 TDX catalog 接口，只增强 `source_request` 小样本调用体验，不新增 DownloaderProfile、CollectorSpec、task template 或定时采集。选择理由：已有外部 TDX Provider 底层实现；不需要第三方 token；字段结构已在 manifest/catalog 中声明；适合单票、单指数、单 ETF 或小榜单临时查询；可以用离线 adapter 样例覆盖 CLI/API/SDK 路由和参数校验，不把真实网络请求放入默认测试。

| interface_name | 数据源 | 本阶段状态变化 | 小样本参数 | CLI/API/SDK | 离线测试 | 是否采集器 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `stock_realtime_snapshot_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已补通用 `axdata request`、`/v1/request/*`、`client.call(...)` 示例/测试 | 离线 gateway/API/SDK/CLI | 否 | 实时快照只做临时预览，不写历史事实表。 |
| `stock_realtime_rank_tdx` | 通达信 | adapter-only -> source_request callable | `category=a_share,count=3` | 已覆盖 | 离线 gateway/API/SDK | 否 | 默认榜单仍为 80 行，`count="all"` 必须显式传入。 |
| `stock_order_book_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已覆盖 | 离线 gateway/API/CLI | 否 | 五档盘口只做当前快照。 |
| `index_realtime_snapshot_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SH` | 已覆盖 | 离线 gateway/API/SDK | 否 | 指数实时快照只做小代码列表查询。 |
| `index_kline_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SH,period=day,count=20`；默认 `count=120` | 已覆盖 | 离线 gateway/API/SDK；adapter 默认 count 测试 | 否 | 默认从 800 收紧为 120，避免临时预览误拉长历史。 |
| `etf_realtime_snapshot_tdx` | 通达信 | adapter-only -> source_request callable | `code=510050.SH` | 已覆盖 | 离线 gateway/API/SDK | 否 | ETF 实时快照只做小代码列表查询。 |
| `etf_kline_tdx` | 通达信 | adapter-only -> source_request callable | `code=510050.SH,period=day,count=20`；默认 `count=120` | 已覆盖 | 离线 gateway/API/SDK；adapter 默认 count 测试 | 否 | 默认从 800 收紧为 120，仍可显式传更大 count。 |
| `concept_constituents_tdx` | 通达信 | adapter-only -> source_request callable | `concept_code=881386,count=5` | 已覆盖 | 离线 gateway/API/SDK | 否 | 概念成分股需要用户提供板块代码，本节不新增板块发现采集任务。 |

本阶段同步增强了通用错误体验：CLI 新增 `axdata request <interface>`，JSON 输出为 ASCII-safe；缺参数返回 `SOURCE_REQUEST_VALIDATION_ERROR` 和下一步提示；API 对 disabled/missing TDX Provider 返回结构化 `SOURCE_UNAVAILABLE`，并给出 `axdata plugin enable axdata.source.tdx_external`，不再在 disabled TDX 接口上只给 404 catalog not found。

## Source Request 可调用性增强第二批 2026-06-29

本节选择 10 个已有 catalog 中的 P0/P1 TDX source-only 接口，继续只增强临时 `source_request` 调用体验和 Web 详情指引，不新增 DownloaderProfile、CollectorSpec、task template 或定时采集。选择依据：底层 adapter 已实现并有离线测试锚点；manifest/catalog 可见；不需要 token；参数能收敛到单票、单指数/ETF榜单或指定日期小样本；适合人工调试与盘中/复盘预览，不适合作为默认入库任务。

| interface_name | 数据源 | 本阶段状态变化 | 小样本参数 | CLI/API/SDK | Web 调用状态 | 是否采集器 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `stock_intraday_today_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已纳入 API/SDK/CLI 离线调用样例 | 显示可临时调用、无默认采集器、推荐 `axdata request` | 否 | 当日分时只做当前交易日预览，不写分钟事实表。 |
| `stock_intraday_history_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ,trade_date=20260519` | 已纳入 | 同上 | 否 | 历史分时需要显式日期，不默认保存分时历史。 |
| `stock_trades_today_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 当日成交明细可能较多，只推荐单票临时查。 |
| `stock_trades_history_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ,trade_date=20260511` | 已纳入 CLI `--params` JSON 测试 | 同上 | 否 | 历史逐笔/成交明细用于复盘小样本。 |
| `stock_auction_process_tdx` | 通达信 | adapter-only -> source_request callable | `code=000988.SZ` | 已纳入 | 同上 | 否 | 竞价过程只做单票观察，不自动沉淀。 |
| `stock_auction_result_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 当日 09:25 竞价结果来自成交明细筛选。 |
| `stock_finance_summary_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 财务快照摘要不是完整 F10 三表，不进入核心财务表。 |
| `stock_finance_profile_tdx` | 通达信 | adapter-only -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 可选 `map_root` 只更新本地码表映射。 |
| `index_realtime_rank_tdx` | 通达信 | adapter-only -> source_request callable | `sort=change_pct,count=5` | 已纳入 | 同上 | 否 | 指数榜单保留小 count，避免临时调用误拉大页。 |
| `etf_realtime_rank_tdx` | 通达信 | adapter-only -> source_request callable | `sort=change_pct,count=5` | 已纳入 | 同上 | 否 | ETF 榜单只做临时排行预览。 |

本节同时增强目录状态：`/v1/request/interfaces` 会保留 disabled/failed/conflict Provider manifest 中的接口目录项，并带 `plugin_status`、`enabled=false`、`next_action` 和 `action_command`；Web 详情页据此区分“可临时调用 source_request”“有兼容下载信息”“需启用插件”“仅目录/尚未接入调用”，并展示推荐 CLI 命令和 `POST /v1/request/{interface_name}` 提示。兼容下载信息可参考 `collection.supported` 和 DownloaderProfile；真正的采集器能力以 CollectorRegistry catalog 为准。本节 10 个接口全部仍不是采集器。

## Source Request 可调用性增强第三批 2026-06-29

本节严格从上一批 `callability_candidate` 中选择 8 个接口。代码核对结果：8 个接口都存在于 TDX 普通行情 catalog/Provider manifest；底层 adapter dispatch 已支持；参数只需要单票、单指数、单 ETF 或单日期小样本；不需要第三方 token；真实调用需要 `axdata.source.tdx_external` 可用并有 TDX 连接；离线测试使用 gateway 样例，不请求真实网络。本节只补齐临时 `source_request` 可调用体验、CLI/API/SDK/Web 示例与测试，不新增 DownloaderProfile、CollectorSpec、task template 或定时采集。

| interface_name | 数据源 | 本阶段状态变化 | 小样本参数 | CLI/API/SDK | Web 调用状态 | 是否采集器 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `stock_intraday_recent_history_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SZ,trade_date=20260519` | 已纳入 API/SDK/CLI 离线调用样例 | 显示可临时调用、无默认采集器、推荐 `axdata request` | 否 | 近期历史分时补充均价和开盘价，只做复盘小样本。 |
| `stock_intraday_buy_sell_strength_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 分时副图买卖力道只查当前单票，不支持日期。 |
| `stock_intraday_volume_comparison_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SZ` | 已纳入 | 同上 | 否 | 成交对比只做当前分时诊断，不默认入库。 |
| `stock_auction_result_history_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SZ,trade_date=20260511` | 已纳入 | 同上 | 否 | 历史 09:25 竞价结果来自历史成交明细筛选。 |
| `index_intraday_today_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SH` | 已纳入 | 同上 | 否 | 指数当日分时用于市场环境预览。 |
| `index_intraday_history_tdx` | 通达信 | callability_candidate -> source_request callable | `code=000001.SH,trade_date=20260617` | 已纳入 CLI `--params` JSON 测试 | 同上 | 否 | 指数历史分时用于指定日期复盘，不保存分钟历史。 |
| `etf_intraday_today_tdx` | 通达信 | callability_candidate -> source_request callable | `code=510050.SH` | 已纳入 | 同上 | 否 | ETF 当日分时与股票/指数分时并列，只做临时 preview。 |
| `etf_trades_today_tdx` | 通达信 | callability_candidate -> source_request callable | `code=510050.SH` | 已纳入 | 同上 | 否 | ETF 当日成交明细保持单标的小样本调用。 |

本阶段没有 blocked 候选；全部 8 个 `callability_candidate` 均已完成临时可调用性增强。它们的 `collection.supported=false` 表示没有兼容下载信息；本阶段未新增 CollectorSpec、采集 profile 或 task template。

### query_only 候选

这些接口适合继续保持源端临时查询或目录展示，不建议在第三批里变成采集器。

| interface_name | 数据源 | 当前状态 | 原因 | 是否需要插件/网络 | 是否建议采集器 |
| --- | --- | --- | --- | --- | --- |
| `stock_financial_statement_tdx` | 通达信 | 仅目录/待增强调用体验 | F10 财务三表口径复杂，适合先做单票结构化预览，不能直接承诺稳定 core 财务表。 | 需要 TDX 插件和真实连接；不需要 token。 | 否，财务表口径定稿前只做 query_only。 |
| `stock_margin_trading_tdx` | 通达信 | 仅目录/待增强调用体验 | 可与已有东方财富融资融券接口做交叉对照，但历史范围、字段口径和稳定性需要先验证。 | 需要 TDX 插件和真实连接；不需要 token。 | 否，已有预装东方财富插件接口可承担轻量写出。 |
| `stock_company_profile_tdx` | 通达信 | 仅目录/待增强调用体验 | 公司概况更像人工核对入口，字段更新频率低且与交易所主数据存在重叠。 | 需要 TDX 插件/F10 能力和真实连接。 | 否，先作为单票查询。 |
| `stock_disclosure_feed_tdx` | 通达信 | 仅目录/待增强调用体验 | 新闻公告路演属于 F10 信息流，去重、正文抓取和长期归档策略未定。 | 需要 TDX 插件/F10 能力和真实连接。 | 否，如需入库应先定义 raw 信息流层。 |

### callability_candidate 候选

当前无剩余候选。上一批列出的 8 个 `callability_candidate` 已在第三批全部移入 `source_request callable` 状态；如果继续扩展，必须先重新从真实 catalog/adapter 和本 inventory 中整理新候选，不能凭感觉追加。

### future_collectable 候选

这些接口未来可能适合补 DownloaderProfile/CollectorSpec 或生产转换策略，但不应在第三批 source_request 可调用性收口里顺手实现。

| interface_name | 数据源 | 当前状态 | 原因 | 是否需要插件/网络 | 是否建议采集器 |
| --- | --- | --- | --- | --- | --- |
| `stock_kline_daily_tdx` | 通达信 | partial | 已有轻量 profile/spec，是 `daily` 当前核心源端；缺口是全市场 raw/staging -> core 转换、分区覆盖和真实源长期 smoke。 | 需要 TDX 插件和真实连接；不需要 token。 | 已有轻量 CollectorSpec；下一步补生产转换，不新增模板。 |
| `stock_adj_factor_tdx` | 通达信 | partial | 已有源端接口和兼容 DownloaderProfile，是复权视图候选输入；不再作为采集器展示。 | 需要 TDX 插件和真实连接；不需要 token。 | 不建议默认采集；按需补重建策略。 |
| `index_kline_tdx` | 通达信 | source_request callable | 第一批已补临时调用；指数行情可作为市场 regime/基准输入，未来可先补 DownloaderProfile。 | 需要 TDX 插件和真实连接；不需要 token。 | 可补 profile，不急着加 task template。 |
| `etf_kline_tdx` | 通达信 | source_request callable | 第一批已补临时调用；ETF 价格序列适合做可选资产层样本。 | 需要 TDX 插件和真实连接；不需要 token。 | 可补 profile，不急着加 task template。 |
| `stock_realtime_snapshot_tdx` | 通达信 | source_request callable | 第一批已补临时调用；如需持久化应作为显式 snapshot/recording，而非污染日线事实表。 | 需要 TDX 插件和真实连接；不需要 token。 | 可选 DownloaderProfile，不建议默认 CollectorSpec。 |
| `concept_constituents_tdx` | 通达信 | source_request callable | 第一批已补临时调用；主题/概念成分适合 snapshot 留痕和 Data Browser 浏览。 | 需要 TDX 插件和真实连接；不需要 token。 | 可补 DownloaderProfile；模板优先级低。 |
| `stock_basic_info_exchange` | 交易所 | complete | 已有预装源插件闭环，是股票主数据候选口径；生产级 latest/history 差异版本仍待加强。 | 需要真实交易所 HTTP；不需要 token。 | 默认 CollectorSpec 已下线；优先完善基础数据同步和转换策略。 |
| `stock_trade_calendar_exchange` | 交易所 | complete | 已有预装源接口和本地日历缓存，是其它采集任务的基础依赖。 | 需要真实交易所 HTTP；不需要 token。 | 默认 CollectorSpec 已下线；优先完善基础数据同步和缓存提示。 |

## Schema / quality 对齐盘点

本节结论：

- `stock_basic_exchange`、`trade_cal`、`daily`、`adj_factor` 的 core schema 继续保持现有稳定字段，不进行破坏性改名。
- `daily` 的稳定字段是 `ts_code`、`trade_date`、`vol`、`amount`；TDX 日线源端字段 `instrument_id`、`trade_time`、`volume` 已在 schema/profile 中声明兼容映射；core 转换任务必须按该映射写入正式 `daily` 分区。
- `adj_factor` 已同时返回 `instrument_id` 与 `ts_code`，正式主键为 `ts_code + trade_date`；profile quality 已检查 `adj_factor` 正数。
- 第一批预装源插件 9 个接口已在 DownloaderProfile output 中声明 primary key、required columns、date/datetime 字段和适用的 numeric positive checks；source-only 接口仍以 catalog/manifest 字段为准。
- `DownloadQualityChecker` 现在统一生成 `quality_status`、`row_count_value`、required/null/missing、duplicate key、date range、numeric checks、schema columns、unexpected columns 和 field mappings；CollectorRun/API/CLI/Web 继续透传同一 `quality` JSON。

## 验证入口

默认离线验证：

```powershell
.\.venv\Scripts\python -m pytest tests\test_builtin_providers.py tests\test_provider_catalog.py tests\test_downloaders.py tests\test_collector_runner.py tests\test_real_source_smoke.py -q
```

默认真实源 smoke 只输出四张核心表 dry skip，不请求网络：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --json
```

显式检查某个 source-only 接口：

```powershell
.\.venv\Scripts\python scripts\smoke_real_sources.py --run `
  --interfaces tencent_realtime_snapshot `
  --output-dir $env:TEMP\axdata-real-source-smoke `
  --json
```

输出目录会包含 `snapshots/<run_id>/<interface>/parquet|csv|duckdb`，并写入 `metadata/real_source_smoke/<run_id>`。这些运行产物不提交。
