# AxData Collector 维护说明

本文件是维护者参考，说明旧 `services.collector` 层的边界。普通用户请优先阅读 `docs/quickstart.md`、`docs/data-layers.md` 和采集器插件文档。

Collector 层负责把已确定的数据集写入本地数据目录。Adapter 只负责取回表格行；任务编排、状态、质量检查和写入应交给 AxData Collector Runner、Writer 和 metadata 体系处理，避免把数据源细节混进调度逻辑。

## 数据集

当前核心数据集包括：

- `stock_basic_exchange`
- `trade_cal`
- `daily`
- `adj_factor`

命令行仍兼容 `stock-basic-exchange`、`trade-cal`、`adj-factor` 这类连字符写法。旧 `stock_basic` 名称作为 `stock_basic_exchange` 的兼容别名保留。

## Adapter 契约

Adapter 继承 `CollectorAdapter`，并实现：

```python
fetch(dataset: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]
```

基类也提供数据集相关 helper：

- `fetch_stock_basic_exchange(**params)`
- `fetch_trade_cal(**params)`
- `fetch_daily(**params)`
- `fetch_adj_factor(**params)`

Adapter 应返回普通字典列表，便于交给验证、存储或消息流水线处理，不应让任务层依赖某个上游 SDK。

## CSV Adapter

`CsvCollectorAdapter` 用于本地开发和离线检查。它可以读取：

- 包含 `stock_basic.csv`、`trade_cal.csv`、`daily.csv`、`adj_factor.csv` 的目录。
- 通过 `path` 指定的单个 CSV 文件。

常用参数：

- `path`：CSV 文件或目录。
- `limit`：最多返回行数。
- `start_date` / `end_date`：按 `trade_date`、`cal_date` 或 `date` 过滤。
- 其它参数：按同名字段做精确字符串匹配。

示例：

```bash
python -m services.worker.cli update daily --adapter csv --path ./data/daily.csv --dry-run
```

命令会输出 task/batch/run metadata、`dataset`、`status`、`started_at`、`finished_at`、`rows` 和 `error`。这些值属于 metadata/manifest，不是普通用户表字段。

## 交易所股票列表 Adapter

`OfficialExchangeStockBasicAdapter` 是 `stock_basic_exchange` 的交易所股票列表 adapter。它从上交所、深交所和北交所公开端点获取股票列表，并归一到 AxData `stock_basic_exchange` schema。

取数策略：

- SSE：使用 `commonQuery.do` JSON 端点。
- SZSE：优先使用 `ShowReport` JSON 分页接口，失败时使用同一报表的 xlsx 下载作为完整替换快照。
- BSE：使用 `nqxxController/nqxxCnzq.do` JSONP 端点；北交所股本返回原始股数，AxData 转换为亿股。

常用参数：

- `exchanges`：逗号分隔的交易所列表，默认 `SSE,SZSE,BSE`。
- `limit`：最多返回行数，适合 dry-run 检查；非 dry-run 写入时拒绝有限结果。
- `page_size`：接口支持分页时的每页数量。

写入质量规则：

- SZSE JSON 和 xlsx 结果不混写；JSON 路径失败时，丢弃 JSON 尝试并用 xlsx 完整替换快照。
- 空结果或有限交易所结果不写入。
- `exchange` 与 `instrument_id` 后缀必须一致，例如 `SZSE` 对应 `.SZ`。
- 每个交易所必须满足最低行数要求；已有快照不能突然低于上次同交易所行数的 90%。
- 单交易所刷新只替换该交易所，保留当前 core 表里的其它交易所数据。

Dry-run：

```bash
python -m services.worker.cli update stock_basic_exchange --adapter official_exchange --param exchanges=SSE,SZSE,BSE --limit 5 --pretty
```

写入当前 AxData 数据目录：

```bash
python -m services.worker.cli update stock_basic_exchange --adapter official_exchange --param exchanges=SSE,SZSE,BSE --no-dry-run --pretty
```

只预览北交所：

```bash
python -m services.worker.cli update stock_basic_exchange --adapter official_exchange --param exchanges=BSE --pretty
```

采集是唯一应该请求交易所 adapter 的路径。SDK 本地查询和 HTTP API 查询应读取已经入库的 Parquet/DuckDB 数据。
