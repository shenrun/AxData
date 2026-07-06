# AxData 插件开发指南

本文面向准备为 AxData 编写数据源、采集器或工具能力的开发者。它描述 AxData 采用的本地插件模型：AxData Core 是数据库、插件容器、任务平台、存储、查询、API、Web 和 CLI 宿主；数据源能力来自预装插件或外部插件。预装能力可以默认启用；社区或第三方插件是用户本地安装、本地启用、本地运行的 Python 代码，用户自行选择来源并承担运行风险。

如果你只是想安装和管理插件，先读 [plugin-install-management.md](plugin-install-management.md)。如果你要查看完整协议字段，读 [plugin-spec.md](plugin-spec.md)。本文更像实际开发手册：从最小目录、manifest、命名、接口、采集能力、打包安装到调试诊断。

插件能力边界和 Web UI 口径以 [axdata-development-standards.md](axdata-development-standards.md) 为准。一个插件包可以同时提供 Provider、Collector、DownloaderProfile 或工具能力，但这些能力的身份、注册表和运行路径必须分开：Provider 不等于 Collector，DownloaderProfile 也不是新采集器身份。

## 1. 插件能提供什么

AxData 插件可以提供一种或多种能力：

| 能力 | 说明 |
| --- | --- |
| Provider | 声明接口、参数、字段、样例，并实现源端临时调用。 |
| DownloaderProfile | 兼容路径：声明某个接口如何批量下载、使用哪个资源组、默认并发和写入建议。 |
| CollectorSpec | 声明一个可由 AxData Collector Runner 运行的独立采集器。 |
| Task Template | 给用户创建 CollectorTask 的安全默认模板。当前仓库内置模板由 core 管理，插件可通过 CollectorSpec 和 manifest 元数据为模板化入口提供素材。 |
| DependencySpec | 声明 Python 依赖和可选包内 wheel，用于安装前预览。 |
| ConfigSchema | 声明需要用户自行配置的环境变量或配置项，只做展示提示。 |

边界速查：

| 能力 | 注册位置 | 主要用户入口 | 是否默认写入 |
| --- | --- | --- | --- |
| Provider | Source Provider Registry | 接口页、`client.call(...)`、`POST /v1/request/{interface}` | 否 |
| CollectorSpec | Collector Registry | 采集页、Collector CLI/API、调度器 | 是 |
| DownloaderProfile | 兼容下载入口 | 旧显式下载路径和诊断 | 仅显式下载时 |

允许的插件形态：

- source_request-only：只有 Provider 和接口临时调用，不提供采集能力。
- Provider + DownloaderProfile：接口可临时调用，也可通过旧下载 profile 显式写出。
- Provider + legacy CollectorSpec：当前兼容路径，接口、下载 profile 和采集器一起提供；新开发不要把它作为最终形态。
- collector-only：不提供新 Provider，声明独立采集器、运行入口和输出数据集。
- 工具型插件：用于清洗、指标或格式转换，不应伪造数据源身份。

源端临时调用和采集入库必须分开。`client.call(...)`、`axdata request` 和 `/v1/request/*` 默认只请求源端一次，不写入 `raw/staging/core/factor`，也不会自动创建采集任务。需要长期保存时，新插件应提供独立 CollectorSpec / Collector manifest 和 runner entry，让运行进入 AxData Collector Runner；不要通过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或旧 DownloaderProfile 链路套接口采集。

## 2. 最小目录结构

Provider 插件的推荐目录：

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
      normalization.py
      downloader_profiles.py
      collectors.py
      axdata-provider.json
      samples/
        demo_snapshot.json
  tests/
    test_manifest.py
    test_adapter.py
    test_catalog.py
