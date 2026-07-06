# AxData Schema 与字段规范

本文说明 AxData 当前核心用户表：`stock_basic_exchange`、`trade_cal`、`daily`、`adj_factor`，以及源端接口进入 Downloader/Collector 写出链路时使用的字段规范。主键、日期格式、价格/成交量/成交额单位和 provider 原始字段兼容策略属于稳定契约；新增字段应保持向后兼容，字段改名或单位变化必须进入新版本或显式映射。

## 通用约定

- 表层级：以下表位于 core 层，面向 Python SDK、HTTP API 和 DuckDB 查询视图。
- 接口即口径：`stock_basic_exchange` 表示交易所股票列表口径；新增接口应以独立名称表达独立口径。
- 事实源：Parquet 文件是长期事实源；DuckDB 是本地查询引擎和可重建视图层。
- 代码格式：A 股统一为 `000001.SZ`、`600000.SH`、`430047.BJ`。
- 交易所代码：查询筛选统一使用 `SSE`、`SZSE`、`BSE`；证券代码后缀 `.SH`、`.SZ`、`.BJ` 只属于 `instrument_id` 或 `ts_code`。
- 日期格式：API 和当前 Parquet 字段统一使用量化常见的 `YYYYMMDD` 字符串；HTTP API 兼容传入 `YYYY-MM-DD` 并转成 `YYYYMMDD`。
- 价格类型：当前使用 `double`；如需严格财务精度，再评估 decimal。
- 价格单位：A 股价格字段 `open`、`high`、`low`、`close`、`pre_close`、`change` 使用人民币元。
- 成交量单位：core `daily.vol` 使用手；源端接口如果返回 `volume`，必须在 profile/schema 中声明映射到 `vol` 或说明保留源端口径。
- 成交额单位：core `daily.amount` 使用千元；source/raw/snapshot 接口可保留源端单位，但必须在字段说明或 profile quality contract 中声明。
- 采集追溯：task、batch、run、adapter、原始参数、质量结果和 manifest 属于 metadata，不作为常规用户表字段返回。

兼容说明：旧的 `stock_basic` 查询名保留为 `stock_basic_exchange` 的兼容别名；新文档、示例和用户主路径统一使用 `stock_basic_exchange`。

## 字段命名规范 v1

字段规范优先尊重已经闭环的 core 表，不为了统一命名破坏现有查询：

| 概念 | 对外稳定字段 | 当前兼容/源端字段 | 说明 |
| --- | --- | --- | --- |
| 统一证券代码 | `instrument_id`、`ts_code` | `symbol` 概念名、`provider_symbol` | `stock_basic_exchange` 使用 `instrument_id`；`daily` 和 `adj_factor` 保留 Tushare 风格 `ts_code`。文档中“统一证券代码 / canonical symbol”指 `000001.SZ` 这一语义，不把既有 `stock_basic_exchange.symbol` 粗暴改名。 |
| 原始证券代码 | `provider_symbol`、`raw_code` | 既有 `symbol` | 既有 `stock_basic_exchange.symbol` 是交易所六位代码，例如 `000001`；新 source/raw 字段如需保留原始代码，优先使用 `provider_symbol` 或 `raw_code`。 |
| 交易所/市场源代码 | `exchange`、`secid` | `tdx_code` | `exchange` 使用 AxData 交易所代码；`secid`、`tdx_code` 等只作为 provider 原始字段保留，不能替代统一证券代码。 |
| 交易日期 | `trade_date`、`cal_date` | `date` | 行情、复权、专题快照使用 `trade_date=YYYYMMDD`；日历表使用 `cal_date=YYYYMMDD`；源端 `date` 必须映射。 |
| 更细粒度时间 | `datetime`、`trade_time`、`quote_time` | provider 原始时间 | 分钟、逐笔、快照等可以使用更具体字段；进入 core 日线时仍需可映射到 `trade_date`。 |
| 价格 | `open`、`high`、`low`、`close`、`pre_close` | provider 原始价格列 | A 股 core 价格单位为人民币元，未复权。 |
| 成交量 | `vol` | `volume` | core `daily` 使用 `vol`，源端常见 `volume` 通过 profile `field_mappings` 标明。 |
| 成交额 | `amount` | provider 原始成交额 | core `daily.amount` 单位为千元；source/snapshot 接口如为元或其它单位，字段说明必须写清。 |
| 复权因子 | `adj_factor` | provider 原始因子 | 必须大于 0。 |
| 采集来源 | metadata 中的 `provider`、`source`、`interface_name` | 不进入常规用户表 | 写出链路在 run metadata/quality 中保留来源，core 用户表默认不加采集追踪列。 |

