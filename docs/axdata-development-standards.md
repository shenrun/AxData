# AxData 数据源、采集器、数据集与 UI 开发规范

本文说明 AxData 数据源接口、采集器、数据集声明、Parquet/DuckDB 分工和 Web UI 的开发规范。新增接口、采集器、数据集或页面改版时，应先对照本文确认能力边界、命名、页面口径和验证规则。

最后更新：2026-07-04。

## 一句话边界

- 数据源接口负责临时请求源端，展示参数、字段、真实静态示例，默认不入库。
- 采集器负责创建任务、调度运行、写本地数据、记录进度、日志和质量结果。
- 数据集声明负责告诉 AxData 采集器会产出什么表、什么字段、什么路径、什么格式；只有真实落盘后，数据页才展示这个 dataset。
- Parquet 是长期数据事实源；DuckDB 是查询引擎和可重建查询缓存，不是 Parquet 的替代品。
- Web UI 必须把接口、采集、数据三条线分清楚，不能让用户误以为临时接口等于采集任务。

## 能力边界

当前 AxData 已经形成三类能力：

| 能力 | 当前入口 | 是否请求源端 | 是否写数据 | 说明 |
| --- | --- | --- | --- | --- |
| 数据源接口 | 接口页、`client.call(...)`、`POST /v1/request/{interface}` | 是 | 默认否 | 展示输入参数、输出字段、静态真实示例；适合临时查询和调试。 |
| 采集器 | 采集页、Collector API、Collector CLI | 是 | 是 | 创建 task、run、写 Parquet、记录 run history 和 quality。 |
| 数据查询 | 数据页、`client.query(...)`、`POST /v1/query` | 否 | 否 | 只读已入库 Parquet/DuckDB 视图，不临时请求源端；数据页只列已有本地输出的数据集。 |

当前约束：

- 新采集器必须是独立 CollectorSpec / runner entry，不应通过 `/v1/request`、SDK `call` 或 ProviderRegistry route 套接口采集。
- 交易所保留为数据源接口和基础数据能力，不作为默认采集器展示。
- 巨潮、腾讯、东方财富、新浪等 HTTP 源主要是 source_request Provider，默认不提供采集器。
- TDX source Provider 和 TDX collector 是两类能力：禁用 source 影响接口，禁用 collector 影响采集页能力。
- `data/snapshot/`、`data/core/`、`metadata/*.sqlite`、`logs/` 等本地运行数据不是代码，不应随便提交或删除。

## 命名规范

### 页面与文档名称

- 使用“数据源开发”，不要使用“软件源开发”。“软件源”容易被理解成 pip/apt/npm 安装源。
- 使用“采集器开发”，不要把采集器叫成接口插件。
- 使用“数据集声明”或“数据声明”，用于描述采集产出的表、schema、路径和查询方式。
- 使用“DuckDB 查询缓存”或“DuckDB 查询层”，不要写成“DuckDB 存储格式”来替代 Parquet。

### 代码标识

| 名称 | 用途 | 示例 |
| --- | --- | --- |
| `provider_id` | 数据源 Provider 身份 | `axdata.source.eastmoney` |
| `source_code` | 数据源短代码 | `eastmoney` |
| `interface_name` | 源端接口名 | `eastmoney_limit_up_pool` |
| `collector_plugin_id` | 采集器插件身份 | `axdata.collector.tdx` |
| `collector_id` / `collector_name` | 采集器能力名 | `stock_kline_daily_tdx` |
| `task_id` | 用户创建的采集任务 | `daily_refresh` |
| `dataset_id` | 采集产出的数据集 | `daily` |
| `table` | 查询层表名 | `daily` |

原则：

- 对用户稳定暴露的名字不要随意改。
- 一个名字只表达一类能力：`interface_name` 不等于 `collector_id`，`collector_id` 不等于 `dataset_id`。
- 如果上游口径不同，应新建接口或数据集，不要复用旧名改语义。

## 数据源 Provider 开发规范

数据源 Provider 负责把一个上游源接入 AxData 的接口目录。它的核心成果是“可调用接口”，不是本地数据文件。

### 必须声明

