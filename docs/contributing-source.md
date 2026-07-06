# 数据源与采集插件贡献指南

本文是 AxData 数据源与采集能力插件开发教程，面向想把新数据源、采集器或相关工具接入 AxData 的开发者。新增插件应按 `docs/plugin-spec.md` 的多能力插件模型设计。

先读：

- `docs/plugin-spec.md`
- `docs/architecture.md`
- `docs/api-design.md`
- `docs/schema.md`
- `docs/data-layers.md`

## 1. 插件能做什么

AxData 插件可以只提供数据源 Provider，也可以提供采集器、下载 profile、工具能力，或者这些能力的组合：

- 只有 Provider：声明接口并实现源端直取。
- Provider + Collector：既提供源端接口，也提供独立 CollectorSpec/runner_entry。
- 只有 Collector：不提供源端接口，只提供特定采集任务。
- 工具型插件：提供可选的数据清洗、指标生成或格式转换能力。

无论插件提供哪类能力，都必须遵守 AxData 的统一运行边界：源端直取不默认落盘；采集必须进入 Collector Runner；写文件必须走 Downloader/Writer；第三方 token 不由 AxData core 托管。

## 2. Provider 应该做什么

Provider 的职责是把某个上游数据源变成 AxData 可识别的源端接口、参数、字段和 Adapter。采集能力由 Collector 插件或独立 CollectorSpec/runner_entry 提供。

Provider 应该做：

- 声明接口名、参数、字段、样例。
- 实现源端直取 Adapter。
- 使用 AxData 统一代码、日期、字段、单位规范。
- 如需 legacy 显式下载，可声明 DownloaderProfile；如需进入采集页，应声明独立 CollectorSpec/runner_entry。
- 提供真实样例和测试。

Provider 不应该做：

- 改写 AxData core schema。
- 在用户普通查询链路里偷偷请求源端。
- 绕过 AxData Writer 自己随意写 core/factor。
- 把第三方源 token 暴露给 AxData 最终用户。
- 自称 official 并指望 Registry 采信；外部插件在本地模型里仍按 community 处理。

## 3. Source Admission Checklist

新增源不要一股脑接入。先做准入测试：

| 检查项 | 要求 |
| --- | --- |
| 合法性 | 确认使用方式不明显违反源站条款或法律风险 |
| 稳定性 | 连续多次请求返回结构稳定 |
| 字段完整性 | 能映射到清晰的 AxData 字段 |
| 频率限制 | 有明确的请求间隔或并发上限建议 |
| 错误行为 | 超时、限流、空结果、字段缺失可识别 |
| 样例 | 至少保留 1 个真实请求样例和 1 个错误样例 |
| 采集价值 | 只有适合沉淀的数据才做采集，不适合的只做源端直取 |

探测没通过的源可以写进准入记录，但不要放入正式接口目录。

## 4. Naming Rules

接口名必须全局唯一，建议格式：

```text
{domain}_{dataset}_{source}
```

示例：

```text
stock_codes_tdx
stock_realtime_snapshot_tencent
announcements_cninfo
financial_statement_sina
```

规则：

- 使用小写 snake_case。
- 名字表达数据口径，不只是上游接口名。
- 不要抢占已有接口名。
- 如果是社区插件，尽量带上明确 source 后缀。
- 不要依赖 `_tdx`、`_sina` 这类后缀触发路由；后缀只是名字的一部分。

Provider 标识：

```text
provider_id = axdata.source.tencent
source_code = tencent
```

`provider_id` 是插件身份，`source_code` 是源命名空间，二者不要混用。

## 5. Project Layout

推荐插件目录：

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
      downloader.py
      samples/
        stock_snapshot.json
  tests/
    test_manifest.py
    test_adapter.py
    test_catalog.py
```

`pyproject.toml` 示例：

```toml
[project]
name = "axdata-source-demo"
version = "0.1.0"
description = "Demo AxData source provider"
requires-python = ">=3.11"
dependencies = ["axdata-core>=0.1.0"]