字段兼容策略：

- 对外 core/query 以表 schema 的稳定字段为准；`daily.ts_code`、`daily.vol`、`stock_basic_exchange.instrument_id` 不在本阶段改名。
- provider 原始字段可以保留在 raw/snapshot/source 输出中，但不能替代 canonical 字段；需要映射时在 DownloaderProfile `output.field_mappings` 或 schema `provider_field_mappings` 中声明。
- 第一批 source-only 接口仍以 catalog/manifest 字段为真相源；进入 core 前必须经过映射、单位确认和质量检查。
- 新增接口如需表达统一证券代码，优先使用 `instrument_id` 或目标 core 表既有字段；避免把 raw 六位代码继续命名为 `symbol`。

当前可用能力说明：以下 schema、主键、storage 和 query 路径已经可用，并有小样本测试覆盖。第一批内置交易所/HTTP 源接口保留轻量 DownloaderProfile 和 source_request 能力，可服务 `stock_basic_exchange` / `trade_cal` 的小样本检查，但不再提供默认 CollectorSpec。TDX 插件中保留 DownloaderProfile 作为 `/v1/downloaders` 兼容入口，同时 8 个 TDX 核心采集器由 `axdata.collector.tdx` 独立 CollectorSpec 提供；`stock_capital_changes_tdx` 与 `stock_adj_factor_tdx` 保留为源端接口和兼容 DownloaderProfile，不再作为采集器进入采集页。TDX source Provider manifest 不再声明 collectors。`stock_kline_daily_tdx` 可通过默认独立采集器写显式代码小样本；`stock_adj_factor_tdx` 保留 schema、source_request 和兼容下载入口，用于复权因子口径验证和重建能力，不作为默认高频采集任务。文档中的其它写入策略表示推荐设计，不应理解为所有真实源都已经具备全市场长期采集能力。

## 第一批源端接口 schema 摘要

这批接口的字段真相源仍是各自 `sources/*/catalog.py` 和 Provider manifest，下面只列主键、默认写入层和主要字段，便于判断采集输出形态。

| interface_name | 层级 | 主键 | 主要字段 |
| --- | --- | --- | --- |
| `stock_trade_calendar_exchange` | core | `cal_date` | `cal_date`、`is_open`、`pretrade_date`、`next_trade_date` |
| `stock_historical_list_exchange` | snapshot | `trade_date + instrument_id` | `trade_date`、`instrument_id`、`symbol`、`exchange`、`name`、`market`、`list_date`、`delist_date`、`listing_status` |
| `stock_basic_info_exchange` | core | `instrument_id` | 复用 `stock_basic_exchange` 字段 |
| `cninfo_announcements` | raw | `instrument_id + announcement_id` | `instrument_id`、`announcement_id`、`title`、`publish_date`、`file_type`、`file_size_kb`、`download_url` |
| `cninfo_announcement_detail` | raw | `download_url` | `announcement_id`、`title`、`content_type`、`file_size_bytes`、`download_url` |
| `tencent_realtime_snapshot` | snapshot | `instrument_id` | `instrument_id`、`quote_time`、`last_price`、`pre_close`、`open`、`high`、`low`、`change_pct`、`amount`、`turnover_rate`、`pe_dynamic`、`pb`、`limit_up_price`、`limit_down_price` |
| `eastmoney_dragon_tiger_daily` | raw | `trade_date + instrument_id + reason` | `trade_date`、`instrument_id`、`reason`、`close_price`、`change_pct`、`buy_amount`、`sell_amount`、`net_buy_amount`、`total_amount` |
| `eastmoney_margin_trading` | raw | `trade_date + instrument_id` | `trade_date`、`instrument_id`、`margin_balance`、`margin_buy_amount`、`margin_repay_amount`、`short_balance`、`total_balance` |
| `eastmoney_research_reports` | raw | `report_id` | `report_id`、`instrument_id`、`title`、`publish_date`、`org_name`、`rating`、`researcher`、`eps_forecast_this_year`、`pe_forecast_this_year` |
| `stock_financial_report_sina` | raw | `statement_type + instrument_id + report_date + item_name` | `statement_type`、`instrument_id`、`report_date`、`statement_name`、`item_name`、`item_value`、`publish_date`、`currency` |