每个数据源接口必须声明：

- `name` / `interface_name`
- 中文名 `display_name_zh`
- `source_code`、`source_name_zh`
- 分类 `category`
- 完整接口目录 `menu_path`
- 输入参数 `parameters`
- 输出字段 `fields`
- 接口页中文短摘要 `summary_zh`
- 接口页中文说明 `description_zh`
- 参数区补充说明 `params_note_zh`
- 参数区静态调用示例 `params_example_zh`
- 调用说明 `description` / `first_stage_strategy`
- 真实静态示例 `example`
- 静态参考表 `reference_sections`
- 是否支持采集。当前 source_request 默认不支持采集，除非另有独立 CollectorSpec。

运行时接口目录当前使用单个 `example`。插件 manifest 协议如果写 `examples` 数组，必须选择一个主样例同步为运行时 `example`，避免接口页不知道展示哪份样例。

Web 左侧接口目录以 Provider manifest / Registry 返回的 `menu_path` 为事实源。插件必须声明完整路径；Web 不为具体数据源硬编码接口树。小源可以用 `["巨潮", "公告数据"]`，大源应声明完整源内分层，例如 `["通达信", "股票数据", "基础数据"]`。

接口页中文内容也以插件 / Provider manifest / Registry 为事实源。Web request 接口页只做通用渲染，不再用旧静态 catalog 为具体接口补标题、说明、参数示例、真实样例或参考表。`summary_zh`、`description_zh`、`params_note_zh`、`params_example_zh` 负责页面文案；`parameters`、`fields`、`example.response`、`reference_sections` 负责事实数据。

### 输入参数

参数必须写清楚：

- 名称
- 类型
- 是否必填
- 默认值
- 中文说明
- 日期格式
- 代码格式
- 远程调用时路径类参数指的是 API 服务器上的路径，不是浏览器电脑上的路径。

示例：

```python
RequestParameter(
    "trade_date",
    "string",
    False,
    "Trade date.",
    "交易日期，YYYYMMDD 或 YYYY-MM-DD，默认今天。",
)
```

### 输出字段

字段必须写清楚：

- 字段名
- 类型
- 中文含义
- 单位
- 是否源端口径
- 是否可能为空

特别注意：

- 价格、成交额、成交量、百分比必须写单位。
- `instrument_id` 是 AxData 统一证券代码，不能用源端原始代码代替。
- 源端原始字段可以保留，但不能冒充 core 层稳定字段。

### 静态真实示例

接口页示例必须是“已经真实请求过的静态快照”，页面打开时不应为了展示示例再实时请求源端。

规范：

- 不能编假数据。
- 不能把源端 0 条误当成正常示例，除非接口本身就是空结果演示。
- 示例参数要尽量选择稳定、可解释的历史日期。
- 如果源端只保留近期数据，示例要写明生成日期，并定期刷新静态快照。
- 返回字段必须和接口字段声明一致。
- 示例最多展示小样本，不能塞全量结果。

当静态样例生成失败时：

- 先判断是参数过期、源端暂时不可用，还是接口事实上没有数据。
- 能用真实参数取到数据的，替换静态样例。
- 长期没有真实数据、字段也无法验证的接口，应讨论是否删除，而不是保留假接口。

### 本地与远程调用

本地 SDK：

- `AxDataClient()` 默认本地模式。
- 本地查询读 Parquet/DuckDB。
- 本地源端直取由本机 adapter 请求源端。
- 本地模式不需要 AxData HTTP token。

远程 SDK/API：

- `AxDataClient(api_base="http://host:8666")` 或 `AXDATA_API_BASE` 进入远程模式。
- 远程调用读的是 API 服务器配置的数据目录。
- 如果服务端开启鉴权，需要传 AxData token。
- token 只属于 AxData API，不等于第三方源 token。

接口页 UI 只应在远程调用说明里提示 token，不要让用户误以为本地 SDK 也必须传 token。

## 采集器开发规范

采集器负责把数据生产成本地资产。只要叫采集，就必须有 task/run 元数据、输出文件和质量结果。

### 独立性

新采集器必须独立：