```

只有 Collector 的插件可以省略 `provider.py` 和 `adapter.py`，但仍应有 `axdata-plugin.json`、`collectors.py`、runner 实现和测试。包名建议使用 `axdata-collector-<name>` 或清晰的组织前缀，Python module 使用小写 snake_case，例如 `axdata_collector_demo`。如果同一包同时提供数据源接口和采集器，也要把接口 ID、采集器 ID 和数据集 ID 分开命名。

`pyproject.toml` 最小示例：

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

V2 多能力插件也可以使用 `axdata.plugins` entry point：

```toml
[project.entry-points."axdata.plugins"]
demo = "axdata_source_demo.plugin:plugin"
```

当前 Registry 同时识别 `axdata.providers` 和 `axdata.plugins`。无论使用哪个 entry point，wheel 或 editable 项目中都必须能找到 `axdata-provider.json` 或 `axdata-plugin.json`。

## 3. Manifest 是必需的

`axdata-provider.json` / `axdata-plugin.json` 是 AxData 识别插件的 manifest。没有 manifest 的 Python 包不算 AxData 插件，即使它声明了 `axdata.providers` 或 `axdata.plugins` entry point。

两种 manifest 的角色：

| 文件 | 当前用途 |
| --- | --- |
| `axdata-provider.json` | 当前 Provider 插件主路径，适合包含 Provider/interfaces/downloaders/legacy collectors 的兼容插件。 |
| `axdata-plugin.json` | 多能力插件通用文件名，适合独立 collector-only 或工具型插件；CollectorRegistry 会以它作为新采集器插件主路径。 |

Registry 发现插件时会先读取 distribution 中的 manifest，不 import Provider 代码。只有用户真正调用接口或运行采集时，才加载插件运行时代码。这能让 `plugin list`、Web 插件页和接口目录保持轻量，也避免破损插件拖垮整个系统。

最小 manifest 骨架：

```json
{
  "manifest_version": "1.0",
  "plugin_api_version": "1.0",
  "plugin": {
    "plugin_id": "axdata.plugin.demo",
    "name_zh": "示例插件",
    "version": "0.1.0",
    "description": "示例数据源和采集能力"
  },
  "provider": {
    "provider_id": "axdata.source.demo",
    "source_code": "demo",
    "source_name_zh": "示例数据源",
    "version": "0.1.0",
    "declared_trust_level": "community",
    "description": "示例 Provider"
  },
  "interfaces": [],
  "downloaders": [],
  "collectors": [],
  "dependencies": [],
  "config_schema": {"required_config": []},
  "required_config": []
}
```

推荐流程是由插件代码生成 manifest，再把 manifest 打进 wheel。不要让 Python 代码、README 和 manifest 变成三份互相漂移的真相源。

## 4. 命名和冲突规则

`provider_id` 是插件身份，必须稳定且全局唯一。推荐：

- `axdata.source.<name>`：个人或项目内源插件。
- `com.example.axdata.source.<name>`：组织或公司前缀。
- 不要使用已有预装插件的 `provider_id`。
- 不要把 `source_code` 当成 `provider_id`。多个 Provider 可以共享 `source_code`，但不能共享 `provider_id`。

`interface_name` 是用户调用、HTTP 路由和 Registry 精确分发的名字，也必须全局唯一。推荐：

- 小写 snake_case。
- 表达数据口径和来源，例如 `stock_snapshot_demo`、`announcements_vendor_x`。
- 外部插件尽量带来源前缀或后缀，例如 `_tdx`、`tencent_`、`myvendor_`。
- 不要依赖后缀触发路由；后缀只是名字的一部分。

冲突规则：

- 同一个 `provider_id` 被重复发现时，Registry 只保留优先级更高的一条有效 Provider，重复候选进入诊断，不进入普通插件列表。
- 不同 `provider_id` 声明同一个 `interface_name` 时，会进入 conflict，而不是静默覆盖。
- 外部插件不能用已有预装插件的 `provider_id` 接管路由。
- 用户可以通过禁用其中一个插件、改名重发插件，或 override 配置解决接口冲突。

## 5. Provider 和接口

Provider 对象最少声明身份、接口目录和 Adapter：

```python
from axdata_core.plugins import SourceProvider

from .adapter import DemoAdapter
from .catalog import INTERFACES, DOWNLOADER_PROFILES


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

    def downloader_profiles(self):
        return tuple(DOWNLOADER_PROFILES)