## 第二批 TDX 源端接口 schema 摘要

这两个接口进入 TDX 插件的源端接口和兼容 DownloaderProfile 链路，用于显式代码样本或小批量检查。其中 `stock_kline_daily_tdx` 另有默认独立 CollectorSpec 可写日线小样本；`stock_adj_factor_tdx` 只保留接口、schema 和兼容下载能力，不作为默认采集器。如需全市场长期更新，应按采集器规范补充专用转换任务。

| interface_name | 层级 | 主键 | 主要字段 |
| --- | --- | --- | --- |
| `stock_kline_daily_tdx` | core | `instrument_id + trade_time + period` | `instrument_id`、`symbol`、`tdx_code`、`exchange`、`trade_time`、`period`、`open`、`high`、`low`、`close`、`volume`、`amount` |
| `stock_adj_factor_tdx` | core | `ts_code + trade_date` | `instrument_id`、`ts_code`、`symbol`、`tdx_code`、`exchange`、`trade_date`、`adj_factor` |

TDX 日 K 线目前是源端 core 样本口径，保留 `instrument_id`、`trade_time`、`volume` 等源端字段；profile 已声明 `instrument_id -> ts_code`、`trade_time -> trade_date`、`volume -> vol` 映射。真正写入稳定 `core.daily` 生产分区前仍需 raw/staging -> core 转换任务把这些字段落到 `daily` schema。

写入策略说明：`stock_adj_factor_tdx` 的推荐目标是 `upsert_by_key ts_code + trade_date` 并按 `trade_date` 分区，但当前不作为默认采集器进入采集页。`stock_kline_daily_tdx` 的推荐目标是 `upsert_by_key instrument_id + trade_time + period` 或转换后 `upsert_by_key ts_code + trade_date`；在正式写入稳定 `core.daily` 前，仍需确认 `trade_time -> trade_date`、`volume -> vol` 等映射和质量规则。

## 写出质量摘要 v1

Downloader/Collector 写出链路的 `quality` 字段保留旧键：

- `schema`
- `primary_key`
- `row_count`

同时新增以下摘要字段，供 CLI/API/Web 现有 JSON 展示直接序列化：

| 字段 | 含义 |
| --- | --- |
| `quality_status` | `ok`、`warn`、`error`。有 blocking 错误为 `error`，只有非阻塞提示为 `warn`。 |
| `row_count_value` | 实际写出行数。 |
| `required_columns_present` | profile/schema 声明的 required columns 是否全部存在。 |
| `missing_required_columns` | 缺失的 required columns。 |
| `null_counts` | required columns 的空值行数。 |
| `duplicate_key_count` | 主键重复影响的行数。 |
| `duplicate_key_samples` | 主键重复样本，限制条数，避免 quality JSON 过大。 |
| `date_field`、`date_range` | 声明日期/时间字段及最小、最大值。 |
| `min_date`、`max_date`、`actual_date_count` | 日期字段归一化到 `YYYYMMDD` 后的最小/最大日期和实际日期数。 |
| `schema_columns`、`expected_columns`、`unexpected_columns` | 实际列、期望列和额外列。 |
| `numeric_positive_checks` | 对价格、成交量、成交额、复权因子等非负/正数列的检查摘要。 |
| `field_mappings` | provider/source 字段到 core canonical 字段的兼容映射。 |
| `write_mode` | 本次写入模式，例如 `snapshot`、`append`、`overwrite_partition`、`replace_range`、`upsert_by_key`。 |
| `partition_by`、`write_primary_key`、`write_date_field` | 写入策略使用的分区字段、主键和日期字段；`primary_key` 旧键仍表示质量检查状态。 |
| `replace_range_start`、`replace_range_end` | `replace_range` 本次替换的日期闭区间。 |
| `rows_before`、`rows_written`、`rows_after` | 写入前、输入和写入后行数；只在 writer 可低风险获得时填充。 |
| `duplicate_rows_dropped`、`partitions_touched` | upsert 去重行数和本次触达的分区标签。 |
| `calendar_coverage_status` | 交易日历对齐状态：`ok`、`warn`、`error`；缺少本地交易日历时为 `warn`。 |
| `expected_trading_day_count`、`actual_trading_day_count` | 数据日期范围内预期交易日数和实际数据日期数。 |
| `missing_trading_dates`、`extra_non_trading_dates` | 缺失交易日样本和非交易日多出样本，限制条数。 |
| `date_gap_count`、`missing_date_samples` | 日期缺口数量和样本。 |
| `per_symbol_date_coverage` | 按证券代码汇总的小样本日期覆盖摘要。 |
| `unexplained_missing_dates`、`suspension_explained_missing_dates` | 缺口解释样本；没有停牌数据时缺口只标记为 unexplained。 |
| `price_ohlc_anomaly_count`、`negative_volume_count`、`negative_amount_count`、`invalid_adj_factor_count` | 日 K 线和复权因子专项异常计数。 |
| `quality_warnings`、`quality_errors` | 可读的问题摘要。 |

