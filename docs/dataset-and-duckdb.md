# AxData 数据集声明与 DuckDB 说明

这页只讲一件事：采集器把数据落到哪里，数据页和 SDK 怎么知道这些文件可以被查询。

## 核心说明

- 数据集声明是采集器和数据页之间的合同，不等于本机已经有这份数据。
- Parquet 是正式数据文件，是长期事实源。
- CSV 是可选导出，方便人工查看。
- JSON / JSONL 只适合调试或兼容，不作为新采集器默认格式。
- DuckDB 是查询工具和可重建查询缓存，不是 Parquet 的备份，也不是必须保存的第二份正式数据。

也就是说，采集器真正应该保证的是 Parquet 文件完整、字段清楚、路径稳定。DuckDB 可以直接读 Parquet，也可以生成查询缓存；缓存坏了或删了，可以从 Parquet 重建。

## 数据集声明必须写什么

每个可查询采集结果都应该声明：

| 字段 | 说明 |
| --- | --- |
| `dataset_id` | 稳定数据集 ID，例如 `daily`、`tdx.stock_codes`。 |
| `display_name_zh` | 中文名，给 Web 和文档展示。 |
| `layer` | 数据层，例如 `snapshot`、`core`、`factor`。 |
| `table` | 查询表名。 |
| `schema` | 字段名、类型、中文说明、单位。 |
| `primary_key` | 主键字段。 |
| `date_field` | 日期字段，没有日期也要说明为空。 |
| `partition_by` | 分区字段，例如 `trade_date`。 |
| `write_mode` | 写入策略，例如 `snapshot`、`overwrite_partition`、`upsert_by_key`。 |
| `formats` | 输出格式，`parquet` 必须支持且默认选中。 |
| `storage_path` | 数据根目录下的预期输出路径。 |
| `queryable` | 是否允许进入查询层；不能单独决定数据页展示。 |
| `duckdb_cache` | 是否声明支持 DuckDB 查询缓存。 |

这里要分清两层：数据集声明说明“采集器会产出什么”，Data Browser 说明“本机已经产出了什么”。只有本地存在输出路径、写入 metadata、run/downloader output 记录或真实 Parquet 文件时，数据页才应该列出这个 dataset；只有 manifest / CollectorSpec 声明但还没采集的 dataset，不进入数据页，也不提供删除数据集按钮。

## 路径规则

推荐新采集器使用“表目录 / 格式目录 / 文件”的结构：

```text
data/core/table=daily/parquet/20260703.parquet
data/snapshot/table=tdx.stock_codes/parquet/latest.parquet
```

一天一个文件时，不要再套很多日期文件夹，优先这样：

```text
data/core/table=daily/parquet/20260703.parquet
```

旧式 `trade_date=20260703/*.parquet` 可以保留读取兼容，但新采集器不要优先采用。

## 多表和多文件

采集器不一定只产出一张表。常见情况：

| 形态 | 例子 | 建议 |
| --- | --- | --- |
| 单表单文件 | 股票列表 latest | `latest.parquet` |
| 一天一个文件 | 日线、榜单 | `partition_by=["trade_date"]` |
| 一只股票一个文件 | 个股长历史 | 明确 `instrument_id` 路径规则 |
| 多张表 | 财务专题 | 一个 collector 声明多个 dataset outputs |
| 多格式 | Parquet + CSV + DuckDB 查询缓存 | Parquet 是主数据，其他是导出或缓存 |

## DuckDB 怎么展示

页面里应写成：

```text
DuckDB 查询缓存
```

展示规则：

- Parquet 默认选中且不可取消。
- DuckDB 查询缓存可以显示，但不强制选中。
- 如果采集器声明支持 DuckDB 查询缓存，则可以让用户勾选。
- 如果采集器没有声明支持，也可以显示禁用态，并标注“采集器未声明”。
- 删除 DuckDB 查询缓存不删除 Parquet 正式数据。

## 数据页怎么读

数据页只回答“本机已经有什么数据”。它不应该临时请求源端，也不应该创建采集任务。

数据页列表必须以本地落盘事实为准。`queryable=true`、`storage_path` 或 `dataset_id` 声明只是查询契约，不能被当成已入库数据。

数据页预览默认读已入库 Parquet，并显示：

- 数据集中文名和 `dataset_id`
- 数据路径
- 当前预览读取的文件
- Parquet 路径
- CSV 路径，如果有
- DuckDB 查询缓存路径，如果有
- schema、主键、日期字段和分区方式
- 最近更新时间、行数和质量状态

单次预览必须有限制，例如最多 100 行；用户选择日期范围时，应尽量裁剪到对应日期文件。

## 删除语义

| 删除动作 | 删除什么 | 不删除什么 |
| --- | --- | --- |
| 删除运行记录 | 单条 run history | 任务配置、数据文件 |
| 删除任务 | 用户创建的任务配置 | 已采集数据 |
| 删除数据集 | 数据根目录下该 dataset 的本地数据目录和索引 | 插件代码、接口定义、采集器定义 |
| 删除 DuckDB 查询缓存 | `.duckdb` 文件或缓存目录 | Parquet 正式数据 |

删除数据集前必须弹窗确认，并显示将删除的根目录。