provider = DemoProvider()
```

Provider 的 `collectors()` 只作为旧 Provider manifest 兼容入口保留。新插件如果要提供采集器，应使用独立 CollectorSpec / Collector manifest 和 `runner_entry`，让采集器进入 CollectorRegistry，而不是把采集器挂在接口 Provider 下面。

Adapter 只负责源端请求和字段归一，默认不落盘：

```python
class DemoAdapter:
    def __init__(self, options=None):
        self.options = dict(options or {})

    def call(self, interface_name, params=None, fields=None, options=None):
        if interface_name == "stock_snapshot_demo":
            return self._stock_snapshot(dict(params or {}), fields)
        raise KeyError(interface_name)
```

Adapter 不应 import 时联网，不应写 Parquet，不应启动后台线程，不应把第三方 token 写进日志。

## 6. 参数、字段和样例

每个 InterfaceSpec 至少写清：

| 字段 | 要求 |
| --- | --- |
| `name` | 全局唯一接口名。 |
| `display_name_zh` | 中文展示名。 |
| `source_code` / `source_name_zh` | 源命名空间和中文名。 |
| `asset_class` | `stock/index/etf/fund/bond/future/option/fx/macro` 之一。 |
| `menu_path` | Web 接口目录完整路径，由插件声明，Web 只负责渲染。 |
| `request_mode` | 通常为 `source_request`。 |
| `summary_zh` | Web 接口页顶部中文短摘要，属于插件接口契约。 |
| `description_zh` | Web 接口页中文正文说明，存在时优先于调试用 `notes` 展示。 |
| `params_note_zh` | 参数区中文补充说明。 |
| `params_example_zh` | 参数区静态 SDK 调用示例，不触发源端请求。 |
| `parameters` | 参数名、类型、是否必填、枚举、默认值和说明。 |
| `fields` | AxData 字段名、类型、单位、是否必填和说明。 |
| `example` / `examples` | 运行时接口目录使用单个 `example`；manifest 协议可写 `examples` 数组，但必须选出主样例给接口页和 API 使用。 |
| `reference_sections` | 可选静态参考表，例如类别码、枚举映射、字段口径说明；属于插件接口契约，不能只写在 Web 里。 |
| `collection` | 兼容下载提示；支持时可指向默认 DownloaderProfile，但不等于 CollectorSpec，也不是采集器 catalog 的事实源。 |

接口目录也属于插件接口契约。小数据源可以声明 `["巨潮", "公告数据"]` 这类两层目录；通达信这类大数据源应声明 `["通达信", "股票数据", "基础数据"]` 这类完整源内分层。不要依赖 Web 静态文件替插件补目录。

接口页中文内容也属于插件接口契约。短摘要、正文说明、参数提示和参数调用示例应写入 `summary_zh`、`description_zh`、`params_note_zh`、`params_example_zh`，让插件安装、分享、禁用和 Web 展示使用同一份事实源。Web request 接口页不应为某个接口维护单独的静态文案副本。

接口页的参考内容也跟插件走。像通达信股本变迁的“类别码参考”这类表，应写入 `reference_sections`，由 Web 通用渲染；Web 不应为某个数据源单独保存一份参考表副本。

参数示例：

```json
{
  "name": "trade_date",
  "display_name_zh": "交易日期",
  "type": "date",
  "required": false,
  "multiple": false,
  "default": null,
  "control": "date",
  "placeholder": "20260105",
  "description": "不填时返回源端最新可用日期。"
}
```

字段示例：

```json
{
  "name": "instrument_id",
  "display_name_zh": "证券代码",
  "type": "string",
  "required": true,
  "unit": null,
  "description": "AxData 统一证券代码，例如 000001.SZ。"
}
```

字段必须尽量使用 AxData 稳定字段，不要把上游原始列名直接暴露给用户。日期使用 `YYYYMMDD`。字段名使用 snake_case。价格、成交量、成交额、股本和百分比必须写单位和口径。

## 7. source_request-only 插件

如果接口只适合临时查询，就做 source_request-only 插件：

- `interfaces[].request_mode = "source_request"`。
- `interfaces[].collection.supported = false`。
- `downloaders = []`。
- `collectors = []`。
- 示例只展示小样本参数，不暗示入库。

适合 source_request-only 的接口包括实时快照、盘口、当日排行、调试接口、服务器状态和低稳定性的网页接口。它们可以通过：

```powershell
.\.venv\Scripts\axdata request stock_snapshot_demo --param code=000001.SZ --json
```

或：

```python
import axdata as ax