- 有 CollectorSpec。
- 有 runner entry。
- 有 dataset/output 声明。
- 有资源组和并发策略。
- 有质量规则。
- 不通过 `/v1/request` 套接口采集。
- 不依赖接口页是否存在同名 `interface_name`。

采集器可以复用公共工具库、字段定义和存储 writer，但不能把接口 Provider 当作采集器身份。

### 必须声明

每个采集器必须声明：

| 字段 | 说明 |
| --- | --- |
| `collector_id` | 采集器能力名。 |
| `collector_plugin_id` | 采集器所属插件。 |
| `display_name_zh` | 用户看到的中文名。 |
| `dataset_id` | 默认产出的数据集。 |
| `runner_entry` | 运行入口。 |
| `resource_group` | 资源组，例如 `tdx`、`http`。 |
| `params_schema` | 创建任务时可配置的输入参数。 |
| `output` | 输出层、格式、路径、写入策略。 |
| `quality` | 主键、必填列、日期字段、数值检查等质量规则。 |
| `required_datasets` | 运行前必须存在的基础数据，例如交易日历。 |

### 任务参数

采集页应区分三类参数：

| 参数区 | 作用 | 例子 |
| --- | --- | --- |
| 基本参数 | 任务名、输出格式、路径、并发档位、资源配置 | task name、formats、server_count |
| 输入参数 | 采集范围和源端请求参数 | code、start_date、end_date、period |
| 输出参数 | 字段、写入策略、数据集说明 | fields、dataset_id、write_mode、partition_by |

创建任务按钮应位于输入/输出配置之后。用户先配置参数，再创建任务。手动采集和定时采集应在任务列表中操作。

### 调度语义

采集器定时任务必须写清楚是自然日还是交易日。

建议：

- A 股行情、榜单、交易相关采集默认“交易日每天”。
- 财报、公告、资讯类可以按自然日，但必须在说明里写清楚。
- 使用交易日定时时，必须依赖本地 `trade_cal`。
- 没有交易日历缓存时，应提示去配置或基础数据页更新交易日历缓存，而不是静默失败。

### 并发与长连接

并发配置应有默认档位，也支持自定义。

推荐 UI：

- 默认档位：保守、标准、激进、自定义。
- 自定义项：服务器数、每服务器长连接数。
- 总并发只做展示，公式为：服务器数 × 每服务器长连接数。
- 不让用户直接填写“总并发”后再反推服务器和连接数。

说明：

- 多线程连接池对 TDX/TDX_EXT 这类源通常是长连接复用。
- 普通 HTTP 源端直取不应默认保活，除非源端和业务明确需要。

### 运行记录

采集器 run history 必须展示：

- 状态
- 开始/结束时间
- 写入行数
- 输出路径
- 进度
- 错误摘要
- 日志路径或 run detail 入口
- 删除单条记录按钮

删除 run history 只删除历史记录，不删除任务配置和已采集数据。删除数据集才删除对应本地数据目录。

## 数据集声明规范

数据集声明是采集器和数据页之间的契约。没有数据集声明，数据页只能靠猜目录和猜字段，采集器变多后会不可控。

### 必须声明的字段

每个采集器产出的数据集应声明：

| 字段 | 说明 |
| --- | --- |
| `dataset_id` | 稳定数据集 ID，例如 `daily`。 |
| `display_name_zh` | 中文名。 |
| `layer` | `raw`、`staging`、`core`、`factor` 或 `snapshot`。 |
| `table` | 查询表名。 |
| `schema` | 字段名、类型、中文说明、单位。 |
| `primary_key` | 主键字段。 |
| `date_field` | 日期字段。 |
| `partition_by` | 分区字段。 |
| `write_mode` | `snapshot`、`append`、`overwrite_partition`、`replace_range`、`upsert_by_key`。 |
| `formats` | 输出格式，`parquet` 必选。 |
| `storage_path` | 预期输出路径。 |
| `queryable` | 是否允许进入查询层；不能单独决定数据页展示。 |
| `duckdb_cache` | 是否支持 DuckDB 查询缓存。 |

