# AxData 插件能力协议

本文说明 AxData 插件的能力声明、Manifest 字段、Registry 发现规则和运行边界。开发新插件时建议先读实践手册 [plugin-development.md](plugin-development.md)，再回到本文核对字段级协议。

AxData 的定位是本地优先、开源可扩展的量化数据基座。插件是本地安装、本地运行、本地承担风险的 Python 扩展包；AxData 不做中心化插件市场、不做插件审核、不做签名信任体系。核心不应被任何单一上游数据源绑定；插件通过能力声明接入，核心提供统一接口目录、参数校验、字段归一、存储、查询、采集、调度、安装管理和状态展示。没有 `axdata-plugin.json` 或 `axdata-provider.json` manifest 的 Python 包不算 AxData 插件；entry point 只是候选入口，缺 manifest 或重复 `provider_id` 的候选只进入诊断，不进入普通插件列表或有效插件统计。

## 1. 包边界

推荐包边界如下：

| 包 | 职责 | 是否绑定具体源 |
| --- | --- | --- |
| `axdata-core` | 插件能力协议、Registry、Manifest schema、AXP 管理、归一化工具、存储、查询、通用 Collector/Downloader 框架 | 否 |
| `axdata` | 面向普通用户的主包，可随包提供预装源插件，可直接 `pip install axdata` 使用 | 通过预装插件提供基础源 |
| `axdata-source-tdx` | TDX 数据源插件，拥有 TDX 普通行情、F10、服务器列表、缓存和采集 profile | 是 |
| `axdata-source-xxx` | 社区或第三方数据源插件，可提供 Provider、Collector、DownloaderProfile 或工具能力 | 可以绑定具体源 |
| `axdata-server` | HTTP API、Web、采集调度、插件管理、远程访问 | 否，依赖 Registry |

`axdata-core` 必须保持中立。所有数据源能力都来自预装插件或外部插件；Core 只提供数据库、插件协议、注册表、任务平台、存储、查询、API、Web 和 CLI。TDX 能力来自可安装、默认可用、可禁用、可从当前管理状态移除的 TDX 插件；插件不可用时 core 只提示用户安装或检查插件状态。

## 1.1 能力模型

插件不再等同于“一个数据源”。一个插件可以提供一种或多种能力：

| 能力 | 说明 |
| --- | --- |
| `providers` | 数据源接口能力，声明接口、参数、字段、样例，并通过 Adapter 做源端临时调用 |
| `collectors` | 独立采集器声明，描述用户可安装、启用、调度的本地资产生产任务 |
| `downloaders` | 兼容下载 profile，描述如何把接口拆请求、资源组、默认并发和输出建议 |
| `tools` | 可选的数据处理、清洗、指标或格式转换能力 |
| `dependencies` | Python 依赖和可选包内 wheels，用于安装前提示和离线安装 |
| `config_schema` | 配置提示，只用于 UI/CLI 展示，不托管第三方 secret |

允许的插件形态：

- 只有 Provider，例如腾讯行情源、巨潮公告源，只负责临时查询。
- Provider + legacy Collector，仅用于旧 Provider manifest 兼容；当前默认 catalog 已没有 TDX legacy collectors。
- 只有 Collector，例如用户写的每日收盘后采集任务，自带 runner 逻辑并写入 AxData 数据层。
- 工具型插件，例如数据清洗、指标生成、格式转换。

AxData 允许插件自由提供能力，但运行时规则由 core 统一托管：接口路由走 Source Provider Registry，采集能力走 Collector Registry，采集执行走 Collector Runner，写入走 Writer/Quality/Metadata，状态、日志、取消、失败退避和资源组限制由 AxData 统一记录和展示。新采集器不能通过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或旧 DownloaderProfile 链路套接口采集；它可以自带取数逻辑。

## 2. 兼容版本

插件系统有两个独立版本号：

| 字段 | 作用 | 示例 | Registry 行为 |
| --- | --- | --- | --- |
| `manifest_version` | Manifest JSON 文件格式版本 | `1.0` | 不支持则拒绝读取 |
| `plugin_api_version` | Provider Python 协议版本 | `1.0` | 不兼容则标记 `incompatible` |

二者不能混用。`manifest_version` 只管元信息文件怎么解析，`plugin_api_version` 只管 Provider、Adapter、Collector、DownloaderProfile、RequestPlanner 等插件能力代码契约。

兼容规则：

- 同一 major 内，只能向后兼容新增字段。
- 删除字段、字段改名、字段语义变化、调用签名变化，都必须升 major。
- Registry 必须同时检查 `manifest_version` 和 `plugin_api_version`。
- 不兼容插件不得被调用，但不得拖垮其他插件。

## 3. Plugin 与 Provider 协议

多能力插件包应只暴露一个插件对象。该对象可以提供 Provider、Collector、DownloaderProfile、Tool 或这些能力的组合。推荐 entry point group 为 `axdata.plugins`：

```toml
[project.entry-points."axdata.plugins"]
tdx = "axdata_source_tdx:plugin"
```

已经存在的 Provider 包仍可继续使用兼容入口 `axdata.providers`：

```toml
[project.entry-points."axdata.providers"]
tdx = "axdata_source_tdx:provider"
```

Registry 实现应同时识别 `axdata.plugins` 和 `axdata.providers`。旧 Provider 对象可视为只提供 Provider 能力的插件；只有 Collector 或工具能力的新插件不应被迫伪造 Provider。

插件对象协议：