client = ax.AxDataClient()
rows = client.call("stock_snapshot_demo", code="000001.SZ")
```

这些调用默认不写入本地数据目录。

## 8. DownloaderProfile

DownloaderProfile 是当前兼容模型的一部分。它说明如何把一个已注册接口变成一次显式下载：资源组、默认参数、并发建议、输出层和写入策略。它可以继续服务旧接口下载和旧 Provider manifest collectors，但新采集器插件不应把 DownloaderProfile 当作采集器身份，也不应要求每个采集器都先有接口。

```json
{
  "name": "demo.stock_snapshot.latest",
  "interface_name": "stock_snapshot_demo",
  "display_name_zh": "示例快照采集",
  "resource_group": "demo.http",
  "mode": "snapshot",
  "default_options": {
    "formats": ["parquet"],
    "timeout_seconds": 10
  },
  "default_limits": {
    "max_active_jobs": 1,
    "max_connections_total": 4,
    "request_interval_ms": 200
  },
  "output": {
    "layer": "snapshot",
    "default_dir_name": "stock_snapshot_demo",
    "write_mode": "snapshot",
    "primary_key": ["instrument_id"],
    "date_field": "trade_date"
  }
}
```

资源组建议使用 `{source_code}.{resource_type}`，例如 `demo.http`、`tdx.quote`、`tdx.f10`。共享同一个上游配额的接口应使用同一个资源组，让 Collector Runner 能做全局排队和限流。

写入策略应与 [data-layers.md](data-layers.md) 对齐。常见模式包括 `snapshot`、`append`、`overwrite_partition`、`replace_range` 和 `upsert_by_key`。声明 `upsert_by_key` 时必须同时声明 `primary_key`；声明 `replace_range` 时必须声明 `date_field`。

## 9. CollectorSpec

CollectorSpec 描述一个可运行采集器。新模型中，采集器和数据源 Provider 是平级插件能力：采集器有自己的 `collector_id`、`collector_plugin_id`、`dataset_id` 和 `runner_entry`，可以自带取数逻辑，不要求存在对应 Provider、`interface_name` 或 `downloader_profile`。插件只声明采集能力，实际排队、状态、日志、失败退避、资源组限制、质量检查和写入由 AxData Collector Runner 执行。

```json
{
  "collector_id": "demo.stock_snapshot.snapshot",
  "display_name_zh": "示例股票快照采集",
  "description": "按小样本参数采集示例股票快照并写出 Parquet。",
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
  }
}
```

独立 CollectorSpec 的推荐字段：

| 字段 | 说明 |
| --- | --- |
| `collector_id` / `name` | 采集器系统 ID，独立于 interface_name 和 dataset_id。 |
| `display_name_zh` | 中文展示名，可与接口中文名相同。 |
| `collector_plugin_id` | 贡献该采集器的插件 ID。 |
| `dataset_id` | 采集结果进入的数据集 ID。 |
| `asset_class` / `category` | 资产类别和业务分类。 |
| `default_params` / `config_schema` | 默认参数与用户可配置项。 |
| `default_schedule` | 默认调度建议，用户可覆盖。 |
| `output` / `quality` | 输出层、路径、写入策略和质量契约。 |
| `runner_entry` | Collector Runner 调用的 Python 入口。 |
| `resource_group` | 全局资源组，用于排队和限流。 |
| `lifecycle_status` | experimental、stable、deprecated 等生命周期状态。 |

`interfaces`、`required_interfaces` 和 `downloader_profile` 是旧 Provider-manifest 兼容字段。旧插件可以继续声明它们，AxData 会作为 legacy collector 导入；新插件不要依赖它们运行。

Collector 插件不要自己长期运行后台线程，不要绕过 AxData 队列直接开并发，不要自己维护一套与 AxData 无关的任务状态。禁用或卸载插件后，插件贡献的 CollectorSpec 会从可用能力中消失；用户已经创建的 Task 和 Run History 保留，依赖状态会变为 disabled、missing 或 uninstalled。

collector-only 插件可以只声明 CollectorSpec 并自带 runner。例如一个本地研究团队可以写“每日收盘后刷新核心表”的插件，它不提供新数据源，也不伪造 Provider；runner 可以直接请求上游、读取本地文件或复用公共库，但不能通过 `/v1/request`、SDK `call` 或 ProviderRegistry route 把接口临时调用伪装成采集。

## 10. Task Template

Task Template 是给用户一键创建 CollectorTask 的产品化入口。当前仓库内置的模板在 `axdata_core.collector_templates.TaskTemplate` 中，字段包括 `template_id`、`collector_name`、`interface_name`、默认参数、输出层、写入策略、依赖插件、安全限制和下一步动作。

插件开发时应把以下信息放进 CollectorSpec、DownloaderProfile 和 manifest：

- 安全默认参数，不要默认全市场重采。
- 推荐 `trigger_type` 或 `default_schedule`。
- `resource_group` 和默认限流。
- `write_mode`、`partition_by`、`primary_key`、`date_field`。
- `required_plugin` 或 required interfaces。
- 当依赖缺失时的可读说明。

把插件能力接入 Web/CLI 模板时，应沿用这些信息。模板只是创建本地任务的默认值，不代表安装插件后会自动联网采集。

## 11. 依赖和配置

插件依赖应同时写在 `pyproject.toml` 和 manifest 的 `dependencies` 中。AxData 默认离线处理依赖；`.axp` 可以携带 dependency wheels。只有用户显式传入 `--allow-online-deps` 或 API 的 `allow_online_deps=true` 时，才允许 pip 使用当前环境配置的索引联网安装。

```json
{
  "name": "beautifulsoup4",
  "version_spec": ">=4.12",
  "optional": false,
  "source": "pypi",
  "wheel": "wheels/beautifulsoup4-4.12.3-py3-none-any.whl",
  "description": "解析网页公告。"
}
```

第三方源 token 不由 AxData core 托管、注入或代理。需要 token 时，插件自行从环境变量或自己的配置文件读取，并在 manifest 中声明展示提示：

```json
{
  "name": "DEMO_TOKEN",
  "kind": "env",
  "required": true,
  "description": "示例源 token，由插件自行读取。"
}
```

不要把 token 写进样例、日志、manifest 或测试快照。

## 12. 打包和安装

开发期 editable 安装：

```powershell
.\.venv\Scripts\python -m pip install -e C:\path\to\axdata-source-demo
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin enable axdata.source.demo
```

普通 pip 安装：

```powershell
.\.venv\Scripts\python -m pip install axdata-source-demo
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin enable axdata.source.demo
```

AXP 是本地安装信封，通常包含：

```text
demo.axp
  manifest.json
  README.md
  LICENSE
  checksums.txt
  wheels/
    axdata_source_demo-0.1.0-py3-none-any.whl
    beautifulsoup4-4.12.3-py3-none-any.whl
  samples/
