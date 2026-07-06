# 插件安装管理

本文描述当前已经实现的 AxData 本地插件安装管理流程：预览、安装、列出、启用、禁用、替换和卸载 AxData 管理的 `.axp` 包。插件作者应先读 [plugin-development.md](plugin-development.md)，再用本文验证安装、启停、卸载和诊断路径。

AxData 插件是本地 Python 扩展。用户在自己的机器上安装和启用插件，并承担本地代码执行风险。AxData 不提供插件市场、插件审核、签名信任体系或沙箱。当前安装管理已包含依赖预览和包内 dependency wheels 离线安装；维护重点是插件作者工具和 UI 引导，不是中心化市场基础设施。只有带 `axdata-provider.json` 或 `axdata-plugin.json` manifest 的 Python 包才会进入普通 AxData 插件列表；缺 manifest 的 entry point 只作为 ignored candidate 出现在诊断信息中。

## Provider 插件

Provider 插件和 Collector 插件是平级能力：Provider 进入源端接口目录，Collector 进入采集页和 CollectorRegistry。当前安装管理从 Provider 插件起步，并在 manifest/Registry 层兼容 collectors、downloaders、dependencies 等能力声明。

每个 Provider 声明：

- 稳定的 `provider_id`，例如 `axdata.source.tencent_external`
- `source_code`，例如 `tencent`
- 源端直取接口，例如 `tencent_realtime_snapshot`
- 可选的 DownloaderProfile
- 可选的 CollectorSpec；进入采集页时应以独立 CollectorSpec/runner_entry 为准
- 可选的依赖声明
- API、CLI、Web 展示所需元数据

真实可执行包格式仍是 Python wheel + entry point + embedded `axdata-provider.json` manifest。AxData 先读 manifest 做目录展示、版本门禁和冲突检查，只有调用具体接口时才 import Provider 代码。

## AXP 安装包

`.axp` 是围绕一个或多个插件 wheel 的本地安装信封。它是一个 zip archive，通常包含：

- `manifest.json`，或 wheel 内嵌的 provider manifest
- `wheels/*.whl`
- `checksums.txt`，记录 sha256 checksum
- 可选 README / LICENSE
- 可选 dependency wheels

AXP 只是分发和安装单位，不决定插件能力类型。安装预览会读取 wheel 内的 `axdata-provider.json` / `axdata-plugin.json` manifest，并按能力声明分流：`provider` + `interfaces` 进入 ProviderRegistry，`collectors` / CollectorSpec 进入 CollectorRegistry。同一个 AXP 可以是 source-only、collector-only，也可以同时包含 Provider 和 Collector 能力。

安装 `.axp` 默认不启用 Provider。外部插件安装后状态为 `disabled`，用户可以先检查 provider、interfaces、downloaders、collectors、dependencies 和 dependency_status，再决定是否 enable。

`checksums.txt` 只用于文件完整性和打包一致性检查。它不证明插件作者身份，不证明代码安全，也不授予内置权限。AxData 当前本地优先模型不实现签名验签。

## 依赖处理策略

当前依赖处理默认离线：

- 预览 manifest、embedded wheel metadata 和简单 bundled `pyproject.toml` 声明的 Python 依赖。
- 检测缺失依赖、版本不满足、非法版本约束、声明但缺失的 dependency wheel。
- 将 `axdata-core` / `axdata` 视为运行中的 AxData 宿主依赖。
- 先安装 `.axp` 包内 dependency wheels，再安装插件 wheel。
- 默认拒绝缺失或版本不满足的 required dependency。
- 只有用户显式 opt-in 时才允许联网安装依赖。
- 清楚报告依赖冲突，但不做复杂自动冲突求解。

如果两个插件需要同一个 Python 包的不兼容版本，AxData 会按安装模式提示或拒绝。插件作者或用户应修正依赖集合、选择兼容版本，或使用单独环境。

## CLI 使用

测试插件安装时建议使用干净或显式指定的 data root。AxData 会把 `metadata`、托管插件目录、
`cache` 和 `logs` 放在 data root 同级；如果需要完整隔离的临时环境，可以把 `--data-root` 指向一个 `data` 子目录：

