# AxData AXP 打包与安装教程

`.axp` 是 AxData 的本地安装信封。它不是插件核心格式，核心格式仍然是 Python wheel + entry point + embedded manifest。AXP 的作用是把 wheel、manifest、README、LICENSE、checksum 和可选依赖 wheels 打成一个用户可上传、可预览、可离线安装的包。

## 1. AXP 是什么

核心说明：

- wheel 是 Python 真正安装的包。
- manifest 告诉 AxData 这个包提供什么能力。
- `.axp` 是把这些东西装进一个压缩包，方便 Web/CLI 安装。
- checksum 只检查文件有没有损坏，不代表安全认证。

AXP 是分发和安装单位，不是能力类型。AxData 不靠 AXP 文件名或目录名判断“数据源插件”还是“采集器插件”，而是读取 wheel 内的 `axdata-provider.json` / `axdata-plugin.json`：

- 声明 `provider` + `interfaces` 的能力进入 ProviderRegistry，是数据源接口能力。
- 声明 `collectors` / CollectorSpec 的能力进入 CollectorRegistry，是采集器能力。
- 同一个 AXP 可以只包含数据源能力、只包含采集器能力，也可以同时包含两者。

AxData 不做插件市场、不做中心审核、不做签名信任体系。安装外部插件本质上就是允许本地 Python 代码运行。

## 2. 推荐包结构

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
    stock_snapshot.json