```python
class AxDataPlugin:
    plugin_id: str
    version: str
    plugin_api_version: str

    def provider(self) -> SourceProvider | None: ...
    def collectors(self) -> Sequence[CollectorSpec]: ...
    def downloader_profiles(self) -> Sequence[DownloaderProfile]: ...
    def tools(self) -> Sequence[ToolSpec]: ...
    def dependencies(self) -> Sequence[DependencySpec]: ...
    def required_config(self) -> Sequence[RequiredConfig]: ...  # compatibility projection
```

当前 Provider 协议继续兼容：

```python
class SourceProvider:
    provider_id: str
    source_code: str
    source_name_zh: str
    version: str
    plugin_api_version: str

    def interfaces(self) -> Sequence[InterfaceSpec]: ...
    def create_adapter(self, options: Mapping[str, object] | None = None) -> SourceAdapter: ...
    def downloader_profiles(self) -> Sequence[DownloaderProfile]: ...
    def required_config(self) -> Sequence[RequiredConfig]: ...  # optional
```

标识符分工：

| 标识符 | 是否全局唯一 | 用途 | 示例 |
| --- | --- | --- | --- |
| `provider_id` | 是 | 数据源插件身份、启停、卸载、冲突归属、日志归属 | `axdata.source.tdx` |
| `source_code` | 否，可共享 | 数据源命名空间、目录分组、接口名前缀建议 | `tdx` |
| `interface_name` | 是 | 用户调用、HTTP 路由、Registry 精确分发 | `stock_codes_tdx` |
| `collector_plugin_id` | 是 | 采集器插件身份、启停、卸载和冲突归属 | `axdata.collector.tdx_daily` |
| `collector_id` | 是 | 采集器系统 ID，供任务模板和调度引用 | `tdx.stock_codes.snapshot` |
| `dataset_id` | 是 | 采集结果数据集 ID，供 Data Browser 和查询目录引用 | `tdx.stock_codes` |

`provider_id` 不等于 `source_code`。`interface_name`、`collector_id` 和 `dataset_id` 也不能混用。它们可以显示同一个中文名，但系统 ID 必须分命名空间。

`required_config()` 是可选声明方法。未实现时等价于返回空列表；实现时只用于生成 manifest 和 UI/CLI 展示配置提示，不代表 AxData 会保存、注入或代理第三方源凭据。

`declared_trust_level`、`homepage`、`license` 和 `description` 也是可选展示属性。`declared_trust_level` 即使由 Provider 代码声明，也仍然只是作者自报，Registry 冲突裁决只能使用 `effective_trust_level`。

## 4. Adapter 契约

Adapter 负责源端直取，不负责把数据写入 AxData 数据层。源端直取遵守 `docs/architecture.md` 和 `docs/data-layers.md` 的边界：默认不写入 `raw`、`staging`、`core` 或 `factor`。

建议接口：

```python
class SourceAdapter:
    def call(
        self,
        interface_name: str,
        params: Mapping[str, object] | None = None,
        fields: Sequence[str] | None = None,
        options: Mapping[str, object] | None = None,
    ) -> SourceResult: ...
```

`SourceResult` 至少包含：

| 字段 | 说明 |
| --- | --- |
| `data` | 已转换为 AxData 字段的记录列表 |
| `schema` | 返回字段 schema |
| `meta` | 源、接口、耗时、分页、数据日期等元信息 |

Adapter 可以使用上游原始字段，但对外返回必须是 AxData 字段。源端特色字段只有在接口规范明确声明时才能暴露。

## 5. Manifest As Build Artifact

Manifest 是 Registry 免 import 读取的唯一元信息产物，但不是人工手写的真相源。

标准流程：

1. Provider 代码声明接口、参数、字段、样例、下载 profile。
2. `axdata plugin build` import Provider，并从 Provider 生成 `axdata-provider.json`。
3. 同一份 manifest 打进 wheel 作为 package/distribution data。
4. Registry 发现 entry point 后，先读取 distribution 内的 manifest，不 import Provider 模块。
5. Registry 用 manifest 做目录展示、版本门禁、信任提示和冲突检查。
6. 只有当某个接口真的被调用，Registry 才 import Provider 并创建 Adapter。
7. `axdata plugin check` 必须校验 manifest 与当前 Provider 代码一致。

Manifest 不允许成为第三个手写真相源。CI 和发布流程应要求 `axdata plugin check` 通过。

## 6. Manifest JSON 结构

当前 Provider manifest 文件名为 `axdata-provider.json`。多能力插件可以使用更通用的 `axdata-plugin.json`；无论文件名如何，manifest 的真相源都是插件代码生成出的能力声明，而不是手写副本。JSON 顶层字段：

```json
{
  "manifest_version": "1.0",
  "plugin_api_version": "1.0",
  "plugin": {
    "plugin_id": "axdata.plugin.tencent",
    "name_zh": "腾讯财经插件",
    "version": "0.1.0",
    "description": "腾讯财经公开行情接口插件"
  },
  "provider": {
    "provider_id": "axdata.source.tencent",
    "source_code": "tencent",
    "source_name_zh": "腾讯财经",
    "version": "0.1.0",
    "declared_trust_level": "community",
    "homepage": "https://example.com",
    "license": "Apache-2.0",
    "description": "腾讯财经公开行情接口 Provider"
  },
  "interfaces": [],
  "collectors": [],
  "downloaders": [],
  "dependencies": [],
  "config_schema": {
    "required_config": []
  },
  "required_config": [],
  "resources": {
    "samples": []
  },
  "build": {
    "generated_at": "2026-06-22T12:00:00Z",
    "axdata_plugin_api_version": "1.0",
    "manifest_hash": "sha256:..."
  }
}
```