[project.entry-points."axdata.providers"]
demo = "axdata_source_demo.provider:provider"
```

## 6. Minimal Provider Example

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

实际 import 路径以后以 `docs/plugin-spec.md` 的实现为准。上面代码表达的是协议形态。

## 7. Interface Spec Checklist

每个接口必须写清：

- `name`
- `display_name_zh`
- `source_code`
- `source_name_zh`
- `asset_class`
- `request_mode`
- `parameters`
- `fields`
- `examples`

接口是否适合采集要单独判断：

| 类型 | 是否建议采集 |
| --- | --- |
| 股票列表、交易日历、公告、财务报表、历史行情 | 通常适合 |
| 实时快照、盘口、当日临时排行 | 默认不采集，除非显式录制 |
| 调试接口、服务器测速、源状态 | 不采集 |

不要为了“目录完整”把所有接口都放进采集页面。采集页面只放已经做完采集器、能稳定写文件、能展示进度和状态的接口。

## 8. 参数设计

参数设计原则：

- 不填表示全量时，必须在 description 写明。
- 支持批量就明确 `multiple = true`。
- 日期用 `YYYYMMDD`。
- 枚举参数要列出可选值。
- 高级执行选项应放在 options，不污染业务参数。

示例：

```json
{
  "name": "trade_date",
  "display_name_zh": "交易日期",
  "type": "date",
  "required": false,
  "description": "不填时返回源端最新可用日期。"
}
```

业务参数和执行参数要分开：

| 类型 | 示例 |
| --- | --- |
| 业务参数 | `code`、`trade_date`、`start_date`、`end_date` |
| 执行参数 | `server_count`、`connections_per_server`、`batch_size`、`workers` |

执行参数应进入 Adapter/Downloader options，并在文档里说明默认值和推荐值。

## 9. 字段设计

字段必须是 AxData 字段，不是上游原始列名。

常用标准：

| 概念 | 字段 |
| --- | --- |
| 统一证券代码 | `instrument_id` 或行情表里的 `ts_code` |
| 股票代码原始数字 | `symbol` |
| 交易所 | `exchange` |
| 交易日期 | `trade_date` |
| 自然日期 | `cal_date` |
| 更新时间 | `update_time` |
| 证券简称 | `name` |

资产类型使用：

```text
stock / index / etf / fund / bond / future / option / fx / macro
```

单位必须写明。例如：

- 价格：人民币元、点、美元等。
- 成交量：手、股、张等。
- 成交额：元、千元、万元等。
- 股本：股、万股、亿股。
- 百分比：说明 `1.23` 是否表示 1.23%。

## 10. Normalization

Provider 应尽量使用 `axdata-core` 的归一化工具。目标规则：

| 输入 | 输出 |
| --- | --- |
| `000001` + `SZSE` | `000001.SZ` |
| `600000` + `SSE` | `600000.SH` |
| `430047` + `BSE` | `430047.BJ` |
| `2026-06-22` | `20260622` |

空值处理：

- 对外返回 `None`/`null`。
- 不要把 `--`、`N/A`、空字符串原样作为缺失值返回。
- 如果上游字段不可靠，字段说明里标注口径。

错误处理：

- 上游超时映射为 `upstream_unavailable` 或等价错误。
- 参数错误映射为 `invalid_request`。
- 限流映射为 `rate_limited`。
- 不要把上游完整堆栈直接返回给用户。

## 11. Adapter Implementation

Adapter 只做源端请求和字段归一，默认不落盘。

建议结构：

```python
class DemoAdapter:
    def __init__(self, options=None):
        self.options = dict(options or {})

    def call(self, interface_name, params=None, fields=None, options=None):
        params = dict(params or {})
        options = {**self.options, **dict(options or {})}

        if interface_name == "demo_snapshot":
            return self._snapshot(params, fields, options)
        raise KeyError(interface_name)