```

说明：

| 文件 | 作用 |
| --- | --- |
| `manifest.json` | 安装前预览用的包级 manifest |
| `wheels/*.whl` | 真正安装的插件 wheel |
| dependency wheels | 离线依赖包 |
| `checksums.txt` | 文件完整性检查 |
| `README.md` | 给用户看的说明 |
| `LICENSE` | 许可说明 |
| `samples/` | 可选样例 |

## 3. 打 wheel

先在插件项目里构建 wheel：

```powershell
.\.venv\Scripts\python -m pip install build
.\.venv\Scripts\python -m build C:\path\to\axdata-source-demo
```

生成结果通常在：

```text
dist/
  axdata_source_demo-0.1.0-py3-none-any.whl
```

构建后要检查 wheel 里有没有 manifest：

```powershell
.\.venv\Scripts\python -m zipfile -l dist\axdata_source_demo-0.1.0-py3-none-any.whl
```

必须能看到：

```text
axdata_source_demo/axdata-provider.json
```

或：

```text
axdata_collector_demo/axdata-plugin.json
```

## 4. 生成 AXP 内容

准备临时目录：

```powershell
$pkg = "$env:TEMP\axdata-demo-axp"
Remove-Item $pkg -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "$pkg\wheels" | Out-Null
Copy-Item C:\path\to\dist\axdata_source_demo-0.1.0-py3-none-any.whl "$pkg\wheels\"
Copy-Item C:\path\to\README.md "$pkg\README.md"
Copy-Item C:\path\to\LICENSE "$pkg\LICENSE"
```

包级 `manifest.json` 可以很薄，但要能让安装前预览知道插件身份：

```json
{
  "format": "axdata.axp",
  "format_version": "1.0",
  "name": "axdata-source-demo",
  "version": "0.1.0",
  "wheels": [
    "wheels/axdata_source_demo-0.1.0-py3-none-any.whl"
  ]
}
```

如果 wheel 内已经有 `axdata-provider.json` 或 `axdata-plugin.json`，AxData 会优先读取 wheel 内 manifest 做能力预览。

## 5. 依赖 wheels

默认安装是离线优先。插件有第三方依赖时，有两种方式：

| 方式 | 说明 |
| --- | --- |
| 包内带 dependency wheels | 推荐给离线安装，AXP 里放依赖 wheel |
| 允许在线安装 | 用户显式选择 `--allow-online-deps` 或 Web 勾选允许联网 |

依赖声明示例：

```json
{
  "dependencies": [
    {
      "name": "beautifulsoup4",
      "version_spec": ">=4.12",
      "optional": false,
      "source": "pypi",
      "wheel": "wheels/beautifulsoup4-4.12.3-py3-none-any.whl",
      "description": "解析网页公告"
    }
  ]
}
```

如果声明了 wheel，却没把文件放进 AXP，预览应该提示缺失。

## 6. checksums.txt

checksum 用于发现包损坏、漏文件或传输不完整。

格式可以是：

```text
sha256  wheels/axdata_source_demo-0.1.0-py3-none-any.whl  <hash>
sha256  README.md  <hash>
sha256  LICENSE  <hash>
```

注意：

- checksum 不是签名。
- checksum 不证明作者身份。
- checksum 不证明插件安全。
- checksum 只证明当前文件和清单匹配。

## 7. 打成 .axp

AXP 本质是 zip：

```powershell
Compress-Archive -Path "$pkg\*" -DestinationPath C:\path\to\demo.axp -Force
```

如果工具链提供 `axdata plugin build`，也应该做这些事：

- 生成 manifest。
- 构建 wheel。
- 检查 wheel 内 manifest。
- 收集 dependency wheels。
- 生成 checksums。
- 打成 `.axp`。
- 运行 preview smoke。

## 7.1 从已安装插件导出 AXP

Web 插件页的“导出 AXP”用于把当前可发现的插件重新打成安装包。它导出的是插件分享/安装单位，不是采集数据包：

- AXP-managed 插件会复用 AxData 管理安装目录里保存的 wheel。
- 仓库随包插件会使用本地包构建 wheel；还未完全外置的预装投影源会生成 bridge wheel，运行时依赖目标环境的 `axdata-core` 提供实现。
- 数据源插件和采集插件走同一个 AXP 包格式；安装时仍按 manifest 判断是 Provider 能力、Collector 能力，或两者都有。
- 导出内容只包含 manifest、wheel、README 和 checksum，不包含本地 `data/`、metadata 数据库、任务历史、run history、logs、cache、API token 或第三方数据源凭据。

API 入口：

```text
GET /v1/plugins/axp/export/{provider_id}
```

这里的 `{provider_id}` 是插件身份参数。对数据源插件通常是 `provider_id`，对 collector-only 插件可以是 `collector_plugin_id`。

## 8. 预览

安装前先预览：

```powershell
.\.venv\Scripts\axdata plugin axp-preview C:\path\to\demo.axp --json
```

预览应该看：

- provider_id / plugin_id / collector_plugin_id 是否正确。
- provider_kind 和 interfaces / collectors 是否和预期能力一致。
- interfaces / collectors 是否符合预期。
- 依赖是否缺失。
- checksum 是否通过。
- 是否能离线安装。
- 是否有冲突。

Web 插件页上传 AXP 时，也应该先展示这些信息，让用户决定是否安装。

## 9. 安装

安装但不启用：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --json
```

安装并启用：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --enable --json
```

允许在线依赖：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --allow-online-deps --json
```

重复安装同一个 Provider：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --replace --json
```

如果这是插件更新，且希望更新后继续启用：

```powershell
.\.venv\Scripts\axdata plugin axp-install C:\path\to\demo.axp --replace --enable --json
```

Web 安装面板会先预览 `.axp`。当它检测到同一个插件身份已经存在时，会把“安装”切换为“更新插件”，并在确认后使用同样的 `replace=true` 逻辑。更新不会删除已采集数据、任务、运行历史、metadata、日志或本地配置。

## 10. 启用和禁用

安装不等于启用。安装只是把包放到 AxData 管理目录；启用后才进入接口目录或采集器目录。

```powershell
.\.venv\Scripts\axdata plugin list --json
.\.venv\Scripts\axdata plugin enable axdata.source.demo
.\.venv\Scripts\axdata plugin disable axdata.source.demo
```

采集器插件同理：启用身份应使用它自己的 `plugin_id` / `collector_plugin_id`，不要伪造成 Provider。禁用后，已有任务和历史记录保留，但任务会显示依赖不可用。

## 11. 卸载

卸载 AXP 管理插件：

```powershell
.\.venv\Scripts\axdata plugin uninstall axdata.source.demo --json
```

如果插件启用中，可能需要先禁用，或显式允许卸载时禁用：

```powershell
.\.venv\Scripts\axdata plugin uninstall axdata.source.demo --disable-first --json
```

卸载不会删除：

- `data/`
- 已采集 Parquet 主数据、CSV 导出和 DuckDB 查询缓存
- metadata
- 用户创建的任务
- run history
- logs

卸载只让插件能力从当前 runtime 消失。

## 12. Web 安装流程

Web 插件页建议流程：

1. 选择 `.axp` 文件。
2. 预览插件身份、能力、依赖、checksum。
3. 用户确认安装。
4. 默认安装后不启用。
5. 用户手动启用。
6. 数据源能力进入接口页；采集器能力进入采集页。

不要把安装、启用、运行采集混成一个按钮。这样用户才知道每一步发生了什么。

## 13. 常见错误

| 现象 | 常见原因 | 修复 |
| --- | --- | --- |
| 预览失败 | AXP 不是合法 zip 或缺 wheel | 检查包结构 |
| 插件安装后不显示 | wheel 内缺 manifest | 修 package data |
| 依赖缺失 | AXP 未带 dependency wheel | 补 wheel 或允许在线安装 |
| checksum 失败 | 文件被修改或清单不匹配 | 重新生成 checksums |
| 重复安装失败 | provider_id 已存在 | 使用 replace 或改 ID |
| 启用失败 | 接口名冲突或版本不兼容 | 禁用冲突插件或更新插件 |

## 14. 发布前检查清单

- wheel 能安装。
- wheel 内包含 manifest。
- manifest 能解析。
- provider_id / collector_plugin_id 稳定唯一。
- interface_name / collector_id / dataset_id 不冲突。
- README 写清数据来源、限制、token 配置。
- LICENSE 存在。
- 依赖声明完整。
- AXP preview 通过。
- 安装、启用、禁用、卸载都跑过。
- 禁用或卸载后不会删除用户数据。