### 6.1 PluginManifest

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `manifest_version` | string | 是 | Manifest JSON 格式版本 |
| `plugin_api_version` | string | 是 | 插件能力协议版本 |
| `plugin` | object | 否 | 插件元信息；当前 Provider manifest 可暂时省略 |
| `provider` | object | 条件必填 | Provider 元信息；插件提供 Provider/interfaces 时必填，只有 Collector/Tool 的插件可省略 |
| `interfaces` | array | 是 | 接口规格列表；没有 Provider 能力时为空数组 |
| `collectors` | array | 否 | 采集任务声明；可由只有采集器的插件提供 |
| `downloaders` | array | 是 | 兼容下载 profile；用于显式下载和 legacy collectors，不是采集器身份 |
| `dependencies` | array | 否 | Python 依赖声明和包内 wheel 索引，用于安装前提示 |
| `config_schema` | object | 否 | 配置提示 schema，不托管第三方 secret |
| `required_config` | array | 是 | 只用于展示的配置提示 |
| `resources` | object | 否 | 样例、文档等资源索引 |
| `build` | object | 否 | 构建信息 |

未知字段处理：

- 同一 major 内新增未知字段，Registry 可以忽略。
- 必填字段缺失必须标记插件 `failed`.
- 字段类型错误必须标记插件 `failed`.