```

要求：

- 参数校验要在请求前完成。
- 网络超时必须设置，不允许无限等待。
- 返回字段必须按 FieldSpec 归一。
- `fields` 选择应尽量在返回前裁剪。
- meta 里尽量记录 `source_code`、`interface_name`、`elapsed_ms`、`data_date`、`request_time`。

不要在 Adapter 里写 Parquet。采集写文件应该走 Downloader/Writer。

## 12. DownloaderProfile 设计

DownloaderProfile 是显式下载/legacy 兼容入口，用来描述一个接口如何批量请求、写文件和做基础质检。它不等于采集器；需要进入采集页或定时任务时，应提供独立 CollectorSpec/runner_entry，并由 Collector Runner 托管。

示例：

```json
{
  "name": "demo.snapshot.latest",
  "interface_name": "demo_snapshot",
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
  }
}
```

资源组命名建议：

```text
{source_code}.{resource_type}
```

示例：

- `tdx.quote`
- `tdx.f10`
- `tdx.ext`
- `tencent.http`
- `cninfo.http`

如果一个源多个接口共用上游连接预算，就让它们共享同一个 `resource_group`。不要给每个接口乱建资源组，否则全局调度无法控制拥挤。

## 13. Collector 设计

插件可以声明采集器，但采集运行必须由 AxData Collector Runner 托管。采集器声明应该回答：

- 采集器 ID、输出数据集和业务口径是什么。
- 使用哪个 `runner_entry` 执行取数逻辑。
- 默认参数是什么。
- 依赖哪些基础数据集或插件能力。
- 使用哪个 resource_group。
- 推荐调度时间是什么。
- 输出到哪个数据层或目录。

采集器不应该做：

- import 时自动启动后台线程。
- 绕过 AxData 队列直接并发运行。
- 绕过 AxData Writer 写 core/factor。
- 自己维护一套与 AxData 无关的任务状态。
- 删除或覆盖用户已有数据。

只有 Collector 的插件是允许的。例如，一个用户可以写一个“每日收盘后刷新日线”的采集插件，它不提供新 Provider，只调用当前 Registry 里已经存在的 `daily_xxx`、`stock_codes_xxx` 和 `trade_cal` 接口。

## 14. Concurrency Guidance

并发不是越大越好。插件只声明推荐预算，最终实际并发由 AxData collector 的全局资源池裁决。

开发者应在 README 或 InterfaceSpec 中说明：

- 默认并发。
- 为什么推荐这个并发。
- 批大小。
- 超时和重试策略。
- 哪些阶段固定串行，哪些阶段可并行。

例如：

```text
最新停牌列表：股票池阶段固定按沪深北并行扫描；停牌状态阶段推荐 4 个服务器 x 每服务器 2 条连接，批大小 80。
```

如果没有实测，不要写“高并发秒级”之类承诺。

## 15. Dependencies

插件应尽量保持依赖少而明确。依赖声明用于安装前预览和风险提示，不代表 AxData 会自动解决所有版本冲突。

建议：

- 在 `pyproject.toml` 中写清 Python 依赖。
- 在 manifest 的 `dependencies` 中写清必需依赖、可选依赖和用途。
- 如果希望 `.axp` 离线安装，把依赖 wheels 放进 `.axp`。
- 不要默认要求联网安装依赖。
- 发现依赖冲突时，优先由插件作者调整版本范围或拆分插件。

AxData 的目标行为是：

- 默认离线。
- 安装前提示缺失依赖。
- 安装前提示明显版本不满足。
- 允许用户显式开启在线依赖安装。
- 不做复杂自动依赖冲突治理。

## 16. Config And Tokens

AxData 不托管第三方源 token。插件需要 token 时自己处理。

推荐方式：

```python
import os

