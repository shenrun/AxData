# AxData 数据源插件开发教程

数据源插件负责把一个上游数据源接入 AxData 的接口目录。它回答的问题是：“用户临时查一次这个源的数据时，参数是什么、返回什么字段、由哪个 Adapter 请求上游。”

它不等于采集器。接口临时调用默认不写入 `data/raw`、`data/staging`、`data/core` 或 `data/factor`，也不会自动创建采集任务。需要长期落盘时，再写独立采集器插件。

本教程的术语和边界以 [axdata-development-standards.md](axdata-development-standards.md) 为准：Provider / Adapter 负责 `source_request`，采集任务、写入、进度、日志和质量结果属于 Collector。

## 1. 什么时候写数据源插件

适合写数据源插件的场景：

- 想把一个上游接口展示到 AxData 的接口页。
- 想让 Python SDK、HTTP API 或 Web 调试页可以按统一参数调用。
- 数据只需要临时查询，不一定要入库。
- 以后可以再为其中一部分接口写采集器。

不适合放在数据源插件里的内容：

- 长期定时任务。
- 后台线程。
- 自己直接写 Parquet。
- 采集进度和任务历史。
- 绕过 AxData Collector Runner 的批量入库。

## 2. 最小目录

推荐目录：

```text
axdata-source-demo/
  pyproject.toml
  README.md
  LICENSE
  src/
    axdata_source_demo/
      __init__.py
      provider.py
      adapter.py
      catalog.py
      axdata-provider.json
      samples/
        stock_snapshot.json
  tests/
    test_manifest.py
    test_adapter.py
    test_catalog.py
```

最小 `pyproject.toml`：

```toml
[project]
name = "axdata-source-demo"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["axdata-core>=0.1.0"]

[project.entry-points."axdata.providers"]
demo = "axdata_source_demo.provider:provider"

[tool.setuptools.package-data]
axdata_source_demo = ["axdata-provider.json", "samples/*.json"]
```

关键点：

- `axdata-provider.json` 必须被打进 wheel。
- entry point 只是候选入口，缺 manifest 不算 AxData 插件。
- Provider 代码不要在 import 时联网。

## 3. 命名规则

Provider 身份：

```text
provider_id = axdata.source.demo
source_code = demo
source_name_zh = 示例数据源
```

接口名建议：

```text
{数据口径}_{来源}
```

例子：

```text
stock_snapshot_demo
announcements_demo
financial_statement_demo
```

规则：

- 使用小写 snake_case。
- 表达数据口径，不只是上游接口原名。
- 不要抢占预装接口名。
- 外部插件最好带来源前缀或后缀。

## 4. 写接口目录

接口目录至少要写清：

| 字段 | 说明 |
| --- | --- |
| `name` | 全局唯一接口名 |
| `display_name_zh` | 中文名 |
| `source_code` | 数据源命名空间 |
| `asset_class` | stock、index、fund 等资产分类 |
| `menu_path` | Web 接口目录完整路径，例如 `["通达信", "股票数据", "基础数据"]` |
| `summary_zh` | 接口页顶部中文短摘要 |
| `description_zh` | 接口页中文正文说明 |
| `params_note_zh` | 参数区中文补充说明 |
| `params_example_zh` | 参数区静态 SDK 调用示例 |
| `parameters` | 参数名、类型、是否必填、默认值、说明 |
| `fields` | 返回字段、类型、含义、单位 |
| `example` | 已真实请求过的静态小样例 |
| `reference_sections` | 可选静态参考表，例如类别码、枚举映射、字段口径说明 |

接口页应能回答三个问题：

- 需要传什么参数？
- 会返回什么字段？
- 这个接口来自哪个插件和数据源？

参数和字段必须带中文说明。日期格式、代码格式、价格/成交量/成交额/百分比单位、是否源端原始口径都要写清楚。`instrument_id` 这类 AxData 统一字段不能被源端原始代码替代。

接口页静态样例必须来自已经真实请求过的小样本快照，不能编假数据，也不能在页面打开时为了展示样例实时请求源端。样例参数应尽量使用稳定历史日期；返回字段必须和接口字段声明一致。

`menu_path` 是接口左侧目录的事实源，必须由插件 catalog / manifest 提供完整路径。Web 只根据 Registry 返回的 `menu_path` 渲染目录，不为具体数据源写死接口树。小源可以使用两层路径，例如 `["巨潮", "公告数据"]`；通达信这类大源应使用三层或更多路径，例如 `["通达信", "股票数据", "行情数据"]`。

接口页中文文案也必须跟插件 / Provider 走。不要把接口的短摘要、正文说明、参数提示或参数调用示例只写在 Web 静态文件里；应写入 `summary_zh`、`description_zh`、`params_note_zh`、`params_example_zh`。Web request 接口页只按 Registry 返回的字段通用渲染，不为具体接口维护静态页面副本。