数据集声明只是“应该怎么产出”的契约，不是“本机已经有数据”的证明。Data Browser / 数据页只能从 `CollectorRun.output_paths`、写入 metadata、Downloader 日志或真实存在的 Parquet 路径发现 dataset；插件 manifest 或 CollectorSpec 里只声明了 `dataset_id`、`queryable`、`storage_path`，但本地没有输出路径或文件时，不应进入数据页列表，也不应暴露删除 dataset 操作。

### 多表与多文件形态

采集器可以产出不同形态的数据：

| 形态 | 例子 | 推荐声明 |
| --- | --- | --- |
| 单表单文件 | 小型主数据 latest | `dataset_id + table + snapshot` |
| 一天一个文件 | 日线、复权、榜单 | `partition_by=["trade_date"]`，路径下 `YYYYMMDD.parquet` |
| 一只股票一个文件 | 个股大历史或高频数据 | `partition_by=["instrument_id"]` 或明确 symbol layout |
| 多张表 | 财务报表、复杂专题 | 一个 collector 可以声明多个 dataset outputs |
| 多格式导出 | Parquet + CSV + DuckDB | Parquet 是主数据，其他是导出/缓存 |

标准路径：

```text
data/core/table=daily/parquet/20260703.parquet
data/core/table=adj_factor/parquet/20260703.parquet
data/snapshot/table=tdx.stock_codes/parquet/latest.parquet
```

当前标准优先采用“格式目录下按天文件”的方式，例如：

```text
data/core/table=adj_factor/parquet/20260703.parquet
```

旧式 `trade_date=20260703/*.parquet` 目录可以继续读取兼容，但新采集器不应优先采用。

### 删除语义

删除必须说清楚范围：

| 删除动作 | 删除什么 | 不删除什么 |
| --- | --- | --- |
| 删除 run history | 单条运行记录 | 任务配置、数据文件 |
| 删除 task | 用户创建的任务配置 | 已采集数据、run history 可按产品策略保留或标记 |
| 删除 dataset | dataset 在 AxData 数据根下的本地数据目录、相关数据索引 | 插件代码、接口、采集器定义 |
| 删除缓存 | 缓存目录或 DuckDB 查询缓存 | Parquet 正式数据 |

删除数据集前必须弹窗确认，并显示将删除的根目录。

## Parquet、CSV、JSON 与 DuckDB

### Parquet

Parquet 是默认且必须支持的正式数据格式。

- 长期保存。
- 作为数据事实源。
- 适合列式扫描、压缩、跨语言读取。
- 数据页默认优先发现和预览 Parquet。
- DuckDB 可以直接读取 Parquet。

### CSV

CSV 是可选导出格式。

- 便于人工查看和外部工具导入。
- 不作为 AxData 的主数据事实源。
- 大数据集不建议默认只存 CSV。

### JSON / JSONL

JSON/JSONL 只作为兼容或调试输出。

- 不作为新采集器默认格式。
- 如果保留，必须标明是调试/兼容用途。

### DuckDB

DuckDB 不是 Parquet 的备份，也不是另一种必须保存的数据格式。

DuckDB 在 AxData 里的角色：

- 查询执行引擎。
- 可以直接读 Parquet。
- 可以保存视图、临时表、索引式缓存和查询缓存。
- 可以重建。

如果页面展示 DuckDB，应命名为：

```text
DuckDB 查询缓存
```

展示规则：

- 如果采集器声明支持 DuckDB 查询缓存，则可选。
- 如果未声明支持，也可以显示但禁用，并标注“采集器未声明”。
- DuckDB 不应强制选中。
- 强制默认选中的只有 Parquet。

核心说明：

- Parquet 是正式文件。
- DuckDB 是用来查这些文件的工具。
- `.duckdb` 文件坏了可以重建。
- 删除 DuckDB 查询缓存不应删除 Parquet 正式数据。

## 数据页规范

数据页回答的是：“本机已经有什么数据，可以怎么查？”

数据页不应请求源端，不应创建采集任务。

数据页列表只展示已经有本地数据实例的 dataset。所谓“本地数据实例”至少应能定位到 AxData 数据根下的输出路径、写入 metadata、run/downloader output 记录或真实 Parquet 文件；单纯的插件声明、CollectorSpec 输出契约或 `queryable=true` 不能让一个空 dataset 出现在数据页。