```powershell
$base = "$env:TEMP\axdata-plugin-smoke"
$root = Join-Path $base "data"
```

安装或启用插件前，先初始化并检查本地运行环境：

```powershell
.\.venv\Scripts\axdata --data-root $root init
.\.venv\Scripts\axdata --data-root $root doctor
.\.venv\Scripts\axdata --data-root $root status
.\.venv\Scripts\axdata --data-root $root config show
```

`doctor` 会报告插件配置路径、AxData 托管的插件 `site-packages`、ProviderRegistry 加载状态、
已安装/已启用/已禁用/失败/冲突的 Provider、TDX 插件状态和最近 Collector 失败信息。它是离线检查：
不会安装依赖、启用插件、导入 Provider 运行时代码，也不会请求真实数据源。

预览归档：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin axp-preview C:\path\to\plugin.axp --json
```

安装归档：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin axp-install C:\path\to\plugin.axp --json
```

安装并显式启用：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin axp-install C:\path\to\plugin.axp --enable --json
```

显式允许在线安装依赖：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin axp-install C:\path\to\plugin.axp --allow-online-deps --json
```

Default dependency handling is offline. If preview reports a missing required dependency, an unsatisfied version,
a declared dependency wheel that is absent from the archive, or an obvious conflict, fix the `.axp` contents or the
plugin environment first. Use `--allow-online-deps` only when you intentionally want pip to use the current
environment's configured indexes.

列出 AxData 托管安装的插件：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin installed --json
```

列出已发现的 Provider 和采集能力：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin list --json
.\.venv\Scripts\axdata --data-root $root plugin collectors --json
```

`plugin list --json`、`plugin info --json`、`plugin installed --json`,
`/v1/plugins/providers`, and `/v1/plugins/installed` include
`status_message`, `next_action`, and `action_command` when AxData can suggest the next local step. Typical cases:
disabled plugins suggest an explicit `plugin enable` command, TDX disabled/missing states use neutral TDX wording,
manifest discovery failures point to the missing `axdata-provider.json` / `axdata-plugin.json`, incompatible plugins
指向 `plugin_api_version`，冲突时会提示禁用其中一个 Provider 或设置 override。

这些 payload 还包含 CLI、API、诊断和 Web 共用的管理字段：

- `install_source`: `preinstalled`, `axp_managed`, `python_environment`, `editable/development`, `missing`, or `unknown`.
- `provider_kind`: `source_plugin`, `collector_plugin`, `tool_plugin`, or `core`.
- `lifecycle_status`: 运行时生命周期状态，例如 `enabled`、`disabled`、`missing` 或 `uninstalled`。
- `can_enable` / `can_disable`: AxData 是否能在当前状态下改变 Provider 路由状态。
- `can_uninstall`: 预装源插件和通过 AxData 托管 `.axp` 流程安装的插件为 true。
- `uninstall_mode`: 预装插件为 `managed_disable`，AxData 托管 AXP 插件为 `physical_remove`。
- `uninstall_block_reason`: 插件无法由 AxData 移除时，返回给用户看的原因。

预装源插件可以启用、禁用、逻辑卸载和重新启用。当前预装卸载是逻辑卸载：AxData 将插件标记为从当前 runtime 移除，隐藏它贡献的 interfaces、downloaders、collectors 和 task templates，但不物理删除随包代码。AXP 托管插件可以物理卸载；如果当前已启用，可以传入 `disable_first=true`。Python environment 或 editable/development 插件会出现在 Provider 状态里，但 AxData 不会从 Python 环境中删除它们；请使用 `pip uninstall` 或移除开发路径。卸载永远不删除 `data/`、已采集 Parquet 文件、用户任务定义、运行历史、metadata 或 logs。

Web 配置页的 Provider 状态和已安装插件卡片会展示同样的 guidance 字段，适合不用切回命令行时先判断“为什么不可用”和“下一步做什么”。Web 不提供插件市场、在线下载中心或自动联网安装依赖。