### 6.2 ProviderInfo

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_id` | string | 是 | 插件唯一身份 |
| `source_code` | string | 是 | 数据源命名空间 |
| `source_name_zh` | string | 是 | 中文数据源名 |
| `version` | string | 是 | Provider 包版本 |
| `declared_trust_level` | string | 是 | 作者自报信任等级，只能用于展示 |
| `homepage` | string | 否 | 项目主页 |
| `license` | string | 否 | 插件许可证 |
| `description` | string | 否 | 简介 |

`declared_trust_level` 保留为兼容展示字段，不作为安全保证。可取值：

- `official`
- `community`
- `unknown`

Registry 不得直接用 `declared_trust_level` 做安全裁决。AxData 不做签名验签系统，也不因为插件自报 `official` 就授予内置权限。

### 6.3 InterfaceSpec

```json
{
  "name": "stock_codes_tdx",
  "display_name_zh": "最新股票列表",
  "source_code": "tdx",
  "source_name_zh": "通达信",
  "category": "股票数据/基础数据",
  "menu_path": ["通达信", "股票数据", "基础数据"],
  "asset_class": "stock",
  "request_mode": "source_request",
  "collection": {
    "supported": true,
    "default_profile": "tdx.stock_codes.latest"
  },
  "parameters": [],
  "fields": [],
  "examples": [],
  "reference_sections": [],
  "summary_zh": "按范围获取最新股票列表。",
  "description_zh": "用于接口页面的中文说明；参数和字段仍以 parameters/fields 为准。",
  "params_note_zh": "不传参数时返回默认范围。",
  "params_example_zh": "client.call(\"stock_codes_tdx\")",
  "limits": {
    "default_limit": 5000,
    "max_limit": 100000
  },
  "notes": "源端直取默认不入库。"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 全局唯一接口名 |
| `display_name_zh` | string | 是 | 中文展示名 |
| `source_code` | string | 是 | 所属数据源命名空间 |
| `source_name_zh` | string | 是 | 中文数据源名 |
| `category` | string | 否 | 展示分类 |
| `menu_path` | array[string] | 否 | 插件声明的完整 Web 菜单路径；Web 只渲染该路径，不为具体数据源补接口树 |
| `asset_class` | string | 是 | 标准资产类型 |
| `request_mode` | string | 是 | `source_request`、`query`、`stream`、`collect` |
| `collection` | object | 否 | 兼容下载提示；可指向 DownloaderProfile，但不等于 CollectorSpec |
| `parameters` | array | 是 | 参数规格 |
| `fields` | array | 是 | 字段规格 |
| `examples` | array | 是 | 真实或可稳定复现的请求样例 |
| `reference_sections` | array | 否 | 接口页静态参考表，例如类别码、枚举映射、字段口径对照；由插件提供，Web 通用渲染 |
| `summary_zh` | string | 否 | Web 接口页顶部中文短摘要；由插件或内置 Provider 提供 |
| `description_zh` | string | 否 | Web 接口页中文正文说明；存在时优先于 `notes` 展示 |
| `params_note_zh` | string | 否 | Web 参数区中文补充说明 |
| `params_example_zh` | string | 否 | Web 参数区静态 SDK 调用示例；不触发源端请求 |
| `limits` | object | 否 | 限制说明 |
| `notes` | string | 否 | 额外说明 |

`asset_class` 标准枚举：

- `stock`
- `index`
- `etf`
- `fund`
- `bond`
- `future`
- `option`
- `fx`
- `macro`

如需新增资产类型，必须先扩展核心规范，再让插件使用。不能由单个插件私自发明新枚举。

### 6.4 ParameterSpec

```json
{
  "name": "code",
  "display_name_zh": "证券代码",
  "type": "string",
  "required": false,
  "multiple": true,
  "default": null,
  "control": "text",
  "placeholder": "000001.SZ",
  "description": "不填表示全量。"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 参数名 |
| `display_name_zh` | string | 是 | 中文名 |
| `type` | string | 是 | `string`、`integer`、`number`、`boolean`、`date`、`datetime`、`enum`、`array`、`object` |
| `required` | boolean | 是 | 是否必填 |
| `multiple` | boolean | 否 | 是否支持多值 |
| `default` | any | 否 | 默认值 |
| `enum` | array | 否 | 枚举候选 |
| `control` | string | 否 | Web 控件建议 |
| `placeholder` | string | 否 | 输入提示 |
| `description` | string | 否 | 说明 |

日期参数应使用 `YYYYMMDD`。HTTP 层可以兼容 `YYYY-MM-DD`，但 Provider 规范里统一写 `YYYYMMDD`。

### 6.5 FieldSpec

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

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | AxData 字段名 |
| `display_name_zh` | string | 是 | 中文名 |
| `type` | string | 是 | `string`、`integer`、`number`、`boolean`、`date`、`datetime` |
| `required` | boolean | 是 | 是否理论必填 |
| `unit` | string/null | 否 | 单位 |
| `description` | string | 否 | 说明 |

字段名必须使用 snake_case。不得暴露上游难懂原始列名，除非接口就是调试接口且文档明确说明。

### 6.6 RequestExample

```json
{
  "title": "按代码查询",
  "request": {
    "interface_name": "stock_codes_tdx",
    "params": {"code": ["000001.SZ", "600000.SH"]},
    "fields": ["instrument_id", "name"]
  },
  "response": {
    "data": [
      {"instrument_id": "000001.SZ", "name": "平安银行"}
    ],
    "schema": [
      {"name": "instrument_id", "type": "string"},
      {"name": "name", "type": "string"}
    ],
    "meta": {"count": 1}
  }
}
```

样例要求：

- 示例必须能反映真实字段和真实参数。
- 可以脱敏，但不能编造不存在的字段。
- 大结果只放 1 到 5 行。
- 如果源端实时波动，样例要标注采集或请求日期。

### 6.7 DownloaderProfile

```json
{
  "name": "tdx.stock_suspensions.latest",
  "interface_name": "stock_suspensions_tdx",
  "display_name_zh": "最新停牌列表采集",
  "resource_group": "tdx.quote",
  "mode": "snapshot",
  "default_options": {
    "formats": ["parquet"],
    "server_count": 4,
    "connections_per_server": 2,
    "batch_size": 80
  },
  "default_limits": {
    "max_active_jobs": 1,
    "max_connections_total": 8,
    "request_interval_ms": 0
  },
  "output": {
    "default_dir_name": "stock_suspensions_tdx",
    "file_name_template": "{interface_name}_{data_date}_{run_time}"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 下载 profile 唯一名 |
| `interface_name` | string | 是 | 对应接口 |
| `display_name_zh` | string | 是 | 中文名 |
| `resource_group` | string | 是 | 资源组，用于全局调度 |
| `mode` | string | 是 | `snapshot`、`incremental`、`history`、`stream_recording` |
| `default_options` | object | 是 | 单任务默认执行参数 |
| `default_limits` | object | 是 | Provider 建议限流，最终由核心调度器裁决 |
| `output` | object | 否 | 文件输出建议 |

`resource_group` 是插件声明，不是 core 写死常量。例如 TDX Provider 可以声明 `tdx.quote`、`tdx.f10`、`tdx.ext`；其他 Provider 可以声明自己的资源组。核心调度器只按声明动态建池。

`default_limits` 是建议值，不是插件的权力边界。管理员配置可以覆盖。DownloaderProfile 只描述一个接口如何被显式下载或被 legacy collector 复用；新采集器应通过 CollectorSpec 的 `runner_entry` 进入 CollectorRegistry。

### 6.8 CollectorSpec

CollectorSpec 描述插件提供的采集任务入口。新模型中，采集器插件和数据源 Provider 插件平级：采集器不要求存在对应 Provider，不要求存在 `interface_name`，也不要求存在 `downloader_profile`。当前 Provider manifest 中的 collectors 是 legacy 兼容路径，可继续读取，但不得作为新插件推荐形态。

```json
{
  "collector_id": "tdx.daily.close_refresh",
  "display_name_zh": "TDX 收盘后日线刷新",
  "description": "收盘后按股票池采集最新日线并写入 AxData 数据层。",
  "collector_plugin_id": "axdata.collector.tdx_daily",
  "dataset_id": "tdx.daily",
  "asset_class": "stock",
  "category": "daily",
  "resource_group": "tdx.quote",
  "runner_entry": "axdata_collector_tdx_daily.runner:run",
  "default_schedule": {
    "kind": "manual_or_cron",
    "cron": "0 18 * * 1-5"
  },
  "default_params": {
    "adjust": "none"
  },
  "output": {
    "layer": "raw",
    "formats": ["parquet"]
  },
  "quality": {
    "required_columns": ["ts_code", "trade_date"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `collector_id` / `name` | string | 是 | 采集器唯一名；`name` 为旧字段别名 |
| `display_name_zh` | string | 是 | 中文名 |
| `description` | string | 否 | 说明 |
| `collector_plugin_id` | string | 是 | 贡献该采集器的插件 ID |
| `dataset_id` | string | 是 | 输出数据集 ID |
| `asset_class` | string | 否 | 资产类别 |
| `category` | string | 否 | 业务分类 |
| `resource_group` | string | 是 | 默认资源组 |
| `runner_entry` | string | 是 | Collector Runner 调用的 Python 入口 |
| `default_schedule` | object | 否 | 默认调度建议，用户可覆盖 |
| `default_params` | object | 是 | 默认采集参数 |
| `config_schema` | object | 否 | 参数和本地配置 schema |
| `output` | object | 否 | 输出层、格式和路径建议 |
| `quality` | object | 否 | 质量检查契约 |
| `lifecycle_status` | string | 否 | `experimental`、`stable`、`deprecated` 等 |
| `interfaces` | array[string] | 否 | deprecated；旧 Provider manifest 兼容字段 |
| `downloader_profile` | string | 否 | deprecated；旧 Provider manifest 兼容字段 |
| `required_interfaces` | array[string] | 否 | deprecated；旧 Provider manifest 兼容字段 |

CollectorSpec 只是声明，不代表插件可以绕过 AxData 统一调度。采集器运行必须进入 AxData Collector Runner，由 core 负责队列、状态、日志、取消、失败退避、资源组限制、写入锁和 metadata 记录。新 runner 路径禁止通过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或旧 DownloaderProfile -> Adapter 的接口采集链路。

### 6.9 DependencySpec

AxData 插件是本地 Python 代码包，依赖风险由用户和插件作者承担。AxData 的职责是安装前检查和提示，不做复杂自动解冲突。

```json
{
  "name": "beautifulsoup4",
  "version_spec": ">=4.12",
  "optional": false,
  "source": "pypi",
  "wheel": "wheels/beautifulsoup4-4.12.3-py3-none-any.whl",
  "description": "解析公告 HTML。"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | Python distribution 名 |
| `version_spec` | string | 否 | PEP 440 版本约束 |
| `optional` | boolean | 是 | 是否可选依赖 |
| `source` | string | 否 | `bundled`、`pypi`、`system` 或说明文本 |
| `wheel` | string | 否 | `.axp` 内置 wheel 路径 |
| `description` | string | 否 | 依赖用途 |

依赖策略：

- 默认不联网安装依赖。
- `.axp` 可以自带依赖 wheels，AxData 可离线安装这些 wheels。
- 如果缺依赖或版本不满足，安装前必须提示。
- 如果发现明显版本冲突，安装前必须提示或拒绝，具体策略由用户确认。
- 只有用户显式开启在线依赖安装时，才允许联网执行 pip 依赖解析。
- AxData 不承诺自动解决复杂依赖冲突；冲突应由插件作者或用户在插件层面适配。

### 6.10 ConfigSchema 与 RequiredConfig

`config_schema` 用来表达插件希望用户自行配置的环境变量、配置文件键或其它本地配置提示。已有的 `required_config` 保留为兼容投影；可以把 `config_schema.required_config` 与顶层 `required_config` 映射为同一组 `RequiredConfig`。新插件优先写 `config_schema`，旧 Provider manifest 继续兼容顶层 `required_config`。

```json
{
  "name": "TUSHARE_TOKEN",
  "kind": "env",
  "required": true,
  "description": "用户自己的 Tushare token。AxData 不保存、不注入、不代理。"
}
```

`required_config` 只用于展示和检查提示。AxData 不托管、不注入、不代理、不保存第三方源凭据。插件如需上游 token，应自行从环境变量、配置文件或它自己的机制读取。

## 7. Serialization Rules

以下 dataclass 或等价模型必须有稳定的 JSON 序列化和反序列化规则：

- `ProviderManifest`
- `ProviderInfo`
- `InterfaceSpec`
- `ParameterSpec`
- `FieldSpec`
- `RequestExample`
- `DownloaderProfile`
- `CollectorSpec`
- `CollectorManifest` / collector plugin manifest
- `RequiredConfig`

规则：

- JSON key 使用 snake_case。
- 输出字段顺序稳定，便于 diff。
- `None` 值默认输出为 `null`，除非字段明确允许省略。
- 时间使用 ISO 8601 UTC 字符串，例如 `2026-06-22T12:00:00Z`。
- 日期使用 `YYYYMMDD`。
- 枚举值使用小写英文或明确约定的大写代码，例如 `SSE`。
- 反序列化时未知字段在同 major 内可忽略，但必须保留 warning。
- 必填字段缺失或类型错误必须失败。

`axdata plugin check` 至少检查：

- manifest 可被当前 Registry 解析。
- Provider 代码生成的新 manifest 与 wheel 内 manifest 一致。
- `provider_id`、`source_code`、`interface_name` 格式合法。
- `interface_name` 在本 Provider 内无重复。
- 所有字段、参数和样例满足 schema。
- `asset_class` 属于标准枚举。
- DownloaderProfile 引用的接口存在。
- 独立 CollectorSpec 包含 `collector_id`、`collector_plugin_id`、`dataset_id`、`runner_entry`、`output` 和 `quality` 等字段。
- legacy Provider manifest CollectorSpec 引用的接口和 DownloaderProfile 存在。

## 8. Registry Discovery

Registry 发现流程：

1. 使用 `importlib.metadata.entry_points(group="axdata.plugins")` 找到多能力候选插件，同时兼容读取 `axdata.providers` 中的旧 Provider 候选。
2. 对每个 entry point 找到所属 distribution。
3. 从 distribution 文件中读取 `axdata-plugin.json` 或兼容读取 `axdata-provider.json`。
4. 不 import Provider 模块，先解析 manifest。
5. 检查 `manifest_version`。
6. 检查 `plugin_api_version`。
7. 计算 `effective_trust_level`。
8. 读取 AxData 启用配置。
9. 将 Provider 能力合并到 Source Provider Registry，建立 `interface_name -> provider_id` 精确路由表。
10. 将 Collector 能力合并到 Collector Registry，建立 `collector_id -> collector_plugin_id` catalog；旧 Provider manifest collectors 以 `legacy_source=provider_manifest` 导入。

旧 `axdata.providers` 候选只提供 Provider 能力；`axdata.plugins` 候选可以没有 Provider，但如果提供 interfaces，则必须声明 provider 信息并满足 Provider 路由规则。

插件状态：

| 状态 | 含义 |
| --- | --- |
| `installed` | 已安装，但未启用 |
| `enabled` | 已启用，可参与 Registry |
| `disabled` | 已禁用，不参与路由 |
| `uninstalled` | 预装插件已从当前 AxData 管理状态移除；能力不参与目录、路由或任务模板，但随包代码未必物理删除 |
| `failed` | manifest 或加载失败 |
| `incompatible` | 版本不兼容 |
| `conflict` | 接口名冲突，需要用户处理 |

一个插件失败不得影响其他插件。Registry API 应返回失败原因，供 Web 和 CLI 展示。

`provider_id` 是 Provider 的唯一身份。Registry 不允许外部 Provider 使用已经注册的预装插件 `provider_id` 覆盖预装插件，也不允许两个外部插件用同一个 `provider_id` 静默互相覆盖。发生重复时，后注册的候选必须标记为 `failed` 并保留原 Provider 的状态和路由。

## 9. 本地信任与责任模型

AxData 插件是用户本地安装并运行的 Python 代码。AxData 不做中心化插件审核、不做插件市场、不做作者签名验签，也不把 manifest 里的作者声明包装成安全保证。用户从哪里拿插件、是否安装、是否启用，均由用户本地自行决定并承担风险。

Manifest 中的 `declared_trust_level` 是作者自报，只能用于展示。Registry 实际使用 `effective_trust_level`，但该字段只服务冲突裁决和 UI 提示，不代表沙箱或安全认证。

`effective_trust_level` 计算规则：

| 情况 | effective trust |
| --- | --- |
| AxData 随主包提供的预装能力 | `official` |
| 本地安装的外部插件 | `community` |
| 来源不明 | `community` |

如果外部插件自报 `official`，Registry 必须降级为 `community`，并可显示“声明为 official，未验证”。AxData 不提供签名升级通道。

Checksum 的作用只限于 `.axp` 文件完整性和打包一致性检查：

- 检查 wheel、manifest、README、LICENSE、samples 等文件是否与包内清单一致。
- 防止文件损坏、传输不完整或打包错误。
- 不证明插件作者身份。
- 不证明代码安全。
- 不授予内置权限。

启用插件即表示允许该插件的 Python 代码在当前环境运行。AxData 不应把 manifest 中“是否联网”“是否安全”“是否 official”等作者声明包装成安全保证。真正的运行授权来自用户自己的安装和启用决定。

## 10. Conflict Resolution

`interface_name` 必须全局唯一。冲突处理规则：

1. 先按 `effective_trust_level` 排序：`official` 高于 `community`。
2. 同级时，预装插件高于外部插件。
3. 用户显式 override 高于默认裁决。
4. 如果两个同级外部 Provider 撞名，且用户没有显式 override，双方都标记为 `conflict`，该接口不可用。
5. 不允许静默覆盖。
6. 不允许因为一个冲突导致整个 Registry 不可用。

示例：

| Provider A | Provider B | 结果 |
| --- | --- | --- |
| 预装插件 | community | 预装插件胜出，community 标记 conflict |
| community | community | 双方 conflict，等待用户处理 |
| community | community + 用户 override | override 指定方胜出 |

用户处理方式：

- 禁用其中一个插件。
- 修改社区插件接口名后重新发布。
- 在 AxData 配置里显式 override 某个 `interface_name` 的 provider。

## 11. Install And Enable

安装不等于启用。

| 动作 | 含义 |
| --- | --- |
| install | pip、Web、AXP 或随 AxData 提供代码包 |
| enable | AxData 配置允许该 Provider 参与 Registry |
| disable | Provider 保留安装，但不参与 Registry |
| uninstall | 外部插件删除代码包；预装插件从当前 AxData 管理状态移除并隐藏能力；都不删除用户数据 |

默认规则：

- AxData Core 不包含不可卸载数据源；真正不可卸载的是 Core 本身。
- `axdata` 随包提供的数据源称为预装插件，可以默认启用，也可以被用户禁用、卸载和重新启用。
- `axdata` 提供的默认能力可以安装后默认 enabled；用户仍可显式 disable。
- TDX 能力来自随项目提供的 TDX 插件；插件不可用时只提示安装或检查插件状态。
- 社区插件默认 disabled。
- Web 上传插件默认 disabled。
- 用户显式 enable 后才允许 Provider 被 import 和调用。

启用配置属于 AxData，不属于 pip。社区或第三方插件即使能被 pip entry point 发现，只要 AxData 配置未启用，Registry 就不得调用该 Provider；默认能力可由 AxData 明确列入默认 enabled 白名单。

卸载插件不删除 `data/`、`metadata/`、`logs/` 中用户已经采集的数据、运行记录或本地任务配置。插件贡献的 interfaces、downloaders、collectors 和 task templates 会随插件禁用或卸载从可用能力中消失；用户创建的 Task 保留，`dependency_status` 变为 `disabled`、`missing` 或 `uninstalled` 后不可运行；Run History 是历史事实，永远保留。重新安装或重新启用插件后，Task 可以恢复运行。

## 12. Routing Rules

最终路由必须是精确路由：

```text
interface_name -> Registry -> Provider -> Adapter
```

旧的 `interface_name.endswith("_tdx")` 或类似后缀兜底不应继续作为路由依据。处理时可以分两步：

1. Registry 精确路由和旧兜底并存，确认全部接口都能命中 Registry。
2. 单独删除旧兜底，并补测试防止回归。

不得让接口名后缀决定 Adapter，否则社区插件可能通过命名误入 TDX 路由。

## 13. 归一化契约

`axdata-core` 提供归一化工具，Provider 应优先使用这些工具，而不是各自实现一套。

标准资产类型：

```text
stock / index / etf / fund / bond / future / option / fx / macro
```

代码与日期：

| 类型 | 标准 |
| --- | --- |
| A 股股票 | `000001.SZ`、`600000.SH`、`430047.BJ` |
| 交易所筛选 | `SSE`、`SZSE`、`BSE` |
| 日期 | `YYYYMMDD` |
| 日期时间 | ISO 8601 或明确时区的字符串 |

字段规则：

- 字段名使用 snake_case。
- 金额、价格、成交量、股本单位必须在 FieldSpec 中写明。
- `pct_chg` 这类百分比字段应写明是 `1.23` 表示 1.23%，还是 `0.0123` 表示 1.23%。
- 空值用 `null`，不要混用空字符串、`--`、`N/A`。
- 错误响应使用 AxData 统一错误码，不泄露上游复杂错误对象。

进入 core/factor 的数据必须遵守 `docs/schema.md` 和 `docs/data-layers.md` 的分层规则。源端直取可以返回临时数据，但字段也应尽量使用同一归一化规范。

## 14. Collector Runner 与 Downloader Engine 契约

核心 Runner/Writer 必须中立。新采集器推荐流程：

```text
Collector Trigger -> CollectorRegistry -> runner_entry -> Records -> Writer -> Quality -> Metadata
```

职责分工：

| 组件 | 职责 |
| --- | --- |
| `CollectorRegistry` | 管理 collector specs、collector-only 插件、runner entry、dataset_id 和 legacy 导入 |
| `CollectorSpec` | 声明采集器 ID、插件 ID、输出数据集、资源组、默认参数、输出和质量契约 |
| `runner_entry` | 执行采集器自带取数逻辑并返回 records 或可写结果 |
| `Writer` | 按格式、路径和写入模式写文件 |
| `Quality` | 做质量检查和统计 |
| `Metadata` | 记录 run、stage、参数、输出文件、质量结果和可追溯信息 |

新 runner 路径禁止通过 `/v1/request`、SDK `call`、ProviderRegistry interface route 或旧 DownloaderProfile -> Adapter 的接口采集链路。采集器可以自带上游客户端、读取本地文件或复用公共库；无论数据从哪里来，写入和质量检查都必须回到 AxData Writer/Quality/Metadata。

当前 legacy 下载引擎流程。它服务显式下载和旧 Provider manifest collectors，不是新采集器主路径：

```text
Collector Trigger -> DownloaderProfile -> RequestPlanner -> Adapter -> Records -> Writer -> Quality -> Metadata
```

职责分工：

| 组件 | 职责 |
| --- | --- |
| `DownloaderProfile` | legacy 字段，声明一个接口如何被下载、默认参数、资源组、输出建议 |
| `RequestPlanner` | 把采集需求拆成源端请求计划 |
| `Adapter` | 执行源端请求 |

旧 Provider manifest collectors 可以继续通过 DownloaderProfile -> RequestPlanner -> Adapter 执行，作为过渡兼容。Collector 负责“什么时候跑、排队、状态和失败处理”；legacy Downloader 负责“怎么批量请求、并发、拿数据、写 Parquet 和质检”；Provider/Adapter 负责“怎么请求具体上游”。TDX 的多服务器、长连接、批大小、代码池、题材补漏、文件命名，都属于 TDX 插件的 Provider/Profile/Planner，不应写死在 core。

## 15. Resource Groups

Provider 可以通过 DownloaderProfile 声明 legacy 下载资源组；独立 CollectorSpec 也应直接声明资源组：

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

本规范只定义插件如何声明资源组。采集调度器本体放到 `docs/collector-scheduling.md` 单独设计。

调度原则：

- 接口级并发是单任务预算，不是全局实际并发。
- 多个定时任务同一时间触发时，应进入队列，而不是同时占满连接。
- 全局资源上限只在一个常驻 collector 服务进程内承诺。
- 多进程绕过 collector 直接运行时，不承诺全局连接预算，只能做文件写冲突保护。
- 手动任务可以插队，但仍受资源组限制。

## 16. 后端 Catalog 契约

长期前端目录不应以 TS 静态文件为真相源。接口目录由插件 manifest 的 `menu_path` 声明，经 Registry 返回给 Web；Web 只做通用渲染，不为通达信、巨潮、腾讯、新浪等具体数据源硬编码接口树。后端 catalog 应由 Registry 生成，并至少提供：

| 字段 | 说明 |
| --- | --- |
| `interface_name` | 接口名 |
| `display_name_zh` | 中文名 |
| `provider_id` | Provider 身份 |
| `source_code` | 数据源命名空间 |
| `source_name_zh` | 中文源名 |
| `asset_class` | 资产类型 |
| `menu_path` | 菜单路径 |
| `parameters` | 参数控件 |
| `fields` | 字段说明 |
| `examples` | 请求样例 |
| `reference_sections` | 静态参考表 |
| `collection` | 是否支持采集 |
| `declared_trust_level` | 作者声明信任等级 |
| `effective_trust_level` | Registry 计算信任等级 |
| `plugin_status` | enabled、disabled、failed、conflict、incompatible |
| `required_config` | 仅展示的配置提示 |

Web 应能展示 disabled、failed、conflict、incompatible 的原因。

## 17. CLI 命令

常用 CLI：

```bash
axdata plugin list
axdata plugin check
axdata plugin build
axdata plugin enable axdata.source.tencent
axdata plugin disable axdata.source.tencent
axdata plugin info axdata.source.tencent
```

命令行为：

| 命令 | 行为 |
| --- | --- |
| `plugin list` | 列出已发现 Provider、状态、版本、effective trust |
| `plugin info` | 展示 manifest、冲突、required_config |
| `plugin check` | 校验 Provider 代码、manifest、样例、profile |
| `plugin build` | 生成 manifest，并可构建 wheel |
| `plugin enable` | 写 AxData 启用配置 |
| `plugin disable` | 写 AxData 禁用配置 |

插件安装可以使用 pip、AXP 或 Web/CLI 提供的安装入口；具体可用命令以当前版本为准。

## 18. AXP 安装包

`.axp` 是 Web/CLI 友好的本地安装信封，不是核心插件格式。核心格式仍然是 Python wheel + entry point + embedded manifest。

AXP 也是分发和安装单位，不是能力类型。导出或安装 AXP 后，AxData 仍按 embedded manifest 中的 `provider`、`interfaces`、`collectors`、`downloaders` 等能力声明分流到 ProviderRegistry 和 CollectorRegistry；不能靠文件名判断它是数据源插件还是采集器插件。

建议结构：

```text
plugin.axp
  manifest.json
  README.md
  LICENSE
  wheels/
    axdata_source_xxx-0.1.0-py3-none-any.whl
  samples/
  checksums.txt
```

Web 安装现实边界：

- 安装 wheel 可能需要依赖解析。
- 依赖可能需要联网，但默认不得联网。
- 依赖可能与当前环境冲突。
- 安装后可能需要刷新 Registry 或重启服务。
- 上传安装默认 disabled，用户确认后才能 enable。

`.axp` 中 manifest 用于安装前预览，checksum 用于完整性和打包一致性检查。AxData 不做签名验签，也不做插件市场。依赖处理规则：

- 安装前预览 Python 依赖和包内 wheels。
- 默认离线安装。
- `.axp` 自带依赖 wheels 时可离线安装。
- 缺依赖或版本不满足时给出清晰提示。
- 明显冲突时提示或拒绝，由用户和插件作者处理。
- 只有用户显式开启 `--allow-online-deps` 或等价 API/UI 选项时，才允许联网安装依赖。

## 19. 当前支持能力

当前实现已经支持 ProviderRegistry、后端 catalog、精确路由、enable/disable、CLI/API/Web、外部腾讯/巨潮/TDX/TDX Ext 包、`.axp` 安装和安装管理。独立采集器体系也已进入主路径：

1. Manifest/Registry 已兼容 `collectors`、`dependencies`、`config_schema`，并保持现有 Provider manifest 兼容。
2. Collector 插件协议已支持独立 CollectorSpec / Collector manifest、collector-only plugin、`runner_entry`、`dataset_id` 和 legacy Provider manifest 导入。
3. CollectorRegistry 已成为 `/v1/plugins/collectors`、CLI `plugin collectors` 和 Web 采集页的采集器 catalog 事实源；ProviderRegistry 不再作为采集器事实源。
4. Collector Runner 已新增 `runner_entry` 路径，统一接入 Writer、Quality 和 Metadata；旧 DownloaderProfile -> RequestPlanner -> Adapter 只作为 legacy 下载引擎保留。
5. 默认 collector catalog 当前是 TDX 9 个 independent collectors；交易所保留 Source Provider 接口和兼容下载入口，但不再提供默认 CollectorSpec；`stock_capital_changes_tdx` 保留为源端接口和兼容下载入口，不再作为采集器展示。巨潮、腾讯、东方财富和新浪仍作为 source_request Provider 保留接口，但默认不提供采集器。

维护者可以继续完善全市场 raw/staging -> core 转换、更多独立 Collector plugin、依赖解析体验、PyPI 发布和版本兼容策略。

## 20. 维护者测试清单

维护插件协议或 Registry 时至少覆盖以下测试：

- Registry 能发现 entry point 对应 distribution。
- Registry 能免 import 读取 embedded manifest。
- 不兼容 `manifest_version` 标记 failed。
- 不兼容 `plugin_api_version` 标记 incompatible。
- 未启用插件不会被 import。
- 调用接口时才 import Provider。
- 内置 official 与 community 撞名时，内置胜出。
- 两个 community 撞名时，双方 conflict。
- 外部插件自报 official 时，effective trust 仍为 community。
- `_tdx` 后缀兜底删除后，未知接口不会误入 TDX Adapter。
- `asset_class = fx` 可通过 manifest 校验。
- DownloaderProfile 引用不存在接口时 check 失败。
- 独立 CollectorSpec 缺少 `collector_id`、`collector_plugin_id`、`dataset_id`、`runner_entry` 或输出/质量契约时 check 失败。
- legacy Provider manifest CollectorSpec 引用不存在接口或 profile 时 check 失败。
- DependencySpec 缺依赖、版本不满足和包内 wheel checksum mismatch 能被安装前检查发现。
- `required_config` 只展示，不写入 secret 存储。