### Dataset 列表

必须展示：

- 数据集中文名
- `dataset_id`
- 来源采集器或数据源
- 层级
- 行数
- 日期范围
- 最近更新时间
- 质量状态
- 支持格式

### Dataset 详情

必须展示：

- 数据路径
- 当前预览读取的是哪份文件
- Parquet 路径
- CSV 路径，如果有
- DuckDB 查询缓存路径，如果有
- schema
- 主键
- 日期字段
- 分区方式
- 写入策略
- 最近 run
- 质量规则和告警

### 预览

预览必须说明：

- 预览来自已入库数据，不请求源端。
- 默认读取 Parquet。
- 如果用户选择日期范围，应尽量裁剪到对应日期文件。
- 单次预览必须有限制，例如最多 100 行。

## 接口页 UI 规范

接口页回答的是：“这个源端接口怎么临时调用，返回什么？”

必须包含：

- 接口名称和数据源。
- 输入参数。
- 输出字段。
- 真实静态样例。
- 默认只展示 curl 调用示例，其他 SDK 示例可折叠。
- 远程模式 token 说明。

输入参数：

- 使用表单或紧凑参数表。
- 不要把说明文案写得像功能介绍卡片。
- 参数字段必须和后端 catalog 对齐。

输出字段：

- 字段表必须有中文含义。
- 单位必须清楚。
- 源端口径字段必须标明。

真实样例：

- 页面打开不实时请求源端。
- 样例来自插件 manifest / Registry 的静态 `example.response`。
- 类别码、枚举映射、字段口径对照等参考表来自插件 `reference_sections`。
- 中文摘要、正文说明、参数提示和参数示例来自插件 / Registry 的 `summary_zh`、`description_zh`、`params_note_zh`、`params_example_zh`。
- Web request 接口页不维护具体接口的静态页面副本；特殊非 request 页面必须单独说明原因。
- 样例数据必须和字段声明对齐。
- 如果样例为空，必须有可解释原因，不能默认为“正常”。

远程 token：

- 只在远程 SDK/API 示例旁边提示。
- 文案要明确“不影响本地 SDK 调用”。

## 采集页 UI 规范

采集页回答的是：“如何把数据保存到本机，并管理任务？”

页面结构：

1. 基本参数。
2. 输入参数。
3. 输出参数。
4. 创建任务。
5. 任务列表。
6. 运行进度。
7. 最近记录。
8. 日志/诊断。

### 基本参数

包含：

- 任务名称。
- 输出格式，多选，Parquet 默认选中且不可取消。
- 存储路径，只显示目录，不把文件名混在目录字段里。
- 文件名规则，如果需要展示，单独一行。
- 并发档位。
- 自定义服务器数和长连接数。

### 输入参数

输入参数默认展开。

- 用户应在输入框或选择器里填写参数。
- 复选、多选、日期范围、代码列表使用合适控件。
- 不要只展示静态文字。
- 输入参数说明优先来自 CollectorRegistry 返回的 CollectorSpec。采集器声明了关联接口时，可以复用 runtime interface catalog 的 `parameters` / `params_note_zh`，但不能回查历史 Web 静态 catalog。

### 输出参数

输出参数可以默认展开，尤其是页面视觉上需要和输入参数平衡时。

包含：

- dataset_id
- 输出字段
- 写入策略
- 分区方式
- 质量规则
- 支持格式
- DuckDB 查询缓存是否支持

输出字段说明优先来自 CollectorSpec 的 `output` / `quality` / 数据集声明。采集器声明了关联接口时，可以复用 runtime interface catalog 的 `fields`，但不能由 Web 为某个采集器硬编码字段口径。

### 创建任务

- 创建任务按钮放在输出参数下面。
- 创建后任务进入任务列表。
- 不在顶部重复放一组“采集操作”造成语义混乱。

### 任务列表

任务列表应是紧凑的一行式表格或列表，不应堆很多无意义卡片。

每行必须包含：

