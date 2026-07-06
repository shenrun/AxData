# AxData 采集器插件开发教程

采集器插件负责把数据生产成本地资产。它回答的问题是：“这个任务怎么运行、写到哪个 dataset、怎么限流、怎么记录进度、怎么做质量检查。”

采集器和数据源接口是独立的。采集器可以自带取数逻辑，也可以读取本地文件或公共库；它不要求存在对应 Provider、`interface_name` 或 `downloader_profile`。但只要要落盘，就必须进入 AxData Collector Runner。

本教程的术语和边界以 [axdata-development-standards.md](axdata-development-standards.md) 为准：Collector 负责 task、run、write、progress、logs 和 quality；Provider / Adapter 只负责临时 `source_request`。

## 1. 什么时候写采集器插件

适合写采集器插件的场景：

- 用户需要创建任务。
- 需要手动采集或交易日定时采集。
- 需要写 Parquet 主数据，并可选额外导出 CSV 或 DuckDB 查询缓存。
- 需要进度、日志、失败记录。
- 需要质量规则和数据集元信息。
- 需要全局资源组和并发限制。

不适合采集器插件的场景：

- 只是临时查一次。
- 不需要落盘。
- 不需要任务状态。

这类场景写数据源 Provider 即可。

## 2. 最小目录

collector-only 插件推荐目录：

```text
axdata-collector-demo/
  pyproject.toml
  README.md
  LICENSE
  src/
    axdata_collector_demo/
      __init__.py
      plugin.py
      collectors.py
      runner.py
      axdata-plugin.json
      samples/
        demo_rows.jsonl
  tests/
    test_manifest.py
    test_runner.py
```

最小 `pyproject.toml`：

```toml
[project]
name = "axdata-collector-demo"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["axdata-core>=0.1.0"]

[project.entry-points."axdata.plugins"]
demo = "axdata_collector_demo.plugin:plugin"

[tool.setuptools.package-data]
axdata_collector_demo = ["axdata-plugin.json", "samples/*.jsonl"]
```

## 3. CollectorSpec

CollectorSpec 是采集器的身份和契约：

```json
{
  "collector_id": "demo.stock_snapshot.snapshot",
  "display_name_zh": "示例股票快照采集",
  "description": "采集示例股票快照并写出本地文件。",
  "collector_plugin_id": "axdata.collector.demo",
  "dataset_id": "demo.stock_snapshot",
  "asset_class": "stock",
  "category": "snapshot",
  "resource_group": "demo.http",
  "runner_entry": "axdata_collector_demo.runner:run",
  "default_schedule": {
    "kind": "manual"
  },
  "default_params": {
    "code": "000001.SZ"
  },
  "required_interfaces": [],
  "output": {
    "layer": "snapshot",
    "formats": ["parquet"]
  },
  "quality": {
    "required_columns": ["instrument_id", "trade_date"],
    "primary_key": ["instrument_id", "trade_date"]
  }
}
```

重要字段：

| 字段 | 说明 |
| --- | --- |
| `collector_id` | 采集器 ID，不等于接口名 |
| `collector_plugin_id` | 贡献该采集器的插件 ID |
| `dataset_id` | 写出的数据集 ID |
| `runner_entry` | Collector Runner 调用的 Python 入口 |
| `resource_group` | 全局资源组，用于限流和排队 |
| `default_params` | 创建任务时的默认参数 |
| `output` | 输出层、dataset、格式、路径和写入策略 |
| `quality` | 质量规则、主键、必填字段 |
| `required_datasets` | 运行前必须存在的基础数据，例如交易日历 |

## 4. runner_entry

`runner_entry` 是实际运行入口。它应该只做一次任务运行，不要自己常驻后台。

示例：

```python
def run(params=None, context=None):
    params = dict(params or {})
    code = params.get("code", "000001.SZ")

    rows = [
        {
            "instrument_id": code,
            "trade_date": "20260703",
            "value": 1.0,
        }
    ]

    return {
        "rows": rows,
        "metadata": {
            "source": "demo",
            "row_count": len(rows),
        },
    }
```

真实插件里，runner 可以请求上游、读取文件或复用公共库。但不要通过 `/v1/request`、SDK `call` 或 ProviderRegistry route 把接口临时调用伪装成采集。

## 5. 输入参数

采集器需要把用户可填参数声明清楚：

- 参数名。
- 类型。
- 是否必填。
- 默认值。
- 枚举值。
- 示例。
- 说明。

例如：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `code` | string/list | 否 | 证券代码，支持单个或多个 |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |
| `formats` | list | 否 | 输出格式列表；`parquet` 是主数据格式，`csv` 和 `duckdb` 可作为额外导出/缓存 |

Web 采集页会根据这些声明展示输入框、选择器和默认值。采集器如果声明了关联接口，Web 可以复用 runtime interface catalog 的参数说明和字段说明；不要依赖 Web 旧静态接口 catalog 为采集器补页面内容。没有关联接口时，采集器自己的 `default_params`、`output`、`quality` 和数据集声明必须足够让用户理解如何创建任务。

## 6. 输出和路径

采集器要声明数据写到哪里。`output` 是采集器和数据页之间的数据集声明契约，至少要表达 `dataset_id`、`layer`、`formats`、`write_mode`、`primary_key`、`date_field`、`partition_by` 和是否支持 DuckDB 查询缓存。

