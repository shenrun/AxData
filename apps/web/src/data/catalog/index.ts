import {
  Activity,
  BookOpen,
  Code2,
  Database,
  Download,
  FileCode2,
  Plug,
  ServerCog,
  Settings,
  Shield,
  Stethoscope
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type {
  ActiveSection,
  CatalogGroup,
  CatalogItem,
  InfoPage,
  IngestionPlan,
  SidebarGroup,
  SourceContractSpec
} from "../../types";
import {
  cninfoNavGroup,
  eastmoneyNavGroup,
  externalCatalogItems,
  externalSourceContracts,
  sinaNavGroup,
  tencentNavGroup
} from "./external";
import { exchangeCatalogItems, exchangeNavGroup, exchangeSourceContracts } from "./exchange";
import { tdxCatalogItems, tdxNavGroup, tdxSourceContracts } from "./tdx";

export const sourceContracts: SourceContractSpec[] = [
  ...tdxSourceContracts,
  ...exchangeSourceContracts,
  ...externalSourceContracts
];

const sourceContractById = new Map(sourceContracts.map((contract) => [contract.id, contract]));

export const sourceDirectCatalogItems: CatalogItem[] = [
  ...tdxCatalogItems,
  ...exchangeCatalogItems,
  ...externalCatalogItems
];


export const catalogItems: CatalogItem[] = sourceDirectCatalogItems.map(withCatalogMetadata);
export const emptyCatalogItem: CatalogItem = {
  id: "empty",
  group: "接口目录",
  title: "接口目录为空",
  name: "未注册接口",
  method: "POST",
  path: "/v1/request/{interface}",
  status: "example",
  icon: Code2,
  cadence: "按需添加",
  key: "按接口定义",
  limit: "尚未配置",
  permission: "按接口定义",
  summary: "当前没有预置数据接口。开发者可以按项目数据需求逐个添加接口说明、适配器和采集任务。",
  description: "空接口底座",
  params: [],
  fields: [],
  sdk: `import axdata as ax

client = ax.AxDataClient()
# 已有通达信临时查询接口：
# df = client.call("stock_codes_tdx", scope="all")`,
  curl: `# 可选：网页按钮、curl、非 Python 客户端才需要
curl http://127.0.0.1:8666/v1/request/interfaces`
};

export const navGroups: CatalogGroup[] = [
  tdxNavGroup,
  exchangeNavGroup,
  cninfoNavGroup,
  tencentNavGroup,
  eastmoneyNavGroup,
  sinaNavGroup
];

export const ingestionPlans: Record<string, IngestionPlan> = {
  stock_basic_exchange: {
    id: "stock_basic_exchange",
    task: "stock_basic_exchange.sync",
    schedule: "每天 22:00",
    timezone: "Asia/Shanghai",
    mode: "交易所口径完整列表全量拉取 + diff",
    writePolicy: "raw 每次保存；staging 标准化；core 按口径文件重建",
    output: "data/core/stock_basic_exchange.parquet",
    status: "enabled",
    summary: "按 stock_basic_exchange 接口口径采集股票列表，清洗成 AxData 字段后写入 core 层口径文件。查询端只面对接口名、参数和字段，不暴露内部映射。",
    inputs: [
      ["stock_basic_exchange", "SSE / SZSE / BSE", "data/core/stock_basic_exchange.parquet", "Parquet"],
      ["字段契约", "股票列表字段契约", "instrument_id 为主键", "AxData schema"],
      ["调度窗口", "交易日晚间刷新", "每天 22:00", "Asia/Shanghai"]
    ],
    pipeline: [
      ["raw", "保存本次采集原始文件", "仅供本地追溯和重放"],
      ["staging", "统一字段、编码、日期和交易所后缀", "600000 -> 600000.SH"],
      ["core", "写入 stock_basic_exchange 口径文件", "data/core/stock_basic_exchange.parquet"],
      ["quality", "校验主键、交易所归属、代码后缀、数量下限和快照骤降", "阻断异常写入"]
    ],
    settings: [
      ["enabled", "true", "是否启用任务"],
      ["schedule", "0 22 * * *", "每天 22:00"],
      ["timezone", "Asia/Shanghai", "交易所本地时区"],
      ["interface", "stock_basic_exchange", "接口名就是口径"],
      ["exchanges", "SSE,SZSE,BSE", "覆盖上交所、深交所、北交所"],
      ["output", "data/core/stock_basic_exchange.parquet", "core 层标准文件"]
    ],
    code: `task: stock_basic_exchange.sync
schedule: "0 22 * * *"
timezone: Asia/Shanghai
interface: stock_basic_exchange
params:
  exchanges: [SSE, SZSE, BSE]
write:
  raw: always
  staging: normalize
  core: data/core/stock_basic_exchange.parquet`
  },
};

export const jobs = [
  ["stock_basic_exchange.sync", "股票列表（交易所）同步", "22:00", "Ready"],
  ["market.daily.sync", "日线行情增量同步", "22:00", "Ready"],
  ["market.calendar.refresh", "交易日历刷新", "22:00", "Ready"],
  ["factor.adjustment.rebuild", "复权因子重算", "03:20", "Paused"]
];

export const sdkModes = [
  {
    id: "local",
    title: "本地 SDK",
    badge: "默认",
    icon: Database,
    summary: "Python 库直接读当前电脑的数据目录和已启用插件，不需要先启动后端。",
    facts: [
      ["写法", "client = ax.AxDataClient()"],
      ["使用位置", "本机数据和本机插件"],
      ["适合", "Notebook、回测、因子计算"]
    ]
  },
  {
    id: "api",
    title: "远程 SDK",
    badge: "同一个库",
    icon: ServerCog,
    summary: "Python 库指向一台正在运行 AxData API 的机器，使用服务器上的数据和插件。",
    facts: [
      ["写法", "AxDataClient(api_base=\"http://服务器IP:8666\")"],
      ["使用位置", "服务器数据和服务器插件"],
      ["适合", "多设备共享、服务器、局域网"]
    ]
  },
  {
    id: "cli-http",
    title: "CLI / HTTP API",
    badge: "通道",
    icon: Activity,
    summary: "CLI 适合临时调用和采集控制；HTTP API 适合 Web、其他语言和服务集成。",
    facts: [
      ["CLI", "axdata request / axdata collector"],
      ["HTTP", "POST /v1/request / POST /v1/query"],
      ["插件位置", "本地 CLI 用本机插件；HTTP 用服务端插件"]
    ]
  }
];

export const sectionNav: Array<{ id: ActiveSection; title: string; icon: LucideIcon }> = [
  { id: "manual", title: "开始", icon: BookOpen },
  { id: "interfaces", title: "接口", icon: Code2 },
  { id: "data", title: "数据", icon: Database },
  { id: "tools", title: "采集", icon: Download },
  { id: "plugins", title: "插件", icon: Plug },
  { id: "diagnostics", title: "诊断", icon: Stethoscope },
  { id: "settings", title: "配置", icon: ServerCog }
];

export const sectionMeta: Record<ActiveSection, { title: string; icon: LucideIcon }> = {
  manual: { title: "开始", icon: BookOpen },
  interfaces: { title: "接口", icon: Code2 },
  data: { title: "数据", icon: Database },
  tools: { title: "采集", icon: Download },
  plugins: { title: "插件", icon: Plug },
  diagnostics: { title: "诊断", icon: Stethoscope },
  settings: { title: "配置", icon: ServerCog }
};

export const manualPages: InfoPage[] = [
  {
    id: "quickstart",
    title: "快速开始",
    subtitle: "第一次使用路径",
    icon: BookOpen,
    eyebrow: "开始",
    summary: "AxData 是聚合量化数据库和本地插件容器。下方架构图先把接口、采集、插件、存储和使用入口分开；接口页负责临时查询说明，采集页展示独立采集器任务，数据落到本地文件后再由数据页和 Python SDK 查询。",
    facts: [
      ["AxData 是什么", "聚合量化数据库 + 本地插件容器"],
      ["本机研究模式", "AxDataClient() 读本机数据和本机插件"],
      ["服务器/API 模式", "AxDataClient(api_base=\"http://服务器IP:8666\") 读服务器数据和插件"],
      ["三个对象", "接口查一次；采集写入 Parquet；数据查看已落盘结果"]
    ],
    details: [
      ["1", "看接口", "接口页展示字段、参数、临时调用示例和插件状态"],
      ["2", "运行采集", "采集页选择独立采集器任务，把样本写入本地 Parquet"],
      ["3", "查看数据", "数据页查看数据集、行数、质量状态、输出路径和预览"],
      ["4", "用 SDK 查询", "本地 SDK 不需要后端；远程 SDK 通过 api_base 访问服务器"],
      ["5", "理解插件", "预装插件随 AxData 提供；外部插件通过 pip、editable 或 AXP 安装，manifest 是必需的"],
      ["6", "写新插件", "先看 docs/plugin-development.md；Web 的开始页也有插件开发入口"]
    ],
    code: `import axdata as ax

client = ax.AxDataClient()
df = client.stock_basic_exchange(
    exchange="SSE",
    region="上海市",
    fields=["instrument_id", "name", "company_full_name"],
)

remote = ax.AxDataClient(api_base="http://服务器IP:8666")
same_schema = remote.daily(ts_code="000001.SZ", start_date="20240101")
print(df.head())`
  },
  {
    id: "development-standards",
    title: "开发指南",
    subtitle: "插件、接口与数据边界",
    icon: BookOpen,
    eyebrow: "规范",
    summary: "这份指南说明 AxData 的数据源接口、采集器、数据集声明、Parquet/DuckDB 分工和 Web UI 口径。新增接口、采集器、数据集或页面文案时，可以先用它确认能力边界和质量检查方式。",
    facts: [
      ["数据源接口", "source_request 临时请求源端，默认不入库"],
      ["采集器", "CollectorSpec + runner_entry + task/run/write/quality"],
      ["数据集声明", "描述 dataset、schema、路径、格式和查询方式；不等于本机已有数据"],
      ["存储分工", "Parquet 是事实源；DuckDB 是查询层/查询缓存"]
    ],
    details: [
      ["使用方式", "先确认职责边界，再进入对应专题文档", "避免把接口、采集和查询混在一起"],
      ["适用范围", "数据源、采集器、插件、数据页、接口页、采集页、插件页、开始页", "以当前系统能力为准"],
      ["质量检查", "接口目录、中文文案、真实样例、测试和构建命令", "按本次改动范围选择对应检查"]
    ],
    codeTitle: "验证命令",
    codeLanguage: "powershell",
    code: `npm run lint:web
npm run build:web
.\\.venv\\Scripts\\python -m compileall -q libs\\axdata_core apps\\api packages\\axdata-sdk services scripts tests
.\\.venv\\Scripts\\python -m pytest -q tests\\test_external_sources.py tests\\test_provider_catalog.py tests\\test_builtin_providers.py`,
    manualMode: "markdown",
    markdownDoc: "axdata-development-standards"
  },
  {
    id: "plugin-development",
    title: "插件开发总览",
    subtitle: "先分清接口和采集",
    icon: FileCode2,
    eyebrow: "开始",
    summary: "AxData 插件可以提供数据源接口、采集器、下载兼容能力或后续工具能力。开始开发前先分清：数据源插件负责临时查询接口；采集器插件负责长期落盘任务。",
    facts: [
      ["数据源插件", "进入 ProviderRegistry；展示接口、参数、字段和临时调用"],
      ["采集器插件", "进入 CollectorRegistry；创建任务、调度运行、写本地文件"],
      ["打包安装", "wheel 是真实 Python 包；AXP 是本地安装信封"],
      ["必需文件", "axdata-provider.json 或 axdata-plugin.json"]
    ],
    details: [
      ["1", "只想查一次", "写数据源 Provider，进入接口目录，不默认落盘"],
      ["2", "想长期保存", "写独立 CollectorSpec 和 runner_entry，进入采集页"],
      ["3", "想给别人安装", "构建 wheel，再打成 AXP，让 Web/CLI 可预览和安装"],
      ["4", "遇到不可用", "先看插件页、诊断页和 status_message / next_action"]
    ],
    codeTitle: "常用检查命令",
    codeLanguage: "powershell",
    code: `axdata plugin list --json
axdata plugin info axdata.source.demo --json
axdata plugin collectors --json

# 必需 manifest
axdata-provider.json
axdata-plugin.json`,
    manualMode: "markdown",
    markdownDoc: "plugin-development"
  },
  {
    id: "source-provider-development",
    title: "数据源开发",
    subtitle: "接口、参数、字段、Adapter",
    icon: Plug,
    eyebrow: "开发",
    summary: "数据源插件负责把一个上游数据源接入 AxData 的接口目录。它只负责临时查询，不负责长期采集入库；接口页的目录、中文文案、参数字段、真实样例和参考表都跟插件 / Registry 走。",
    facts: [
      ["注册位置", "ProviderRegistry"],
      ["用户入口", "接口页、SDK call、HTTP /v1/request"],
      ["必需 manifest", "axdata-provider.json"],
      ["核心代码", "provider.py / adapter.py / catalog.py"]
    ],
    details: [
      ["职责", "声明接口、目录、中文文案、参数、字段、样例和参考表，并实现源端请求 Adapter"],
      ["不做", "不创建任务，不写 Parquet，不维护采集进度"],
      ["命名", "provider_id、source_code、interface_name 都要稳定清晰"],
      ["验证", "plugin list、plugin info、/v1/request/interfaces、接口调用 smoke"]
    ],
    code: `# 开发期安装
.\\.venv\\Scripts\\python -m pip install -e C:\\path\\to\\axdata-source-demo
.\\.venv\\Scripts\\axdata plugin list --json
.\\.venv\\Scripts\\axdata plugin enable axdata.source.demo

# 调接口
curl -X POST http://127.0.0.1:8666/v1/request/stock_snapshot_demo \\
  -H "Content-Type: application/json" \\
  -d "{\\"params\\":{\\"code\\":\\"000001.SZ\\"},\\"persist\\":false}"`,
    manualMode: "markdown",
    markdownDoc: "source-provider-development"
  },
  {
    id: "collector-plugin-development",
    title: "采集器开发",
    subtitle: "任务、调度、落盘、质量规则",
    icon: Download,
    eyebrow: "开发",
    summary: "采集器插件负责把数据生产成本地资产。它有独立的 CollectorSpec、runner_entry、dataset_id、资源组和质量规则；采集页内容跟 CollectorRegistry / CollectorSpec 走，不应该挂在接口 Provider 或 Web 静态页面下面。",
    facts: [
      ["注册位置", "CollectorRegistry"],
      ["用户入口", "采集页、collector CLI、调度器"],
      ["必需 manifest", "axdata-plugin.json"],
      ["核心代码", "collectors.py / runner.py"]
    ],
    details: [
      ["职责", "声明采集器页面内容、创建任务、手动采集、交易日定时、写文件、记录 run history"],
      ["不做", "不绕过 AxData 队列，不由插件自行长期开后台线程"],
      ["输出", "声明 dataset_id、格式、路径、写入策略和质量契约"],
      ["验证", "plugin collectors、collector task、run-now、data preview"]
    ],
    code: `# 查看采集器目录
.\\.venv\\Scripts\\axdata plugin collectors --json
curl http://127.0.0.1:8666/v1/plugins/collectors

# 创建并运行任务
.\\.venv\\Scripts\\axdata collector task create demo.stock_snapshot.snapshot --name "示例快照"
.\\.venv\\Scripts\\axdata collector run-now <task_id>`,
    manualMode: "markdown",
    markdownDoc: "collector-plugin-development"
  },
  {
    id: "dataset-duckdb",
    title: "数据集声明与 DuckDB",
    subtitle: "dataset、Parquet、查询缓存",
    icon: Database,
    eyebrow: "开发",
    summary: "数据集声明是采集器和数据页之间的契约。它说明会产出的 dataset、schema、主键、日期字段、分区、写入策略和格式；只有真实落盘后才进入数据页。Parquet 是正式数据文件，DuckDB 只负责查询和可重建缓存。",
    facts: [
      ["dataset_id", "采集产物的稳定 ID"],
      ["Parquet", "默认且必选的长期事实源"],
      ["DuckDB", "查询执行层和可重建查询缓存"],
      ["数据页", "只读已有本地输出的数据，不请求源端"]
    ],
    details: [
      ["声明内容", "layer、table、schema、primary_key、date_field、partition_by、write_mode", "说明采集产物，不把空声明当已入库数据"],
      ["格式边界", "Parquet 主数据；CSV 导出；JSON/JSONL 调试兼容；DuckDB 查询缓存", "删除缓存不删除 Parquet"],
      ["预览边界", "默认读 Parquet，单次有 limit，按日期尽量裁剪文件", "不把 DuckDB 暴露成任意 SQL 编辑器"]
    ],
    code: `dataset_id: daily
layer: core
table: daily
formats: [parquet]
write_mode: upsert_by_key
partition_by: [trade_date]
primary_key: [ts_code, trade_date]
duckdb_cache: optional`,
    manualMode: "markdown",
    markdownDoc: "dataset-and-duckdb"
  },
  {
    id: "ui-standards",
    title: "UI 规范",
    subtitle: "接口、采集、数据、插件、开始页",
    icon: Settings,
    eyebrow: "开发",
    summary: "Web UI 的核心要求是把接口、采集和数据查询三条线分清楚。request 接口页由 Registry runtime catalog 通用渲染，采集页由 CollectorRegistry / CollectorSpec 驱动，数据页查看本地已有数据，插件页区分 Provider、Collector 和 DownloaderProfile。",
    facts: [
      ["接口页", "插件目录、中文文案、参数、字段、真实静态样例、远程 token 说明"],
      ["采集页", "CollectorSpec 内容、基本参数、输入参数、输出参数、任务、进度、日志"],
      ["数据页", "本地数据集、Parquet 预览、质量、删除范围"],
      ["插件页", "Provider / Collector / DownloaderProfile 分开展示"]
    ],
    details: [
      ["开始页", "文档入口", "短入口加详细 Markdown，不做营销页"],
      ["接口页", "回答临时调用", "内容来自插件 / Registry，页面打开不实时请求源端样例"],
      ["采集页", "回答如何保存到本机", "内容来自 CollectorRegistry / CollectorSpec，创建任务后再手动采集或定时采集"],
      ["数据页", "回答本机有什么数据", "删除 dataset 前说明目录和范围"]
    ],
    code: `# UI 术语
数据源开发，不使用旧称
DuckDB 查询缓存，只作可重建查询层
手动采集，不使用旧按钮文案
数据页只列已有本地输出的数据集
数据页预览来自已入库 Parquet`,
    manualMode: "markdown",
    markdownDoc: "ui-standards"
  },
  {
    id: "axp-packaging",
    title: "打包安装",
    subtitle: "wheel、AXP、依赖、卸载",
    icon: FileCode2,
    eyebrow: "开发",
    summary: "wheel 是真正安装的 Python 包，AXP 是给 Web/CLI 预览和安装用的本地信封。AXP 是包，不是能力类型；数据源和采集能力由插件 manifest 声明。",
    facts: [
      ["真实包", "Python wheel + entry point + embedded manifest"],
      ["安装信封", ".axp zip archive"],
      ["能力识别", "按 provider / interfaces / collectors 声明分流"],
      ["默认策略", "离线优先，缺依赖会提示"],
      ["安全边界", "checksum 只检查完整性，不证明安全"]
    ],
    details: [
      ["1", "构建 wheel", "确认 wheel 内包含 axdata-provider.json 或 axdata-plugin.json"],
      ["2", "整理 AXP", "放入 wheels、manifest.json、README、LICENSE、checksums"],
      ["3", "预览安装", "先 axp-preview，检查 source-only、collector-only 或混合能力"],
      ["4", "卸载规则", "卸载插件不删除 data、metadata、任务、run history 或日志"]
    ],
    code: `# 构建 wheel
.\\.venv\\Scripts\\python -m build C:\\path\\to\\axdata-source-demo

# 预览和安装 AXP
.\\.venv\\Scripts\\axdata plugin axp-preview C:\\path\\to\\demo.axp --json
.\\.venv\\Scripts\\axdata plugin axp-install C:\\path\\to\\demo.axp --json
.\\.venv\\Scripts\\axdata plugin axp-install C:\\path\\to\\demo.axp --enable --json`,
    manualMode: "markdown",
    markdownDoc: "axp-packaging-guide"
  },
  {
    id: "plugin-troubleshooting",
    title: "插件排错",
    subtitle: "安装、启用、冲突、诊断",
    icon: Stethoscope,
    eyebrow: "开发",
    summary: "插件不可用时，不要先猜代码。先看插件列表、安装记录、诊断页和 next_action：大多数问题是 manifest 缺失、未启用、依赖缺失、接口冲突或安装来源不支持卸载。",
    facts: [
      ["诊断入口", "axdata doctor / Web 诊断页"],
      ["管理入口", "插件页"],
      ["常见问题", "manifest、依赖、冲突、未启用"],
      ["历史数据", "插件卸载不删除已采集数据"]
    ],
    details: [
      ["manifest 缺失", "entry point 可见但普通列表没有", "检查 wheel package data"],
      ["依赖缺失", "AXP preview 提示 missing dependency", "补 dependency wheel 或允许在线安装"],
      ["接口冲突", "两个 Provider 声明同名接口", "禁用一个、改名或配置 override"],
      ["任务不可跑", "采集器插件禁用/缺失", "重新启用插件或保留任务等待依赖恢复"]
    ],
    code: `.\\.venv\\Scripts\\axdata doctor
.\\.venv\\Scripts\\axdata status
.\\.venv\\Scripts\\axdata plugin list --json
.\\.venv\\Scripts\\axdata plugin installed --json
.\\.venv\\Scripts\\axdata plugin collectors --json`,
    manualMode: "markdown",
    markdownDoc: "plugin-install-management"
  },
  {
    id: "architecture",
    title: "架构说明",
    subtitle: "接口、采集、数据、使用入口",
    icon: Database,
    eyebrow: "开始",
    summary: "AxData 可以按一张结构图理解：上游源先进入数据源 Provider 或采集器 Collector；接口临时查询只返回结果，采集入库才写本地文件；Parquet 是长期事实源，DuckDB 是查询层；本地研究优先用 Python SDK，远程共享走 API。",
    facts: [
      ["接口临时查询", "ProviderRegistry -> Adapter -> 即时返回，默认不入库"],
      ["采集入库", "CollectorRegistry -> Runner -> Writer -> Parquet"],
      ["本地数据", "Parquet 是事实源；DuckDB 只是查询层/查询缓存"],
      ["使用入口", "本地 SDK 直读；远程 SDK/API 访问服务器；Web 只做本机管理"]
    ],
    details: [
      ["1. 数据源", "Provider / Adapter / 本地文件 / 外部服务", "只描述源端能力，不等于采集任务"],
      ["2. 接口路径", "接口页、SDK call、HTTP /v1/request", "临时查一次；不写 raw/staging/core/factor"],
      ["3. 采集路径", "CollectorSpec、runner_entry、任务列表", "手动或定时运行；写 Parquet、run history、日志和质量结果"],
      ["4. 数据层", "data/raw、staging、core、factor + metadata/logs", "文件可追溯，数据页只读已入库数据"],
      ["5. 查询层", "DuckDB / Query API / Data Browser", "DuckDB 可以读 Parquet，缓存坏了可重建"],
      ["6. 用户入口", "Python SDK、HTTP API、CLI、Web", "本地 SDK 不需要后端；远程 SDK/API 使用服务器数据和服务器插件"]
    ],
    code: `上游数据源 / 本地文件
        │
        ├─ 数据源 Provider ── ProviderRegistry ── 源端直取 ── 即时返回
        │                                      └─ 默认不入库
        │
        └─ 采集器 Collector ─ CollectorRegistry ─ Runner ─ Writer / Quality
                                               │
                                               ▼
                              Parquet 主数据 + metadata / logs
                                               │
                                               ▼
                              DuckDB 查询层 / 数据页 / Query API
                                               │
                                               ▼
                              本地 SDK / 远程 SDK / HTTP / CLI / Web`
  },
  {
    id: "lan",
    title: "服务器使用",
    subtitle: "还是用同一个 Python 库",
    icon: Shield,
    eyebrow: "开始",
    summary: "如果数据放在另一台电脑或服务器上，Python 代码还是用 axdata 库，只是在创建 client 时多给一个 API 地址。Web 控制台只在服务端本机管理，远程研究电脑直接用 SDK/API。",
    facts: [
      ["本机写法", "ax.AxDataClient()"],
      ["服务器写法", "ax.AxDataClient(api_base=\"http://服务器地址:8666\")"],
      ["Web 管理", "只在服务端本机打开"],
      ["安全建议", "开放 API 到局域网时启用 token"]
    ],
    details: [
      ["启动 API", "让另一台电脑通过 SDK/API 访问 AxData", "API 默认 8666"],
      ["Python 库", "AxDataClient(api_base=\"http://你的电脑局域网IP:8666\")", "方法名、参数和字段保持不变"],
      ["网页界面", "服务端本机打开 Web 控制台", "不提供远程 Web 入口"],
      ["跨域", "AXDATA_CORS_ORIGINS", "开发自定义前端或反代时配置"],
      ["网络", "只在可信网络开放", "不建议裸露到公网"]
    ],
    code: `$env:AXDATA_API_HOST = "0.0.0.0"
$env:AXDATA_API_PORT = "8666"
npm run dev:api

# 远程研究电脑：
client = ax.AxDataClient(api_base="http://服务器IP:8666", token="axd_...")`
  },
  {
    id: "sdk",
    title: "Python SDK 主入口",
    subtitle: "本机和服务器都是同一种写法",
    icon: Code2,
    eyebrow: "开始",
    summary: "Python SDK 是研究代码面对的主入口。本地 SDK 直接使用本机数据和本机插件；远程 SDK 通过 api_base 访问一台 AxData API 服务，使用服务器上的数据和插件。",
    facts: [
      ["入口", "import axdata as ax"],
      ["本机数据", "ax.AxDataClient()"],
      ["服务器数据", "ax.AxDataClient(api_base=\"http://服务器地址\")"],
      ["CLI", "适合命令行临时调用或采集控制"],
      ["HTTP API", "适合 Web、其他语言和服务集成"],
      ["字段选择", "fields 支持字符串或列表"],
      ["返回形态", "面向 DataFrame 使用"]
    ],
    details: [
      ["本机数据", "默认研究方式", "读取当前电脑已采集入库的数据，或临时请求当前电脑可访问的数据源"],
      ["服务器数据", "多设备共享方式", "只是多传 api_base，后面的 call/query 写法不变"],
      ["实时数据", "以后从 SDK 暴露", "快照/订阅用于实时读取"],
      ["网页界面", "不能直接 import Python 库", "接口页的请求预览会交给后端执行"],
      ["ingest", "入库动作", "拉取源数据并写入 raw -> staging -> core/factor"]
    ],
    code: `import axdata as ax

client = ax.AxDataClient()
stocks = client.stock_basic_exchange(fields=["instrument_id", "name", "region", "company_full_name"])
bars = client.daily(ts_code="000001.SZ", start_date="20240101")`
  }
];

export const settingPages: InfoPage[] = [
  {
    id: "access",
    title: "访问与连接",
    subtitle: "本机、远程访问和 token",
    icon: Settings,
    eyebrow: "配置",
    summary: "Web 控制台默认只在本机管理 AxData。这里用于查看本机连接状态，并给远程 SDK/API 发放和删除访问 token。",
    facts: [
      ["本机", "无需 token"],
      ["远程", "一端一个 token"],
      ["端口", "API 8666 / Web 8667"]
    ],
    details: [
      ["AXDATA_API_HOST", "API 监听地址", "默认 127.0.0.1"],
      ["AXDATA_API_PORT", "API 端口", "默认 8666"],
      ["Web 监听地址", "固定 127.0.0.1", "不提供远程 Web 入口"],
      ["AXDATA_WEB_PORT", "Web 端口", "默认 8667，可自定义"]
    ]
  },
  {
    id: "base_data",
    title: "基础数据",
    subtitle: "交易日历和系统依赖",
    icon: Database,
    eyebrow: "配置",
    summary: "查看和同步 AxData 运行采集任务前需要的基础数据。交易日历用于判断交易日、补采范围和日线类任务依赖。",
    facts: [
      ["交易日历", "采集任务基础依赖"],
      ["一键同步", "默认覆盖当日前后 180 天"],
      ["指定范围", "可补全历史或未来日期"],
      ["本地保存", "写入本地数据目录"]
    ],
    details: [
      ["trade_cal", "交易日历", "日线、复权因子等任务运行前会检查"],
      ["/v1/trade-calendar/cache", "状态接口", "读取本地覆盖范围"],
      ["/v1/trade-calendar/cache/refresh", "同步接口", "刷新或补全指定范围"]
    ]
  },
  {
    id: "tdx_servers",
    title: "通达信连接",
    subtitle: "普通行情与扩展行情服务器",
    icon: ServerCog,
    eyebrow: "数据源连接",
    summary: "",
    facts: [],
    details: []
  }
];

export const manualGroups: SidebarGroup[] = [
  { title: "开始使用", items: manualPages.filter((item) => item.id === "quickstart") },
  {
    title: "开发规范",
    items: manualPages.filter((item) =>
      ["development-standards", "source-provider-development", "collector-plugin-development", "dataset-duckdb", "ui-standards"].includes(item.id)
    )
  },
  {
    title: "插件与安装",
    items: manualPages.filter((item) =>
      ["plugin-development", "axp-packaging", "plugin-troubleshooting"].includes(item.id)
    )
  },
  { title: "系统设计", items: manualPages.filter((item) => ["architecture", "lan"].includes(item.id)) },
  { title: "开发调用", items: manualPages.filter((item) => item.id === "sdk") }
];

export const settingGroups: SidebarGroup[] = [
  { title: "访问", items: settingPages.filter((item) => item.id === "access") },
  { title: "基础数据", items: settingPages.filter((item) => item.id === "base_data") },
  { title: "数据源连接", items: settingPages.filter((item) => item.id === "tdx_servers") }
];

function withCatalogMetadata(item: CatalogItem): CatalogItem {
  const contract = sourceContractById.get(item.id);
  const parts = item.group.split("/").map((part) => part.trim()).filter(Boolean);
  const sourceName = parts[0] ?? "";
  const sourceCode = item.sourceCode ?? staticSourceCode(sourceName);
  const assetClass = item.assetClass ?? staticAssetClass(parts, item.name);
  const category = item.category ?? contract?.group ?? (parts.at(-1) ?? item.group);
  const sourcePath = item.sourcePath ?? staticSourcePath(item.group, sourceName, category, sourceCode);
  return {
    ...item,
    sourcePath,
    sourceCode,
    sourceNameZh: item.sourceNameZh ?? sourceName,
    assetClass,
    category
  };
}

function staticSourcePath(group: string, sourceName: string, category: string, sourceCode: string) {
  if (sourceCode === "tdx") {
    return group;
  }
  return sourceName && category && category !== sourceName
    ? `${sourceName} / ${category}`
    : group;
}

function staticSourceCode(sourceName: string) {
  const sourceMap: Record<string, string> = {
    通达信: "tdx",
    交易所: "exchange",
    巨潮: "cninfo",
    腾讯财经: "tencent",
    东方财富: "eastmoney",
    新浪财经: "sina"
  };
  return sourceMap[sourceName] ?? "";
}

function staticAssetClass(parts: string[], name: string) {
  const assetLabel = parts.find((part) => part.endsWith("数据") && part !== parts[0]) ?? "";
  if (assetLabel.includes("ETF")) return "etf";
  if (assetLabel.includes("指数")) return "index";
  if (assetLabel.includes("期货")) return "future";
  if (assetLabel.includes("期权")) return "option";
  if (assetLabel.includes("基金")) return "fund";
  if (assetLabel.includes("债券")) return "bond";
  if (assetLabel.includes("外汇")) return "fx";
  if (assetLabel.includes("宏观")) return "macro";
  if (name.startsWith("etf_")) return "etf";
  if (name.startsWith("index_")) return "index";
  return "stock";
}
