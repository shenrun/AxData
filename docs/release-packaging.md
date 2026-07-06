# AxData 发布打包验证

本文记录 AxData 发布到 PyPI 前的本地验证流程。这里的命令只构建和安装本地候选包，不会上传 PyPI、TestPyPI 或 GitHub。

## 包边界

AxData 仓库是 workspace，不建议把根目录的 `axdata-workspace` 当作用户包发布。

面向 PyPI 的候选包包括：

| 包名 | 目录 | 用途 |
| --- | --- | --- |
| `axdata-core` | `libs/axdata_core` | 核心协议、存储、查询、插件、CLI 和采集框架 |
| `axdata` | `packages/axdata-sdk` | 用户侧 Python SDK 和 `import axdata` 入口 |
| `axdata-source-tdx` | `packages/axdata-source-tdx` | 通达信数据源 Provider |
| `axdata-source-tdx-ext` | `packages/axdata-source-tdx-ext` | 通达信扩展行情 Provider |
| `axdata-source-tencent` | `packages/axdata-source-tencent` | 腾讯财经 Provider |
| `axdata-source-cninfo` | `packages/axdata-source-cninfo` | 巨潮 Provider |

`axdata` 用户主包依赖 `axdata-core[parquet]`，并带上本地诊断和 API 运行所需的 FastAPI、uvicorn、pydantic、python-multipart 等依赖；直接安装 `axdata-core` 仍保持更轻量，插件开发者可按需安装 `axdata-core[parquet]`。

普通用户发布后的推荐安装入口是：

```powershell
python -m pip install axdata
```

`axdata` 会同时安装当前默认数据源插件：`axdata-source-tdx`、`axdata-source-tdx-ext`、`axdata-source-tencent` 和 `axdata-source-cninfo`。TDX/TDX Ext 插件安装后应默认可用，用户不需要在快速开始里手动执行 `plugin enable`。

发布顺序应先发 `axdata-core`，再发数据源插件包，最后发 `axdata`。

## 本地 PyPI Readiness

运行：

```powershell
.\.venv\Scripts\python scripts\pypi_readiness.py --json
```

脚本会在临时目录内完成：

- 复制各候选包源码，避免在仓库源码目录生成 `dist/`、`build/` 或 `*.egg-info`。
- 为每个候选包构建 wheel 和 sdist。
- 运行 `twine check` 检查包元数据和 README 渲染。
- 创建全新的安装 venv，从本地 wheel 安装候选包。
- 验证 `import axdata`、`import axdata_core` 和各数据源插件模块。
- 验证 Provider entry point、包内 `axdata-provider.json` 和关键资源文件。
- 验证 `axdata` 的 wheel 元数据包含当前默认数据源插件依赖。
- 验证随项目提供的 TDX/TDX Ext Provider 安装后默认进入 enabled 状态。
- 运行 `axdata --help`、`axdata init`、`axdata doctor`、`axdata status`、`axdata plugin list`。

保留临时目录以便排错：

```powershell
$work = "$env:TEMP\axdata-pypi-readiness"
.\.venv\Scripts\python scripts\pypi_readiness.py --work-dir $work --json
```

如果只想跳过 `twine check`：

```powershell
.\.venv\Scripts\python scripts\pypi_readiness.py --skip-twine-check --json
```

## 不包含的动作

该脚本不做：

- 不上传 PyPI。
- 不上传 TestPyPI。
- 不创建 GitHub release。
- 不修改 git remote。
- 不推送代码。
- 不请求真实数据源。

真正发布前还应先在 TestPyPI 演练一次完整安装链路，并确认包名、版本号、依赖、README 渲染、命令行入口和插件发现都符合预期。