```json
{
  "output": {
    "layer": "core",
    "dataset_id": "demo.stock_snapshot",
    "formats": ["parquet", "csv", "duckdb"],
    "write_mode": "upsert_by_key",
    "primary_key": ["instrument_id", "trade_date"],
    "date_field": "trade_date"
  }
}
```

Parquet 是正式数据文件，默认必选且不应被用户取消。CSV 是导出格式；JSON/JSONL 只适合作为调试或兼容输出；DuckDB 是查询缓存或查询层，可重建，不能替代 Parquet。

常见写入策略：

| 策略 | 说明 |
| --- | --- |
| `snapshot` | 每次生成一份快照 |
| `append` | 追加写入 |
| `replace_range` | 替换某个日期范围 |
| `upsert_by_key` | 按主键去重更新 |
| `overwrite_partition` | 覆盖分区 |

日线类数据通常按交易日写文件。比如 Parquet 格式可以落到：

```text
data/core/table=daily/parquet/20260703.parquet
```

不要把一天拆成很多层无意义目录，除非数据量和查询模式真的需要。

## 7. 质量规则

质量规则用于防止坏数据悄悄入库：

```json
{
  "quality": {
    "required_columns": ["instrument_id", "trade_date", "close"],
    "primary_key": ["instrument_id", "trade_date"],
    "non_negative_columns": ["open", "high", "low", "close", "volume", "amount"],
    "date_field": "trade_date"
  }
}
```

常见检查：

- 必填字段存在。
- 主键不重复。
- 日期范围正确。
- 数值非负。
- 复权因子大于 0。
- 交易日历覆盖。
- 写入前后行数合理。

## 8. 调度

采集器只声明默认建议，用户最终在任务列表里决定手动采集还是定时采集。

示例：

```json
{
  "default_schedule": {
    "kind": "trading_day",
    "time": "18:30",
    "timezone": "Asia/Shanghai"
  }
}
```

“每天定时”对 A 股日线类任务通常应该理解为交易日每天。没有交易日历缓存时，应提示用户去配置页更新交易日历缓存，而不是静默按自然日跑。

## 9. 并发和资源组

插件可以声明建议预算，但实际资源由 AxData 统一裁决。

```json
{
  "resource_group": "demo.http",
  "default_limits": {
    "mode": "balanced",
    "source_server_count": 1,
    "connections_per_server": 2,
    "max_concurrency": 2
  }
}
```

规则：

- 共享上游配额的采集器使用同一个 `resource_group`。
- 不要在 runner 里无限开线程。
- 不要绕过 AxData 的资源池。
- 默认给保守档，允许用户自定义。

## 10. Web 页面应该展示什么

采集器详情页至少要展示：

- 基本参数：任务名称、格式、路径、并发档位。
- 输入参数：用户真正要填的业务参数。
- 输出参数：字段、类型、质量规则。
- 创建任务按钮。
- 任务列表：窄行展示任务名称、状态、手动采集、定时开关、定时时间、删除。
- 最近采集记录：默认 3 条即可。
- 进度：放在当前任务行或任务详情的运行状态区域。
- 日志或 run detail：展示错误摘要、日志路径和下一步动作。

这些内容的事实源是 CollectorSpec / CollectorRegistry，以及可选关联的 runtime interface catalog。Web 不为具体采集器维护静态页面副本，不把旧接口静态 catalog 当作采集器详情来源。

不要展示历史兼容字段作为主信息，例如 `downloader_profile`、legacy interface 映射等。这些适合诊断，不适合普通配置页。

## 11. 本地验证

安装开发插件：

```powershell
.\.venv\Scripts\python -m pip install -e C:\path\to\axdata-collector-demo
```

查看采集器目录：

```powershell
.\.venv\Scripts\axdata plugin collectors --json
curl http://127.0.0.1:8666/v1/plugins/collectors
```

创建任务并运行：

```powershell
.\.venv\Scripts\axdata collector task create demo.stock_snapshot.snapshot --name "示例快照"
.\.venv\Scripts\axdata collector run-now <task_id>
.\.venv\Scripts\axdata collector runs --task-id <task_id>
```

检查数据：

```powershell
.\.venv\Scripts\axdata data list
.\.venv\Scripts\axdata data inspect demo.stock_snapshot
.\.venv\Scripts\axdata data preview demo.stock_snapshot --limit 3
```

## 12. 常见错误

| 现象 | 常见原因 | 修复 |
| --- | --- | --- |
| 采集器不出现 | 缺 `axdata-plugin.json` | 把 manifest 打进 wheel |
| 可以看到插件但不能运行 | `runner_entry` 不存在或导入失败 | 检查入口路径 |
| 任务一直 blocked | required dataset 缺失 | 先采集或同步基础数据 |
| 定时任务不跑 | 调度未启用或交易日历缺失 | 开启定时并更新交易日历 |
| 写入失败 | output/quality/字段不匹配 | 对齐 dataset 字段和质量规则 |
| 插件禁用后任务不可跑 | 这是正常状态 | 重新启用插件或删除任务 |

## 13. 边界红线

采集器插件不要做这些事：

- import 时联网。
- 自己长期运行后台线程。
- 自己维护一套任务数据库。
- 绕过 AxData Writer 写 core/factor。
- 绕过资源池开大量连接。
- 把临时接口调用包装成采集。
- 删除用户数据、metadata 或 run history。

采集器只声明和执行单次运行，任务生命周期由 AxData 管。