这些检查按 profile/schema 声明执行：没有日期字段的接口不会因为缺日期而失败；source-only 接口也可以只检查 row_count、required columns 和 primary key。
交易日历检查只对 `daily`、`adj_factor`、`stock_kline_daily_tdx`、`stock_adj_factor_tdx` 等行情/复权样本启用。当前采集任务层已经支持 `required_datasets=["trade_cal"]`：任务运行前会先检查本地交易日历基础数据，缺失或覆盖不足时阻止运行并返回清楚的 `dependency_missing` 提示；质量检查阶段则在已有日历基础上继续记录日期缺口、非交易日和 `calendar_next_action`。日期缺口不必然表示源端错误，可能来自停牌、未上市/退市、源端遗漏或采集范围不完整。当前没有历史停牌日期库时，缺口默认归入 `unexplained_missing_dates`。

Data Browser 会直接消费这些字段：列表页优先展示 `quality_status`、`row_count_value`、`date_field/date_range`、`schema_columns`、`quality_warnings`、`quality_errors`、`field_mappings` 和写入 metadata。旧 run metadata 没有这些 richer 字段时，浏览层会从候选 Parquet 补充 `columns`、`row_count` 和日期范围，写入字段保持空值；补充查询只针对已发现的 parquet 路径，并带默认 limit，不会触发源端请求。

## stock_basic_exchange

股票列表（交易所）。一行代表交易所官方股票列表口径下的一只证券。

主键：`instrument_id`

建议写入策略：交易所当前完整列表每日 22:00 拉取；raw 每次保存，core latest 可整表 `snapshot` 重建，core history 只在 diff 变化时写入版本；稳定主键路径可演进为 `upsert_by_key instrument_id`。采集任务、批次、运行参数、质量结果和写入 metadata 写入 metadata/manifest。

调用和识别约定：

| 概念 | 示例 | 说明 |
| --- | --- | --- |
| 精确查一只股票 | `instrument_id=600000.SH` | 推荐方式；后缀已经说明上市交易所 |
| 按交易所查 | `exchange=SSE` | `SSE`=上交所，`SZSE`=深交所，`BSE`=北交所 |
| 原始证券代码 | `symbol=600000` | 不带后缀，主要用于和交易所列表核对 |

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `instrument_id` | string | 是 | AxData 统一证券代码，例如 `000001.SZ`、`600000.SH`、`430047.BJ`；后缀已表示上市交易所 |
| `symbol` | string | 是 | 交易所原始证券代码，例如 `000001` |
| `exchange` | string | 是 | 交易所筛选代码，建议值 `SSE`、`SZSE`、`BSE` |
| `asset_type` | string | 是 | 资产类型，本表固定为 `stock` |
| `name` | string | 是 | 证券简称 |
| `security_full_name` | string | 否 | 证券全称，源不提供时为空 |
| `market_code` | string | 否 | 市场板块代码 |
| `market` | string | 否 | 市场板块，例如主板、创业板、科创板、北交所 |
| `industry_code` | string | 否 | 行业代码，使用交易所官方列表口径 |
| `industry` | string | 否 | 行业名称，使用交易所官方列表口径 |
| `region_code` | string | 否 | 地区代码 |
| `region` | string | 否 | 地区名称 |
| `company_code` | string | 否 | 交易所官方公司代码 |
| `company_short_name` | string | 否 | 交易所官方公司简称 |
| `company_full_name` | string | 否 | 公司法定全称 |
| `company_short_name_en` | string | 否 | 公司英文简称 |
| `company_full_name_en` | string | 否 | 公司英文全称 |
| `listing_status` | string | 是 | AxData 上市状态，建议值 `listed`、`delisted`、`suspended`、`unknown` |
| `list_date` | string | 否 | 上市日期，`YYYYMMDD` |
| `delist_date` | string | 否 | 退市日期，未退市为空 |
| `total_share` | double | 否 | 总股本，单位：亿股 |
| `float_share` | double | 否 | 流通股本，单位：亿股 |
| `is_profit` | string | 否 | 是否尚未盈利，保留交易所列表标记 |
| `is_vie` | string | 否 | 是否具有协议控制架构，保留交易所列表标记 |
| `has_weighted_voting_rights` | string | 否 | 是否具有表决权差异安排，保留交易所列表标记 |
| `sponsor` | string | 否 | 保荐机构或主办券商，源不提供时为空 |
| `share_report_date` | string | 否 | 股本数据报告日期，`YYYYMMDD` |