token = os.environ.get("TUSHARE_TOKEN")
```

Manifest 可以声明：

```json
{
  "name": "TUSHARE_TOKEN",
  "kind": "env",
  "required": true,
  "description": "用户自己的 Tushare token。"
}
```

这只是 UI/CLI 提示。AxData 不保存、不注入、不代理这个 token。

如果 AxData 部署在局域网或服务器给多人用，第三方源凭据只应留在服务端运行环境中，最终用户通过 AxData API token 访问 AxData，不直接接触源 token。

## 17. Examples And Samples

每个接口至少提供一个样例：

- 请求参数。
- 响应字段。
- 1 到 5 行数据。
- 请求日期或数据日期。

实时类接口样例要标明时间：

```json
{
  "title": "单票实时快照",
  "request_time": "2026-06-22T15:05:00+08:00",
  "request": {
    "interface_name": "demo_snapshot",
    "params": {"code": "000001.SZ"}
  },
  "response": {
    "data": [{"instrument_id": "000001.SZ", "name": "平安银行"}]
  }
}
```

样例不能只是空结构。Web 接口页、README 和测试都要尽量复用同一批样例，避免漂移。

## 18. Testing Checklist

至少写这些测试：

- Provider 能返回 interfaces。
- `axdata plugin check` 能生成并校验 manifest。
- 每个接口参数校验通过。
- 每个接口字段名与 FieldSpec 一致。
- 样例响应字段存在。
- 网络失败能转成 AxData 错误。
- 超时不会卡死。
- `fields` 裁剪有效。
- DownloaderProfile 引用的接口存在。
- CollectorSpec 引用的接口和 DownloaderProfile 存在。
- 依赖声明能被安装前检查读取。
- `asset_class` 属于标准枚举。
- 不需要 token 的接口在无 token 环境下可跑。
- 需要 token 的接口在无 token 环境下给出清晰错误。

如果是接入公开网页或非官方接口，还要有结构变更测试：字段缺失时不能静默返回错误数据。

## 19. Build And Check

目标流程：

```bash
axdata plugin check
axdata plugin build
python -m build
```

`plugin check` 应失败的情况：

- manifest 无法解析。
- Provider 生成 manifest 与包内 manifest 不一致。
- `provider_id` 不合法。
- 接口名重复。
- 字段名不是 snake_case。
- `asset_class` 不在标准枚举。
- DownloaderProfile 指向不存在接口。
- CollectorSpec 指向不存在接口或 profile。
- dependency wheel checksum 不匹配。
- 样例字段和 FieldSpec 不一致。

`plugin build` 应做：

- 从 Provider 生成 `axdata-provider.json`。
- 写入 package data。
- 可选生成 `.axp` 所需预览 manifest。

在工具链覆盖完整流程前，内置源调整时也应该按这些规则手动检查。

## 20. 发布

基础发布方式：

```bash
pip install axdata-source-demo
axdata plugin list
axdata plugin enable axdata.source.demo
```

发布前检查：

- README 写明数据来源和风险。
- LICENSE 清楚。
- 依赖尽量少。
- 无硬编码私人 token。
- 无默认写入用户数据目录的副作用。
- 无 import 时立即联网。
- 样例和测试通过。

插件 import 时不要执行网络请求。只有被调用时才请求源端。

## 21. Security And Trust

社区插件本质上是用户安装并运行的 Python 代码。Manifest 里的声明不能当安全保证。

必须诚实说明：

- AxData 不做插件签名验签，不做插件市场，不做插件审核。
- 外部插件默认 community。
- 自报 official 不会被采信，也不会获得内置权限。
- 启用插件意味着允许其代码运行。
- “是否联网”只是作者声明，不是沙箱保证。

插件作者不要伪装成 AxData 内置能力。数据源插件可以由 AxData 项目或社区以独立包发布，但签名体系不属于当前主线目标。

## 22. Common Mistakes

避免这些问题：

- 把上游原始字段直接暴露给用户。
- 接口名只写上游接口代号，看不出口径。
- 在 Adapter 里写文件。
- import 插件时就联网。
- 把第三方 token 写进样例或日志。
- 把实时快照默认放进采集目录。
- 每个接口各自发明日期格式。
- 每个接口各自发明资产类型。
- 手写 manifest 后忘记同步 Provider。
- 社区插件抢内置接口名。
- 在 Collector 插件里自己开后台线程绕过 AxData 调度。
- 依赖范围写得过宽，导致用户环境升级后插件失效。

## 23. First Good Plugin

第一个外部化插件建议选轻量、边界清楚、不会牵扯复杂长连接的源，例如腾讯财经快照或巨潮公告。它应验证：

- Provider 协议能表达真实接口。
- Registry 能免 import 展示目录。
- 调用时才 import Adapter。
- Web 能从后端 catalog 展示接口。
- `plugin check` 能防止 manifest 漂移。

等轻量插件跑通后，再拆 TDX。TDX 包含普通行情、拓展行情、F10、服务器测速、多连接采集和缓存，复杂度高，不适合作为第一个验证插件协议的对象。