启用或禁用 Provider：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin enable axdata.source.tencent_external
.\.venv\Scripts\axdata --data-root $root plugin disable axdata.source.tencent_external
.\.venv\Scripts\axdata --data-root $root doctor
```

卸载预装插件或已禁用的外部插件：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin uninstall axdata.source.tencent --json
.\.venv\Scripts\axdata --data-root $root plugin uninstall axdata.source.tencent_external --json
```

对于 AXP 托管的外部插件，默认拒绝直接卸载已启用的 Provider。可以先禁用，也可以使用：

```powershell
.venv\Scripts\python -m axdata_core.cli --data-root $root plugin uninstall axdata.source.tencent_external --disable-first --json
```

再次安装同一个 Provider：

```powershell
.\.venv\Scripts\axdata --data-root $root plugin axp-install C:\path\to\plugin.axp --replace --json
```

不带 `--replace` 时，同一个 `provider_id` 的重复安装会被拒绝。`--replace` 会覆盖 AxData 托管的安装记录和托管包文件。除非同时传入 `--enable`，替换后的插件仍保持禁用状态。

Web 的 AXP 安装面板遵循同一规则：先预览上传的 `.axp`，如果发现同一个插件身份已经存在于 AXP 安装记录中，按钮会从“安装”切换为“更新插件”。当前 API/CLI 返回字段仍统一叫 `provider_id`，对数据源插件通常就是 Provider ID，对 collector-only 插件则承载对应的插件身份。更新时 Web 会提交 `replace=true`；如果用户勾选“更新后保持启用”，同时提交 `enable=true`。更新只替换插件包和安装记录，不删除 `data/`、metadata、采集任务、运行历史、日志、缓存、API token 或第三方凭据。

## API 使用

API 使用当前运行服务的 data root。

- `POST /v1/plugins/axp/preview`：预览上传的 `.axp`。
- `POST /v1/plugins/axp/install`：安装上传的 `.axp`。
- `GET /v1/plugins/axp/export/{provider_id}`：把已发现插件导出为可下载的 `.axp`。
- `GET /v1/plugins/installed`：列出 AxData 托管安装的插件。
- `DELETE /v1/plugins/installed/{provider_id}`：卸载托管插件或预装插件。
- `POST /v1/plugins/installed/{provider_id}/uninstall`：卸载托管插件或预装插件。
- `POST /v1/plugins/providers/{provider_id}/enable`：启用 Provider。
- `POST /v1/plugins/providers/{provider_id}/disable`：禁用 Provider。

AXP 上传使用 multipart form 字段 `file`。安装接口接受以下 form 字段：

- `enable=true`：安装后显式启用。
- `replace=true`：替换同一 `provider_id` 的既有托管安装。
- `allow_online_deps=true`：允许 pip 从当前配置的索引安装缺失依赖。

重复安装会返回 `409`，除非安装表单传入 `replace=true`。缺少必需依赖会返回 `400`，除非依赖可以由包内 dependency wheels 满足，或调用方显式传入 `allow_online_deps=true`。卸载已启用的 AXP 托管插件会返回 `409`，除非传入 `disable_first=true`。卸载预装插件会返回 `uninstall_mode=managed_disable`，隐藏该插件的运行能力，但不删除数据或历史。尝试卸载仅从 Python 环境或 editable/development 路径发现的 Provider 时，会返回错误并提示使用 `pip uninstall` 或移除开发路径。

AXP 导出返回文件响应。路径参数是插件身份：数据源插件通常是 `provider_id`，collector-only 插件可以是 `collector_plugin_id`。导出的归档只包含插件 manifest、wheels、README 和 checksums；不包含已采集的 Parquet/CSV/DuckDB 数据、metadata 数据库、task 或 run history、logs、cache、AxData API token 或第三方数据源凭据。

## TDX 插件使用

TDX 能力来自独立插件包，不属于 core 的可运行能力。普通 TDX 和 TDX Ext 扩展行情是两个独立 Provider：