- 任务名。
- 输出路径摘要。
- 手动采集按钮。
- 定时采集类型。
- 定时时间。
- 定时开关。
- 最近状态。
- 删除任务按钮。

文案：

- 使用“手动采集”，不要用有歧义的“采集一次”。
- 如果选择定时采集，应先设置定时时间。
- A 股行情默认使用“交易日每天”。

### 运行进度

采集进度适合放在任务列表下方或最近记录上方。

必须展示：

- 当前运行状态。
- 阶段。
- 已处理行数或日期。
- 进度条。
- 错误摘要。
- 日志入口。

### 最近记录

默认展示最近 3 条即可。

每条记录应支持单独删除。删除前需要确认。删除 run history 不删除数据文件。

## 插件页 UI 规范

插件页回答的是：“当前安装了哪些能力，它们提供什么接口和采集器？”

必须区分：

- Provider 数据源能力。
- Collector 采集能力。
- DownloaderProfile 兼容能力。
- 预装、AXP、pip、editable 等安装来源。

插件卡片的“导出 AXP”只导出插件安装包。导出内容不得包含已采集数据、metadata 数据库、任务历史、run history、日志、缓存、AxData API token 或第三方数据源凭据；导入后仍按 manifest 的 Provider / Collector 能力声明进入对应 Registry。

所有诊断项都要有中文解释。不能只显示英文 key。

删除插件时必须弹窗说明：

- 会隐藏/移除哪些接口或采集器。
- 不会删除哪些数据。
- 如果是预装插件，是逻辑卸载还是物理删除。

## 开始页规范

开始页是开发文档入口，不是营销页。

建议栏目：

- 快速开始。
- 数据源开发。
- 采集器开发。
- 数据集声明与 DuckDB。
- UI 规范。
- 打包安装。
- 插件排错。
- 架构说明。
- 服务器使用。
- Python SDK 主入口。

每个栏目要短，但能点进详细文档。长内容放下方或 Markdown 文档，不挤在左侧导航。

开始页术语必须和项目一致：

- 数据源，不叫软件源。
- 采集器，不叫下载器。
- DuckDB 查询缓存，不叫数据备份。
- 接口页，不叫采集页。

## 验证规范

改动不同层级后，应至少执行对应检查。

### 文档和 UI 文案

```powershell
npm run build:web
```

### Python 契约、API、采集和存储

```powershell
.venv\Scripts\python.exe -m compileall -q libs\axdata_core apps\api packages\axdata-sdk services scripts tests
```

### 重点测试

```powershell
.venv\Scripts\python.exe -m pytest tests\test_external_sources.py tests\test_builtin_providers.py tests\test_provider_catalog.py -q
```

如果已有历史测试因为未同步的旧断言失败，应在最终说明中明确失败原因，不能假装全绿。

### 手动验证

```powershell
npm run dev:api
npm run dev:web
curl http://127.0.0.1:8666/health
curl http://127.0.0.1:8666/v1/config
curl http://127.0.0.1:8666/v1/request/interfaces
curl http://127.0.0.1:8666/v1/plugins/collectors
curl http://127.0.0.1:8666/v1/data/datasets
```

## 维护流程

开发规范用于约束已经进入 AxData 的产品能力。新增或调整功能时，按下面流程维护文档、页面和测试：

1. 明确改动属于数据源接口、采集器、数据集、插件管理、数据浏览或 UI 文案中的哪一类。
2. 更新对应专题文档，并保持开始页入口、接口页、采集页和插件页的术语一致。
3. 接口变更需要同步参数、字段、中文说明、真实样例、SDK 示例和 source_request 路由测试。
4. 采集器变更需要同步 CollectorSpec、runner_entry、任务参数、输出 dataset、质量规则和运行状态展示。
5. 数据集变更需要说明 schema、Parquet 路径、DuckDB 查询缓存、预览来源和删除范围。
6. UI 变更需要检查中文文案、空状态、错误状态、加载状态和移动/桌面布局。
7. 完成后运行本页列出的相关验证命令，并在进度文档中记录结果。

开发规范不是任务清单；它只描述 AxData 已采用的边界、命名、页面口径和验证规则。