当前运行时接口目录使用单个 `example`，对应 `SourceRequestInterface.example`。插件 manifest 里如果按协议写了 `examples` 数组，也要选出一个主样例同步到运行时 `example`，给接口页和 API 返回使用。

接口页参考表必须跟插件 manifest 走。不要把类别码、参数槽含义、枚举映射这类内容只写到 Web 静态页面里；应写入 `reference_sections`，让插件分享、安装、禁用和 Web 展示保持同一份事实源。

## 5. 写 Provider

Provider 对象负责把接口目录和 Adapter 交给 AxData：

```python
from axdata_core.plugins import SourceProvider

from .adapter import DemoAdapter
from .catalog import INTERFACES


class DemoProvider(SourceProvider):
    provider_id = "axdata.source.demo"
    source_code = "demo"
    source_name_zh = "示例数据源"
    version = "0.1.0"
    plugin_api_version = "1.0"

    def interfaces(self):
        return tuple(INTERFACES)

    def create_adapter(self, options=None):
        return DemoAdapter(options=options)


provider = DemoProvider()
```

新插件不要把采集器挂在 Provider 下面。Provider 的 `collectors()` 是旧兼容路径，不是新插件推荐方式。

## 6. 写 Adapter

Adapter 只负责源端请求和字段归一：

```python
class DemoAdapter:
    def __init__(self, options=None):
        self.options = dict(options or {})

    def call(self, interface_name, params=None, fields=None, options=None):
        params = dict(params or {})
        if interface_name == "stock_snapshot_demo":
            return self._stock_snapshot(params, fields)
        raise KeyError(interface_name)
```

Adapter 应该做：

- 校验参数。
- 调用上游。
- 处理超时、限流、空结果和字段缺失。
- 把字段归一到 AxData 命名。
- 支持 `fields` 字段选择。

Adapter 不应该做：

- 写 Parquet。
- 创建采集任务。
- 启动长期后台线程。
- 把 token 写入日志。

本地 SDK 模式下，`AxDataClient()` 直接使用本机数据目录和本机 Adapter，不需要 AxData HTTP token。只有 `AxDataClient(api_base="http://host:8666")`、`AXDATA_API_BASE` 或跨机器 HTTP/API 调用，且服务端开启鉴权时，才需要 AxData token。第三方源 token 由插件自行读取和保护，不能写入样例、日志或 manifest。

## 7. Manifest

`axdata-provider.json` 是 AxData 发现插件的主文件。最小骨架：

```json
{
  "manifest_version": "1.0",
  "plugin_api_version": "1.0",
  "provider": {
    "provider_id": "axdata.source.demo",
    "source_code": "demo",
    "source_name_zh": "示例数据源",
    "version": "0.1.0",
    "declared_trust_level": "community",
    "description": "示例数据源 Provider"
  },
  "interfaces": [],
  "downloaders": [],
  "collectors": [],
  "dependencies": [],
  "config_schema": {"required_config": []}
}
```

推荐做法是由插件代码生成 manifest，再把它打进 wheel，避免 README、Python 代码和 manifest 三份内容漂移。

## 8. 本地开发验证

开发期安装：

```powershell
.\.venv\Scripts\python -m pip install -e C:\path\to\axdata-source-demo
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin info axdata.source.demo --json
```

启用插件：

```powershell
.\.venv\Scripts\axdata plugin enable axdata.source.demo
```

检查接口是否进入目录：

```powershell
curl http://127.0.0.1:8666/v1/request/interfaces
```

调用接口：

```powershell
curl -X POST http://127.0.0.1:8666/v1/request/stock_snapshot_demo ^
  -H "Content-Type: application/json" ^
  -d "{\"params\":{\"code\":\"000001.SZ\"},\"persist\":false}"
```

HTTP 请求体必须把接口参数放进 `params`。CLI 的 `--param code=000001.SZ` 和本地 SDK 的 `client.call("stock_snapshot_demo", code="000001.SZ")` 只是更顺手的写法，底层进入 HTTP API 时会转换成 `params`。

## 9. 常见错误

| 现象 | 常见原因 | 修复 |
| --- | --- | --- |
| 插件不出现在普通列表 | wheel 没带 manifest | 检查 package data |
| 诊断里出现 ignored candidate | 有 entry point 但缺 manifest | 补 `axdata-provider.json` |
| 接口冲突 | interface_name 被其他插件占用 | 改名或禁用冲突插件 |
| 启用失败 | plugin_api_version 不兼容 | 调整 manifest 版本 |
| 调用时报错 | Adapter 参数或上游响应变化 | 加参数校验和错误处理 |

## 10. 和采集器的边界

数据源插件只提供“查一次”的能力。采集器插件提供“长期落盘”的能力。

如果 Provider 或 Adapter 开始承担以下职责，应拆成采集器：

- 定时每天跑。
- 写入本地数据目录。
- 需要进度、日志、失败重试。
- 需要资源组、限流、写入锁。
- 需要质量检查。

采集器应该进入 CollectorRegistry，通过 `runner_entry` 由 AxData Collector Runner 执行。