| Provider | 包 | 数据范围 |
| --- | --- | --- |
| `axdata.source.tdx_external` | `axdata-source-tdx` | 股票、指数、ETF、K 线、F10、短线等普通行情接口。 |
| `axdata.source.tdx_ext_external` | `axdata-source-tdx-ext` | 期货、期权、基金、债券、外汇、宏观等扩展行情接口。 |

普通 TDX 与 TDX Ext 互相独立，禁用其中一个不应影响另一个。通过 `axdata`、随包 wheel 或当前源码仓库安装时，TDX 与 TDX Ext 默认可用；用户仍可用 `plugin disable <provider_id>` 按需关闭。扩展行情接口会以“通达信扩展行情”一级菜单进入运行目录。

用户路径是：

1. 安装 TDX 或 TDX Ext 插件包，或安装包含对应 Provider 的 `.axp`。
2. `plugin list` 或 `GET /v1/plugins/providers` 确认 Provider 可见。
3. `GET /v1/request/interfaces` 查看对应接口是否进入运行目录。
4. 使用 `client.call(...)`、`/v1/request/*`、Downloader 或 Collector task。

未安装或被显式禁用时，系统会在 Provider 状态中提示原因；禁用后的接口不会参与路由。用户文档不提供 core 可运行兜底路径。

本地开发时可以直接 editable 安装插件包：

```powershell
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx
.\.venv\Scripts\python -m pip install -e packages\axdata-source-tdx-ext
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata doctor
```

AXP 或第三方 Python 包安装只让 Provider 可被发现；启用状态仍由 AxData 插件配置控制，默认 disabled。AxData 随包提供的 TDX/TDX Ext 包是发布入口的默认能力，安装后默认 enabled；当前仓库开发环境也会把随仓库提供的 TDX 与 TDX Ext 包投影为预装插件。只有包文件、manifest 或 import 路径损坏时才显示 missing。

## 发布安装检查

仓库提供一个临时环境检查脚本，用于验证发布/安装体验，不提交任何 venv、wheelhouse、AXP 或数据产物。默认使用当前解释器创建临时 venv，安装本地 workspace、`axdata-core`、`axdata` SDK 和 TDX 插件，运行 `axdata --help/init/config show/doctor/status`，并检查 TDX manifest 和资源文件。

快速 editable 插件路径：

```powershell
.\.venv\Scripts\python scripts\packaging_smoke.py --json
```

AXP 插件路径：

```powershell
.\.venv\Scripts\python scripts\packaging_smoke.py --tdx-mode axp --json
```

保留临时目录以便排错：

```powershell
$work = "$env:TEMP\axdata-packaging-smoke"
.\.venv\Scripts\python scripts\packaging_smoke.py --tdx-mode axp --work-dir $work --json
```

这个检查不运行真实源请求；真实源小样本仍使用 `scripts\smoke_real_sources.py --run` 显式触发。

## 预装插件与 Core

AxData Core 是数据库、插件协议、Registry、任务平台、存储/查询层、API、Web 和 CLI 宿主。Core 不是数据源，不能通过插件管理卸载。

随 AxData 提供的数据源是预装插件。它们不是通过 `.axp` 安装，但 AxData 仍可在本地插件状态中管理其生命周期：启用、禁用、逻辑卸载、重新安装或重新启用。逻辑卸载使用 `uninstall_mode=managed_disable`：插件贡献的 interfaces、downloaders、collectors 和 task templates 会从当前 runtime 中消失，但随包代码、已采集数据、metadata、用户创建的 Task 定义和 Run History 保留。

## 当前边界

- 签名验签不属于当前本地优先插件模型。外部 `.axp` 按本地 community 插件处理。
- 不做插件市场。
- `.axp` 安装只处理明显依赖状态和包内 dependency wheels，不做复杂依赖冲突求解。
- 在线依赖安装必须显式 opt-in，并委托当前环境配置的 pip indexes。
- 预装插件卸载当前是逻辑卸载，不物理删除随包代码。
- Python 环境或 editable/development 路径发现的非预装 Provider 会在状态页可见，但不由 AxData 删除。
- 卸载不删除用户数据、Parquet、日志、metadata、用户 Task 或 Run History。