索引建议：

- `instrument_id`
- `exchange`
- `listing_status`
- `industry`
- `region`

## trade_cal

交易日历表，一行代表一个交易所的一个自然日。

主键：`exchange + cal_date`

建议写入策略：按交易所和年份 `overwrite_partition`，或按 `cal_date` 使用 `replace_range`；节假日发布后允许修订未来日期。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `exchange` | string | 是 | 交易所，建议值 `SSE`、`SZSE`、`BSE` |
| `cal_date` | string | 是 | 自然日期，`YYYYMMDD` |
| `is_open` | boolean | 是 | 是否交易日 |
| `pretrade_date` | string | 否 | 上一个交易日，`YYYYMMDD`；非交易日也可填写最近上一交易日 |

约束：

- 同一 `exchange + cal_date` 只能有一行。
- `is_open = true` 时，`pretrade_date` 应早于 `cal_date`，首个交易日可为空。

## daily

股票日行情表，一行代表一只股票在一个交易日的未复权日线行情。

主键：`ts_code + trade_date`

建议写入策略：按 `trade_date` 分区增量写入；历史修订按分区重写或按 `date_field=trade_date` 使用 `replace_range`；稳定 core 写入可使用 `upsert_by_key ts_code + trade_date`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `ts_code` | string | 是 | AxData 统一证券代码 |
| `trade_date` | string | 是 | 交易日期，`YYYYMMDD` |
| `open` | double | 否 | 开盘价，未复权，人民币元 |
| `high` | double | 否 | 最高价，未复权，人民币元 |
| `low` | double | 否 | 最低价，未复权，人民币元 |
| `close` | double | 否 | 收盘价，未复权，人民币元 |
| `pre_close` | double | 否 | 昨收价，未复权，人民币元 |
| `change` | double | 否 | 涨跌额，人民币元 |
| `pct_chg` | double | 否 | 涨跌幅，百分比数值，例如 `1.23` 表示 1.23% |
| `vol` | double | 否 | 成交量，单位：手 |
| `amount` | double | 否 | 成交额，单位：千元 |

约束：

- `trade_date` 必须是对应交易所开市日。
- `high >= low`。
- 若 OHLC 均非空，则 `high >= open`、`high >= close`、`low <= open`、`low <= close`。
- `vol >= 0`，`amount >= 0`。
- core 层 `daily` 不保存前复权或后复权价格。

分区建议：

```text
data/core/table=daily/parquet/20260605.parquet
```

## adj_factor

复权因子表，一行代表一只股票在一个交易日的复权因子。

主键：`ts_code + trade_date`

建议写入策略：按 `trade_date` 分区增量写入；发生分红送转修订时重建受影响区间；目标写入模式为 `upsert_by_key ts_code + trade_date`。当前 `stock_adj_factor_tdx` 保留为源端接口、schema 和兼容下载能力，不作为默认采集器进入采集页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `ts_code` | string | 是 | AxData 统一证券代码 |
| `trade_date` | string | 是 | 交易日期，`YYYYMMDD` |
| `adj_factor` | double | 是 | 复权因子，必须大于 0 |

复权视图口径：

- 未复权价格来自 `daily`。
- 复权因子来自 `adj_factor`。
- 前复权/后复权价格由查询层或 factor 层派生，不直接写入 `daily`。
- 具体公式需要按选定主接口口径固定，并在 API metadata 中暴露 `adjust_method`。

约束：

- `adj_factor > 0`。
- `trade_date` 应覆盖 `daily` 中对应证券的交易日。
- 同一主键只能有一条记录。

分区建议：

```text
data/core/table=adj_factor/parquet/20260605.parquet
```