```

预览和安装：

```powershell
.\.venv\Scripts\axdata plugin axp-preview C:\path\to\demo.axp --json
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --json
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --enable --json
```

Web 插件页的“导出 AXP”导出的是插件安装包，不是数据导出。导出包只应包含 manifest、wheels、README 和 checksums，不包含本地 `data/`、metadata、任务历史、run history、logs、cache 或任何 token。安装后仍由 manifest 判断它提供 Provider、Collector 还是组合能力。

AXP checksum 只用于文件完整性和打包一致性检查，不证明作者身份，不证明代码安全，也不授予特殊权限。

## 13. 启用、禁用和卸载

对社区或第三方插件，安装不等于启用。插件只有启用后才进入接口路由、Downloader/Collector 能力和 task template 可用性判断；`axdata` 默认能力可安装后默认启用，但仍允许用户禁用。

```powershell
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin info axdata.source.demo --json
.\.venv\Scripts\axdata plugin enable axdata.source.demo
.\.venv\Scripts\axdata plugin disable axdata.source.demo
.\.venv\Scripts\axdata plugin uninstall axdata.source.demo --json
```

生命周期规则：

- 预装插件可启用、禁用、逻辑卸载和重新启用；逻辑卸载只隐藏当前 runtime 的能力，不物理删除随包代码。
- AXP 管理插件可以由 AxData 物理卸载。
- pip 或 editable/development 安装的外部插件由 Python 环境管理；AxData 会提示使用 `pip uninstall` 或移除开发路径。
- 卸载任何插件都不会删除 `data/`、已采集 Parquet、metadata、用户 Task 或 Run History。

## 14. 调试和诊断

常用命令：

```powershell
.\.venv\Scripts\axdata doctor --json
.\.venv\Scripts\axdata status --json
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin info axdata.source.demo --json
.\.venv\Scripts\axdata request stock_snapshot_demo --param code=000001.SZ --json
.\.venv\Scripts\axdata plugin collectors --json
.\.venv\Scripts\axdata collector task list --json
.\.venv\Scripts\axdata collector task templates --json
.\.venv\Scripts\axdata collector run list --json
```

HTTP/API 排查：

```powershell
curl http://127.0.0.1:8666/v1/plugins/providers
curl http://127.0.0.1:8666/v1/request/interfaces
curl http://127.0.0.1:8666/v1/plugins/collectors
curl http://127.0.0.1:8666/v1/collector/tasks/templates
```

如果 entry point 可见但缺少 `axdata-plugin.json` / `axdata-provider.json`，它会作为 ignored candidate 进入 `doctor/status` 诊断，例如 `plugins.ignored_candidates` 和 `registry.ignored_candidate_count`。它不会出现在普通 `plugin list`、`/v1/plugins/providers` 或 Web 普通插件列表里，也不会计入有效插件统计。常见修复：

- 确认 wheel 的 package data 包含 manifest。
- editable 安装时确认 `direct_url.json`、`top_level.txt` 和源码目录能定位到 manifest。
- 确认 entry point 指向的 distribution 和 manifest 属于同一个包。
- 确认没有复用已有 `provider_id`。

接口冲突时，`plugin list --json` 和 Provider 状态会显示 conflict。不要通过改用户本地配置偷偷覆盖别人接口；更稳的做法是改名、禁用冲突插件，或在用户明确知道的情况下设置 override。

## 15. 测试清单

至少覆盖：

- manifest 能解析，且包含 `axdata-provider.json` 或 `axdata-plugin.json`。
- wheel 包含 manifest、entry point、README/LICENSE 和需要的样例资源。
- `provider_id` 和 `interface_name` 合法且不重复。
- Provider 的 `interfaces()`、`downloader_profiles()`、`collectors()` 与 manifest 一致。
- 插件 discovery 不 import Provider runtime。
- 真正调用接口时才 import Adapter。
- 参数校验、字段裁剪、错误映射和空结果处理。
- DownloaderProfile 引用的接口存在。
- 独立 CollectorSpec 包含 `collector_id`、`collector_plugin_id`、`dataset_id`、`runner_entry`、`output` 和 `quality` 等新字段。
- legacy Provider manifest CollectorSpec 引用的接口和 DownloaderProfile 存在。
- source_request-only 接口不误标为 CollectorSpec 或默认采集器。
- 缺 token、缺依赖、网络超时、上游限流能给出可读错误。
- 禁用插件后接口不可调用，采集任务依赖状态变为 disabled。
- 不同 `provider_id` 的同名接口进入 conflict，不静默覆盖。

默认测试不应请求真实网络。真实源 smoke 必须显式 opt-in，并写入临时目录或用户指定输出目录。

## 16. 本地风险边界

AxData 插件就是本地 Python 代码。启用插件意味着允许该插件在当前 Python 环境里运行。Manifest 中的作者、信任等级、是否联网、依赖说明都只是声明或展示信息，不是沙箱保证。

当前产品边界：

- 不做插件市场。
- 不做中心审核。
- 不做签名信任体系。
- 不做沙箱。
- 不自动联网安装依赖。
- 不保存、注入或代理第三方源 token。

插件作者应该清楚写明数据来源、使用限制、依赖、网络行为、默认并发和失败边界。用户应该只安装自己信任来源的插件，并在需要隔离依赖时使用单独 Python 环境。
