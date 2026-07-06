import { Activity, BarChart3, Code2, Database, FileText } from "lucide-react";
import type { CatalogGroup, CatalogItem, SourceContractSpec } from "../../types";

export const tdxSourceContracts: SourceContractSpec[] = [
  {
    id: "stock_codes_tdx",
    interfaceName: "stock_codes_tdx",
    title: "最新股票列表",
    group: "基础数据",
    cadence: "现用现查",
    key: "instrument_id",
    summary: "按股票范围临时获取通达信股票列表，可取全部、主板、科创板、CDR、创业板或北交所。",
    params: [
      ["name", "string/list", "否", "股票简称：例如 平安银行、浦发银行"],
      ["code", "string/list", "否", "股票代码：支持 000001、000001.SZ、sz000001"],
      ["scope", "string/list", "否", "股票范围：all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
      ["symbol", "string", "交易所原始六位代码"],
      ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
      ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["market", "string", "按规则识别的板块名称"]
    ]
  },
  {
    id: "stock_suspensions_tdx",
    interfaceName: "stock_suspensions_tdx",
    title: "最新停牌列表",
    group: "基础数据",
    cadence: "现用现查",
    key: "instrument_id",
    summary: "默认扫描通达信全市场股票池，返回当前停牌股票。",
    params: [
      ["scope", "string/list", "否", "股票范围：默认 all 全市场；调试时可传 main、star、chinext、bse、cdr"],
      ["code", "string/list", "否", "调试用股票代码：支持 000001、000001.SZ、sz000001"],
      ["name", "string/list", "否", "调试用股票简称过滤"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码，例如 000004.SZ"],
      ["symbol", "string", "交易所原始六位代码"],
      ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000004"],
      ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["market", "string", "按规则识别的板块名称"]
    ]
  },
  {
    id: "stock_st_list_tdx",
    interfaceName: "stock_st_list_tdx",
    title: "最新ST股票列表",
    group: "基础数据",
    cadence: "现用现查",
    key: "instrument_id",
    summary: "默认扫描通达信全市场股票池，返回当前 ST / *ST 股票。",
    params: [
      ["name", "string/list", "否", "股票简称：例如 平安银行、浦发银行"],
      ["code", "string/list", "否", "股票代码：支持 000001、000001.SZ、sz000001"],
      ["scope", "string/list", "否", "股票范围：all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码，例如 000004.SZ"],
      ["symbol", "string", "交易所原始六位代码"],
      ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000004"],
      ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["market", "string", "按规则识别的板块名称"],
      ["st_type", "string", "识别出的 ST 类型：ST 或 *ST"]
    ]
  }
];

const tdxSourceRequestCallModes = {
  id: "call-modes",
  title: "调用方式对比",
  icon: BarChart3,
  columns: ["调用方式", "后端常驻", "适合场景", "说明"],
  rows: [
    ["本地 SDK：普通 request", "否", "本机脚本、Notebook、偶发查询", "AxDataClient().call(...) 直接在本机请求源端，不启动 API 后端"],
    ["本地 SDK：高频 session", "否", "盘中反复请求实时快照、榜单、盘口", "client.session(source=\"tdx\") 复用本地 provider adapter 和 TDX 长连接池"],
    ["远程 SDK", "是", "数据服务放在服务器或局域网机器上", "AxDataClient(api_base=...) 通过远程 API 调用服务端数据源"],
    ["HTTP 桥接", "是", "网页按钮、curl、非 Python 客户端", "通过 AxData API 服务转发一次性 request"]
  ]
};

const tdxStreamCallModes = {
  id: "stream-call-modes",
  title: "调用方式对比",
  icon: Activity,
  columns: ["调用方式", "后端常驻", "适合场景", "说明"],
  rows: [
    ["本地 SDK stream", "否", "本机脚本、Notebook、实时看盘", "AxDataClient().stream(...) 在本机进程内订阅 TDX，不需要启动 API 后端"],
    ["远程 SDK stream", "是", "服务放在服务器或局域网机器上", "AxDataClient(api_base=...) 继续通过服务端 WebSocket 订阅"],
    ["WebSocket", "是", "网页、桌面端、非 Python 客户端", "直接连接 /v1/stream 通道，按订阅消息接收 snapshot 和 update"]
  ]
};

const dailyShareFields = [
  ["trade_date", "口径日期", "date/string", "盘前股本口径日期"],
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["total_share", "总股本", "number", "总股本，来自财务快照，单位：股"],
  ["float_share", "流通股本", "number", "流通股本，来自财务快照，单位：股"],
  ["free_float_share_z", "流通股本Z", "number", "流通股本Z（自由流通股本口径），来自统计资源，单位：股"],
  ["finance_updated_date", "财务更新日期", "date/string", "财务快照更新日期；不是本次请求时间戳"],
  ["share_source", "字段来源标记", "string", "普通使用可忽略；用于说明这行里的总股本、流通股本、流通股本Z分别有没有取到"]
];

const dailyPriceLimitFields = [
  ["trade_date", "口径日期", "date/string", "涨跌停价格口径日期"],
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["name", "证券简称", "string", "证券简称；用于识别 ST、N、C 等名称标记"],
  ["name_flag", "名称标记", "string", "N、C、ST、*ST；没有识别到时为空"],
  ["pre_close_trade_date", "基准收盘日", "date/string", "实际使用的基准收盘日；不传日期时由交易日历确定，传日期时为日 K 基准日"],
  ["pre_close", "基准收盘价", "number", "单位：元；不传日期时来自实时快照（盘中用昨收，非交易日或收盘后用最近交易日最新价），传日期时来自日 K 收盘价"],
  ["pre_close_source", "基准来源", "string", "tdx_realtime_snapshot 或 tdx_daily_kline"],
  ["limit_up_price", "涨停价", "number", "涨停价，单位：元"],
  ["limit_down_price", "跌停价", "number", "跌停价，单位：元"],
  ["limit_ratio_pct", "涨跌停比例", "number", "百分比数值"],
  ["limit_rule", "计算规则", "string", "main_10pct、st_5pct、chinext_20pct、star_20pct、bse_30pct、ipo_first_day、ipo_first_5_days"],
  ["limit_status", "计算状态", "string", "normal 正常计算；no_price_limit 无涨跌幅限制；missing_pre_close 缺少基准收盘价"]
];

const limitLadderFields = [
  ["trade_date", "天梯日期", "date/string", "这张连板天梯对应的交易日"],
  ["ladder_level", "连板高度", "integer", "当前几连板；封住涨停时按历史连板数加今天计算"],
  ["limit_board_text", "连板状态", "string", "几天几板，例如 7天5板"],
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["name", "证券简称", "string", "证券简称"],
  ["last_price", "最新价", "number", "最新价，单位：元"],
  ["change_pct", "涨跌幅", "number", "当前涨跌幅，百分比数值"],
  ["limit_status", "涨停状态", "string", "sealed 当前封住涨停；touched 盘中触及涨停但当前未封住"],
  ["amount", "成交额", "number", "当前成交额，单位：元"],
  ["seal_amount", "封单额", "number", "当前封单额，单位：元"],
  ["seal_to_amount_ratio", "封成比", "number", "封单额 / 当前成交额"],
  ["free_float_market_value", "流通市值Z", "number", "流通股本Z * 当前价，单位：元"],
  ["primary_theme", "主题材", "string", "过滤噪音题材后，优先按题材内涨停数排序，其次看最高板、连板数和个股关联度，取排序第一的一个题材"],
  ["secondary_themes", "辅助题材", "string", "主题材之后最多三个有效题材，用 + 连接；会过滤持股、指数、宽泛标签类题材"],
  ["year_limit_up_days", "年涨停天数", "integer", "年内涨停天数"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["pre_close", "昨收价", "number", "昨收价，单位：元"],
  ["limit_up_price", "涨停价", "number", "按昨收价和涨跌停规则计算的涨停价，单位：元"]
];

const themeStrengthRankFields = [
  ["rank", "排名", "integer", "题材排行名次"],
  ["trade_date", "排行日期", "date/string", "这张题材强度排行对应的交易日"],
  ["topic_type", "题材类型", "string", "theme 主题题材；sector 板块题材"],
  ["topic_name", "题材名称", "string", "题材名称"],
  ["topic_id", "题材ID", "string", "题材 ID；源端没有给出时为空"],
  ["theme_strength_score", "强度分", "number", "排序用综合分，按涨停数量、最高板和连板股数量计算"],
  ["limit_up_count", "涨停数量", "integer", "题材内当前封住涨停的股票数量"],
  ["highest_ladder_level", "最高板", "integer", "题材内最高连板高度"],
  ["lianban_stock_count", "连板股数量", "integer", "题材内二连板及以上股票数量"],
  ["first_board_count", "首板数量", "integer", "题材内首板股票数量"],
  ["leader_instrument_id", "代表股票代码", "string", "题材内高度最高的代表股票代码"],
  ["leader_name", "代表股票", "string", "题材内高度最高的代表股票简称"],
  ["leader_ladder_level", "代表股票高度", "integer", "代表股票连板高度"],
  ["leader_limit_board_text", "代表股票状态", "string", "代表股票几天几板，例如 7天5板"],
  ["leader_seal_amount", "代表股票封单额", "number", "代表股票当前封单额，单位：元"],
  ["seal_amount_sum", "封单额合计", "number", "题材内涨停股封单额合计，单位：元"],
  ["amount_sum", "成交额合计", "number", "题材内涨停股成交额合计，单位：元"],
  ["top_stock_summary", "代表股票摘要", "string", "题材内代表股票，按连板高度和封单额排序"]
];

export const tdxCatalogItems: CatalogItem[] = tdxSourceContracts.map((contract) => ({
  id: contract.id,
  group: `通达信/股票数据/${contract.group}`,
  title: contract.title,
  name: contract.interfaceName,
  method: "POST",
  path: `/v1/request/${contract.interfaceName}`,
  status: "example",
  icon: contract.group === "行情快照" || contract.group === "K 线" || contract.group === "分时" ? BarChart3 : Database,
  cadence: contract.cadence,
  key: contract.key,
  limit: "不限制",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: contract.summary,
  description:
    contract.id === "stock_suspensions_tdx"
      ? "这个接口默认扫全市场股票池，只返回当前停牌股票；默认不写本地数据。"
      : contract.id === "stock_st_list_tdx"
        ? "这个接口默认扫全市场股票池，只返回当前名称带 ST / *ST 的股票；默认不写本地数据。"
      : "这个接口按调用参数范围返回股票列表：全部、主板、科创板、CDR、创业板或北交所；默认只取股票，不写本地数据。",
  overview: [
    ["接口名称", contract.interfaceName],
    [
      "接口功能",
      contract.id === "stock_suspensions_tdx"
        ? "获取通达信最新停牌列表"
        : contract.id === "stock_st_list_tdx"
          ? "获取通达信最新ST股票列表"
          : "获取通达信最新股票列表"
    ]
  ],
  notice:
    contract.id === "stock_codes_tdx"
      ? "筛选规则：\n沪 sh600/601/603/605\n科创板 sh688\n深 sz000/001/002/003/004/300/301\n北 bj92\nCDR sh689"
      : undefined,
  paramsNote:
    contract.id === "stock_suspensions_tdx"
      ? "不传参数时，默认扫描全市场并返回当前停牌列表。"
      : contract.id === "stock_st_list_tdx"
        ? "不传参数时，默认扫描全市场并返回当前 ST / *ST 股票列表。"
      : "不传参数时，默认获取全量列表。",
  paramsExample:
    contract.id === "stock_suspensions_tdx"
      ? `# 默认扫描全市场当前停牌
client.call("${contract.interfaceName}")

# 调试指定股票
client.call("${contract.interfaceName}", code=["000004.SZ", "600717.SH"])`
      : contract.id === "stock_st_list_tdx"
        ? `# 默认扫描全市场当前 ST / *ST 股票
client.call("${contract.interfaceName}")

# 调试指定股票
client.call("${contract.interfaceName}", code=["000004.SZ", "002102.SZ"])`
      : `# 单个
client.call("${contract.interfaceName}", code="000001.SZ")

# 批量：Python SDK 推荐列表写法
client.call("${contract.interfaceName}", code=["000001.SZ", "600000.SH"])`,
  params: contract.params,
  fields: contract.fields,
  callModes: tdxSourceRequestCallModes,
  sdk: `# 本机请求通达信${contract.id === "stock_suspensions_tdx" ? "最新停牌列表" : contract.id === "stock_st_list_tdx" ? "最新ST股票列表" : "最新股票列表"}
import axdata as ax

client = ax.AxDataClient()
df = client.call("${contract.interfaceName}", scope="all")
print(df)`,
  remoteSdk: `# AxData 服务放在服务器或局域网机器上
import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("${contract.interfaceName}", scope="all")
print(df)`,
  curl: `# 网页按钮、curl、非 Python 客户端使用
curl -X POST "http://127.0.0.1:8666/v1/request/${contract.interfaceName}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"scope":"all"},"persist":false}'`
}));

tdxCatalogItems.push({
  id: "stock_daily_share_tdx",
  group: "通达信/股票数据/基础数据",
  title: "每日股本（盘前）",
  name: "stock_daily_share_tdx",
  method: "POST",
  path: "/v1/request/stock_daily_share_tdx",
  status: "ready",
  icon: Database,
  cadence: "盘前资料，现用现查",
  key: "trade_date,instrument_id",
  limit: "每个标的一行；不传 code 默认全量，内部按 80 只一批请求财务快照",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "返回盘前可用的总股本、流通股本和流通股本Z。",
  description: "这个接口会临时请求财务快照，并读取 AxData 项目缓存里的盘前统计资源。total_share、float_share 来自财务快照；free_float_share_z 和 trade_date 来自盘前统计资源。finance_updated_date 是单只股票财务快照自己的更新日期，不是本次请求时间戳。",
  overview: [
    ["接口名称", "stock_daily_share_tdx"],
    ["接口功能", "获取每日股本（盘前）"]
  ],
  paramsNote: "不传 code 默认返回全量股票；需要限制范围时传 scope，需要单只或多只时再传 code。缓存缺失或当天未刷新时系统会自动更新。",
  paramsExample: `# 全量股票
client.call("stock_daily_share_tdx")

# 主板全量
client.call("stock_daily_share_tdx", scope="main")

# 单个标的
client.call("stock_daily_share_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_daily_share_tdx", code=["000001.SZ", "600000.SH"])

# 强制刷新统计资源后再返回
client.call("stock_daily_share_tdx", code="000001.SZ", refresh_stats=True)`,
  params: [
    ["code", "string/list", "否", "证券代码：不传或传 all 表示全量；也支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["scope", "string/list", "否", "股票范围：code 不传或为 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all"],
    ["refresh_stats", "boolean", "否", "是否强制刷新盘前统计缓存；默认 false"],
    ["stats_cache_root", "string", "否", "盘前统计资源缓存目录；不传时使用项目 cache/tdx/stats"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: dailyShareFields,
  interfaceExamples: [
    {
      id: "daily-share-source-values",
      title: "字段来源标记",
      icon: FileText,
      columns: ["取值", "含义"],
      rows: [
        ["finance_snapshot+tdxstat", "总股本、流通股本、流通股本Z都拿到了"],
        ["finance_snapshot", "只拿到总股本、流通股本"],
        ["tdxstat", "只拿到流通股本Z"],
        ["empty", "没有拿到有效股本字段"]
      ]
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_daily_share_tdx")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_daily_share_tdx")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_daily_share_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"all","scope":"all"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_daily_price_limit_tdx",
  group: "通达信/股票数据/基础数据",
  title: "涨跌停价格",
  name: "stock_daily_price_limit_tdx",
  method: "POST",
  path: "/v1/request/stock_daily_price_limit_tdx",
  status: "ready",
  icon: Database,
  cadence: "现用现查",
  key: "trade_date,instrument_id",
  limit: "每个标的一行；不传 code 默认全量；不传日期走快照昨收，传日期走日 K",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "返回目标交易日的涨停价、跌停价；默认用实时快照昨收快速计算最新全量。",
  description: "这个接口按目标交易日 T 生成涨停价和跌停价。不传 trade_date 时默认返回最新全量，用实时快照作为基准：盘中用快照昨收，非交易日或收盘后用最近交易日最新价，并用交易日历确定目标交易日；传 trade_date 时走历史日 K，用目标日前一根有效日 K 收盘价作为基准。再按主板、创业板、科创板、北交所、ST 和新股名称标记计算。N/C 新股标记返回无涨跌幅限制状态。",
  overview: [
    ["接口名称", "stock_daily_price_limit_tdx"],
    ["接口功能", "获取涨跌停价格"]
  ],
  paramsNote: "不传 code 默认返回全量股票；不传 trade_date 是最新快照口径，速度更快。需要历史固定日期时再传 trade_date，此时会逐只读取日 K。",
  paramsExample: `# 全量股票
client.call("stock_daily_price_limit_tdx")

# 主板全量
client.call("stock_daily_price_limit_tdx", scope="main")

# 单个标的
client.call("stock_daily_price_limit_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_daily_price_limit_tdx", code=["000001.SZ", "688001.SH"])

# 指定历史目标交易日 T
client.call("stock_daily_price_limit_tdx", code="000001.SZ", trade_date="20260617")`,
  params: [
    ["code", "string/list", "否", "证券代码：不传或传 all 表示全量；也支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["scope", "string/list", "否", "股票范围：code 不传或为 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all"],
    ["trade_date", "string", "否", "目标交易日 T，格式 YYYYMMDD 或 YYYY-MM-DD；不传时默认返回最新全量，用实时快照昨收计算；传入时走日 K 历史精确计算"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: dailyPriceLimitFields,
  dataExamples: [
    {
      id: "daily-price-limit-source",
      title: "价格来源",
      icon: FileText,
      columns: ["字段", "含义", "说明"],
      rows: [
        ["pre_close_trade_date", "基准收盘日", "不传日期时由交易日历确定；传日期时为实际使用的日 K 基准日"],
        ["pre_close_source", "基准来源", "不传日期为 tdx_realtime_snapshot；传日期为 tdx_daily_kline"],
        ["limit_status", "计算状态", "normal 正常计算；no_price_limit 表示无涨跌幅限制"]
      ]
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_daily_price_limit_tdx")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_daily_price_limit_tdx")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_daily_price_limit_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"scope":"all"},"persist":false}'`
});

type KlinePeriodSpec = {
  id: string;
  title: string;
  summary: string;
  periodText: string;
  retentionText: string;
  periodParams: string[][];
  defaultArgs: string;
  adjustText: string;
};

const klineFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_time", "datetime/string", "K 线结束时间；秒 K 精确到秒，分钟/自定义分钟精确到分钟，日线及以上为周期结束交易日 15:00:00+08:00"],
  ["period", "string", "周期名称，例如 5s、1m、day、week"],
  ["open", "number", "开盘价"],
  ["high", "number", "最高价"],
  ["low", "number", "最低价"],
  ["close", "number", "收盘价"],
  ["volume", "number", "成交量"],
  ["amount", "number", "成交额"]
];

const secondCycleAdjust = "复权参数：none 不复权，qfq 前复权，hfq 后复权，fixed_qfq 定点前复权；默认 none，秒级复权以实测结果为准。";
const standardCycleAdjust = "复权参数：none 不复权，qfq 前复权，hfq 后复权，fixed_qfq 定点前复权；默认 none。";

const klinePeriodSpecs: KlinePeriodSpec[] = [
  {
    id: "stock_kline_second_tdx",
    title: "秒K线",
    summary: "获取通达信秒级聚合 K 线，默认建议 5 秒；适合短线用户查看极短周期价格节奏。",
    periodText: "秒级 K 线，seconds 可在 1-60 内自定义；默认/推荐 5 秒。",
    retentionText: "3s 8个交易日、4s 10个交易日、5s 12个交易日、10s 24个交易日、15s/30s/60s 28个交易日；以实际服务器和标的返回为准。",
    periodParams: [["seconds", "integer", "否", "聚合秒数：1-60 内可自定义；推荐 3、4、5、10、15、30、60；默认 5"]],
    defaultArgs: `code="000001.SZ", seconds=5`,
    adjustText: secondCycleAdjust
  },
  {
    id: "stock_kline_minute_tdx",
    title: "分钟K线",
    summary: "获取通达信固定分钟 K 线，包括 1、5、15、30、60 分钟。",
    periodText: "固定分钟周期：1m、5m、15m、30m、60m；其他分钟数请使用自定义分钟K线。",
    retentionText: "1m 94个交易日、5m/15m/30m/60m 494个交易日；以实际服务器和标的返回为准。",
    periodParams: [["period", "string", "否", "固定分钟周期：1m、5m、15m、30m、60m；默认 1m。其他分钟数请使用自定义分钟K线"]],
    defaultArgs: `code="000001.SZ", period="1m"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_nminute_tdx",
    title: "自定义分钟K线",
    summary: "获取通达信自定义分钟扩展周期 K 线，例如 10 分钟 K、20 分钟 K。",
    periodText: "自定义分钟扩展周期，例如 10m、20m、120m。",
    retentionText: "minutes=10 覆盖 494个交易日；其他 minutes 以实际服务器和标的返回为准。",
    periodParams: [["minutes", "integer", "是", "聚合分钟数：范围 2-1440；已抽测 2、3、10、20、120、1440 分钟可返回"]],
    defaultArgs: `code="000001.SZ", minutes=10`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_daily_tdx",
    title: "日K线",
    summary: "获取通达信日 K 线，可用于查看不复权、前复权或后复权的最新口径历史行情。",
    periodText: "日 K。",
    retentionText: "上市以来；以实际服务器和标的返回为准。",
    periodParams: [],
    defaultArgs: `code="000001.SZ", adjust="none"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_nday_tdx",
    title: "自定义日K线",
    summary: "获取通达信自定义日扩展周期 K 线，例如 2 日 K、45 日 K。",
    periodText: "自定义日扩展周期，例如 2d、45d。",
    retentionText: "上市以来；其他 days 以实际服务器和标的返回为准。",
    periodParams: [["days", "integer", "是", "聚合日数：范围 2-365；已抽测 2、45、365 日可返回"]],
    defaultArgs: `code="000001.SZ", days=45, adjust="none"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_weekly_tdx",
    title: "周K线",
    summary: "获取通达信周 K 线。",
    periodText: "周 K。",
    retentionText: "上市以来；以实际服务器和标的返回为准。",
    periodParams: [],
    defaultArgs: `code="000001.SZ", adjust="none"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_monthly_tdx",
    title: "月K线",
    summary: "获取通达信月 K 线。",
    periodText: "月 K。",
    retentionText: "上市以来；以实际服务器和标的返回为准。",
    periodParams: [],
    defaultArgs: `code="000001.SZ", adjust="none"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_quarterly_tdx",
    title: "季K线",
    summary: "获取通达信季 K 线。",
    periodText: "季 K。",
    retentionText: "上市以来；以实际服务器和标的返回为准。",
    periodParams: [],
    defaultArgs: `code="000001.SZ", adjust="none"`,
    adjustText: standardCycleAdjust
  },
  {
    id: "stock_kline_yearly_tdx",
    title: "年K线",
    summary: "获取通达信年 K 线。",
    periodText: "年 K。",
    retentionText: "上市以来；以实际服务器和标的返回为准。",
    periodParams: [],
    defaultArgs: `code="000001.SZ", adjust="none"`,
    adjustText: standardCycleAdjust
  }
];

function createKlineCatalogItem(spec: KlinePeriodSpec): CatalogItem {
  const isImplemented = spec.id.startsWith("stock_kline_");
  const implementationLabel = isImplemented ? "" : "设计草案，暂未接入后端";
  const requestPath = isImplemented ? `/v1/request/${spec.id}` : `/docs/tdx/${spec.id}`;
  const params = [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ...spec.periodParams,
    ["adjust", "string", "否", spec.adjustText],
    ["anchor_date", "string", "否", "定点前复权锚点日期，仅 adjust=fixed_qfq 时使用，格式 YYYYMMDD 或 YYYY-MM-DD"]
  ];

  return {
    id: spec.id,
    group: "通达信/股票数据/行情数据",
    title: spec.title,
    name: spec.id,
    method: "POST",
    path: requestPath,
    status: isImplemented ? "ready" : "example",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time,period",
    limit: "默认返回全量历史；批量 code 会逐代码请求后合并，默认最高 8 路并发",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: isImplemented ? spec.summary : `${spec.summary}当前先作为接口目录占位，尚未接入后端。`,
    description: isImplemented
      ? `这个接口拉取${spec.periodText}默认只做现用现查，不涉及入库；批量 code 由后端并发拆分请求后合并。`
      : `这个接口拟拉取${spec.periodText}接口页只负责现用现查，不涉及入库。`,
    overview: [
      ["接口名称", spec.id],
      ["接口功能", klineFunctionText(spec)],
      ["周期类型", spec.periodText],
      ["实测范围", spec.retentionText]
    ],
    paramsExample: `${implementationLabel ? `# ${implementationLabel}\n` : ""}# 单个
client.call("${spec.id}", ${spec.defaultArgs})

# 批量请求多个标的
client.call("${spec.id}", ${klineBatchArgs(spec)})`,
    params,
    fields: klineFields,
    callModes: tdxSourceRequestCallModes,
    sdk: `${implementationLabel ? `# ${implementationLabel}\n` : ""}import axdata as ax

client = ax.AxDataClient()
df = client.call("${spec.id}", ${spec.defaultArgs})
print(df)`,
    remoteSdk: `${implementationLabel ? `# ${implementationLabel}\n` : ""}import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("${spec.id}", ${spec.defaultArgs})
print(df)`,
    curl: `${implementationLabel ? `# ${implementationLabel}\n` : ""}curl -X POST "http://127.0.0.1:8666/v1/request/${spec.id}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":${klineCurlParams(spec)},"persist":false}'`
  };
}

function klineFunctionText(spec: KlinePeriodSpec) {
  if (spec.id === "stock_kline_second_tdx") {
    return "获取通达信秒级聚合 K 线";
  }
  return spec.summary.replace(/。$/, "");
}

function klineBatchArgs(spec: KlinePeriodSpec) {
  return spec.defaultArgs.replace('code="000001.SZ"', 'code=["000001.SZ", "600000.SH"]');
}

function klineCurlParams(spec: KlinePeriodSpec) {
  const params: Record<string, string | number | string[]> = { code: ["000001.SZ", "600000.SH"] };
  if (spec.id === "stock_kline_second_tdx") params.seconds = 5;
  if (spec.id === "stock_kline_minute_tdx") params.period = "1m";
  if (spec.id === "stock_kline_nminute_tdx") params.minutes = 10;
  if (spec.id === "stock_kline_nday_tdx") params.days = 45;
  return JSON.stringify(params);
}

const intradayHistoryFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_date", "date/string", "交易日期，YYYYMMDD"],
  ["trade_time", "datetime/string", "分时点时间"],
  ["minute_index", "integer", "分时点序号，从 0 开始"],
  ["price", "number", "该分钟分时价格"],
  ["volume", "number", "该分钟成交量"],
  ["prev_close", "number", "昨收价"]
];

const intradayRecentHistoryFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_date", "date/string", "交易日期，YYYYMMDD"],
  ["trade_time", "datetime/string", "分时点时间"],
  ["time_label", "time/string", "分时点时间标签，格式 HH:MM"],
  ["minute_index", "integer", "分时点序号，从 0 开始"],
  ["price", "number", "该分钟分时价格"],
  ["avg_price", "number", "该分钟分时均价"],
  ["volume", "number", "该分钟成交量"],
  ["prev_close", "number", "昨收价"],
  ["open_price", "number", "开盘价"]
];

const intradayTodayFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["time_label", "time/string", "分时点时间，由返回顺序映射得到，格式 HH:MM"],
  ["minute_index", "integer", "分时点序号，从 0 开始"],
  ["price", "number", "该分钟分时价格"],
  ["avg_price", "number", "该分钟分时均价"],
  ["volume", "number", "该分钟成交量"]
];

const intradayBuySellStrengthFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["minute_time", "时间", "string", "分时副图横轴时间，格式 HH:MM"],
  ["minute_index", "序号", "integer", "当前分时副图点序号，从 0 开始"],
  ["bid_order", "委买", "number", "买卖力道副图中的委买"],
  ["ask_order", "委卖", "number", "买卖力道副图中的委卖"]
];

const intradayVolumeComparisonFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["minute_time", "时间", "string", "分时副图横轴时间，格式 HH:MM"],
  ["minute_index", "序号", "integer", "当前分时副图点序号，从 0 开始"],
  ["today_volume", "今日成交量", "number", "成交对比副图中的今日累计成交量"],
  ["yesterday_volume", "昨日成交量", "number", "成交对比副图中的昨日同分时点累计成交量"],
  ["volume_change", "变动", "number", "今日成交量减昨日成交量"],
  ["volume_change_pct", "变动比例", "number", "百分比数值；例如 34.44 表示 34.44%"]
];

const orderBookFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["level", "档位", "integer", "盘口档位，1 到 5"],
  ["bid_price", "委买价", "number", "该档委买价"],
  ["bid_volume", "委买量", "integer", "该档委买量，A 股常见口径为手"],
  ["ask_price", "委卖价", "number", "该档委卖价"],
  ["ask_volume", "委卖量", "integer", "该档委卖量，A 股常见口径为手"]
];

const realtimeSnapshotFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["last_price", "最新价", "number", "当前最新价，单位：元"],
  ["pre_close", "昨收价", "number", "上一交易日收盘价，单位：元"],
  ["open", "开盘价", "number", "当日开盘价，单位：元"],
  ["high", "最高价", "number", "当日最高价，单位：元"],
  ["low", "最低价", "number", "当日最低价，单位：元"],
  ["change", "涨跌额", "number", "最新价相对昨收价的涨跌额，单位：元"],
  ["change_pct", "涨跌幅", "number", "百分比数值；例如 1.23 表示上涨 1.23%，-0.85 表示下跌 0.85%"],
  ["open_change_pct", "开盘涨幅", "number", "派生计算：(开盘价 - 昨收价) / 昨收价 * 100"],
  ["high_change_pct", "最高涨幅", "number", "派生计算：(最高价 - 昨收价) / 昨收价 * 100"],
  ["low_change_pct", "最低涨幅", "number", "派生计算：(最低价 - 昨收价) / 昨收价 * 100"],
  ["amplitude_pct", "振幅", "number", "百分比数值；按 (最高价 - 最低价) / 昨收价 * 100 计算"],
  ["average_price", "均价", "number", "派生计算：成交额 / (成交量 * 100)，单位：元"],
  ["average_change_pct", "均涨幅", "number", "派生计算：(均价 - 昨收价) / 昨收价 * 100"],
  ["drawdown_pct", "回头波", "number", "派生计算：(最高价 - 最新价) / 昨收价 * 100"],
  ["attack_pct", "攻击波", "number", "派生计算：(最新价 - 最低价) / 昨收价 * 100"],
  ["volume", "成交量", "integer", "总成交量，单位：手"],
  ["current_volume", "现手", "integer", "最近一笔成交量，单位：手；不是累计成交量"],
  ["amount", "成交额", "number", "成交额，单位：元"],
  ["inside_volume", "内盘", "integer", "内盘成交量，单位：手"],
  ["outside_volume", "外盘", "integer", "外盘成交量，单位：手"],
  ["inside_outside_ratio", "内外比", "number", "派生计算：内盘 / 外盘"],
  ["open_amount", "开盘金额", "number", "开盘金额，单位：元"],
  ["open_amount_ratio_pct", "开盘占比", "number", "派生计算：开盘金额 / 成交额 * 100"],
  ["bid1_price", "买一价", "number", "买一价，单位：元"],
  ["bid1_volume", "买一量", "integer", "买一量，单位：手"],
  ["ask1_price", "卖一价", "number", "卖一价，单位：元"],
  ["ask1_volume", "卖一量", "integer", "卖一量，单位：手"],
  ["locked_amount", "封单额", "number", "按买一价 * 买一量 * 100 计算，单位：元"],
  ["bid1_ask1_volume_diff", "买卖一量差", "integer", "买一量减卖一量，单位：手"],
  ["bid1_ask1_balance_pct", "买卖一量差占比", "number", "按 (买一量 - 卖一量) / (买一量 + 卖一量) * 100 计算"],
  ["rise_speed", "涨速", "number", "百分比数值"],
  ["short_turnover", "短换手", "number", "百分比数值"],
  ["min2_amount", "2分钟金额", "number", "近 2 分钟成交金额，单位：元"],
  ["opening_rush", "开盘抢筹", "number", "百分比数值"],
  ["vol_rise_speed", "量涨速", "number", "百分比数值"],
  ["entrust_ratio", "委比", "number", "百分比数值"],
  ["activity", "活跃度", "integer", "通达信实时快照携带的活跃度数值"]
];

const realtimeRankFields = [
  ["rank", "名次", "integer", "榜单名次，从 1 开始，按当前返回结果顺序连续编号"],
  ...realtimeSnapshotFields
];

const indexCodeFields = [
  ["instrument_id", "统一指数代码", "string", "AxData 统一指数代码，例如 000001.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位指数代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["name", "指数简称", "string", "指数简称"],
  ["index_type", "指数类型", "string", "official_index 常规指数；tdx_block_index 通达信板块/行业/题材指数"],
  ["previous_close", "昨收", "number", "代码表携带的昨收点位"]
];

const indexSnapshotFields = [
  ["instrument_id", "统一指数代码", "string", "AxData 统一指数代码，例如 000001.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位指数代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["last_price", "最新点位", "number", "当前最新点位"],
  ["pre_close", "昨收点位", "number", "上一交易日收盘点位"],
  ["open", "开盘点位", "number", "当日开盘点位"],
  ["high", "最高点位", "number", "当日最高点位"],
  ["low", "最低点位", "number", "当日最低点位"],
  ["change", "涨跌点数", "number", "最新点位相对昨收点位的涨跌点数"],
  ["change_pct", "涨跌幅", "number", "百分比数值；例如 1.23 表示上涨 1.23%"],
  ["open_change_pct", "开盘涨幅", "number", "百分比数值"],
  ["high_change_pct", "最高涨幅", "number", "百分比数值"],
  ["low_change_pct", "最低涨幅", "number", "百分比数值"],
  ["amplitude_pct", "振幅", "number", "百分比数值"],
  ["volume", "成交量", "integer", "指数快照携带的成交量"],
  ["current_volume", "现量", "integer", "指数快照携带的最近成交量"],
  ["amount", "成交额", "number", "指数快照携带的成交额，单位：元"],
  ["open_amount", "开盘金额", "number", "开盘金额，单位：元"],
  ["rise_speed", "涨速", "number", "百分比数值"],
  ["activity", "活跃度", "integer", "通达信实时快照携带的活跃度数值"]
];

const indexRankFields = [
  ["rank", "名次", "integer", "榜单名次，从 1 开始"],
  ...indexSnapshotFields
];

const indexKlineFields = [
  ["instrument_id", "统一指数代码", "string", "AxData 统一指数代码，例如 000001.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位指数代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_time", "K线时间", "datetime/string", "K 线时间"],
  ["period", "周期", "string", "K 线周期"],
  ["open", "开盘点位", "number", "开盘点位"],
  ["high", "最高点位", "number", "最高点位"],
  ["low", "最低点位", "number", "最低点位"],
  ["close", "收盘点位", "number", "收盘点位"],
  ["volume", "成交量", "number", "指数 K 线成交量"],
  ["amount", "成交额", "number", "指数 K 线成交额，单位：元"],
  ["up_count", "上涨家数", "integer", "指数 K 线携带的上涨家数"],
  ["down_count", "下跌家数", "integer", "指数 K 线携带的下跌家数"]
];

const etfSnapshotFields = [
  ["instrument_id", "统一 ETF 代码", "string", "AxData 统一 ETF 代码，例如 510050.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位 ETF 代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh510050"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["last_price", "最新价", "number", "当前最新价，单位：元"],
  ["pre_close", "昨收价", "number", "上一交易日收盘价，单位：元"],
  ["open", "开盘价", "number", "当日开盘价，单位：元"],
  ["high", "最高价", "number", "当日最高价，单位：元"],
  ["low", "最低价", "number", "当日最低价，单位：元"],
  ["change", "涨跌额", "number", "最新价相对昨收价的涨跌额，单位：元"],
  ["change_pct", "涨跌幅", "number", "百分比数值；例如 1.23 表示上涨 1.23%"],
  ["open_change_pct", "开盘涨幅", "number", "百分比数值"],
  ["high_change_pct", "最高涨幅", "number", "百分比数值"],
  ["low_change_pct", "最低涨幅", "number", "百分比数值"],
  ["amplitude_pct", "振幅", "number", "百分比数值"],
  ["volume", "成交量", "integer", "ETF 快照携带的成交量，单位：手"],
  ["current_volume", "现量", "integer", "ETF 快照携带的最近成交量，单位：手"],
  ["amount", "成交额", "number", "成交额，单位：元"],
  ["open_amount", "开盘金额", "number", "开盘金额，单位：元"],
  ["rise_speed", "涨速", "number", "百分比数值"],
  ["activity", "活跃度", "integer", "通达信实时快照携带的活跃度数值"]
];

const etfRankFields = [
  ["rank", "名次", "integer", "榜单名次，从 1 开始"],
  ...etfSnapshotFields
];

const etfKlineFields = [
  ["instrument_id", "统一 ETF 代码", "string", "AxData 统一 ETF 代码，例如 510050.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位 ETF 代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh510050"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_time", "K线时间", "datetime/string", "K 线时间"],
  ["period", "周期", "string", "K 线周期"],
  ["open", "开盘价", "number", "开盘价，单位：元"],
  ["high", "最高价", "number", "最高价，单位：元"],
  ["low", "最低价", "number", "最低价，单位：元"],
  ["close", "收盘价", "number", "收盘价，单位：元"],
  ["volume", "成交量", "number", "ETF K 线成交量，单位：手"],
  ["amount", "成交额", "number", "ETF K 线成交额，单位：元"],
  ["up_count", "上涨家数", "integer", "ETF K 线通常为空"],
  ["down_count", "下跌家数", "integer", "ETF K 线通常为空"]
];

const quoteRefreshStreamFields = [
  ["type", "消息类型", "string", "snapshot、update、heartbeat、status 或 error"],
  ["stream", "订阅接口", "string", "固定为 stock_quote_refresh_tdx"],
  ["request_id", "请求编号", "string", "客户端订阅消息里的 id/request_id，服务端原样带回；可选字段"],
  ["subscription_id", "订阅编号", "string", "服务端返回的订阅编号，用于区分同一连接上的不同订阅"],
  ["server_time", "服务端时间", "datetime/string", "服务端发送消息的时间"],
  ["data", "行情数据", "array", "snapshot/update 消息里的行情行数组；订阅时传 fields 会只返回指定字段"],
  ["status", "状态", "string", "status 消息里返回，例如 unsubscribed"],
  ["error", "错误信息", "object", "error 消息里返回，包含 code、message、details"],
  ["data.instrument_id", "统一证券代码", "string", "data 行字段，AxData 统一证券代码，例如 000001.SZ"],
  ["data.symbol", "原始代码", "string", "data 行字段，交易所原始六位代码"],
  ["data.exchange", "交易所", "string", "data 行字段，AxData 交易所代码：SSE、SZSE、BSE"],
  ["data.trade_time", "行情时间", "time/datetime", "data 行字段，行情更新时间；源端未返回时为空"],
  ["data.last_price", "最新价", "number", "data 行字段，当前最新价，单位：元"],
  ["data.pre_close", "昨收价", "number", "data 行字段，上一交易日收盘价，单位：元"],
  ["data.open", "开盘价", "number", "data 行字段，当日开盘价，单位：元"],
  ["data.high", "最高价", "number", "data 行字段，当日最高价，单位：元"],
  ["data.low", "最低价", "number", "data 行字段，当日最低价，单位：元"],
  ["data.change", "涨跌额", "number", "data 行字段，最新价相对昨收价的涨跌额，单位：元"],
  ["data.change_pct", "涨跌幅", "number", "data 行字段，百分比数值；例如 1.23 表示上涨 1.23%"],
  ["data.volume", "成交量", "integer", "data 行字段，总成交量，单位：手"],
  ["data.current_volume", "现手", "integer", "data 行字段，最近一笔成交量，单位：手"],
  ["data.amount", "成交额", "number", "data 行字段，成交额，单位：元"],
  ["data.inside_volume", "内盘", "integer", "data 行字段，内盘成交量，单位：手"],
  ["data.outside_volume", "外盘", "integer", "data 行字段，外盘成交量，单位：手"],
  ["data.bid1_price", "买一价", "number", "data 行字段，买一价，单位：元"],
  ["data.bid1_volume", "买一量", "integer", "data 行字段，买一量，单位：手"],
  ["data.ask1_price", "卖一价", "number", "data 行字段，卖一价，单位：元"],
  ["data.ask1_volume", "卖一量", "integer", "data 行字段，卖一量，单位：手"]
];

const realtimeRankCategoryRows = [
  ["全部 A 股", "a_share", "默认票池，包含沪深北 A 股范围"],
  ["沪市 A 股", "sse", "上交所 A 股"],
  ["深市 A 股", "szse", "深交所 A 股"],
  ["科创板", "star", "科创板股票"],
  ["创业板", "chinext", "创业板股票"],
  ["北交所", "bse", "北交所股票"]
];

const realtimeRankSortRows = [
  ["涨跌幅", "change_pct", "默认排序，常见涨幅榜"],
  ["最新价", "last_price", "按最新成交价排序"],
  ["成交量", "volume", "按总成交量排序"],
  ["成交额", "amount", "按成交额排序"],
  ["振幅", "amplitude_pct", "按当日振幅排序"],
  ["委比", "entrust_ratio", "按委买委卖比例排序"],
  ["内外比", "inside_outside_ratio", "按内盘/外盘比例排序"],
  ["封成比", "seal_fill_ratio", "封单额相对成交额的比例"],
  ["封单额", "locked_amount", "按当前封单金额排序"],
  ["开盘金额", "open_amount", "按开盘成交金额排序"],
  ["开盘换手", "open_turnover", "按开盘换手相关口径排序"],
  ["量比", "volume_ratio", "按量比排序"],
  ["换手率", "turnover_rate", "按换手率排序"],
  ["流通市值", "float_market_cap", "按流通市值排序"],
  ["总市值", "total_market_cap", "按总市值排序"],
  ["强弱度", "strength", "按强弱度排序"],
  ["涨速", "rise_speed", "按涨速排序"],
  ["活跃度", "activity", "按活跃度排序"],
  ["短换手", "short_turnover", "按短线换手口径排序"],
  ["量涨速", "vol_rise_speed", "按成交量变化速度排序"],
  ["主力净额", "main_net_amount", "按主力净额排序；部分标的可能为空"],
  ["开盘抢筹", "opening_rush", "按开盘抢筹排序"],
  ["2 分钟金额", "min2_amount", "按近 2 分钟成交金额排序"],
  ["开盘涨幅", "open_change_pct", "按开盘相对昨收涨幅排序"],
  ["最高涨幅", "high_change_pct", "按当日最高价相对昨收涨幅排序"],
  ["最低涨幅", "low_change_pct", "按当日最低价相对昨收涨幅排序"],
  ["回头波", "drawdown_pct", "按最高价回落幅度排序"],
  ["攻击波", "attack_pct", "按最低价上攻幅度排序"]
];

const realtimeRankFilterRows = [
  ["排除次新", "exclude_new", "排除未开板次新等新股范围"],
  ["排除科创板", "exclude_kcb", "从结果中排除科创板"],
  ["排除 ST", "exclude_st", "从结果中排除 ST 股票"],
  ["排除创业板", "exclude_cyb", "从结果中排除创业板"],
  ["排除北交所", "exclude_bj", "从结果中排除北交所"]
];

const tradeDetailTodayFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_date", "date/string", "当日成交明细通常为空；历史成交明细返回交易日期，YYYYMMDD"],
  ["trade_time", "time/string", "成交时间，HH:MM"],
  ["trade_datetime", "datetime/string", "当日成交明细通常为空；历史成交明细由 trade_date 和 trade_time 组合得到"],
  ["trade_index", "integer", "成交明细序号，用于保持同一标的返回记录的相对顺序"],
  ["price", "number", "成交价"],
  ["volume", "number", "成交量，A 股常见口径为手"],
  ["order_count", "integer", "成交笔数 / 聚合笔数"],
  ["side", "string", "成交方向：buy、sell、neutral；少数未识别状态会保留原始状态标记，实测为盘后定价成交"]
];

const tradeDetailHistoryFields = [
  ...tradeDetailTodayFields.slice(0, 4),
  ["trade_date", "date/string", "交易日期，YYYYMMDD"],
  tradeDetailTodayFields[5],
  ["trade_datetime", "datetime/string", "成交日期时间，由 trade_date 和 trade_time 组合得到"],
  ...tradeDetailTodayFields.slice(7)
];

const auctionProcessFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["auction_time", "时间", "time/string", "竞价过程时间，格式 HH:MM:SS"],
  ["auction_index", "序号", "integer", "竞价过程记录序号，从 0 开始"],
  ["price", "竞价价格", "number", "竞价价格，单位：元"],
  ["matched_volume", "撮合量", "integer", "撮合量，A 股常见口径为手"],
  ["matched_amount_estimated", "估算撮合金额", "number", "按 竞价价格 * 撮合量 * 100 计算，单位：元"],
  ["unmatched_volume", "未撮合量", "integer", "未撮合量绝对值"],
  ["unmatched_amount_estimated", "估算未撮合金额", "number", "按 竞价价格 * 未撮合量 * 100 计算，单位：元"],
  ["unmatched_direction", "未撮合方向", "integer", "正数为 1，负数为 -1，未撮合量为 0 时为 0"]
];

const auctionResultFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["auction_time", "竞价时间", "time/string", "竞价结果时间，从成交明细中筛选 09:25"],
  ["trade_index", "成交序号", "integer", "09:25 成交明细在源端返回中的序号"],
  ["price", "竞价价格", "number", "竞价结果价格，单位：元"],
  ["volume", "成交量", "number", "竞价结果成交量，A 股常见口径为手"],
  ["amount", "成交额", "number", "按 价格 * 成交量 * 100 计算，单位：元"],
  ["order_count", "成交笔数", "integer", "09:25 成交笔数 / 聚合笔数"]
];

const auctionResultHistoryFields = [
  ...auctionResultFields.slice(0, 4),
  ["trade_date", "交易日期", "date/string", "交易日期，YYYYMMDD；由历史接口 trade_date 参数确定"],
  auctionResultFields[4],
  ["auction_datetime", "竞价日期时间", "datetime/string", "由 trade_date 和 09:25 组合得到"],
  ...auctionResultFields.slice(5)
];

const auctionIndicatorFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["stats_date", "统计日期", "date/string", "本地统计资源对应日期；用于昨日成交额、昨日封单额等历史分母"],
  ["open_price", "开盘价", "number", "开盘价，单位：元"],
  ["pre_close", "昨收价", "number", "昨收价，单位：元"],
  ["open_change_pct", "开盘涨幅", "number", "按 开盘价 / 昨收价 计算的涨跌幅，百分比数值"],
  ["open_amount", "开盘金额", "number", "开盘集合竞价成交金额，单位：元"],
  ["open_volume_hand", "开盘成交量", "number", "按 开盘金额 / 开盘价 / 100 估算，单位：手"],
  ["open_volume_ratio", "开盘量比", "number", "开盘成交量 / 近 5 个完整交易日平均每分钟成交量"],
  ["open_turnover_z", "开盘换手Z", "number", "开盘成交量 / 流通股本Z，百分比数值"],
  ["open_prev_amount_ratio", "开盘昨比", "number", "开盘金额 / 昨成交额 * 100"],
  ["auction_prev_volume_ratio", "竞价昨比", "number", "今日开盘成交量 / 昨开盘成交量"],
  ["opening_rush", "开盘抢筹", "number", "实时快照携带的开盘抢筹数值"],
  ["open_prev_seal_ratio", "开盘昨封比", "number", "开盘金额 / 昨封单额 * 100"],
  ["prev_amount", "昨成交额", "number", "昨日全天成交额，单位：元"],
  ["prev_seal_amount", "昨封单额", "number", "昨日收盘封单额，单位：元；负值通常表示跌停封单"],
  ["prev2_seal_amount", "前封单额", "number", "前一统计日封单额，单位：元"],
  ["prev_open_volume_hand", "昨开盘成交量", "number", "昨日开盘集合竞价成交量，单位：手"],
  ["prev_open_amount", "昨开盘金额", "number", "昨日开盘集合竞价成交金额，单位：元"],
  ["float_shares", "流通股", "number", "普通财务快照口径流通股，单位：股"],
  ["float_market_value", "流通市值", "number", "流通股 * 当前价，单位：元"],
  ["free_float_shares", "流通股本Z", "number", "流通股本Z（TDX 自由流通股本口径），单位：股"],
  ["free_float_market_value", "流通市值Z", "number", "流通股本Z * 当前价，单位：元"],
  ["seal_amount", "封单额", "number", "当前涨停/跌停封单金额，单位：元"],
  ["seal_to_amount_ratio", "封成比", "number", "封单额 / 当前成交额"],
  ["seal_to_float_ratio", "封流比", "number", "封单额 / 流通市值Z * 100"],
  ["seal_prev_ratio", "封昨比", "number", "当前封单额 / 昨封单额"],
  ["limit_stat_days", "统计天数", "integer", "几天几板里的统计天数"],
  ["limit_up_count_in_stat_days", "统计涨停数", "integer", "几天几板里的涨停次数"],
  ["limit_board_text", "几天几板", "string", "由统计天数和统计涨停数组合，例如 7天5板"],
  ["limit_up_streak_days", "连板天数", "integer", "当前连续涨停天数"],
  ["year_limit_up_days", "年涨停天数", "integer", "当年涨停天数"]
];

tdxCatalogItems.push({
  id: "stock_auction_process_tdx",
  group: "通达信/股票数据/竞价数据",
  title: "竞价明细",
  name: "stock_auction_process_tdx",
  method: "POST",
  path: "/v1/request/stock_auction_process_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘前竞价阶段现用现查",
  key: "instrument_id,auction_time",
  limit: "返回单个标的集合竞价阶段的过程明细",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取单只股票集合竞价明细里的价格、撮合量、未撮合量和方向原始值。",
  description: "这个接口用于查看源端返回的集合竞价明细，适合观察开盘集合竞价和收盘集合竞价过程中的价格、撮合量和未撮合量变化。开盘段实测常见覆盖 09:15 到 09:25 前，不包含 09:25 最终开盘成交结果；收盘段实测常见覆盖 14:57 至 15:00 前后。它不能单独替代成交明细接口。",
  overview: [
    ["接口名称", "stock_auction_process_tdx"],
    ["接口功能", "获取集合竞价明细"],
    ["时间范围", "开盘段实测常见覆盖 09:15 至 09:25 前，不包含 09:25 最终开盘成交结果；收盘段实测常见覆盖 14:57 至 15:00 前后"]
  ],
  paramsExample: `# 单个标的
client.call("stock_auction_process_tdx", code="000988.SZ")

# 批量请求多个标的
client.call("stock_auction_process_tdx", code=["000988.SZ", "300308.SZ"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: auctionProcessFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_auction_process_tdx", code="000988.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_auction_process_tdx", code="000988.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_auction_process_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000988.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_auction_result_tdx",
  group: "通达信/股票数据/竞价数据",
  title: "竞价结果",
  name: "stock_auction_result_tdx",
  method: "POST",
  path: "/v1/request/stock_auction_result_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,auction_time",
  limit: "从当日成交明细中筛选 09:25 竞价结果；分页由后端处理",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当日 09:25 开盘竞价结果；来自当日成交明细，不是竞价过程明细。",
  description: "这个接口按股票代码请求当前交易日成交明细，并只保留 09:25 的开盘竞价结果。它返回的是竞价最终成交结果，不是 09:15 到 09:25 之间的过程变化。",
  overview: [
    ["接口名称", "stock_auction_result_tdx"],
    ["接口功能", "获取当日 09:25 开盘竞价结果"],
    ["结果来源", "当日成交明细 0x0FC5 中 09:25 那笔"]
  ],
  paramsExample: `# 单个标的
client.call("stock_auction_result_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_auction_result_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: auctionResultFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_auction_result_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_auction_result_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_auction_result_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_auction_result_history_tdx",
  group: "通达信/股票数据/竞价数据",
  title: "历史竞价结果",
  name: "stock_auction_result_history_tdx",
  method: "POST",
  path: "/v1/request/stock_auction_result_history_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_date,auction_time",
  limit: "从指定交易日成交明细中筛选 09:25 竞价结果；分页由后端处理",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取指定交易日 09:25 开盘竞价结果；来自历史成交明细，不是竞价过程明细。",
  description: "这个接口按股票代码和交易日期请求历史成交明细，并只保留 09:25 的开盘竞价结果。它适合复盘某一天的竞价最终成交价格、成交量和成交额。",
  overview: [
    ["接口名称", "stock_auction_result_history_tdx"],
    ["接口功能", "获取历史 09:25 开盘竞价结果"],
    ["结果来源", "历史成交明细 0x0FC6 中 09:25 那笔"]
  ],
  paramsExample: `# 单个标的
client.call("stock_auction_result_history_tdx", code="000001.SZ", trade_date="20260511")

# 批量请求多个标的
client.call("stock_auction_result_history_tdx", code=["000001.SZ", "600000.SH"], trade_date="20260511")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: auctionResultHistoryFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_auction_result_history_tdx", code="000001.SZ", trade_date="20260511")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_auction_result_history_tdx", code="000001.SZ", trade_date="20260511")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_auction_result_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","trade_date":"20260511"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_shortline_indicators_tdx",
  group: "通达信/股票数据/短线数据",
  title: "短线指标",
  name: "stock_shortline_indicators_tdx",
  method: "POST",
  path: "/v1/request/stock_shortline_indicators_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "instrument_id",
  limit: "每个标的返回一行短线指标；批量 code 会合并返回",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "按股票代码计算开盘金额、开盘量比、开盘换手Z、封成比、封流比、几天几板等短线指标。",
  description: "这个接口会临时请求实时快照、日 K、财务快照，并使用 AxData 项目缓存里的统计资源作为历史分母，返回一行短线指标。它是源端直取和本地计算结果，不写入本地数据层。",
  overview: [
    ["接口名称", "stock_shortline_indicators_tdx"],
    ["接口功能", "计算短线指标"],
    ["数据来源", "实时快照、日 K、财务快照、本地统计资源"],
  ],
  paramsNote: "默认不用管这些缓存参数；系统会使用 AxData 项目缓存，缓存缺失或当天未刷新时自动从源端刷新。只有想强制刷新或改缓存目录时才需要传下面的可选参数。",
  paramsExample: `# 单个标的
client.call("stock_shortline_indicators_tdx", code="002971.SZ")

# 批量请求多个标的
client.call("stock_shortline_indicators_tdx", code=["002971.SZ", "000001.SZ"])

# 强制刷新统计资源后再计算
client.call("stock_shortline_indicators_tdx", code="002971.SZ", refresh_stats=True)

# 指定自动下载统计资源的缓存目录
client.call("stock_shortline_indicators_tdx", code="002971.SZ", stats_cache_root=r"D:\\axdata-cache\\tdx\\stats")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["refresh_stats", "boolean", "否", "是否强制从源端刷新 AxData 项目缓存里的统计资源；默认 false"],
    ["stats_cache_root", "string", "否", "自动下载统计资源的缓存目录；不传时使用项目 cache/tdx/stats"],
    ["stats_root", "string", "否", "可选覆盖路径；可传包含 tdxstat.cfg/tdxstat2.cfg 的目录，或直接传 zhb.zip 文件路径"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: auctionIndicatorFields,
  dataExamples: [
    {
      id: "auction-indicator-formulas",
      title: "核心计算口径",
      icon: FileText,
      note: "这些指标是源端字段和本地统计分母组合计算出来的，不是单个原始字段直接照搬。",
      columns: ["指标", "计算公式", "说明"],
      rows: [
        ["开盘量比", "今日开盘成交量 / 近 5 个完整交易日平均每分钟成交量", "近 5 日成交量来自日 K"],
        ["开盘换手Z", "今日开盘成交量 / 流通股本Z * 100", "流通股本Z使用本地统计资源口径"],
        ["开盘昨比", "今日开盘金额 / 昨成交额 * 100", "昨成交额来自本地统计资源"],
        ["竞价昨比", "今日开盘成交量 / 昨开盘成交量", "昨开盘成交量来自本地统计资源"],
        ["开盘昨封比", "今日开盘金额 / 昨封单额 * 100", "昨封单额来自本地统计资源"],
        ["封成比", "当前封单额 / 当前成交额", "当前成交额来自实时快照"],
        ["封流比", "当前封单额 / 流通市值Z * 100", "流通市值Z按流通股本Z和当前价计算"],
        ["封昨比", "当前封单额 / 昨封单额", "昨封单额来自本地统计资源"]
      ]
    },
    {
      id: "auction-indicator-inputs",
      title: "数据来源",
      icon: Database,
      columns: ["来源", "提供字段", "说明"],
      rows: [
        ["实时快照", "开盘价、昨收价、当前价、当前成交额、开盘金额、封单额、开盘抢筹", "用于当前竞价状态和封单相关指标"],
        ["日 K", "近 5 个完整交易日成交量", "用于开盘量比分母"],
        ["财务快照", "普通流通股", "用于普通流通股和流通市值展示"],
        ["本地统计资源", "昨成交额、昨封单额、前封单额、昨开盘量、昨开盘金额、流通股本Z、连板统计", "用于竞价历史分母和涨停统计"]
      ]
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_shortline_indicators_tdx", code="002971.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_shortline_indicators_tdx", code="002971.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_shortline_indicators_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"002971.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_quote_refresh_tdx",
  group: "通达信/股票数据/实时数据",
  title: "实时增量行情",
  name: "stock_quote_refresh_tdx",
  method: "WS",
  path: "/v1/stream/stock_quote_refresh_tdx",
  status: "ready",
  icon: Activity,
  cadence: "盘中长连接订阅",
  key: "instrument_id",
  limit: "默认先发当前快照，再持续推送有变化标的的最新行情",
  permission: "本机自用可直接订阅；开放给局域网时再配置 token",
  summary: "通过本地 SDK stream 或远程 WebSocket 订阅股票实时增量行情；本地 Python 不需要启动 API 后端。",
  description: "这个接口用于持续接收关注股票的最新行情变化。订阅建立后先返回一批当前快照，之后推送有变化标的的最新状态；没有变化时 data 为空。它不是普通一次性请求，也不会默认写入本地数据。",
  overview: [
    ["接口名称", "stock_quote_refresh_tdx"],
    ["接口功能", "订阅股票实时增量行情"],
    ["调用方式", "本地 SDK stream / 远程 SDK stream / WebSocket"],
    ["当前状态", "已接入 WebSocket、SDK 长连接和行情增量源"],
  ],
  paramsExample: `# 本地 SDK stream：不需要启动 API 后端
client = ax.AxDataClient()

with client.stream(
    "stock_quote_refresh_tdx",
    code=["000001.SZ", "600000.SH"],
    interval_ms=3000,
) as stream:
    for event in stream:
        print(event.type, event.data)`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001.SZ、600000.SH；批量传数组，单次最多 100 只"],
    ["fields", "string/list", "否", "可选返回字段；不传时返回默认实时行情字段"],
    ["interval_ms", "integer", "否", "刷新间隔，默认 3000 毫秒，最小 500 毫秒"],
    ["initial_snapshot", "boolean", "否", "订阅后是否先返回当前快照，默认 true"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: quoteRefreshStreamFields,
  callModes: tdxStreamCallModes,
  dataExamples: [
    {
      id: "quote-refresh-message-types",
      title: "消息类型",
      icon: Activity,
      note: "客户端按 type 判断消息用途；行情行放在 data 里。",
      columns: ["type", "含义", "说明"],
      rows: [
        ["subscribed", "订阅确认", "服务端确认订阅参数和订阅编号"],
        ["snapshot", "初始快照", "订阅建立后返回当前最新行情"],
        ["update", "增量更新", "后续只推送有变化的标的最新状态"],
        ["heartbeat", "心跳响应", "客户端发送 ping 或 heartbeat 时返回"],
        ["status", "状态变化", "取消订阅、关闭等状态"],
        ["error", "错误", "参数错误、源端不可用或权限问题"]
      ]
    },
    {
      id: "quote-refresh-subscribe-example",
      title: "订阅消息示例",
      icon: Code2,
      note: "WebSocket 连接建立后，客户端发送这一条 JSON 消息开始订阅。",
      columns: ["位置", "示例", "说明"],
      rows: [
        ["连接地址", "ws://127.0.0.1:8666/v1/stream/stock_quote_refresh_tdx", "本机 API 服务地址；有 token 时可在查询参数里带 token"],
        ["op", "subscribe", "订阅动作"],
        ["params.code", "[\"000001.SZ\", \"600000.SH\"]", "订阅标的列表"],
        ["params.fields", "[\"instrument_id\", \"last_price\", \"change_pct\", \"volume\", \"amount\"]", "可选字段列表"],
        ["params.interval_ms", "3000", "刷新间隔，单位毫秒"],
        ["params.initial_snapshot", "true", "订阅后先返回当前快照"]
      ]
    },
    {
      id: "quote-refresh-response-example",
      title: "返回消息示例",
      icon: Activity,
      note: "一条 WebSocket 消息就是一个 JSON 对象；行情数据放在 data 数组里。",
      columns: ["type", "示例内容", "说明"],
      rows: [
        ["subscribed", "{\"type\":\"subscribed\",\"stream\":\"stock_quote_refresh_tdx\",\"subscription_id\":\"sub_xxx\"}", "订阅确认"],
        ["snapshot", "{\"type\":\"snapshot\",\"data\":[{\"instrument_id\":\"000001.SZ\",\"last_price\":10.14,\"change_pct\":-1.36}]}", "初始快照"],
        ["update", "{\"type\":\"update\",\"data\":[{\"instrument_id\":\"000001.SZ\",\"last_price\":10.15,\"change_pct\":-1.26}]}", "后续刷新"],
        ["update", "{\"type\":\"update\",\"data\":[]}", "没有增量变化时仍返回空数组"],
        ["heartbeat", "{\"type\":\"heartbeat\",\"data\":{\"active\":true}}", "客户端主动 ping/heartbeat 时返回"]
      ]
    }
  ],
  sdk: `import axdata as ax

client = ax.AxDataClient()

with client.stream(
    "stock_quote_refresh_tdx",
    code=["000001.SZ", "600000.SH"],
    fields=["instrument_id", "last_price", "change_pct", "volume", "amount"],
    interval_ms=3000,
) as stream:
    for event in stream:
        if event.type in {"snapshot", "update"}:
            print(event.data)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")

with client.stream("stock_quote_refresh_tdx", code=["000001.SZ", "600000.SH"]) as stream:
    for event in stream:
        print(event.type, event.data)`,
  curl: `# WebSocket 地址
ws://127.0.0.1:8666/v1/stream/stock_quote_refresh_tdx

# 连接后发送订阅消息
{
  "op": "subscribe",
  "params": {
    "code": ["000001.SZ", "600000.SH"],
    "fields": ["instrument_id", "last_price", "change_pct", "volume", "amount"],
    "interval_ms": 3000,
    "initial_snapshot": true
  }
}

# 服务端会返回类似消息
{
  "type": "snapshot",
  "stream": "stock_quote_refresh_tdx",
  "subscription_id": "sub_xxx",
  "data": [
    {
      "instrument_id": "000001.SZ",
      "last_price": 10.14,
      "change_pct": -1.36,
      "volume": 1000,
      "amount": 1014000
    }
  ]
}`
});

tdxCatalogItems.push({
  id: "stock_limit_ladder_tdx",
  group: "通达信/股票数据/短线数据",
  title: "连板天梯",
  name: "stock_limit_ladder_tdx",
  method: "POST",
  path: "/v1/request/stock_limit_ladder_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "trade_date,ladder_level,instrument_id",
  limit: "默认返回主板完整连板天梯；传 count 可只取前 N 条",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前连板天梯，默认返回主板完整天梯，返回连板高度、连板状态、封单额、流通市值Z、主题材和辅助题材。",
  description: "这个接口用于短线看盘：后端实时扫描当前 A 股涨幅榜，按涨跌停规则判断封板状态，再结合盘前统计资源计算连板高度、几天几板和年涨停天数。默认只统计主板，ST / *ST 不纳入连板天梯和题材涨停数量统计；需要创业板、科创板、北交所等范围时传 scope。默认返回完整天梯；只想取前 N 条时再传 count。题材会先过滤持股、指数、定增、宽泛标签等噪音项，再优先按题材内涨停数排序，其次看最高板、连板数和个股关联度，主题材取一个，辅助题材最多取三个。",
  overview: [
    ["接口名称", "stock_limit_ladder_tdx"],
    ["接口功能", "获取当前连板天梯"]
  ],
  paramsExample: `# 主板完整连板天梯
client.call("stock_limit_ladder_tdx")

# 全市场完整连板天梯
client.call("stock_limit_ladder_tdx", scope="all")

# 同时包含触及涨停但当前未封住的股票
client.call("stock_limit_ladder_tdx", include_touched=True)

# 只取前 20 条
client.call("stock_limit_ladder_tdx", count=20)`,
  params: [
    ["count", "integer/string", "否", "返回数量；默认 all 返回完整天梯，也可传数字只返回前 N 条，最大 500"],
    ["scope", "string/list", "否", "股票范围；默认 main 主板；可传 all、star、chinext、bse、cdr"],
    ["include_touched", "boolean", "否", "是否包含盘中触及涨停但当前未封住的股票；默认 false"],
    ["topic_type", "string", "否", "题材类型：theme 主题题材，sector 板块题材；默认 theme"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: limitLadderFields,
  dataExamples: [
    {
      id: "limit-ladder-status-values",
      title: "涨停状态",
      icon: FileText,
      columns: ["状态", "含义", "说明"],
      rows: [
        ["sealed", "当前封住涨停", "最新价在涨停价，且买一/封单能确认仍封住"],
        ["touched", "触及涨停但未封住", "盘中最高价到过涨停价，但当前没有按封住涨停处理"]
      ]
    },
    {
      id: "limit-ladder-theme-sort",
      title: "题材排序",
      icon: BarChart3,
      columns: ["字段", "含义", "说明"],
      rows: [
        ["primary_theme", "主题材", "过滤噪音题材后，优先按题材内涨停数排序，其次看最高板、连板数和个股关联度，取排序第一的题材"],
        ["secondary_themes", "辅助题材", "主题材之后最多三个题材，用 + 连接"],
        ["过滤项", "不适合作为短线题材的标签", "例如持股、指数成分、定增、融资融券、财报等宽泛或属性类标签"],
        ["题材强度", "题材统计指标", "涨停数量、最高板、连板股数量等详细指标请看题材强度排行接口"]
      ]
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_limit_ladder_tdx")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_limit_ladder_tdx")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_limit_ladder_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"scope":"main"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_theme_strength_rank_tdx",
  group: "通达信/股票数据/短线数据",
  title: "题材强度排行",
  name: "stock_theme_strength_rank_tdx",
  method: "POST",
  path: "/v1/request/stock_theme_strength_rank_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "trade_date,rank,topic_name",
  limit: "默认返回完整题材排行；传 count 可只取前 N 条",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "按当前涨停池统计题材强度，返回涨停数量、最高板、连板股数量、封单额合计和代表股票。",
  description: "这个接口用于看当前短线题材强弱：后端复用连板天梯的涨停池口径，默认只统计主板、当前封住涨停的股票，并剔除 ST / *ST。题材强度优先看涨停数量，再看最高板、连板股数量和封单额合计。默认返回完整排行；只想取前 N 条时再传 count。",
  overview: [
    ["接口名称", "stock_theme_strength_rank_tdx"],
    ["接口功能", "获取当前题材强度排行"]
  ],
  paramsExample: `# 主板完整题材强度排行
client.call("stock_theme_strength_rank_tdx")

# 全市场完整题材强度排行
client.call("stock_theme_strength_rank_tdx", scope="all")

# 只取前 20 个题材
client.call("stock_theme_strength_rank_tdx", count=20)`,
  params: [
    ["count", "integer/string", "否", "返回数量；默认 all 返回完整题材排行，也可传数字只返回前 N 条，最大 500"],
    ["scope", "string/list", "否", "股票范围；默认 main 主板；可传 all、star、chinext、bse、cdr"],
    ["topic_type", "string", "否", "题材类型：theme 主题题材，sector 板块题材；默认 theme"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: themeStrengthRankFields,
  dataExamples: [
    {
      id: "theme-strength-sort",
      title: "排序口径",
      icon: BarChart3,
      columns: ["指标", "含义", "说明"],
      rows: [
        ["涨停数量", "题材内当前封住涨停的股票数", "只统计涨停池，ST / *ST 不纳入统计"],
        ["最高板", "题材内最高连板高度", "用于识别题材高度"],
        ["连板股数量", "题材内二连板及以上股票数", "不是连板高度，是股票数量"],
        ["强度分", "排序用综合分", "用于稳定排序；实际阅读时优先看涨停数量、最高板和连板股数量"]
      ]
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_theme_strength_rank_tdx")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_theme_strength_rank_tdx")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_theme_strength_rank_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"scope":"main"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_realtime_rank_tdx",
  group: "通达信/股票数据/实时数据",
  title: "实时榜单",
  name: "stock_realtime_rank_tdx",
  method: "POST",
  path: "/v1/request/stock_realtime_rank_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "rank,instrument_id",
  limit: '默认返回前 80 条；count="all" 时取完整当前榜单',
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前实时榜单，支持按 A 股、板块或市场范围排序取数。",
  description: '这个接口不是按代码查询，而是按榜单范围、排序字段和返回数量请求行情。默认返回前 80 条；count="all" 时后端会自动取完整当前榜单。返回字段与实时快照保持一致，并额外返回名次；盘口只包含买一卖一，完整五档继续使用五档盘口接口。',
  overview: [
    ["接口名称", "stock_realtime_rank_tdx"],
    ["接口功能", "获取当前实时榜单"],
    ["默认范围", "A 股"],
    ["默认排序", "涨跌幅降序"]
  ],
  paramsExample: `# A 股涨幅榜前 80 条
client.call("stock_realtime_rank_tdx", category="a_share", sort="change_pct", count=80)

# 成交额榜，排除 ST
client.call("stock_realtime_rank_tdx", sort="amount", filters=["exclude_st"], count=50)

# 取完整当前榜单
client.call("stock_realtime_rank_tdx", category="a_share", sort="change_pct", count="all")`,
  params: [
    ["category", "string/integer", "否", "股票榜单范围，默认全部 A 股；可用值见下方“榜单范围对照”"],
    ["sort", "string/integer", "否", "排序字段，默认涨跌幅；可用值见下方“排序字段对照”"],
    ["count", "integer/string", "否", '返回数量，默认 80；传 "all" 表示取完整当前榜单'],
    ["ascending", "boolean", "否", "是否升序；默认 false，表示按排序字段降序；升序为 true"],
    ["filters", "string/list/integer", "否", "可选排除条件；可用值见下方“过滤条件对照”"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: realtimeRankFields,
  dataExamples: [
    {
      id: "realtime-rank-category-values",
      title: "榜单范围对照",
      icon: Database,
      note: "category 决定从哪个股票票池里取数据；这里是股票数据接口，只展示股票相关范围。",
      columns: ["中文名称", "参数值", "说明"],
      rows: realtimeRankCategoryRows
    },
    {
      id: "realtime-rank-sort-values",
      title: "排序字段对照",
      icon: BarChart3,
      note: "sort 决定榜单按哪个指标排序；默认按涨跌幅降序。",
      columns: ["中文名称", "参数值", "说明"],
      rows: realtimeRankSortRows
    },
    {
      id: "realtime-rank-filter-values",
      title: "过滤条件对照",
      icon: FileText,
      note: "filters 用来排除某些股票范围；多个条件可以用列表传入。",
      columns: ["中文名称", "参数值", "说明"],
      rows: realtimeRankFilterRows
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_realtime_rank_tdx", category="a_share", sort="change_pct", count=80)
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_realtime_rank_tdx", sort="amount", count="all")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_realtime_rank_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"category":"a_share","sort":"change_pct","count":80},"persist":false}'`
});

const indexCatalogItems: CatalogItem[] = [
  {
    id: "index_codes_tdx",
    group: "通达信/指数数据/基础数据",
    title: "指数列表",
    name: "index_codes_tdx",
    method: "POST",
    path: "/v1/request/index_codes_tdx",
    status: "ready",
    icon: Database,
    cadence: "现用现查",
    key: "instrument_id",
    limit: "默认返回常规指数；需要通达信板块/行业/题材指数时传 include_tdx_block_index=true",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取通达信代码表里的指数列表，默认只返回常规指数。",
    description: "这个接口和最新股票列表同源，都是从代码总表里筛选。股票列表只筛股票，指数列表只筛指数。",
    overview: [
      ["接口名称", "index_codes_tdx"],
      ["接口功能", "获取指数列表"],
      ["默认范围", "常规指数"],
      ["可选范围", "include_tdx_block_index=true 时包含通达信板块/行业/题材指数"]
    ],
    paramsExample: `# 常规指数列表
client.call("index_codes_tdx")

# 指定几个指数
client.call("index_codes_tdx", code=["000001.SH", "399001.SZ", "899050.BJ"])

# 包含通达信板块/行业/题材指数
client.call("index_codes_tdx", include_tdx_block_index=True)`,
    params: [
      ["name", "string/list", "否", "指数简称过滤，例如 上证指数、沪深300"],
      ["code", "string/list", "否", "指数代码：支持 000001.SH、399001.SZ、sh000001"],
      ["exchange", "string/list", "否", "交易所过滤：all 全部、SSE 上交所、SZSE 深交所、BSE 北交所；默认 all"],
      ["include_tdx_block_index", "boolean", "否", "是否包含通达信板块/行业/题材指数；默认 false"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: indexCodeFields,
    dataExamples: [
      {
        id: "index-codes-real",
        title: "返回结果示例",
        icon: Database,
        columns: ["instrument_id", "symbol", "tdx_code", "exchange", "name", "index_type", "previous_close"],
        rows: [
          ["000001.SH", "000001", "sh000001", "SSE", "上证指数", "official_index", "4108.0762"],
          ["399001.SZ", "399001", "sz399001", "SZSE", "深证成指", "official_index", "15880.9512"],
          ["899050.BJ", "899050", "bj899050", "BSE", "北证50", "official_index", "1280.246"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_codes_tdx", code=["000001.SH", "399001.SZ", "899050.BJ"])
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("index_codes_tdx")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_codes_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":["000001.SH","399001.SZ","899050.BJ"]},"persist":false}'`
  },
  {
    id: "index_realtime_snapshot_tdx",
    group: "通达信/指数数据/实时数据",
    title: "指数实时快照",
    name: "index_realtime_snapshot_tdx",
    method: "POST",
    path: "/v1/request/index_realtime_snapshot_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "盘中现用现查",
    key: "instrument_id",
    limit: "每个指数返回一行当前快照；批量 code 会合并返回",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取指数当前快照，返回点位、涨跌幅、成交量和成交额。",
    description: "这个接口按指数代码请求当前快照。指数没有真实五档盘口，所以这里只返回指数有意义的行情字段。",
    overview: [
      ["接口名称", "index_realtime_snapshot_tdx"],
      ["接口功能", "获取指数实时快照"]
    ],
    paramsExample: `# 单个指数
client.call("index_realtime_snapshot_tdx", code="000001.SH")

# 批量请求多个指数
client.call("index_realtime_snapshot_tdx", code=["000001.SH", "399001.SZ", "899050.BJ"])`,
    params: [["code", "string/list", "是", "指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传数组或英文逗号分隔字符串"]],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: indexSnapshotFields,
    dataExamples: [
      {
        id: "index-snapshot-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "last_price", "pre_close", "open", "high", "low", "change_pct", "volume", "amount"],
        rows: [
          ["000001.SH", "4092.76", "4108.08", "4094.23", "4117.45", "4080.29", "-0.3729", "428544019", "1003780374528"],
          ["399001.SZ", "15970.86", "15880.95", "15826.79", "16075.6", "15825.32", "0.5662", "504870820", "1132737855488"],
          ["899050.BJ", "1268.39", "1280.25", "1275.57", "1278.96", "1258.41", "-0.9264", "5108289", "14103057408"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_realtime_snapshot_tdx", code=["000001.SH", "399001.SZ"])
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("index_realtime_snapshot_tdx", code="000001.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_realtime_snapshot_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":["000001.SH","399001.SZ"]},"persist":false}'`
  },
  {
    id: "index_realtime_rank_tdx",
    group: "通达信/指数数据/实时数据",
    title: "指数实时榜单",
    name: "index_realtime_rank_tdx",
    method: "POST",
    path: "/v1/request/index_realtime_rank_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "盘中现用现查",
    key: "rank,instrument_id",
    limit: "默认返回前 80 条",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取当前指数榜单，可按涨跌幅、成交额等排序。",
    description: "这个接口是指数榜单，不是完整指数列表。完整目录请用指数列表。",
    overview: [
      ["接口名称", "index_realtime_rank_tdx"],
      ["接口功能", "获取指数实时榜单"],
      ["默认排序", "涨跌幅降序"]
    ],
    paramsExample: `# 指数涨幅榜前 80 条
client.call("index_realtime_rank_tdx", sort="change_pct", count=80)

# 指数成交额榜
client.call("index_realtime_rank_tdx", sort="amount", count=50)`,
    params: [
      ["sort", "string/integer", "否", "排序字段，默认涨跌幅；常用 change_pct、amount、volume、rise_speed"],
      ["start", "integer", "否", "高级分页起点，从 0 开始；一般不用传"],
      ["count", "integer", "否", "返回前多少条，默认 80"],
      ["ascending", "boolean", "否", "是否升序；默认 false，表示按排序字段降序；升序为 true"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: indexRankFields,
    dataExamples: [
      {
        id: "index-rank-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["rank", "instrument_id", "last_price", "change_pct", "amount"],
        rows: [
          ["1", "399363.SZ", "16048.85", "4.1884", "295172800512"],
          ["2", "000682.SH", "3112.72", "3.8855", "150859415552"],
          ["3", "000685.SH", "4589.6", "3.7723", "153039339520"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_realtime_rank_tdx", sort="change_pct", count=80)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("index_realtime_rank_tdx", sort="amount", count=50)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_realtime_rank_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"sort":"change_pct","count":80},"persist":false}'`
  },
  {
    id: "index_quote_refresh_tdx",
    group: "通达信/指数数据/实时数据",
    title: "指数实时增量行情",
    name: "index_quote_refresh_tdx",
    method: "POST",
    path: "/v1/request/index_quote_refresh_tdx",
    status: "ready",
    icon: Activity,
    cadence: "盘中现用现查",
    key: "instrument_id",
    limit: "每次请求返回一次刷新快照；后续可包装成长连接订阅",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "请求一次指数行情刷新数据。",
    description: "这是请求式的指数刷新接口，适合后续包装成指数实时订阅；普通页面展示用指数实时快照也可以。",
    overview: [
      ["接口名称", "index_quote_refresh_tdx"],
      ["接口功能", "获取一次指数实时刷新行情"]
    ],
    paramsExample: `client.call("index_quote_refresh_tdx", code=["000001.SH", "000300.SH"])`,
    params: [["code", "string/list", "是", "指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传数组或英文逗号分隔字符串"]],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: indexSnapshotFields,
    dataExamples: [
      {
        id: "index-refresh-real",
        title: "返回结果示例",
        icon: Activity,
        columns: ["instrument_id", "last_price", "change_pct", "amount"],
        rows: [["000001.SH", "4092.76", "-0.3729", "1003780374528"]]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_quote_refresh_tdx", code=["000001.SH", "000300.SH"])
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_quote_refresh_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":["000001.SH","000300.SH"]},"persist":false}'`
  },
  {
    id: "index_kline_tdx",
    group: "通达信/指数数据/行情数据",
    title: "指数K线",
    name: "index_kline_tdx",
    method: "POST",
    path: "/v1/request/index_kline_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time,period",
    limit: "默认返回 800 条；count 可调整",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取指数 K 线，包含 OHLC、成交量额，以及上涨家数、下跌家数。",
    description: "指数 K 线必须按指数口径请求，和股票 K 线不同；指数返回里可带上涨家数和下跌家数。",
    overview: [
      ["接口名称", "index_kline_tdx"],
      ["接口功能", "获取指数 K 线"],
      ["支持周期", "day、week、month、quarter、year、1m、5m、15m、30m、60m"]
    ],
    paramsExample: `# 日K
client.call("index_kline_tdx", code="000001.SH", period="day", count=800)

# 5分钟K
client.call("index_kline_tdx", code="000001.SH", period="5m", count=300)`,
    params: [
      ["code", "string/list", "是", "指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传数组"],
      ["period", "string", "否", "K线周期：day、week、month、quarter、year、1m、5m、15m、30m、60m；默认 day"],
      ["count", "integer", "否", "返回条数，默认 800"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: indexKlineFields,
    dataExamples: [
      {
        id: "index-kline-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_time", "period", "open", "close", "volume", "amount", "up_count", "down_count"],
        rows: [
          ["000001.SH", "2026-06-16T15:00:00+08:00", "day", "4094.21", "4091.89", "6156682.88", "1369613008896", "1087", "1222"],
          ["000001.SH", "2026-06-17T15:00:00+08:00", "day", "4074.29", "4108.08", "6080774.4", "1403145945088", "785", "1534"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_kline_tdx", code="000001.SH", period="day", count=800)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("index_kline_tdx", code="000001.SH", period="day", count=800)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_kline_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SH","period":"day","count":800},"persist":false}'`
  },
  {
    id: "index_intraday_today_tdx",
    group: "通达信/指数数据/行情数据",
    title: "指数当日分时",
    name: "index_intraday_today_tdx",
    method: "POST",
    path: "/v1/request/index_intraday_today_tdx",
    status: "ready",
    icon: Activity,
    cadence: "盘中现用现查",
    key: "instrument_id,time_label",
    limit: "不传日期，只返回当前交易日已经产生的分时点",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取指数当前交易日分时图数据，包含价格、均价和分钟成交量。",
    description: "这个接口返回指数当日分时，不是历史接口，也不写本地数据。",
    overview: [
      ["接口名称", "index_intraday_today_tdx"],
      ["接口功能", "获取指数当日分时"]
    ],
    paramsExample: `client.call("index_intraday_today_tdx", code="000001.SH")`,
    params: [["code", "string/list", "是", "指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传数组"]],
    fields: intradayTodayFields,
    dataExamples: [
      {
        id: "index-intraday-today-real",
        title: "返回结果示例",
        icon: Activity,
        columns: ["instrument_id", "time_label", "price", "avg_price", "volume"],
        rows: [
          ["000001.SH", "09:31", "4096.11", "4094.1612", "4434416"],
          ["000001.SH", "09:32", "4097.48", "4093.3912", "3362027"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_intraday_today_tdx", code="000001.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_intraday_today_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SH"},"persist":false}'`
  },
  {
    id: "index_intraday_history_tdx",
    group: "通达信/指数数据/行情数据",
    title: "指数历史分时",
    name: "index_intraday_history_tdx",
    method: "POST",
    path: "/v1/request/index_intraday_history_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time",
    limit: "返回所选交易日的分时点；完整交易日通常为 240 个点",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取指数指定交易日历史分时价格和成交量。",
    description: "这个历史分时源返回价格和成交量，不带分时均价；当日均价请看指数当日分时。",
    overview: [
      ["接口名称", "index_intraday_history_tdx"],
      ["接口功能", "获取指数历史分时"],
      ["注意", "不包含分时均价"]
    ],
    paramsExample: `client.call("index_intraday_history_tdx", code="000001.SH", trade_date="20260617")`,
    params: [
      ["code", "string/list", "是", "指数代码：支持 000001.SH、399001.SZ、sh000001；批量可传数组"],
      ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
    ],
    fields: intradayHistoryFields,
    dataExamples: [
      {
        id: "index-intraday-history-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_date", "trade_time", "price", "volume"],
        rows: [
          ["000001.SH", "20260617", "2026-06-17T09:31:00+08:00", "4079.36", "8184626"],
          ["000001.SH", "20260617", "2026-06-17T09:32:00+08:00", "4079.21", "6265905"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("index_intraday_history_tdx", code="000001.SH", trade_date="20260617")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/index_intraday_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SH","trade_date":"20260617"},"persist":false}'`
  }
];

tdxCatalogItems.push(...indexCatalogItems);

const etfCodeFields = [
  ["instrument_id", "统一证券代码", "string", "AxData 统一证券代码，例如 510050.SH"],
  ["symbol", "原始代码", "string", "交易所原始六位代码"],
  ["tdx_code", "TDX 代码", "string", "TDX 带市场前缀代码，例如 sh510050"],
  ["exchange", "交易所", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["name", "ETF简称", "string", "ETF 简称"],
  ["previous_close", "昨收", "number", "代码表携带的昨收价"]
];

const etfCatalogItems: CatalogItem[] = [
  {
    id: "etf_codes_tdx",
    group: "通达信/ETF数据/基础数据",
    title: "ETF列表",
    name: "etf_codes_tdx",
    method: "POST",
    path: "/v1/request/etf_codes_tdx",
    status: "ready",
    icon: Database,
    cadence: "现用现查",
    key: "instrument_id",
    limit: "返回通达信代码表里的 ETF 列表",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取通达信代码表里的 ETF 列表。",
    description: "这个接口和最新股票列表同源，都是从代码总表里筛选。股票列表只筛股票，ETF 列表只筛 ETF。",
    overview: [
      ["接口名称", "etf_codes_tdx"],
      ["接口功能", "获取 ETF 列表"],
      ["默认范围", "全市场 ETF"]
    ],
    paramsExample: `# 全部 ETF 列表
client.call("etf_codes_tdx")

# 指定几个 ETF
client.call("etf_codes_tdx", code=["510050.SH", "510300.SH", "159915.SZ"])`,
    params: [
      ["name", "string/list", "否", "ETF 简称过滤，例如 50ETF、沪深300ETF"],
      ["code", "string/list", "否", "ETF 代码：支持 510050.SH、159915.SZ、sh510050"],
      ["exchange", "string/list", "否", "交易所过滤：all 全部、SSE 上交所、SZSE 深交所；默认 all"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: etfCodeFields,
    dataExamples: [
      {
        id: "etf-codes-real",
        title: "返回结果示例",
        icon: Database,
        columns: ["instrument_id", "symbol", "tdx_code", "exchange", "name", "previous_close"],
        rows: [
          ["510300.SH", "510300", "sh510300", "SSE", "沪深300ETF华泰柏", "4.958000183105469"],
          ["510050.SH", "510050", "sh510050", "SSE", "上证50ETF华夏", "3.015000104904175"],
          ["159915.SZ", "159915", "sz159915", "SZSE", "创业板ETF易方达", "4.183000087738037"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_codes_tdx", code=["510050.SH", "510300.SH", "159915.SZ"])
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_codes_tdx")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_codes_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":["510050.SH","510300.SH","159915.SZ"]},"persist":false}'`
  },
  {
    id: "etf_realtime_snapshot_tdx",
    group: "通达信/ETF数据/实时数据",
    title: "ETF实时快照",
    name: "etf_realtime_snapshot_tdx",
    method: "POST",
    path: "/v1/request/etf_realtime_snapshot_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "盘中现用现查",
    key: "instrument_id",
    limit: "每个 ETF 返回一行当前快照；批量 code 会合并返回",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 当前快照，返回价格、涨跌幅、成交量和成交额。",
    description: "这个接口按 ETF 代码请求当前快照，返回 ETF 有意义的行情字段。",
    overview: [
      ["接口名称", "etf_realtime_snapshot_tdx"],
      ["接口功能", "获取 ETF 实时快照"]
    ],
    paramsExample: `# 单个 ETF
client.call("etf_realtime_snapshot_tdx", code="510050.SH")

# 批量请求多个 ETF
client.call("etf_realtime_snapshot_tdx", code=["510050.SH", "510300.SH", "159915.SZ"])`,
    params: [["code", "string/list", "是", "ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传数组或英文逗号分隔字符串"]],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: etfSnapshotFields,
    dataExamples: [
      {
        id: "etf-snapshot-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "last_price", "pre_close", "open", "high", "low", "change_pct", "volume", "amount"],
        rows: [
          ["510050.SH", "3.017", "3.015", "3.005", "3.036", "3.003", "0.066335", "8261911", "2493979136"],
          ["510300.SH", "4.984", "4.958", "4.943", "5.001", "4.941", "0.524405", "12933430", "6434057216"],
          ["159915.SZ", "4.269", "4.183", "4.169", "4.288", "4.16", "2.055941", "10580532", "4493982720"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_realtime_snapshot_tdx", code=["510050.SH", "510300.SH"])
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_realtime_snapshot_tdx", code="510050.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_realtime_snapshot_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":["510050.SH","510300.SH"]},"persist":false}'`
  },
  {
    id: "etf_realtime_rank_tdx",
    group: "通达信/ETF数据/实时数据",
    title: "ETF实时榜单",
    name: "etf_realtime_rank_tdx",
    method: "POST",
    path: "/v1/request/etf_realtime_rank_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "盘中现用现查",
    key: "rank,instrument_id",
    limit: "默认返回前 80 条",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取当前 ETF 榜单，可按涨跌幅、成交额等排序。",
    description: "这个接口是 ETF 榜单，不是完整 ETF 列表。完整目录请用 ETF 列表。",
    overview: [
      ["接口名称", "etf_realtime_rank_tdx"],
      ["接口功能", "获取 ETF 实时榜单"],
      ["默认排序", "涨跌幅降序"]
    ],
    paramsExample: `# ETF 涨幅榜前 80 条
client.call("etf_realtime_rank_tdx", sort="change_pct", count=80)

# ETF 成交额榜
client.call("etf_realtime_rank_tdx", sort="amount", count=50)`,
    params: [
      ["sort", "string/integer", "否", "排序字段，默认涨跌幅；常用 change_pct、amount、volume、rise_speed"],
      ["start", "integer", "否", "高级分页起点，从 0 开始；一般不用传"],
      ["count", "integer", "否", "返回前多少条，默认 80"],
      ["ascending", "boolean", "否", "是否升序；默认 false，表示按排序字段降序；升序为 true"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: etfRankFields,
    dataExamples: [
      {
        id: "etf-rank-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["rank", "instrument_id", "last_price", "change_pct", "amount"],
        rows: [
          ["1", "159022.SZ", "1.3", "11.683849", "44542640"],
          ["2", "159142.SZ", "1.49", "6.049822", "130340440"],
          ["3", "159141.SZ", "1.465", "6.005789", "98316912"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_realtime_rank_tdx", sort="change_pct", count=80)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_realtime_rank_tdx", sort="amount", count=50)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_realtime_rank_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"sort":"change_pct","count":80},"persist":false}'`
  },
  {
    id: "etf_kline_tdx",
    group: "通达信/ETF数据/行情数据",
    title: "ETFK线",
    name: "etf_kline_tdx",
    method: "POST",
    path: "/v1/request/etf_kline_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time,period",
    limit: "默认返回 800 条；count 可调整",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF K 线，包含 OHLC、成交量额。",
    description: "ETF K 线和指数 K 线使用同一套报文结构，上涨家数和下跌家数对 ETF 通常为空。",
    overview: [
      ["接口名称", "etf_kline_tdx"],
      ["接口功能", "获取 ETF K 线"],
      ["支持周期", "day、week、month、quarter、year、1m、5m、15m、30m、60m"]
    ],
    paramsExample: `# 日K
client.call("etf_kline_tdx", code="510050.SH", period="day", count=800)

# 5分钟K
client.call("etf_kline_tdx", code="510050.SH", period="5m", count=300)`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传数组"],
      ["period", "string", "否", "K线周期：day、week、month、quarter、year、1m、5m、15m、30m、60m；默认 day"],
      ["count", "integer", "否", "返回条数，默认 800"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: etfKlineFields,
    dataExamples: [
      {
        id: "etf-kline-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_time", "period", "open", "close", "volume", "amount"],
        rows: [
          ["510050.SH", "2026-06-16T15:00:00+08:00", "day", "3.022", "2.993", "6528254.72", "1961038848"],
          ["510050.SH", "2026-06-17T15:00:00+08:00", "day", "2.988", "3.015", "11308651.52", "3390973184"],
          ["510050.SH", "2026-06-18T15:00:00+08:00", "day", "3.005", "3.017", "8261911.04", "2493979136"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_kline_tdx", code="510050.SH", period="day", count=800)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_kline_tdx", code="510050.SH", period="day", count=800)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_kline_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH","period":"day","count":800},"persist":false}'`
  },
  {
    id: "etf_intraday_today_tdx",
    group: "通达信/ETF数据/行情数据",
    title: "ETF当日分时",
    name: "etf_intraday_today_tdx",
    method: "POST",
    path: "/v1/request/etf_intraday_today_tdx",
    status: "ready",
    icon: Activity,
    cadence: "盘中现用现查",
    key: "instrument_id,time_label",
    limit: "不传日期，只返回当前交易日已经产生的分时点",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 当前交易日分时图数据，包含价格、均价和分钟成交量。",
    description: "这个接口返回 ETF 当日分时，不是历史接口，也不写本地数据。",
    overview: [
      ["接口名称", "etf_intraday_today_tdx"],
      ["接口功能", "获取 ETF 当日分时"]
    ],
    paramsExample: `client.call("etf_intraday_today_tdx", code="510050.SH")`,
    params: [["code", "string/list", "是", "ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传数组"]],
    fields: intradayTodayFields,
    dataExamples: [
      {
        id: "etf-intraday-today-real",
        title: "返回结果示例",
        icon: Activity,
        columns: ["instrument_id", "time_label", "price", "avg_price", "volume"],
        rows: [
          ["510050.SH", "09:31", "3.008", "3.00555", "87013"],
          ["510050.SH", "09:32", "3.013", "3.00778", "68482"],
          ["510050.SH", "09:33", "3.008", "3.00848", "80191"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_intraday_today_tdx", code="510050.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_intraday_today_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH"},"persist":false}'`
  },
  {
    id: "etf_intraday_history_tdx",
    group: "通达信/ETF数据/行情数据",
    title: "ETF历史分时",
    name: "etf_intraday_history_tdx",
    method: "POST",
    path: "/v1/request/etf_intraday_history_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time",
    limit: "返回所选交易日的分时点；完整交易日通常为 240 个点",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 指定交易日历史分时价格和成交量。",
    description: "这个历史分时源返回价格和成交量，不带分时均价；当日均价请看 ETF 当日分时。",
    overview: [
      ["接口名称", "etf_intraday_history_tdx"],
      ["接口功能", "获取 ETF 历史分时"],
      ["注意", "不包含分时均价"]
    ],
    paramsExample: `client.call("etf_intraday_history_tdx", code="510050.SH", trade_date="20260617")`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050.SH、159915.SZ、sh510050；批量可传数组"],
      ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
    ],
    fields: intradayHistoryFields,
    dataExamples: [
      {
        id: "etf-intraday-history-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_date", "trade_time", "price", "volume"],
        rows: [
          ["510050.SH", "20260617", "2026-06-17T09:31:00+08:00", "2.994", "320686"],
          ["510050.SH", "20260617", "2026-06-17T09:32:00+08:00", "2.987", "819743"],
          ["510050.SH", "20260617", "2026-06-17T09:33:00+08:00", "2.988", "348842"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_intraday_history_tdx", code="510050.SH", trade_date="20260617")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_intraday_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH","trade_date":"20260617"},"persist":false}'`
  },
  {
    id: "etf_trades_today_tdx",
    group: "通达信/ETF数据/行情数据",
    title: "ETF当日成交明细",
    name: "etf_trades_today_tdx",
    method: "POST",
    path: "/v1/request/etf_trades_today_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_time,trade_index",
    limit: "返回当前交易日服务器可取的成交明细；分页由后端处理",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 当前交易日成交明细；请求式分页由后端处理。",
    description: "这个接口按 ETF 代码请求当前交易日的成交明细，不是实时订阅流，也不写入本地数据层。",
    overview: [
      ["接口名称", "etf_trades_today_tdx"],
      ["接口功能", "获取 ETF 当前交易日成交明细"],
      ["数据粒度", "成交明细"]
    ],
    paramsExample: `# 单个标的
client.call("etf_trades_today_tdx", code="510050.SH")

# 批量请求多个标的
client.call("etf_trades_today_tdx", code=["510050.SH", "159915.SZ"])`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050、510050.SH、sh510050；批量可传数组或英文逗号分隔字符串"]
    ],
    fields: tradeDetailTodayFields,
    dataExamples: [
      {
        id: "etf-trades-today-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_time", "trade_index", "price", "volume", "order_count", "side"],
        rows: [
          ["510050.SH", "09:25", "3600", "3.005", "38954", "6023", "neutral"],
          ["510050.SH", "09:30", "3601", "3.007", "5693", "5951", "buy"],
          ["510050.SH", "09:30", "3602", "3.006", "9380", "5951", "sell"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_trades_today_tdx", code="510050.SH")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_trades_today_tdx", code="510050.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_trades_today_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH"},"persist":false}'`
  },
  {
    id: "etf_trades_history_tdx",
    group: "通达信/ETF数据/行情数据",
    title: "ETF历史成交明细",
    name: "etf_trades_history_tdx",
    method: "POST",
    path: "/v1/request/etf_trades_history_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,trade_datetime,trade_index",
    limit: "返回指定交易日服务器可取的成交明细；分页由后端处理",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 指定交易日成交明细；适合复盘某一天逐笔/聚合成交。",
    description: "这个接口按 ETF 代码和交易日期请求历史成交明细，不是 K 线，也不写入本地数据层。",
    overview: [
      ["接口名称", "etf_trades_history_tdx"],
      ["接口功能", "获取 ETF 指定交易日历史成交明细"],
      ["数据粒度", "成交明细"]
    ],
    paramsExample: `# 单个标的
client.call("etf_trades_history_tdx", code="510050.SH", trade_date="20260511")

# 批量请求多个标的
client.call("etf_trades_history_tdx", code=["510050.SH", "159915.SZ"], trade_date="20260511")`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050、510050.SH、sh510050；批量可传数组或英文逗号分隔字符串"],
      ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
    ],
    fields: tradeDetailHistoryFields,
    dataExamples: [
      {
        id: "etf-trades-history-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "trade_date", "trade_datetime", "trade_index", "price", "volume", "order_count", "side"],
        rows: [
          ["510050.SH", "20260511", "2026-05-11T09:25:00+08:00", "3600", "3.09", "49676", "6149", "neutral"],
          ["510050.SH", "20260511", "2026-05-11T09:30:00+08:00", "3601", "3.091", "15896", "6167", "buy"],
          ["510050.SH", "20260511", "2026-05-11T09:30:00+08:00", "3602", "3.089", "12302", "6167", "sell"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_trades_history_tdx", code="510050.SH", trade_date="20260511")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_trades_history_tdx", code="510050.SH", trade_date="20260511")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_trades_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH","trade_date":"20260511"},"persist":false}'`
  },
  {
    id: "etf_auction_process_tdx",
    group: "通达信/ETF数据/竞价数据",
    title: "ETF竞价明细",
    name: "etf_auction_process_tdx",
    method: "POST",
    path: "/v1/request/etf_auction_process_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "盘前竞价阶段现用现查",
    key: "instrument_id,auction_time",
    limit: "返回单个 ETF 集合竞价阶段的过程明细",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取单只 ETF 集合竞价明细里的价格、撮合量、未撮合量和方向原始值。",
    description: "这个接口用于查看源端返回的 ETF 集合竞价明细，适合观察开盘集合竞价和收盘集合竞价过程中的价格、撮合量和未撮合量变化。开盘段实测常见覆盖 09:15 到 09:25 前，不包含 09:25 最终开盘成交结果；收盘段实测常见覆盖 14:57 至 15:00 前后。它不能单独替代成交明细接口。",
    overview: [
      ["接口名称", "etf_auction_process_tdx"],
      ["接口功能", "获取 ETF 集合竞价明细"],
      ["时间范围", "开盘段实测常见覆盖 09:15 至 09:25 前，不包含 09:25 最终开盘成交结果；收盘段实测常见覆盖 14:57 至 15:00 前后"]
    ],
    paramsExample: `# 单个标的
client.call("etf_auction_process_tdx", code="510050.SH")

# 批量请求多个标的
client.call("etf_auction_process_tdx", code=["510050.SH", "159915.SZ"])`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050、510050.SH、sh510050；批量可传数组或英文逗号分隔字符串"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: auctionProcessFields,
    dataExamples: [
      {
        id: "etf-auction-process-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "auction_time", "auction_index", "price", "matched_volume", "unmatched_volume", "unmatched_direction"],
        rows: [
          ["510050.SH", "09:15:02", "0", "3", "100", "38", "1"],
          ["510050.SH", "09:15:05", "1", "3.002", "101", "21", "1"],
          ["510050.SH", "09:15:08", "2", "3.015", "145", "9", "-1"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_auction_process_tdx", code="510050.SH")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_auction_process_tdx", code="510050.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_auction_process_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH"},"persist":false}'`
  },
  {
    id: "etf_auction_result_tdx",
    group: "通达信/ETF数据/竞价数据",
    title: "ETF竞价结果",
    name: "etf_auction_result_tdx",
    method: "POST",
    path: "/v1/request/etf_auction_result_tdx",
    status: "ready",
    icon: BarChart3,
    cadence: "现用现查",
    key: "instrument_id,auction_time",
    limit: "从当日成交明细中筛选 09:25 竞价结果；分页由后端处理",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "获取 ETF 当日 09:25 开盘竞价结果；来自当日成交明细，不是竞价过程明细。",
    description: "这个接口按 ETF 代码请求当前交易日成交明细，并只保留 09:25 的开盘竞价结果。它返回的是竞价最终成交结果，不是 09:15 到 09:25 之间的过程变化。",
    overview: [
      ["接口名称", "etf_auction_result_tdx"],
      ["接口功能", "获取 ETF 当日 09:25 开盘竞价结果"],
      ["结果来源", "当日成交明细中的 09:25 那笔"]
    ],
    paramsExample: `# 单个标的
client.call("etf_auction_result_tdx", code="510050.SH")

# 批量请求多个标的
client.call("etf_auction_result_tdx", code=["510050.SH", "159915.SZ"])`,
    params: [
      ["code", "string/list", "是", "ETF 代码：支持 510050、510050.SH、sh510050；批量可传数组或英文逗号分隔字符串"]
    ],
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: auctionResultFields,
    dataExamples: [
      {
        id: "etf-auction-result-real",
        title: "返回结果示例",
        icon: BarChart3,
        columns: ["instrument_id", "auction_time", "trade_index", "price", "volume", "amount", "order_count"],
        rows: [
          ["510050.SH", "09:25", "3600", "3.005", "38954", "11705677", "6023"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("etf_auction_result_tdx", code="510050.SH")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("etf_auction_result_tdx", code="510050.SH")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/etf_auction_result_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"510050.SH"},"persist":false}'`
  }
];

tdxCatalogItems.push(...etfCatalogItems);

const tdxExtCommonFields = [
  ["instrument_id", "统一代码", "string", "AxData 扩展资产统一代码"],
  ["symbol", "源端代码", "string", "源端品种代码"],
  ["asset_type", "资产类型", "string", "futures 期货、option 期权、fund 基金、bond 债券、fx 外汇、macro 宏观"],
  ["exchange", "交易所/场所", "string", "归一后的交易所或资产场所"],
  ["market_name", "市场名称", "string", "本机扩展资产目录中的市场名称"],
  ["market_group", "市场分组", "string", "本机扩展资产目录中的分组名称"]
];

const tdxExtCommonParams = [
  ["code", "string/list", "否", "品种代码过滤；可传单个、列表或英文逗号分隔字符串"],
  ["exchange", "string/list", "否", "交易所或资产场所过滤；不传或 all 表示全部"],
  ["name", "string/list", "否", "名称、品种或市场关键词过滤"],
  ["limit", "integer", "否", "返回前多少行，默认 1000"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtCodeParams = [
  ["code", "string/list", "是", "品种代码；可传单个、列表或英文逗号分隔字符串"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtKlineParams = [
  ["code", "string/list", "是", "品种代码；可传单个、列表或英文逗号分隔字符串"],
  ["period", "string", "否", "K线周期：1m、5m、15m、30m、60m、day、week、month、quarter、year；默认 day"],
  ["limit", "integer", "否", "每个品种返回前多少根，默认 30"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtIntradayHistoryParams = [
  ["code", "string/list", "是", "品种代码；可传单个、列表或英文逗号分隔字符串"],
  ["trade_date", "date/string", "是", "交易日期，YYYYMMDD 或 YYYY-MM-DD"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtTradesHistoryParams = [
  ["code", "string/list", "是", "品种代码；可传单个、列表或英文逗号分隔字符串"],
  ["trade_date", "date/string", "是", "交易日期，YYYYMMDD 或 YYYY-MM-DD"],
  ["limit", "integer", "否", "每个品种返回多少笔，默认返回最新一页的 120 笔；all=true 时作为总数量上限"],
  ["all", "boolean", "否", "是否自动翻页取完整逐笔，并按时间顺序返回；默认 false"],
  ["page_size", "integer", "否", "all=true 时每页请求笔数，默认 1800"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtTradesTodayParams = [
  ["code", "string/list", "是", "品种代码；可传单个、列表或英文逗号分隔字符串"],
  ["limit", "integer", "否", "每个品种返回多少笔，默认返回最新一页的 120 笔；all=true 时作为总数量上限"],
  ["all", "boolean", "否", "是否自动翻页取完整逐笔，并按时间顺序返回；默认 false"],
  ["page_size", "integer", "否", "all=true 时每页请求笔数，默认 1800"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtOptionChainParams = [
  ["product_code", "string/list", "否", "期权品种代码过滤，例如 AP"],
  ["contract_month", "string/list", "否", "合约月份过滤，YYYYMM"],
  ["exchange", "string/list", "否", "交易所过滤；不传表示全部"],
  ["limit", "integer", "否", "返回前多少个行权价，默认 50"],
  ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
];

const tdxExtQuoteLevelFields = (() => {
  const fields: string[][] = [];
  const levelZh = ["", "一", "二", "三", "四", "五"];
  for (let level = 1; level <= 5; level += 1) {
    fields.push(
      [`bid${level}_price`, `买${levelZh[level]}价`, "number", "源端有值时返回"],
      [`bid${level}_volume`, `买${levelZh[level]}量`, "integer", "源端有值时返回"],
      [`ask${level}_price`, `卖${levelZh[level]}价`, "number", "源端有值时返回"],
      [`ask${level}_volume`, `卖${levelZh[level]}量`, "integer", "源端有值时返回"]
    );
  }
  return fields;
})();

const tdxExtQuoteFields = [
  ["instrument_id", "品种代码", "string", "AxData 统一品种代码"],
  ["symbol", "源端代码", "string", "源端品种代码"],
  ["exchange", "交易场所", "string", "交易所或资产场所"],
  ["name", "名称", "string", "可确认时返回品种名称"],
  ["trade_date", "行情日期", "date/string", "行情日期"],
  ["last_price", "最新价", "number", "最新价或最新值"],
  ["pre_close", "昨收", "number", "昨收或上期值"],
  ["pre_settlement", "昨结算", "number", "源端有值时返回"],
  ["open", "开盘价", "number", "开盘价或本期值"],
  ["high", "最高价", "number", "最高价或本期高值"],
  ["low", "最低价", "number", "最低价或本期低值"],
  ["settlement", "结算价", "number", "源端有值时返回"],
  ["average_price", "均价", "number", "源端有值时返回"],
  ["volume", "成交量", "integer", "按源端行情口径返回"],
  ["amount", "成交额", "number", "源端有值时返回"],
  ["open_interest", "持仓量", "integer", "源端有值时返回"],
  ["open_interest_change", "持仓变化", "integer", "源端有值时返回"],
  ["inside_volume", "内盘量", "integer", "源端有值时返回"],
  ["outside_volume", "外盘量", "integer", "源端有值时返回"],
  ...tdxExtQuoteLevelFields
];

const tdxExtKlineFields = [
  ["instrument_id", "品种代码", "string", "AxData 统一品种代码"],
  ["symbol", "源端代码", "string", "源端品种代码"],
  ["exchange", "交易场所", "string", "交易所或资产场所"],
  ["name", "名称", "string", "可确认时返回品种名称"],
  ["trade_time", "K线时间", "date/string", "K线日期或时间"],
  ["period", "周期", "string", "K线周期"],
  ["open", "开盘价", "number", "开盘价或本期值"],
  ["high", "最高价", "number", "最高价或本期高值"],
  ["low", "最低价", "number", "最低价或本期低值"],
  ["close", "收盘价", "number", "收盘价或本期值"],
  ["volume", "成交量", "integer", "K线成交量，按源端周期口径返回"],
  ["open_interest", "持仓量", "integer", "源端有值时返回"],
  ["settlement", "结算价", "number", "源端有值时返回"]
];

const tdxExtIntradayFields = [
  ["instrument_id", "品种代码", "string", "AxData 统一品种代码"],
  ["symbol", "源端代码", "string", "源端品种代码"],
  ["exchange", "交易场所", "string", "交易所或资产场所"],
  ["name", "名称", "string", "可确认时返回品种名称"],
  ["trade_date", "交易日期", "date/string", "历史分时的交易日期；当日分时为空"],
  ["time_label", "分时时间", "string", "分时时间"],
  ["price", "价格", "number", "分时价格或数值"],
  ["average_price", "均价", "number", "分时均价或均值"],
  ["volume", "成交量", "integer", "按源端口径返回"]
];

const tdxExtTradeFields = [
  ["instrument_id", "品种代码", "string", "AxData 统一品种代码"],
  ["symbol", "源端代码", "string", "源端品种代码"],
  ["exchange", "交易场所", "string", "交易所或资产场所"],
  ["name", "名称", "string", "可确认时返回品种名称"],
  ["trade_date", "交易日期", "date/string", "交易日期"],
  ["time_label", "成交时间", "string", "成交时间，精确到秒"],
  ["price", "成交价", "number", "成交价"],
  ["volume", "成交量", "integer", "按源端逐笔口径返回"],
  ["position_change", "仓差", "integer", "源端有值时返回"],
  ["open_close_type", "开平类型", "string", "可确认时返回，如双开、双平、多开、空开、多平、空平、多换、空换、换手"]
];

const tdxExtOptionChainFields = [
  ["product_code", "品种代码", "string", "期权品种代码"],
  ["product_name", "品种名称", "string", "期权品种名称"],
  ["exchange", "交易所", "string", "交易所"],
  ["contract_month", "合约月份", "string", "YYYYMM"],
  ["strike_price", "行权价", "number", "行权价"],
  ["call_instrument_id", "认购合约", "string", "认购合约代码"],
  ["call_symbol", "认购源端代码", "string", "认购源端代码"],
  ["call_last_price", "认购最新价", "number", "认购最新价"],
  ["call_volume", "认购成交量", "integer", "认购成交量"],
  ["call_open_interest", "认购持仓量", "integer", "认购持仓量"],
  ["put_instrument_id", "认沽合约", "string", "认沽合约代码"],
  ["put_symbol", "认沽源端代码", "string", "认沽源端代码"],
  ["put_last_price", "认沽最新价", "number", "认沽最新价"],
  ["put_volume", "认沽成交量", "integer", "认沽成交量"],
  ["put_open_interest", "认沽持仓量", "integer", "认沽持仓量"],
  ...(() => {
    const fields: string[][] = [];
    const levelZh = ["", "一", "二", "三", "四", "五"];
    for (const [side, label] of [["call", "认购"], ["put", "认沽"]]) {
      for (let level = 1; level <= 5; level += 1) {
        fields.push(
          [`${side}_bid${level}_price`, `${label}买${levelZh[level]}价`, "number", "源端有值时返回"],
          [`${side}_bid${level}_volume`, `${label}买${levelZh[level]}量`, "integer", "源端有值时返回"],
          [`${side}_ask${level}_price`, `${label}卖${levelZh[level]}价`, "number", "源端有值时返回"],
          [`${side}_ask${level}_volume`, `${label}卖${levelZh[level]}量`, "integer", "源端有值时返回"]
        );
      }
    }
    return fields;
  })()
];

function createTdxExtCatalogItem(spec: {
  id: string;
  title: string;
  group: string;
  summary: string;
  key: string;
  params?: string[][];
  fields: string[][];
  paramsExample: string;
  exampleColumns: string[];
  exampleRows: string[][];
  description?: string;
  dataSourceLabel?: string;
  exampleNote?: string;
}): CatalogItem {
  const dataSourceLabel = spec.dataSourceLabel ?? "本机扩展资产目录";
  return {
    id: spec.id,
    group: `通达信扩展行情/${spec.group}`,
    title: spec.title,
    name: spec.id,
    method: "POST",
    path: `/v1/request/${spec.id}`,
    status: "ready",
    icon: Database,
    cadence: "现用现查",
    key: spec.key,
    limit: "limit 控制返回行数",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: spec.summary,
    sourceCode: "tdx_ext",
    sourceNameZh: "通达信扩展行情",
    providerId: "axdata.source.tdx_ext_external",
    description: spec.description ?? spec.summary,
    overview: [
      ["接口名称", spec.id],
      ["接口功能", spec.title],
      ["数据来源", dataSourceLabel]
    ],
    paramsNote: "默认不用传 tdx_root；只有 API 服务器上的通达信安装目录不是常见位置，或想指定某个 hq_cache 目录时才需要传。",
    paramsExample: spec.paramsExample,
    params: spec.params ?? tdxExtCommonParams,
    fieldColumns: ["字段", "中文名", "类型", "说明"],
    fields: spec.fields,
    dataExamples: [
      {
        id: `${spec.id}-real`,
        title: "返回结果示例",
        icon: Database,
        note: spec.exampleNote ?? "以下样例来自本机扩展资产目录；实际返回会随本机目录更新变化。",
        columns: spec.exampleColumns,
        rows: spec.exampleRows
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = ${spec.paramsExample.split("\n").find((line) => line.trim().startsWith("client.call(")) ?? `client.call("${spec.id}")`}
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("${spec.id}")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/${spec.id}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"limit":3},"persist":false}'`
  };
}

const tdxExtCatalogItems: CatalogItem[] = [
  createTdxExtCatalogItem({
    id: "tdx_ext_markets_tdx",
    title: "扩展市场列表",
    group: "期货数据",
    summary: "读取本机扩展资产市场目录，用于查看期货、期权、基金、债券、外汇、宏观等市场分组。",
    key: "market_name",
    params: [
      ["asset_type", "string/list", "否", "资产类型过滤：futures、option、fund、bond、fx、macro"],
      ["name", "string/list", "否", "市场名称关键词过滤"],
      ["limit", "integer", "否", "返回前多少行，默认 500"],
      ["tdx_root", "string", "否", "本机通达信目录（可选，高级）：用于读取本机通达信扩展行情代码表；不填时自动发现。远程调用时指 API 服务器上的通达信目录，不是浏览器所在电脑。"]
    ],
    fields: [
      ["market_name", "市场名称", "string", "市场名称"],
      ["short_name", "市场简称", "string", "市场简称"],
      ["market_group", "市场分组", "string", "市场分组"],
      ["asset_type", "资产类型", "string", "资产类型"],
      ["asset_type_zh", "资产类型中文", "string", "资产类型中文名"]
    ],
    paramsExample: `# 查看期货市场
client.call("tdx_ext_markets_tdx", asset_type="futures", limit=5)`,
    exampleColumns: ["market_name", "short_name", "market_group", "asset_type", "asset_type_zh"],
    exampleRows: [
      ["纽约COMEX", "CO", "期货现货", "futures", "期货"],
      ["纽约NYMEX", "NY", "期货现货", "futures", "期货"],
      ["芝加哥CBOT", "CB", "期货现货", "futures", "期货"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "tdx_ext_instruments_tdx",
    title: "扩展品种列表",
    group: "期货数据",
    summary: "读取本机扩展资产品种目录，可按资产类型、代码、交易所或关键词过滤。",
    key: "instrument_id",
    params: [["asset_type", "string/list", "否", "资产类型过滤：futures、option、fund、bond、fx、macro"], ...tdxExtCommonParams],
    fields: [
      ...tdxExtCommonFields,
      ["product_code", "品种代码", "string", "期货/期权品种代码；可确认时返回"],
      ["product_name", "品种名称", "string", "期货/期权品种名称；可确认时返回"],
      ["contract_month", "合约月份", "string", "YYYYMM；可确认时返回"],
      ["contract_type", "合约类型", "string", "可确认时返回合约类型"],
      ["option_type", "期权方向", "string", "call 或 put；可确认时返回"],
      ["strike_price", "行权价", "number", "期权行权价"],
      ["fund_type", "基金类型", "string", "基金市场类型"],
      ["bond_type", "债券类型", "string", "债券市场类型"],
      ["base_currency", "基础货币", "string", "外汇基础货币"],
      ["quote_currency", "报价货币", "string", "外汇报价货币"],
      ["indicator_category", "指标分类", "string", "宏观指标分类"]
    ],
    paramsExample: `# 查看外汇品种
client.call("tdx_ext_instruments_tdx", asset_type="fx", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "base_currency", "quote_currency"],
    exampleRows: [
      ["AUDUSD.FX", "AUDUSD", "fx", "FX", "基本汇率", "环球行情", "AUD", "USD"],
      ["CNHHKD.FX", "CNHHKD", "fx", "FX", "基本汇率", "环球行情", "CNH", "HKD"],
      ["CNHUSD.FX", "CNHUSD", "fx", "FX", "基本汇率", "环球行情", "CNH", "USD"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "futures_contracts_tdx",
    title: "期货合约列表",
    group: "期货数据",
    summary: "返回本机扩展资产目录中可识别的期货合约列表。",
    key: "instrument_id",
    fields: [
      ...tdxExtCommonFields,
      ["product_code", "品种代码", "string", "期货品种代码"],
      ["product_name", "品种名称", "string", "期货品种名称"],
      ["contract_month", "合约月份", "string", "YYYYMM；可确认时返回"],
      ["contract_type", "合约类型", "string", "contract 合约、continuous 连续、index 指数或 other"]
    ],
    paramsExample: `# 中金所期货合约
client.call("futures_contracts_tdx", exchange="CFFEX", limit=5)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "product_code", "product_name", "contract_month", "contract_type"],
    exampleRows: [
      ["IC2606.CFFEX", "IC2606", "futures", "CFFEX", "中金所期货", "期货现货", "IC", "中证", "202606", "contract"],
      ["IC2607.CFFEX", "IC2607", "futures", "CFFEX", "中金所期货", "期货现货", "IC", "中证", "202607", "contract"],
      ["IC2609.CFFEX", "IC2609", "futures", "CFFEX", "中金所期货", "期货现货", "IC", "中证", "202609", "contract"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "option_contracts_tdx",
    title: "期权合约列表",
    group: "期权数据",
    summary: "返回本机扩展资产目录中可识别的期权合约列表。",
    key: "instrument_id",
    fields: [
      ...tdxExtCommonFields,
      ["product_code", "品种代码", "string", "期权标的品种代码"],
      ["product_name", "品种名称", "string", "期权标的品种名称"],
      ["contract_month", "合约月份", "string", "YYYYMM"],
      ["option_type", "期权方向", "string", "call 认购，put 认沽"],
      ["strike_price", "行权价", "number", "期权行权价"]
    ],
    paramsExample: `# 郑州商品期权
client.call("option_contracts_tdx", exchange="CZCE", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "product_code", "product_name", "contract_month", "option_type", "strike_price"],
    exampleRows: [
      ["AP2610-C-10000.CZCE", "AP2610-C-10000", "option", "CZCE", "郑州商品期权", "期权", "AP", "苹果", "202610", "call", "10000"],
      ["AP2610-C-10200.CZCE", "AP2610-C-10200", "option", "CZCE", "郑州商品期权", "期权", "AP", "苹果", "202610", "call", "10200"],
      ["AP2610-C-6400.CZCE", "AP2610-C-6400", "option", "CZCE", "郑州商品期权", "期权", "AP", "苹果", "202610", "call", "6400"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "fund_codes_tdx",
    title: "基金列表",
    group: "基金数据",
    summary: "返回本机扩展资产目录中的基金代码和可确认的净值字段；ETF 交易类接口仍放在 ETF 数据里。",
    key: "instrument_id",
    fields: [
      ...tdxExtCommonFields,
      ["fund_type", "基金类型", "string", "基金市场类型"],
      ["update_date", "净值日期", "date/string", "可确认时返回净值日期"],
      ["nav", "单位净值", "number", "可确认时返回单位净值"],
      ["accumulated_nav", "累计净值/累计值", "number", "可确认时返回累计净值或累计值"]
    ],
    paramsExample: `# 指定基金代码
client.call("fund_codes_tdx", code="159007", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "fund_type", "update_date", "nav", "accumulated_nav"],
    exampleRows: [
      ["159007.FUND", "159007", "fund", "FUND", "开放式基金", "基金理财", "开放式基金", "20260617", "0.7922", "20560.32"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "bond_codes_tdx",
    title: "债券列表",
    group: "债券数据",
    summary: "返回本机扩展资产目录中可识别的债券或资金市场品种。",
    key: "instrument_id",
    fields: [...tdxExtCommonFields, ["bond_type", "债券类型", "string", "债券市场类型"]],
    paramsExample: `# 债券/资金市场品种
client.call("bond_codes_tdx", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "bond_type"],
    exampleRows: [
      ["10YCDB.BOND", "10YCDB", "bond", "BOND", "资金市场", "其它", "资金市场"],
      ["10YGB.BOND", "10YGB", "bond", "BOND", "资金市场", "其它", "资金市场"],
      ["1YCDB.BOND", "1YCDB", "bond", "BOND", "资金市场", "其它", "资金市场"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "fx_codes_tdx",
    title: "外汇品种列表",
    group: "外汇数据",
    summary: "返回本机扩展资产目录中的外汇货币对列表。",
    key: "instrument_id",
    fields: [...tdxExtCommonFields, ["base_currency", "基础货币", "string", "基础货币"], ["quote_currency", "报价货币", "string", "报价货币"]],
    paramsExample: `# 指定几个货币对
client.call("fx_codes_tdx", code=["USDCNY", "EURUSD"])`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "base_currency", "quote_currency"],
    exampleRows: [
      ["EURUSD.FX", "EURUSD", "fx", "FX", "基本汇率", "环球行情", "EUR", "USD"],
      ["USDCNY.FX", "USDCNY", "fx", "FX", "基本汇率", "环球行情", "USD", "CNY"]
    ]
  }),
  createTdxExtCatalogItem({
    id: "macro_indicators_tdx",
    title: "宏观指标列表",
    group: "宏观数据",
    summary: "返回本机扩展资产目录中的宏观指标代码；指标值、日期和单位未确认前不包装成正式字段。",
    key: "instrument_id",
    fields: [
      ...tdxExtCommonFields,
      ["indicator_category", "指标分类", "string", "指标分类"],
      ["unit", "单位", "string", "已确认时返回"],
      ["frequency", "发布频度", "string", "已确认时返回"]
    ],
    paramsExample: `# 宏观指标代码
client.call("macro_indicators_tdx", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "asset_type", "exchange", "market_name", "market_group", "indicator_category", "unit", "frequency"],
    exampleRows: [
      ["1_GDP.MACRO", "1_GDP", "macro", "MACRO", "宏观指标", "其它", "1", "亿元", "年"],
      ["2_CPI.MACRO", "2_CPI", "macro", "MACRO", "宏观指标", "其它", "2", "元", "月"],
      ["1_MSR.MACRO", "1_MSR", "macro", "MACRO", "宏观指标", "其它", "1", "", ""]
    ]
  }),
  createTdxExtCatalogItem({
    id: "futures_realtime_snapshot_tdx",
    title: "期货实时快照",
    group: "期货数据",
    summary: "请求期货当前快照，返回最新价、结算价、成交量、成交额、持仓量和五档盘口等字段。",
    key: "instrument_id",
    params: tdxExtCodeParams,
    fields: tdxExtQuoteFields,
    paramsExample: `# 期货快照
client.call("futures_realtime_snapshot_tdx", code="IC2607.CFFEX")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "last_price", "open_interest", "bid1_price", "bid1_volume", "ask1_price", "ask1_volume", "bid5_price", "bid5_volume", "ask5_price", "ask5_volume"],
    exampleRows: [["IC2607.CFFEX", "IC2607", "CFFEX", "20260703", "8688.799805", "60372", "8688", "9", "8693.799805", "1", "", "0", "", "0"]],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实源端快照请求；实际数值会随行情变化。"
  }),
  createTdxExtCatalogItem({
    id: "futures_kline_tdx",
    title: "期货K线",
    group: "期货数据",
    summary: "请求期货K线，返回OHLC、成交量、持仓量和结算价。",
    key: "instrument_id + trade_time",
    params: tdxExtKlineParams,
    fields: tdxExtKlineFields,
    paramsExample: `# 期货日K
client.call("futures_kline_tdx", code="IC2607.CFFEX", period="day", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_time", "period", "open", "high", "low", "close", "volume", "open_interest", "settlement"],
    exampleRows: [["IC2607.CFFEX", "IC2607", "CFFEX", "20260703", "day", "8671.200195", "8805", "8592.200195", "8688.799805", "45511", "60372", "8718.799805"]],
    dataSourceLabel: "扩展资产源端K线请求",
    exampleNote: "以下样例来自真实源端K线请求；成交量按源端周期口径返回。"
  }),
  createTdxExtCatalogItem({
    id: "futures_intraday_today_tdx",
    title: "期货当日分时",
    group: "期货数据",
    summary: "请求期货当日分时，返回价格、均价和分时成交量。",
    key: "instrument_id + time_label",
    params: tdxExtCodeParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 期货当日分时
client.call("futures_intraday_today_tdx", code="IC2607.CFFEX")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["IC2607.CFFEX", "IC2607", "CFFEX", "", "09:30", "8672.800781", "8682.989258", "1593"]],
    dataSourceLabel: "扩展资产源端分时请求",
    exampleNote: "以下样例来自真实源端当日分时请求；分时时间按源端交易时段返回。"
  }),
  createTdxExtCatalogItem({
    id: "futures_intraday_history_tdx",
    title: "期货历史分时",
    group: "期货数据",
    summary: "请求指定交易日的期货历史分时。",
    key: "instrument_id + trade_date + time_label",
    params: tdxExtIntradayHistoryParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 期货历史分时
client.call("futures_intraday_history_tdx", code="IC2607.CFFEX", trade_date="20260703")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["IC2607.CFFEX", "IC2607", "CFFEX", "20260703", "09:30", "8672.800781", "8682.989258", "1593"]],
    dataSourceLabel: "扩展资产源端历史分时请求",
    exampleNote: "以下样例来自真实源端历史分时请求。"
  }),
  createTdxExtCatalogItem({
    id: "futures_trades_history_tdx",
    title: "期货历史逐笔",
    group: "期货数据",
    summary: "请求指定交易日期货逐笔成交，返回秒级时间、成交价、成交量、仓差和可确认的开平类型。",
    key: "instrument_id + trade_date + time_label",
    params: tdxExtTradesHistoryParams,
    fields: tdxExtTradeFields,
    paramsExample: `# 期货历史逐笔
client.call("futures_trades_history_tdx", code="IC2607.CFFEX", trade_date="20260703", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "volume", "position_change", "open_close_type"],
    exampleRows: [
      ["IC2607.CFFEX", "IC2607", "CFFEX", "20260703", "14:59:58", "8688", "1", "0", "空换"],
      ["IC2607.CFFEX", "IC2607", "CFFEX", "20260703", "14:59:58", "8688.8", "1", "0", "多换"]
    ],
    dataSourceLabel: "扩展资产源端历史逐笔请求",
    exampleNote: "以下样例来自真实源端历史逐笔请求；默认返回最新一页逐笔，all=true 时自动翻页并按时间顺序返回。"
  }),
  createTdxExtCatalogItem({
    id: "futures_trades_today_tdx",
    title: "期货当日逐笔",
    group: "期货数据",
    summary: "请求期货当日逐笔成交，返回秒级时间、成交价、成交量、仓差和可确认的开平类型。",
    key: "instrument_id + time_label",
    params: tdxExtTradesTodayParams,
    fields: tdxExtTradeFields,
    paramsExample: `# 期货当日逐笔
client.call("futures_trades_today_tdx", code="IC2607.CFFEX", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "volume", "position_change", "open_close_type"],
    exampleRows: [
      ["IC2607.CFFEX", "IC2607", "CFFEX", "", "14:59:58", "8688", "1", "0", "空换"],
      ["IC2607.CFFEX", "IC2607", "CFFEX", "", "14:59:58", "8688.8", "1", "0", "多换"]
    ],
    dataSourceLabel: "扩展资产源端当日逐笔请求",
    exampleNote: "以下样例来自真实源端当日逐笔请求；默认返回最新一页逐笔，all=true 时自动翻页并按时间顺序返回。"
  }),
  createTdxExtCatalogItem({
    id: "option_realtime_snapshot_tdx",
    title: "期权实时快照",
    group: "期权数据",
    summary: "请求期权当前快照，返回价格、结算、成交量额、持仓量和五档盘口。",
    key: "instrument_id",
    params: tdxExtCodeParams,
    fields: tdxExtQuoteFields,
    paramsExample: `# 期权快照
client.call("option_realtime_snapshot_tdx", code="AP2610-C-10000.CZCE")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "last_price", "open_interest", "bid1_price", "bid1_volume", "ask1_price", "ask1_volume", "bid5_price", "bid5_volume", "ask5_price", "ask5_volume"],
    exampleRows: [["AP2610-C-10000.CZCE", "AP2610-C-10000", "CZCE", "20260703", "11.5", "8672", "11", "1", "11.5", "2", "", "0", "", "0"]],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实源端快照请求；希腊值、隐含波动率未确认前不展示。"
  }),
  createTdxExtCatalogItem({
    id: "option_chain_tdx",
    title: "期权T型报价",
    group: "期权数据",
    summary: "用期权合约列表和实时快照拼出 T 型报价，按行权价组织认购、认沽两侧行情。",
    key: "product_code + contract_month + strike_price",
    params: tdxExtOptionChainParams,
    fields: tdxExtOptionChainFields,
    paramsExample: `# 苹果期权T型报价
client.call("option_chain_tdx", product_code="AP", contract_month="202610", limit=3)`,
    exampleColumns: ["product_code", "product_name", "exchange", "contract_month", "strike_price", "call_instrument_id", "call_last_price", "call_bid1_price", "call_bid1_volume", "call_ask1_price", "call_ask1_volume", "call_bid5_price", "call_ask5_price", "put_instrument_id", "put_last_price", "put_bid1_price", "put_bid1_volume", "put_ask1_price", "put_ask1_volume", "put_bid5_price", "put_ask5_price"],
    exampleRows: [
      ["AP", "苹果", "CZCE", "202610", "6400", "AP2610-C-6400.CZCE", "", "832.5", "1", "1301.5", "1", "", "", "AP2610-P-6400.CZCE", "22.5", "19", "1", "24", "1", "", ""],
      ["AP", "苹果", "CZCE", "202610", "6500", "AP2610-C-6500.CZCE", "", "743", "1", "1206", "1", "", "", "AP2610-P-6500.CZCE", "26", "25.5", "1", "29.5", "1", "", ""],
      ["AP", "苹果", "CZCE", "202610", "6600", "AP2610-C-6600.CZCE", "", "656", "1", "1112.5", "1", "", "", "AP2610-P-6600.CZCE", "35.5", "32.5", "1", "42", "1", "", ""]
    ],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实合约和快照拼接；希腊值和隐含波动率未确认前不展示。"
  }),
  createTdxExtCatalogItem({
    id: "option_kline_tdx",
    title: "期权K线",
    group: "期权数据",
    summary: "请求期权K线，返回OHLC、成交量、持仓量和结算价。",
    key: "instrument_id + trade_time",
    params: tdxExtKlineParams,
    fields: tdxExtKlineFields,
    paramsExample: `# 期权日K
client.call("option_kline_tdx", code="AP2610-C-10000.CZCE", period="day", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_time", "period", "open", "high", "low", "close", "volume", "open_interest", "settlement"],
    exampleRows: [["AP2610-C-10000.CZCE", "AP2610-C-10000", "CZCE", "20260703", "day", "12.5", "13.5", "11", "11.5", "568", "8672", "12.5"]],
    dataSourceLabel: "扩展资产源端K线请求",
    exampleNote: "以下样例来自真实源端K线请求。"
  }),
  createTdxExtCatalogItem({
    id: "option_intraday_today_tdx",
    title: "期权当日分时",
    group: "期权数据",
    summary: "请求期权当日分时，返回价格、均价和分时成交量。",
    key: "instrument_id + time_label",
    params: tdxExtCodeParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 期权当日分时
client.call("option_intraday_today_tdx", code="AP2610-C-10000.CZCE")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["AP2610-C-10000.CZCE", "AP2610-C-10000", "CZCE", "", "09:00", "7", "7", "0"]],
    dataSourceLabel: "扩展资产源端分时请求",
    exampleNote: "以下样例来自真实源端当日分时请求。"
  }),
  createTdxExtCatalogItem({
    id: "option_intraday_history_tdx",
    title: "期权历史分时",
    group: "期权数据",
    summary: "请求指定交易日的期权历史分时。",
    key: "instrument_id + trade_date + time_label",
    params: tdxExtIntradayHistoryParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 期权历史分时
client.call("option_intraday_history_tdx", code="AP2610-C-10000.CZCE", trade_date="20260703")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["AP2610-C-10000.CZCE", "AP2610-C-10000", "CZCE", "20260703", "09:00", "7", "7", "0"]],
    dataSourceLabel: "扩展资产源端历史分时请求",
    exampleNote: "以下样例来自真实源端历史分时请求。"
  }),
  createTdxExtCatalogItem({
    id: "fund_nav_tdx",
    title: "基金净值",
    group: "基金数据",
    summary: "返回可确认的基金净值、累计净值和净值日期；ETF交易类接口仍在ETF数据里。",
    key: "fund_id",
    params: tdxExtCodeParams,
    fields: [
      ["fund_id", "基金代码", "string", "AxData 基金代码"],
      ["symbol", "源端代码", "string", "基金代码"],
      ["fund_type", "基金类型", "string", "基金市场类型"],
      ["name", "名称", "string", "可确认时返回基金名称"],
      ["update_date", "净值日期", "date/string", "净值日期"],
      ["nav", "单位净值", "number", "单位净值"],
      ["accumulated_nav", "累计净值/累计值", "number", "累计净值或累计值"]
    ],
    paramsExample: `# 基金净值
client.call("fund_nav_tdx", code="159007")`,
    exampleColumns: ["fund_id", "symbol", "fund_type", "name", "update_date", "nav", "accumulated_nav"],
    exampleRows: [["159007.FUND", "159007", "开放式基金", "", "20260617", "0.7922", "20560.32"]],
    dataSourceLabel: "本机扩展资产净值缓存",
    exampleNote: "以下样例来自本机真实净值缓存；实际返回会随本机目录更新变化。"
  }),
  createTdxExtCatalogItem({
    id: "fund_nav_series_tdx",
    title: "基金净值走势",
    group: "基金数据",
    summary: "请求基金净值走势，按净值序列理解，不和ETF交易价格混用。",
    key: "instrument_id + trade_time",
    params: tdxExtKlineParams,
    fields: tdxExtKlineFields,
    paramsExample: `# 基金净值走势
client.call("fund_nav_series_tdx", code="159007", period="day", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_time", "period", "open", "high", "low", "close", "volume"],
    exampleRows: [["159007.FUND", "159007", "FUND", "20260618", "day", "0.7922", "0.7922", "0.7922", "0.7922", "0"]],
    dataSourceLabel: "扩展资产源端K线请求",
    exampleNote: "以下样例来自真实源端序列请求；基金应按净值走势理解。"
  }),
  createTdxExtCatalogItem({
    id: "bond_realtime_snapshot_tdx",
    title: "债券实时快照",
    group: "债券数据",
    summary: "请求债券或资金市场品种的当前快照；收益率和剩余期限未确认前不展示。",
    key: "instrument_id",
    params: tdxExtCodeParams,
    fields: tdxExtQuoteFields,
    paramsExample: `# 债券快照
client.call("bond_realtime_snapshot_tdx", code="10YGB.BOND")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "last_price", "pre_close", "volume", "inside_volume", "outside_volume", "bid1_price", "bid1_volume", "ask1_price", "ask1_volume", "bid5_price", "ask5_price"],
    exampleRows: [["10YGB.BOND", "10YGB", "BOND", "20260618", "1.724", "1.723", "250", "191", "59", "", "0", "", "0", "", ""]],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实源端快照请求；收益率字段未确认前不展示。"
  }),
  createTdxExtCatalogItem({
    id: "bond_kline_tdx",
    title: "债券K线",
    group: "债券数据",
    summary: "请求债券或资金市场品种的K线。",
    key: "instrument_id + trade_time",
    params: tdxExtKlineParams,
    fields: tdxExtKlineFields,
    paramsExample: `# 债券日K
client.call("bond_kline_tdx", code="10YGB.BOND", period="day", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_time", "period", "open", "high", "low", "close", "volume"],
    exampleRows: [["10YGB.BOND", "10YGB", "BOND", "20260618", "day", "1.723", "1.725", "1.72", "1.724", "250"]],
    dataSourceLabel: "扩展资产源端K线请求",
    exampleNote: "以下样例来自真实源端K线请求。"
  }),
  createTdxExtCatalogItem({
    id: "fx_realtime_snapshot_tdx",
    title: "外汇实时快照",
    group: "外汇数据",
    summary: "请求外汇当前快照，返回最新价、五档买卖价和日内高低。",
    key: "instrument_id",
    params: tdxExtCodeParams,
    fields: tdxExtQuoteFields,
    paramsExample: `# 外汇快照
client.call("fx_realtime_snapshot_tdx", code="USDCNY.FX")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "last_price", "high", "low", "bid1_price", "bid1_volume", "ask1_price", "ask1_volume", "bid5_price", "bid5_volume", "ask5_price", "ask5_volume"],
    exampleRows: [["USDCNY.FX", "USDCNY", "FX", "20260619", "6.7693", "6.7705", "6.7658", "6.7683", "0", "6.7703", "0", "", "0", "", "0"]],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实源端快照请求；实际数值会随行情变化。"
  }),
  createTdxExtCatalogItem({
    id: "fx_kline_tdx",
    title: "外汇K线",
    group: "外汇数据",
    summary: "请求外汇K线。",
    key: "instrument_id + trade_time",
    params: tdxExtKlineParams,
    fields: tdxExtKlineFields,
    paramsExample: `# 外汇日K
client.call("fx_kline_tdx", code="USDCNY.FX", period="day", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_time", "period", "open", "high", "low", "close", "volume"],
    exampleRows: [["USDCNY.FX", "USDCNY", "FX", "20260618", "day", "6.7575", "6.77", "6.7573", "6.7575", "0"]],
    dataSourceLabel: "扩展资产源端K线请求",
    exampleNote: "以下样例来自真实源端K线请求。"
  }),
  createTdxExtCatalogItem({
    id: "fx_intraday_today_tdx",
    title: "外汇当日分时",
    group: "外汇数据",
    summary: "请求外汇当日分时。",
    key: "instrument_id + time_label",
    params: tdxExtCodeParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 外汇当日分时
client.call("fx_intraday_today_tdx", code="USDCNY.FX")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["USDCNY.FX", "USDCNY", "FX", "", "05:00", "6.7575", "6.7575", "0"]],
    dataSourceLabel: "扩展资产源端分时请求",
    exampleNote: "以下样例来自真实源端当日分时请求。"
  }),
  createTdxExtCatalogItem({
    id: "fx_intraday_history_tdx",
    title: "外汇历史分时",
    group: "外汇数据",
    summary: "请求指定日期的外汇历史分时。",
    key: "instrument_id + trade_date + time_label",
    params: tdxExtIntradayHistoryParams,
    fields: tdxExtIntradayFields,
    paramsExample: `# 外汇历史分时
client.call("fx_intraday_history_tdx", code="USDCNY.FX", trade_date="20260618")`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "average_price", "volume"],
    exampleRows: [["USDCNY.FX", "USDCNY", "FX", "20260618", "05:00", "6.7575", "6.7575", "0"]],
    dataSourceLabel: "扩展资产源端历史分时请求",
    exampleNote: "以下样例来自真实源端历史分时请求。"
  }),
  createTdxExtCatalogItem({
    id: "fx_trades_history_tdx",
    title: "外汇历史逐笔",
    group: "外汇数据",
    summary: "请求指定日期外汇逐笔明细。外汇样本可能没有成交量和开平类型，按源端真实值返回。",
    key: "instrument_id + trade_date + time_label",
    params: tdxExtTradesHistoryParams,
    fields: tdxExtTradeFields,
    paramsExample: `# 外汇历史逐笔
client.call("fx_trades_history_tdx", code="USDCNY.FX", trade_date="20260618", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "volume", "position_change", "open_close_type"],
    exampleRows: [
      ["USDCNY.FX", "USDCNY", "FX", "20260618", "00:42:02", "6.7658", "0", "0", ""],
      ["USDCNY.FX", "USDCNY", "FX", "20260618", "00:52:02", "6.7671", "0", "0", ""]
    ],
    dataSourceLabel: "扩展资产源端历史逐笔请求",
    exampleNote: "以下样例来自真实源端历史逐笔请求；默认返回最新一页逐笔，外汇成交量可能为 0，all=true 时自动翻页并按时间顺序返回。"
  }),
  createTdxExtCatalogItem({
    id: "fx_trades_today_tdx",
    title: "外汇当日逐笔",
    group: "外汇数据",
    summary: "请求外汇当日逐笔明细。外汇样本可能没有成交量和开平类型，按源端真实值返回。",
    key: "instrument_id + time_label",
    params: tdxExtTradesTodayParams,
    fields: tdxExtTradeFields,
    paramsExample: `# 外汇当日逐笔
client.call("fx_trades_today_tdx", code="USDCNY.FX", limit=3)`,
    exampleColumns: ["instrument_id", "symbol", "exchange", "trade_date", "time_label", "price", "volume", "position_change", "open_close_type"],
    exampleRows: [
      ["USDCNY.FX", "USDCNY", "FX", "", "00:42:02", "6.7658", "0", "0", ""],
      ["USDCNY.FX", "USDCNY", "FX", "", "00:52:02", "6.7671", "0", "0", ""]
    ],
    dataSourceLabel: "扩展资产源端当日逐笔请求",
    exampleNote: "以下样例来自真实源端当日逐笔请求；默认返回最新一页逐笔，外汇成交量可能为 0，all=true 时自动翻页并按时间顺序返回。"
  }),
  createTdxExtCatalogItem({
    id: "macro_indicator_snapshot_tdx",
    title: "宏观指标快照",
    group: "宏观数据",
    summary: "请求宏观指标最近值；单位未确认时保持为空。",
    key: "indicator_id",
    params: tdxExtCodeParams,
    fields: [
      ["indicator_id", "指标代码", "string", "AxData 宏观指标代码"],
      ["symbol", "源端代码", "string", "源端指标代码"],
      ["name", "指标名称", "string", "可确认时返回指标名称"],
      ["indicator_category", "指标分类", "string", "可确认时返回"],
      ["value", "最新值", "number", "最新值"],
      ["period_date", "指标期", "date/string", "指标期日期"],
      ["pre_value", "上一期值", "number", "上一期值"],
      ["unit", "单位", "string", "已确认时返回"],
      ["frequency", "发布频度", "string", "已确认时返回"]
    ],
    paramsExample: `# 宏观指标快照
client.call("macro_indicator_snapshot_tdx", code="1_GDP.MACRO")`,
    exampleColumns: ["indicator_id", "symbol", "name", "indicator_category", "value", "period_date", "pre_value", "unit", "frequency"],
    exampleRows: [["1_GDP.MACRO", "1_GDP", "", "1", "1401879.25", "20251231", "1348066.25", "亿元", "年"]],
    dataSourceLabel: "扩展资产源端实时请求",
    exampleNote: "以下样例来自真实源端请求；单位和发布频度只在已确认时返回。"
  }),
  createTdxExtCatalogItem({
    id: "macro_indicator_series_tdx",
    title: "宏观指标序列",
    group: "宏观数据",
    summary: "请求宏观指标序列，返回日期和值；单位未确认时保持为空。",
    key: "indicator_id + period_date",
    params: tdxExtKlineParams,
    fields: [
      ["indicator_id", "指标代码", "string", "AxData 宏观指标代码"],
      ["symbol", "源端代码", "string", "源端指标代码"],
      ["name", "指标名称", "string", "可确认时返回指标名称"],
      ["period_date", "指标期", "date/string", "指标期日期"],
      ["period", "周期", "string", "序列周期"],
      ["value", "本期值", "number", "本期值"],
      ["open", "开值", "number", "源端有值时返回"],
      ["high", "高值", "number", "源端有值时返回"],
      ["low", "低值", "number", "源端有值时返回"],
      ["unit", "单位", "string", "已确认时返回"],
      ["frequency", "发布频度", "string", "已确认时返回"]
    ],
    paramsExample: `# 宏观指标序列
client.call("macro_indicator_series_tdx", code="1_GDP.MACRO", period="day", limit=3)`,
    exampleColumns: ["indicator_id", "symbol", "period_date", "period", "value", "open", "high", "low", "unit", "frequency"],
    exampleRows: [["1_GDP.MACRO", "1_GDP", "20251231", "day", "1401879.25", "1401879.25", "1401879.25", "1401879.25", "亿元", "年"]],
    dataSourceLabel: "扩展资产源端序列请求",
    exampleNote: "以下样例来自真实源端序列请求；单位和发布频度只在已确认时返回。"
  })
];

tdxCatalogItems.push(...tdxExtCatalogItems);

tdxCatalogItems.push({
  id: "stock_realtime_snapshot_tdx",
  group: "通达信/股票数据/实时数据",
  title: "实时快照",
  name: "stock_realtime_snapshot_tdx",
  method: "POST",
  path: "/v1/request/stock_realtime_snapshot_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "instrument_id",
  limit: "每个标的返回一行当前行情快照；批量 code 会合并返回",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前行情快照，返回价格、成交量额、内外盘、买一卖一、已解析盘中指标和派生指标。",
  description: "这个接口按股票代码请求当前行情快照，每个标的一般返回 1 行，适合做实时列表和个股详情页的行情总览。涨速、短换手、2分钟金额、开盘抢筹、量涨速、委比来自实时快照解析；开盘涨幅、最高涨幅、最低涨幅、均价、均涨幅、回头波、攻击波、内外比、开盘占比、封单额、买卖一量差由当前快照字段计算。",
  overview: [
    ["接口名称", "stock_realtime_snapshot_tdx"],
    ["接口功能", "获取当前行情快照"]
  ],
  paramsExample: `# 单个标的
client.call("stock_realtime_snapshot_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_realtime_snapshot_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: realtimeSnapshotFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_realtime_snapshot_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_realtime_snapshot_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_realtime_snapshot_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_order_book_tdx",
  group: "通达信/股票数据/实时数据",
  title: "五档盘口",
  name: "stock_order_book_tdx",
  method: "POST",
  path: "/v1/request/stock_order_book_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "instrument_id,level",
  limit: "每个标的返回 1-5 档盘口；批量 code 会合并返回",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前五档盘口快照，返回买一到买五、卖一到卖五的价格和量。",
  description: "这个接口按股票代码请求当前盘口快照，每个标的一般返回 5 行，一行对应一个盘口档位。",
  overview: [
    ["接口名称", "stock_order_book_tdx"],
    ["接口功能", "获取当前五档盘口"]
  ],
  paramsExample: `# 单个标的
client.call("stock_order_book_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_order_book_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: orderBookFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_order_book_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_order_book_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_order_book_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_intraday_buy_sell_strength_tdx",
  group: "通达信/股票数据/实时数据",
  title: "买卖力道",
  name: "stock_intraday_buy_sell_strength_tdx",
  method: "POST",
  path: "/v1/request/stock_intraday_buy_sell_strength_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "instrument_id,minute_time,minute_index",
  limit: "返回当前通达信分时页买卖力道副图序列；不支持传日期或时间",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取通达信当前个股分时页下方买卖力道副图数据。",
  description: "这个接口只按股票代码请求当前分时副图买卖力道，不是历史接口，也不能指定日期或某一分钟。",
  overview: [
    ["接口名称", "stock_intraday_buy_sell_strength_tdx"],
    ["接口功能", "获取当前个股分时副图买卖力道"],
    ["数据粒度", "分时副图点"]
  ],
  paramsExample: `# 单个标的
client.call("stock_intraday_buy_sell_strength_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_intraday_buy_sell_strength_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: intradayBuySellStrengthFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_intraday_buy_sell_strength_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_intraday_buy_sell_strength_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_buy_sell_strength_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_intraday_volume_comparison_tdx",
  group: "通达信/股票数据/实时数据",
  title: "成交对比",
  name: "stock_intraday_volume_comparison_tdx",
  method: "POST",
  path: "/v1/request/stock_intraday_volume_comparison_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "盘中现用现查",
  key: "instrument_id,minute_time,minute_index",
  limit: "返回当前通达信分时页成交对比副图序列；不支持传日期或时间",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取通达信当前个股分时页下方成交对比副图数据。",
  description: "这个接口只按股票代码请求当前分时副图成交对比，返回今日和昨日同分时点累计成交量；不能指定日期或某一分钟。",
  overview: [
    ["接口名称", "stock_intraday_volume_comparison_tdx"],
    ["接口功能", "获取当前个股分时副图成交对比"],
    ["数据粒度", "分时副图点"]
  ],
  paramsExample: `# 单个标的
client.call("stock_intraday_volume_comparison_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_intraday_volume_comparison_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fieldColumns: ["字段", "中文名", "类型", "说明"],
  fields: intradayVolumeComparisonFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_intraday_volume_comparison_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_intraday_volume_comparison_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_volume_comparison_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_intraday_today_tdx",
  group: "通达信/股票数据/行情数据",
  title: "当日分时",
  name: "stock_intraday_today_tdx",
  method: "POST",
  path: "/v1/request/stock_intraday_today_tdx",
  status: "ready",
  icon: Activity,
  cadence: "盘中现用现查",
  key: "instrument_id,time_label",
  limit: "不传日期，只返回当前交易日已经产生的分时点",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前交易日分时图数据，包含分时价格、分时均价和分钟成交量。",
  description: "这个接口返回当前交易日已经产生的分时走势图数据，不是 K 线，没有 open/high/low/close，也不做复权价格计算。响应本身不带日期，分时点时间由返回顺序映射得到。",
  overview: [
    ["接口名称", "stock_intraday_today_tdx"],
    ["接口功能", "获取当前交易日分时走势图"],
    ["时间范围", "盘中返回已产生分时点；收盘后通常为 09:31 至 15:00 的完整分时"],
    ["区别", "当日分时不传日期；历史分时需要传 trade_date"]
  ],
  paramsExample: `# 单个
client.call("stock_intraday_today_tdx", code="000001.SZ")

# 批量：Python SDK 推荐列表写法
client.call("stock_intraday_today_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组"]],
  fields: intradayTodayFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_intraday_today_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_intraday_today_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_today_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"fields":["instrument_id","time_label","price","avg_price","volume"],"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_intraday_history_tdx",
  group: "通达信/股票数据/行情数据",
  title: "历史分时",
  name: "stock_intraday_history_tdx",
  method: "POST",
  path: "/v1/request/stock_intraday_history_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_time",
  limit: "返回所选交易日的分时点；完整 A 股交易日通常为 240 个点",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取指定交易日的历史分时价格和分钟成交量。",
  description: "这个接口返回单只或多只标的在指定交易日的分时走势，不是 K 线，不做复权价格计算，也不写入本地数据层。",
  overview: [
    ["接口名称", "stock_intraday_history_tdx"],
    ["接口功能", "获取指定交易日历史分时走势"],
    ["数据粒度", "分钟分时点"]
  ],
  paramsNote: "必须传 code 和 trade_date；trade_date 支持 YYYYMMDD 或 YYYY-MM-DD。",
  paramsExample: `# 单个标的
client.call("stock_intraday_history_tdx", code="000001.SZ", trade_date="20260519")

# 批量请求多个标的
client.call("stock_intraday_history_tdx", code=["000001.SZ", "600000.SH"], trade_date="20260519")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
  ],
  fields: intradayHistoryFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_intraday_history_tdx", code="000001.SZ", trade_date="20260519")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_intraday_history_tdx", code="000001.SZ", trade_date="20260519")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","trade_date":"20260519"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_intraday_recent_history_tdx",
  group: "通达信/股票数据/行情数据",
  title: "近期历史分时",
  name: "stock_intraday_recent_history_tdx",
  method: "POST",
  path: "/v1/request/stock_intraday_recent_history_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_time",
  limit: "返回近期交易日的分时点；完整 A 股交易日通常为 240 个点",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取近期交易日历史分时图数据，包含分时价格、分时均价、分钟成交量、昨收价和开盘价。",
  description: "这个接口适合补充近期历史分时图上的均价线和开盘价。它不是 K 线，不做复权价格计算，也不写入本地数据层。",
  overview: [
    ["接口名称", "stock_intraday_recent_history_tdx"],
    ["接口功能", "获取近期交易日历史分时图"],
    ["数据粒度", "分钟分时点"],
    ["区别", "相比历史分时，多返回分时均价和开盘价"]
  ],
  paramsNote: "必须传 code 和 trade_date；trade_date 支持 YYYYMMDD 或 YYYY-MM-DD。",
  paramsExample: `# 单个标的
client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")

# 批量请求多个标的
client.call("stock_intraday_recent_history_tdx", code=["000001.SZ", "600000.SH"], trade_date="20260519")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
  ],
  fields: intradayRecentHistoryFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_intraday_recent_history_tdx", code="000001.SZ", trade_date="20260519")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_intraday_recent_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","trade_date":"20260519"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_trades_today_tdx",
  group: "通达信/股票数据/行情数据",
  title: "当日成交明细",
  name: "stock_trades_today_tdx",
  method: "POST",
  path: "/v1/request/stock_trades_today_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_time,trade_index",
  limit: "返回当前交易日服务器可取的成交明细；分页由后端处理",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取当前交易日成交明细；请求式分页由后端处理。",
  description: "这个接口按股票代码请求当前交易日的成交明细，不是实时订阅流，也不写入本地数据层。",
  overview: [
    ["接口名称", "stock_trades_today_tdx"],
    ["接口功能", "获取当前交易日成交明细"],
    ["数据粒度", "成交明细"]
  ],
  paramsExample: `# 单个标的
client.call("stock_trades_today_tdx", code="000001.SZ")

# 批量请求多个标的
client.call("stock_trades_today_tdx", code=["000001.SZ", "600000.SH"])`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"]
  ],
  fields: tradeDetailTodayFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_trades_today_tdx", code="000001.SZ")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_trades_today_tdx", code="000001.SZ")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_trades_today_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
});

tdxCatalogItems.push({
  id: "stock_trades_history_tdx",
  group: "通达信/股票数据/行情数据",
  title: "历史成交明细",
  name: "stock_trades_history_tdx",
  method: "POST",
  path: "/v1/request/stock_trades_history_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_datetime,trade_index",
  limit: "返回指定交易日服务器可取的成交明细；分页由后端处理",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "获取指定交易日成交明细；适合复盘某一天逐笔/聚合成交。",
  description: "这个接口按股票代码和交易日期请求历史成交明细，不是 K 线，也不写入本地数据层。",
  overview: [
    ["接口名称", "stock_trades_history_tdx"],
    ["接口功能", "获取指定交易日历史成交明细"],
    ["数据粒度", "成交明细"]
  ],
  paramsExample: `# 单个标的
client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")

# 批量请求多个标的
client.call("stock_trades_history_tdx", code=["000001.SZ", "600000.SH"], trade_date="20260511")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["trade_date", "string", "是", "交易日期，格式 YYYYMMDD 或 YYYY-MM-DD"]
  ],
  fields: tradeDetailHistoryFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_trades_history_tdx", code="000001.SZ", trade_date="20260511")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_trades_history_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","trade_date":"20260511"},"persist":false}'`
});

tdxCatalogItems.push(...klinePeriodSpecs.map(createKlineCatalogItem));

const capitalChangeFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["ts_code", "string", "与 instrument_id 相同，兼容股票事件类字段"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["event_date", "date/string", "事件日期，YYYYMMDD"],
  ["category_raw", "integer", "TDX 原始事件类别码"],
  ["category_name", "string", "按 TDX 客户端内置类别表映射的事件名称"],
  ["c1", "number", "事件参数槽 1；具体含义看 category_raw"],
  ["c2", "number", "事件参数槽 2；具体含义看 category_raw"],
  ["c3", "number", "事件参数槽 3；具体含义看 category_raw"],
  ["c4", "number", "事件参数槽 4；具体含义看 category_raw"],
  ["c1_raw_hex", "string", "参数 1 的 TDX 原始字节，主要用于解析排查"],
  ["c2_raw_hex", "string", "参数 2 的 TDX 原始字节，主要用于解析排查"],
  ["c3_raw_hex", "string", "参数 3 的 TDX 原始字节，主要用于解析排查"],
  ["c4_raw_hex", "string", "参数 4 的 TDX 原始字节，主要用于解析排查"],
  ["record_hex", "string", "完整 TDX 原始记录；源端未带原始记录时返回 AxData 根据事件字段生成的稳定行键"]
];

const capitalChangeCategoryRows = [
  ["1", "除权除息", "直接参与", "现金分红", "配股价", "送转股", "配股"],
  ["2", "送配股上市", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["3", "非流通股上市", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["4", "未知股本变动", "不直接参与", "未知/保留", "未知/保留", "未知/保留", "未知/保留"],
  ["5", "股本变化", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["6", "增发新股", "不直接参与", "保留", "增发价", "增发数量", "保留"],
  ["7", "股份回购", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["8", "增发新股上市", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["9", "转配股上市", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["10", "可转债上市", "不直接参与", "前流通股本", "前总股本", "后流通股本", "后总股本"],
  ["11", "扩缩股", "不直接参与", "保留", "保留", "扩缩股比例", "保留"],
  ["12", "非流通股缩股", "不直接参与", "保留", "保留", "缩股比例", "保留"],
  ["13", "送认购权证", "不直接参与", "权证行权价", "保留", "权证份数/比例", "保留"],
  ["14", "送认沽权证", "不直接参与", "权证行权价", "保留", "权证份数/比例", "保留"],
  ["15", "重整调整", "不直接参与", "通常为 0", "通常为 0", "重整比例", "通常为 0"]
];

tdxCatalogItems.push({
  id: "stock_capital_changes_tdx",
  group: "通达信/股票数据/基础数据",
  title: "股本变迁",
  name: "stock_capital_changes_tdx",
  method: "POST",
  path: "/v1/request/stock_capital_changes_tdx",
  status: "ready",
  icon: FileText,
  cadence: "现用现查",
  key: "instrument_id,event_date,category_raw",
  limit: "可按股票范围或所选标的返回通达信 0x000f 股本变迁记录；category 可缩小到除权除息等类别",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "查询通达信 0x000f 股本变迁、除权除息等事件记录，是复权因子计算的追溯依据。",
  description: "这个接口返回 TDX 0x000f 事件的 AxData 化视图，不做复权价格计算，也不写入本地数据层。",
  overview: [
    ["接口名称", "stock_capital_changes_tdx"],
    ["接口功能", "查询通达信股本变迁/除权除息原始记录"],
    ["复权关系", "当前 stock_adj_factor_tdx 只直接使用 category=1 除权除息事件和未复权日 K 计算"]
  ],
  paramsNote: "code 不填时按 scope 展开股票池；不传 category 时返回全部事件；传 category=xdxr 或 1 时只返回除权除息记录。",
  paramsExample: `# 单票全部股本变迁事件
client.call("stock_capital_changes_tdx", code="000001.SZ")

# 只看除权除息事件
client.call("stock_capital_changes_tdx", code="000001.SZ", category="xdxr")

# 全市场源端查询口径
client.call("stock_capital_changes_tdx", scope="all", category="xdxr")

# 批量查询
client.call("stock_capital_changes_tdx", code=["000001.SZ", "600000.SH"], category="xdxr")`,
  params: [
    ["scope", "string/list", "否", "股票范围：code 不传或为 all 时生效；all 全部、main 主板、star 科创板、chinext 创业板、bse 北交所、cdr CDR；默认 all"],
    ["code", "string/list", "否", "证券代码：可选；支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串。不填则按股票范围请求全量"],
    ["category", "integer/string/list", "否", "可选事件类别过滤：可传任意 TDX 原始类别码；常用别名：1/xdxr 为除权除息，5/equity 为股本变化，15/restructure 为重整调整"]
  ],
  fields: capitalChangeFields,
  dataExamples: [
    {
      id: "capital-change-categories",
      title: "类别码参考",
      icon: FileText,
      note: "c1/c2/c3/c4 是固定的 4 个参数槽；同一列在不同 category 下含义不同。当前复权因子只直接使用 category=1；其他类别作为股本变迁和公司行为证据保留。",
      columns: ["category", "名称", "复权因子关系", "c1", "c2", "c3", "c4"],
      rows: capitalChangeCategoryRows
    }
  ],
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_capital_changes_tdx", code="000001.SZ", category="xdxr")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_capital_changes_tdx", code="000001.SZ", category="xdxr")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_capital_changes_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","category":"xdxr"},"persist":false}'`
});

const adjFactorFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["ts_code", "string", "与 instrument_id 相同，兼容 AxData core adj_factor 表字段"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["trade_date", "date/string", "交易日期，YYYYMMDD"],
  ["adj_factor", "number", "按请求复权口径计算出的复权因子"]
];

tdxCatalogItems.push({
  id: "stock_adj_factor_tdx",
  group: "通达信/股票数据/行情数据",
  title: "复权因子",
  name: "stock_adj_factor_tdx",
  method: "POST",
  path: "/v1/request/stock_adj_factor_tdx",
  status: "ready",
  icon: BarChart3,
  cadence: "现用现查",
  key: "instrument_id,trade_date",
  limit: "默认返回所选标的全量日线交易日；批量 code 会逐代码请求后合并",
  permission: "本机自用可直接请求；开放给局域网时再配置 token",
  summary: "用通达信 0x000f 的 category=1 除权除息事件和未复权日 K，重算每日前复权或后复权因子。",
  description: "这个接口返回 AxData 基于股本变迁事件计算出的每日复权因子，不返回复权后的 K 线价格；它和通达信自带复权 K 可能存在口径误差。",
  overview: [
    ["接口名称", "stock_adj_factor_tdx"],
    ["接口功能", "计算通达信股票每日复权因子"],
    ["计算依据", "stock_capital_changes_tdx 的 category=1 除权除息事件 + 未复权日 K"],
    ["复权方向", "adjust=qfq 前复权因子；adjust=hfq 后复权因子"],
    ["口径说明", "不承诺等同通达信自带复权 K，可能存在误差"]
  ],
  paramsNote: "不传 adjust 时默认 qfq；anchor_date 只在 qfq 下可传，hfq 不使用锚点。",
  paramsExample: `# 普通前复权因子
client.call("stock_adj_factor_tdx", code="000001.SZ", adjust="qfq")

# 定点前复权因子
client.call("stock_adj_factor_tdx", code="000001.SZ", adjust="qfq", anchor_date="2024-12-31")

# 后复权因子
client.call("stock_adj_factor_tdx", code="000001.SZ", adjust="hfq")`,
  params: [
    ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
    ["adjust", "string", "否", "复权方向：qfq 前复权因子，hfq 后复权因子；默认 qfq"],
    ["anchor_date", "string", "否", "可选的前复权锚点日期，格式 YYYYMMDD 或 YYYY-MM-DD；仅 adjust=qfq 时使用"]
  ],
  fields: adjFactorFields,
  callModes: tdxSourceRequestCallModes,
  sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_adj_factor_tdx", code="000001.SZ", adjust="qfq")
print(df)`,
  remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_adj_factor_tdx", code="000001.SZ", adjust="qfq")
print(df)`,
  curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_adj_factor_tdx" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ","adjust":"qfq"},"persist":false}'`
});

const financeCommonFields = [
  ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
  ["symbol", "string", "交易所原始六位代码"],
  ["tdx_code", "string", "TDX 带市场前缀代码，例如 sz000001"],
  ["exchange", "string", "AxData 交易所代码：SSE、SZSE、BSE"],
  ["updated_date", "date/string", "财务快照更新/报告日期，YYYYMMDD"]
];

const financeSummaryFields = [
  ...financeCommonFields,
  ["ipo_date", "date/string", "TDX 财务快照携带的上市日期，YYYYMMDD"],
  ["total_share", "number", "总股本，单位：股"],
  ["float_share", "number", "流通股本，单位：股"],
  ["eps", "number", "每股收益，单位：元/股"],
  ["bps", "number", "每股净资产，单位：元/股"],
  ["total_assets", "number", "总资产，单位：元"],
  ["net_assets", "number", "净资产，单位：元"],
  ["revenue", "number", "营业收入，单位：元"],
  ["net_profit", "number", "净利润，单位：元"],
  ["operating_cashflow", "number", "经营现金流量，单位：元"],
  ["shareholder_count", "integer", "股东人数"]
];

const financeShareCapitalFields = [
  ...financeCommonFields,
  ["total_share", "number", "总股本，单位：股"],
  ["float_share", "number", "流通股本，单位：股"],
  ["state_share", "number", "国家股，单位：股"],
  ["founder_legal_person_share", "number", "发起法人股，单位：股"],
  ["legal_person_share", "number", "法人股，单位：股"],
  ["b_share", "number", "B 股股本，单位：股"],
  ["h_share", "number", "H 股股本，单位：股"],
  ["shareholder_count", "integer", "股东人数"]
];

const financeBalanceFields = [
  ...financeCommonFields,
  ["total_assets", "number", "总资产，单位：元"],
  ["current_assets", "number", "流动资产，单位：元"],
  ["fixed_assets", "number", "固定资产，单位：元"],
  ["intangible_assets", "number", "无形资产，单位：元"],
  ["current_liabilities", "number", "流动负债，单位：元"],
  ["long_term_liabilities", "number", "长期负债，单位：元"],
  ["capital_reserve", "number", "资本公积金，单位：元"],
  ["net_assets", "number", "净资产，单位：元"],
  ["accounts_receivable", "number", "应收账款，单位：元"],
  ["inventory", "number", "存货，单位：元"]
];

const financeProfitCashflowFields = [
  ...financeCommonFields,
  ["revenue", "number", "营业收入，单位：元"],
  ["main_business_profit", "number", "主营业务利润，单位：元"],
  ["operating_profit", "number", "营业利润，单位：元"],
  ["investment_income", "number", "投资收益，单位：元"],
  ["operating_cashflow", "number", "经营现金流量，单位：元"],
  ["total_cashflow", "number", "总现金流量，单位：元"],
  ["total_profit", "number", "利润总额，单位：元"],
  ["after_tax_profit", "number", "税后利润，单位：元"],
  ["net_profit", "number", "净利润，单位：元"],
  ["undistributed_profit", "number", "未分配利润，单位：元"],
  ["eps", "number", "每股收益，单位：元/股"],
  ["bps", "number", "每股净资产，单位：元/股"]
];

const financeProfileFields = [
  ...financeCommonFields,
  ["ipo_date", "date/string", "TDX 财务快照携带的上市日期，YYYYMMDD"],
  ["province_raw", "integer", "TDX 财务快照携带的地区/省份原始码"],
  ["province_name", "string", "由 province_raw 通过 AxData TDX 地区码表映射得到的地区/省份名称"],
  ["province_board_name", "string", "由 province_raw 通过 AxData TDX 地区码表映射得到的地区板块名称"],
  ["province_board_code", "string", "由 province_raw 通过 AxData TDX 地区码表映射得到的地区板块代码"],
  ["industry_raw", "integer", "TDX 财务快照携带的行业原始码"],
  ["tdx_industry_code", "string", "由股票代码通过 AxData TDX 行业码表映射得到的行业板块代码"],
  ["tdx_industry_name", "string", "由股票代码通过 AxData TDX 行业码表映射得到的行业板块名称"],
  ["tdx_industry_path", "string", "由股票代码通过 AxData TDX 行业码表映射得到的行业板块路径"],
  ["tdx_research_industry_code", "string", "由股票代码通过 AxData TDX 行业码表映射得到的研究行业代码"],
  ["tdx_research_industry_name", "string", "由股票代码通过 AxData TDX 行业码表映射得到的研究行业名称"],
  ["tdx_research_industry_path", "string", "由股票代码通过 AxData TDX 行业码表映射得到的研究行业路径"]
];

type FinanceViewSpec = {
  id: string;
  title: string;
  summary: string;
  functionText: string;
  key: string;
  fields: string[][];
  supportsMapRoot?: boolean;
};

const financeViewSpecs: FinanceViewSpec[] = [
  {
    id: "stock_finance_summary_tdx",
    title: "财务基础摘要",
    summary: "获取通达信 0x0010 基础财务快照中的常用财务、股本和每股指标。",
    functionText: "获取基础财务摘要",
    key: "instrument_id,updated_date",
    fields: financeSummaryFields
  },
  {
    id: "stock_share_capital_tdx",
    title: "股本结构",
    summary: "获取通达信 0x0010 财务快照中的总股本、流通股本、股本类别和股东人数。",
    functionText: "获取股本结构快照",
    key: "instrument_id,updated_date",
    fields: financeShareCapitalFields
  },
  {
    id: "stock_balance_summary_tdx",
    title: "资产负债摘要",
    summary: "获取通达信 0x0010 财务快照中的资产、负债、净资产、应收和存货等摘要字段。",
    functionText: "获取资产负债摘要",
    key: "instrument_id,updated_date",
    fields: financeBalanceFields
  },
  {
    id: "stock_profit_cashflow_summary_tdx",
    title: "利润现金流摘要",
    summary: "获取通达信 0x0010 财务快照中的收入、利润、现金流和每股指标摘要。",
    functionText: "获取利润现金流摘要",
    key: "instrument_id,updated_date",
    fields: financeProfitCashflowFields
  },
  {
    id: "stock_finance_profile_tdx",
    title: "财务资料标签",
    summary: "获取通达信 0x0010 财务快照中的上市日期、地区和行业标签字段。",
    functionText: "获取财务资料标签",
    key: "instrument_id,updated_date",
    fields: financeProfileFields,
    supportsMapRoot: true
  }
];

function createFinanceCatalogItem(spec: FinanceViewSpec): CatalogItem {
  return {
    id: spec.id,
    group: "通达信/股票数据/财务数据",
    title: spec.title,
    name: spec.id,
    method: "POST",
    path: `/v1/request/${spec.id}`,
    status: "ready",
    icon: FileText,
    cadence: "现用现查",
    key: spec.key,
    limit: "批量 code 会合并返回；空记录会过滤",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: spec.summary,
    description: "这个接口来自 TDX 0x0010 基础财务快照，适合做快速字段预览和轻量对照；它不是完整 F10 财务报表，也不写入本地数据层。",
    overview: [
      ["接口名称", spec.id],
      ["接口功能", spec.functionText],
      ...(spec.supportsMapRoot
        ? [["映射来源", "默认使用 AxData 内置 TDX 码表快照；传 map_root 时读取用户本地码表"]]
        : [])
    ],
    paramsNote: spec.supportsMapRoot
      ? "map_root 可选；不传时使用内置映射快照，传入时读取该目录下的 incon.dat、tdxzs.cfg、tdxhy.cfg 更新地区和行业映射。"
      : undefined,
    paramsExample: `# 单个标的
client.call("${spec.id}", code="000001.SZ")

# 批量请求多个标的
client.call("${spec.id}", code=["000001.SZ", "600000.SH"])${
      spec.supportsMapRoot
        ? `

# 使用本机 TDX 码表更新映射
client.call("${spec.id}", code="000001.SZ", map_root=r"C:\\APP\\tdx")`
        : ""
    }`,
    params: [
      ["code", "string/list", "是", "证券代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"],
      ...(spec.supportsMapRoot
        ? [
            [
              "map_root",
              "string",
              "否",
              "本地 TDX 码表目录；不传用内置映射，传入时从该目录读取 incon.dat、tdxzs.cfg、tdxhy.cfg"
            ]
          ]
        : [])
    ],
    fields: spec.fields,
    dataExamples: [
      ...(spec.supportsMapRoot
        ? [
            {
              id: `${spec.id}-maps`,
              title: "映射规则",
              icon: Database,
              note: "默认使用 AxData 内置 TDX 码表快照；需要更新时传 map_root 指向本地 TDX 目录。完整码表不在本页展开。",
              columns: ["字段", "使用码表", "说明"],
              rows: [
                ["province_name / province_board_*", "tdxzs.cfg", "由 province_raw 查地区板块名称和代码"],
                ["tdx_industry_*", "tdxhy.cfg + incon.dat", "由股票代码查行业代码，再由 incon.dat 查中文名和路径"],
                [
                  "tdx_research_industry_*",
                  "tdxhy.cfg + incon.dat",
                  "由股票代码查研究行业代码，再由 incon.dat 查中文名和路径"
                ]
              ]
            }
          ]
        : []),
      {
        id: `${spec.id}-units`,
        title: "单位说明",
        icon: Database,
        note: "这些字段直接返回统一后的数值单位。",
        columns: ["字段类型", "单位", "示例字段"],
        rows: [
          ["股本类", "股", "total_share / float_share / b_share / h_share"],
          ["金额类", "元", "total_assets / revenue / net_profit / operating_cashflow"],
          ["每股类", "元/股", "eps / bps"]
        ]
      }
    ],
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("${spec.id}", code="000001.SZ")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("${spec.id}", code="000001.SZ")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/${spec.id}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
  };
}

tdxCatalogItems.push(...financeViewSpecs.map(createFinanceCatalogItem));

type F10CatalogSpec = {
  id: string;
  title: string;
  group: "F10数据" | "短线数据";
  summary: string;
  functionText: string;
  key: string;
  params: string[][];
  paramsNote?: string;
  fields: string[][];
  exampleParams: string;
  curlParams?: F10ParamsObject;
  exampleRow?: Record<string, string | number | boolean | null>;
  exampleRows?: Array<Record<string, string | number | boolean | null>>;
  note?: string;
};

type F10ParamValue = string | number | boolean | Array<string | number | boolean>;
type F10ParamsObject = Record<string, F10ParamValue>;

// F10 field and preview rows are generated from the backend F10 contract and live source samples.
const f10ParamCatalog: Record<string, string[][]> = {
  "stock_ipo_listing_profile_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ]
  ],
  "stock_index_constituent_changes_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；不传返回全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；不传返回全部记录"
    ]
  ],
  "stock_company_profile_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "type",
      "string",
      "否",
      "资料类型：listing 发行上市信息，index_change 指数调入调出；默认 listing"
    ]
  ],
  "stock_business_composition_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "period",
      "string",
      "否",
      "报告期，格式 YYYYMMDD；不传时返回全部可用报告期"
    ]
  ],
  "stock_financial_statement_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ]
  ],
  "stock_financial_diagnosis_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "dimension",
      "string",
      "否",
      "诊断维度：operation 营运能力、profit 盈利能力、growth 成长能力、cashflow 现金流、asset_quality 资产质量、z_score Z值预警、score 综合评分；默认 score"
    ]
  ],
  "stock_forecast_consensus_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ]
  ],
  "stock_dividend_history_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_year",
      "string",
      "否",
      "起始年份，可选；不传返回全部记录"
    ],
    [
      "end_year",
      "string",
      "否",
      "结束年份，可选；不传返回全部记录"
    ]
  ],
  "stock_dividend_metrics_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "metric",
      "string",
      "否",
      "指标：dividend_yield 股息率、payout_ratio 股利支付率、cash_financing 派现融资；默认 dividend_yield"
    ],
    [
      "view",
      "string",
      "否",
      "展示方式：trend 走势、ranking 排名、summary 总览；不传时 dividend_yield/payout_ratio 默认 trend，cash_financing 默认 summary"
    ]
  ],
  "stock_equity_financing_events_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "event_type",
      "string",
      "否",
      "事件类型：placement 增发、rights_issue 配股、incentive 股权激励、convertible_bond 可转债；默认 placement"
    ]
  ],
  "stock_private_placement_allocations_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "event_date",
      "string",
      "否",
      "增发日期，格式 YYYYMMDD 或 YYYY-MM-DD；不传返回全部可用增发日期的获配明细"
    ]
  ],
  "stock_shareholder_change_plans_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "direction",
      "string",
      "否",
      "方向筛选：increase 增持、decrease 减持；不传返回全部方向"
    ],
  ],
  "stock_northbound_holding_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；不传返回全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；不传返回全部记录"
    ]
  ],
  "stock_margin_trading_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；不传返回源端全部记录，传入后按统计日期筛选"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；不传返回源端全部记录，传入后按统计日期筛选"
    ]
  ],
  "stock_chip_distribution_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "按统计日期过滤的起始日期；不传返回源端本次给出的全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "按统计日期过滤的结束日期；不传返回源端本次给出的全部记录"
    ]
  ],
  "stock_research_reports_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "rating",
      "string",
      "否",
      "评级筛选：all、buy、overweight、neutral、underweight、sell；默认 all"
    ],
    [
      "keyword",
      "string",
      "否",
      "标题关键字，可选"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ],
    [
      "cursor",
      "string",
      "否",
      "分页游标；不传从第一页开始"
    ]
  ],
  "stock_analyst_rating_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "按评级统计日期过滤的起始日期；不传返回源端本次给出的记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "按评级统计日期过滤的结束日期；不传返回源端本次给出的记录"
    ]
  ],
  "stock_institution_holding_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "按报告日期过滤的起始日期；不传返回源端本次给出的全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "按报告日期过滤的结束日期；不传返回源端本次给出的全部记录"
    ]
  ],
  "stock_governance_guarantees_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "period",
      "string",
      "否",
      "报告期；不传自动取最新可用报告期"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20；该接口单期可能有大量明细"
    ]
  ],
  "stock_violation_cases_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "按立案日期过滤的起始日期；不传返回源端本次给出的全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "按立案日期过滤的结束日期；不传返回源端本次给出的全部记录"
    ]
  ],
  "stock_regulatory_actions_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "按处罚公布日期过滤的起始日期；不传返回源端本次给出的全部记录"
    ],
    [
      "end_date",
      "string",
      "否",
      "按处罚公布日期过滤的结束日期；不传返回源端本次给出的全部记录"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "stock_score_summary_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ]
  ],
  "stock_disclosure_feed_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "category",
      "string",
      "否",
      "类型：news 新闻、announcement 公告、roadshow 路演；默认 announcement"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "stock_event_drivers_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；按事件创建日期过滤"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；按事件创建日期过滤"
    ],
    [
      "include_detail",
      "boolean",
      "否",
      "是否补充详情正文，默认 false"
    ]
  ],
  "stock_topic_exposure_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "topic_type",
      "string",
      "否",
      "题材类型：sector 板块题材、theme 主题题材；默认 theme"
    ]
  ],
  "concept_related_boards_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ]
  ],
  "concept_constituents_tdx": [
    [
      "concept_code",
      "string",
      "是",
      "板块代码；先用相关板块接口按股票代码查询，取返回的 board_code 填入"
    ],
    [
      "count",
      "integer",
      "否",
      "返回前多少只，默认 20，最大 500"
    ]
  ],
  "concept_capital_flow_tdx": [
    [
      "concept_code",
      "string",
      "是",
      "题材或行业 ID；可先从个股题材接口返回的 topic_id 中选择，部分 ID 可能没有资金走势"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；按 date 过滤"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；按 date 过滤"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20，最大 500"
    ]
  ],
  "concept_control_series_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；按 date 过滤"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；按 date 过滤"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "concept_control_ranking_tdx": [
    [
      "concept_code",
      "string",
      "是",
      "题材或行业 ID；可先从个股题材接口返回的 topic_id 中选择，部分 ID 可能没有控盘榜单"
    ],
    [
      "count",
      "integer",
      "否",
      "返回前多少条榜单记录，默认 20，最大 500；记录按日期榜单拍平后计数"
    ]
  ],
  "concept_constituent_comparison_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "concept_code",
      "string",
      "是",
      "题材 ID"
    ],
    [
      "compare_type",
      "string",
      "否",
      "对比类型：return 涨幅，financial 财务；默认 return"
    ],
    [
      "sort_by",
      "string",
      "否",
      "源端排序字段，默认 zdf；实测不同字段可能仍按源端默认排序"
    ]
  ],
  "stock_valuation_metrics_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；按 date 过滤"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；按 date 过滤"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "stock_valuation_series_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "metric",
      "string",
      "否",
      "指标：pe、pb、pcf、ps；默认 pe"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选；按 date 过滤"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选；按 date 过滤"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "stock_valuation_band_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "metric",
      "string",
      "否",
      "指标：pe 或 pb；默认 pe"
    ],
    [
      "start_date",
      "string",
      "否",
      "起始日期，可选"
    ],
    [
      "end_date",
      "string",
      "否",
      "结束日期，可选"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ],
  "stock_return_calendar_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "year",
      "string",
      "否",
      "年份，可选；不传返回全部可用年份"
    ]
  ],
  "stock_market_rankings_tdx": [
    [
      "code",
      "string/list",
      "是",
      "股票代码：支持 000001、000001.SZ、sz000001；批量可传列表或英文逗号分隔字符串"
    ],
    [
      "scope",
      "string",
      "否",
      "范围：market 全市场排名，industry 为传入股票所属行业内排名；默认 market。建议单只股票调用"
    ],
    [
      "count",
      "integer",
      "否",
      "返回条数，默认 20"
    ]
  ]
};

const f10FieldCatalog: Record<string, string[][]> = {
  "stock_ipo_listing_profile_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "stock_type",
      "string",
      "股票类别"
    ],
    [
      "list_date",
      "date/string",
      "上市日期"
    ],
    [
      "issue_method",
      "string",
      "发行方式"
    ],
    [
      "issue_system",
      "string",
      "发行制度"
    ],
    [
      "par_value",
      "number",
      "每股面值，单位：元"
    ],
    [
      "issue_price",
      "number",
      "发行价格，单位：元"
    ],
    [
      "issue_volume",
      "number",
      "发行数量"
    ],
    [
      "raised_amount",
      "number",
      "实际募资总额"
    ],
    [
      "net_raised_amount",
      "number",
      "实际募资净额"
    ],
    [
      "first_open",
      "number",
      "首日开盘价，单位：元"
    ],
    [
      "first_close",
      "number",
      "首日收盘价，单位：元"
    ],
    [
      "lead_underwriter",
      "string",
      "主承销商"
    ],
    [
      "sponsor",
      "string",
      "上市保荐人"
    ]
  ],
  "stock_index_constituent_changes_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "publish_date",
      "date/string",
      "指数调整公布日期"
    ],
    [
      "change_direction",
      "string",
      "指数调入/调出方向"
    ],
    [
      "index_name",
      "string",
      "指数名称"
    ],
    [
      "publish_date_change_pct",
      "number",
      "公布日涨跌幅，单位：%"
    ],
    [
      "effective_date",
      "date/string",
      "指数调整日期"
    ],
    [
      "effective_date_change_pct",
      "number",
      "调整日涨跌幅，单位：%"
    ]
  ],
  "stock_company_profile_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "stock_type",
      "string",
      "股票类别"
    ],
    [
      "list_date",
      "date/string",
      "上市日期"
    ],
    [
      "issue_method",
      "string",
      "发行方式"
    ],
    [
      "issue_system",
      "string",
      "发行制度"
    ],
    [
      "par_value",
      "number",
      "每股面值，单位：元"
    ],
    [
      "issue_price",
      "number",
      "发行价格，单位：元"
    ],
    [
      "issue_volume",
      "number",
      "发行数量"
    ],
    [
      "raised_amount",
      "number",
      "实际募资总额"
    ],
    [
      "net_raised_amount",
      "number",
      "实际募资净额"
    ],
    [
      "first_open",
      "number",
      "首日开盘价，单位：元"
    ],
    [
      "first_close",
      "number",
      "首日收盘价，单位：元"
    ],
    [
      "lead_underwriter",
      "string",
      "主承销商"
    ],
    [
      "sponsor",
      "string",
      "上市保荐人"
    ],
    [
      "publish_date",
      "date/string",
      "指数调整公布日期"
    ],
    [
      "change_direction",
      "string",
      "指数调入/调出方向"
    ],
    [
      "index_name",
      "string",
      "指数名称"
    ],
    [
      "publish_date_change_pct",
      "number",
      "公布日涨跌幅，单位：%"
    ],
    [
      "effective_date",
      "date/string",
      "指数调整日期"
    ],
    [
      "effective_date_change_pct",
      "number",
      "调整日涨跌幅，单位：%"
    ]
  ],
  "stock_business_composition_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "report_period",
      "date/string",
      "报告期"
    ],
    [
      "dimension",
      "string",
      "分类方式"
    ],
    [
      "item_order",
      "integer",
      "序号或层级"
    ],
    [
      "item_name",
      "string",
      "主营构成项目"
    ],
    [
      "revenue",
      "number",
      "主营收入"
    ],
    [
      "revenue_ratio_pct",
      "number",
      "收入占比，单位：%"
    ],
    [
      "cost",
      "number",
      "主营成本"
    ],
    [
      "cost_ratio_pct",
      "number",
      "成本占比，单位：%"
    ],
    [
      "gross_profit",
      "number",
      "毛利"
    ],
    [
      "profit_ratio_pct",
      "number",
      "利润占比，单位：%"
    ],
    [
      "gross_margin_pct",
      "number",
      "毛利率，单位：%"
    ]
  ],
  "stock_financial_statement_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "report_period",
      "date/string",
      "报告期"
    ],
    [
      "cash",
      "number",
      "货币资金"
    ],
    [
      "trading_financial_assets",
      "number",
      "交易性金融资产"
    ],
    [
      "notes_receivable",
      "number",
      "应收票据"
    ],
    [
      "accounts_receivable",
      "number",
      "应收账款"
    ],
    [
      "current_assets",
      "number",
      "流动资产合计"
    ],
    [
      "total_assets",
      "number",
      "资产总计"
    ],
    [
      "short_term_borrowing",
      "number",
      "短期借款"
    ],
    [
      "notes_payable",
      "number",
      "应付票据"
    ],
    [
      "accounts_payable",
      "number",
      "应付账款"
    ],
    [
      "current_liabilities",
      "number",
      "流动负债合计"
    ],
    [
      "total_liabilities",
      "number",
      "负债合计"
    ],
    [
      "share_capital",
      "number",
      "实收资本或股本"
    ],
    [
      "capital_reserve",
      "number",
      "资本公积金"
    ],
    [
      "undistributed_profit",
      "number",
      "未分配利润"
    ],
    [
      "parent_equity",
      "number",
      "归母权益合计"
    ],
    [
      "total_equity",
      "number",
      "所有者权益合计"
    ],
    [
      "liabilities_and_equity",
      "number",
      "负债和股东权益合计"
    ]
  ],
  "stock_financial_diagnosis_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "stock_name",
      "string",
      "股票简称"
    ],
    [
      "compare_group",
      "string",
      "对比行业或板块"
    ],
    [
      "report_period",
      "date/string",
      "报告期"
    ],
    [
      "rank",
      "integer",
      "个股排名"
    ],
    [
      "rank_change",
      "number",
      "排名或评分变化"
    ],
    [
      "rating_code",
      "string",
      "评价等级码"
    ],
    [
      "score",
      "number",
      "源端综合评分"
    ],
    [
      "percentile",
      "number",
      "分位或打败比例"
    ],
    [
      "warning_value",
      "number",
      "Z 值或预警值"
    ]
  ],
  "stock_forecast_consensus_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "forecast_start_year",
      "integer",
      "预测起始年份"
    ],
    [
      "align_flag",
      "string",
      "年份对齐标记"
    ],
    [
      "eps_year1",
      "number",
      "未来第一年预测每股收益"
    ],
    [
      "eps_year2",
      "number",
      "未来第二年预测每股收益"
    ],
    [
      "eps_year3",
      "number",
      "未来第三年预测每股收益"
    ],
    [
      "net_profit_year1",
      "number",
      "未来第一年预测归母净利润"
    ],
    [
      "net_profit_year2",
      "number",
      "未来第二年预测归母净利润"
    ],
    [
      "net_profit_year3",
      "number",
      "未来第三年预测归母净利润"
    ],
    [
      "revenue_year1",
      "number",
      "未来第一年预测营业收入"
    ],
    [
      "revenue_year2",
      "number",
      "未来第二年预测营业收入"
    ],
    [
      "revenue_year3",
      "number",
      "未来第三年预测营业收入"
    ],
    [
      "forecast_institution_count",
      "integer",
      "预测机构数量"
    ]
  ],
  "stock_dividend_history_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "report_period",
      "date/string",
      "分红年度或报告期"
    ],
    [
      "board_date",
      "date/string",
      "董事会日期"
    ],
    [
      "plan",
      "string",
      "分红方案"
    ],
    [
      "eps",
      "number",
      "每股收益"
    ],
    [
      "roe_weighted_pct",
      "number",
      "加权净资产收益率，单位：%"
    ],
    [
      "record_date",
      "date/string",
      "股权登记日"
    ],
    [
      "ex_dividend_date",
      "date/string",
      "除权派息日"
    ],
    [
      "progress",
      "string",
      "方案进度"
    ],
    [
      "progress_code",
      "string",
      "方案进度码"
    ],
    [
      "payout_ratio_pct",
      "number",
      "股利支付率，单位：%"
    ],
    [
      "target_holder",
      "string",
      "派发对象"
    ]
  ],
  "stock_dividend_metrics_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "日期或期间"
    ],
    [
      "metric_value",
      "number",
      "指标值"
    ],
    [
      "benchmark_value",
      "number",
      "对照值"
    ],
    [
      "rank",
      "integer",
      "排名；排名类指标返回"
    ],
    [
      "stock_name",
      "string",
      "证券简称；排名类指标返回"
    ],
    [
      "stock_code",
      "string",
      "股票代码；排名类指标返回"
    ],
    [
      "summary_total",
      "number",
      "汇总总额；总览类指标返回"
    ],
    [
      "cash_dividend_total",
      "number",
      "累计现金分红；总览类指标返回"
    ]
  ],
  "stock_equity_financing_events_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "event_date",
      "date/string",
      "事件日期"
    ],
    [
      "event_type",
      "string",
      "事件类型"
    ],
    [
      "plan",
      "string",
      "方案或关键条款"
    ],
    [
      "amount",
      "number",
      "融资金额"
    ],
    [
      "price",
      "number",
      "发行、配股、授予或转股价格"
    ],
    [
      "volume",
      "number",
      "发行、配股、授予或债券规模"
    ],
    [
      "progress",
      "string",
      "进度、状态或融资方式"
    ]
  ],
  "stock_private_placement_allocations_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "event_date",
      "date/string",
      "增发日期"
    ],
    [
      "allocator",
      "string",
      "获配机构"
    ],
    [
      "allocated_volume",
      "number",
      "获配数量，单位：股"
    ],
    [
      "subscribed_volume",
      "number",
      "申购数量，单位：股"
    ],
    [
      "allocated_amount",
      "number",
      "获配金额，单位：元"
    ],
    [
      "lock_months",
      "number",
      "锁定期，单位：月"
    ],
    [
      "institution_type",
      "string",
      "机构类型"
    ],
    [
      "unlock_date",
      "date/string",
      "解禁日期"
    ],
    [
      "shareholder_id",
      "string",
      "股东 ID"
    ]
  ],
  "stock_shareholder_change_plans_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "announcement_date",
      "date/string",
      "最新公告日"
    ],
    [
      "direction",
      "string",
      "变动方向"
    ],
    [
      "shareholder_name",
      "string",
      "股东名称"
    ],
    [
      "shareholder_role",
      "string",
      "股东身份或职务"
    ],
    [
      "planned_volume_upper",
      "number",
      "拟变动数量上限，单位：股"
    ],
    [
      "planned_ratio_upper_pct",
      "number",
      "拟变动上限占总股本比例，单位：%"
    ],
    [
      "planned_amount_upper",
      "number",
      "拟变动资金上限，单位：元；源端未按金额披露时为空"
    ],
    [
      "start_date",
      "date/string",
      "起始变动日期"
    ],
    [
      "end_date",
      "date/string",
      "截止变动日期"
    ],
    [
      "progress",
      "string",
      "进度"
    ],
    [
      "detail_id",
      "string",
      "详情记录 ID"
    ]
  ],
  "stock_northbound_holding_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "channel_type",
      "string",
      "当前持股记录对应的交易通道；有记录的深市标为深股通，沪市标为沪股通"
    ],
    [
      "date",
      "date/string",
      "指标日期"
    ],
    [
      "holding_ratio_pct",
      "number",
      "持股比例，单位：%"
    ],
    [
      "holding_volume",
      "number",
      "持股数量，单位：股"
    ],
    [
      "change_volume",
      "number",
      "变动股数，单位：股"
    ],
    [
      "change_pct",
      "number",
      "较上期变化，单位：%"
    ],
    [
      "close",
      "number",
      "收盘价，单位：元"
    ]
  ],
  "stock_margin_trading_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "margin_net_buy",
      "number",
      "融资净买入"
    ],
    [
      "margin_balance",
      "number",
      "融资余额"
    ],
    [
      "short_balance",
      "number",
      "融券相关统计"
    ]
  ],
  "stock_chip_distribution_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "统计日期"
    ],
    [
      "profit_ratio_pct",
      "number",
      "获利比例，单位：%"
    ],
    [
      "cost90_concentration",
      "number",
      "90% 成本集中度"
    ],
    [
      "cost90_range",
      "string",
      "90% 成本区间"
    ],
    [
      "cost70_concentration",
      "number",
      "70% 成本集中度"
    ],
    [
      "cost70_range",
      "string",
      "70% 成本区间"
    ]
  ],
  "stock_research_reports_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "rating",
      "string",
      "评级类别"
    ],
    [
      "analyst",
      "string",
      "研究员"
    ],
    [
      "publish_date",
      "date/string",
      "撰写日期"
    ],
    [
      "detail_id",
      "string",
      "研报详情 ID"
    ],
    [
      "title",
      "string",
      "研报标题"
    ],
    [
      "attachment",
      "string",
      "研报附件标识"
    ]
  ],
  "stock_analyst_rating_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "评级统计日期"
    ],
    [
      "buy_count",
      "integer",
      "买入家数"
    ],
    [
      "overweight_count",
      "integer",
      "增持家数"
    ],
    [
      "neutral_count",
      "integer",
      "中性家数"
    ],
    [
      "underweight_count",
      "integer",
      "减持家数"
    ],
    [
      "sell_count",
      "integer",
      "卖出家数"
    ],
    [
      "target_price",
      "number",
      "平均目标价"
    ],
    [
      "target_price_low",
      "number",
      "目标价下限"
    ],
    [
      "target_price_high",
      "number",
      "目标价上限"
    ],
    [
      "current_price",
      "number",
      "当前价"
    ],
    [
      "upside_pct",
      "number",
      "上涨空间，单位：%"
    ]
  ],
  "stock_institution_holding_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "报告日期"
    ],
    [
      "report_period",
      "string",
      "报告期名称"
    ],
    [
      "institution_holding_ratio_pct",
      "number",
      "机构持仓比例，单位：%"
    ],
    [
      "close",
      "number",
      "当期收盘价，单位：元"
    ]
  ],
  "stock_governance_guarantees_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "report_period",
      "date/string",
      "报告期"
    ],
    [
      "guarantor",
      "string",
      "担保方"
    ],
    [
      "guaranteed_party",
      "string",
      "被担保方"
    ],
    [
      "amount",
      "number",
      "担保金额"
    ],
    [
      "currency",
      "string",
      "币种"
    ],
    [
      "guarantee_type",
      "string",
      "担保类型"
    ],
    [
      "is_completed",
      "string",
      "是否履行完毕"
    ],
    [
      "is_related_party",
      "string",
      "是否关联交易"
    ],
    [
      "actual_date",
      "date/string",
      "实际发生日"
    ],
    [
      "term",
      "number/string",
      "担保期限，源端原值，可能为数字或空"
    ]
  ],
  "stock_violation_cases_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "case_date",
      "date/string",
      "立案日期"
    ],
    [
      "case_type",
      "string",
      "立案类型"
    ],
    [
      "publish_date",
      "date/string",
      "处罚公布日期，源端可能为空"
    ],
    [
      "progress",
      "string",
      "案情进展"
    ],
    [
      "detail_id",
      "string",
      "违法事实详情 ID"
    ],
    [
      "decision",
      "string",
      "处罚决定，源端可能为空"
    ]
  ],
  "stock_regulatory_actions_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "publish_date",
      "date/string",
      "处罚公布日期"
    ],
    [
      "target",
      "string",
      "处罚对象"
    ],
    [
      "action",
      "string",
      "监管措施"
    ],
    [
      "content",
      "string",
      "函件内容"
    ],
    [
      "link",
      "string",
      "链接，源端可能为空"
    ]
  ],
  "stock_score_summary_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "score",
      "number",
      "源端综合评分"
    ],
    [
      "industry_rank",
      "integer",
      "行业排名名次"
    ],
    [
      "industry_rank_total",
      "integer",
      "行业排名总数"
    ],
    [
      "market_rank",
      "integer",
      "A 股市场排名名次"
    ],
    [
      "market_rank_total",
      "integer",
      "A 股市场排名总数"
    ],
    [
      "market_win_pct",
      "number",
      "打败 A 股百分比"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "capital_score",
      "number",
      "资金面评分"
    ],
    [
      "fundamental_score",
      "number",
      "基本面评分"
    ],
    [
      "news_score",
      "number",
      "消息面评分"
    ],
    [
      "theme_score",
      "number",
      "主题面评分"
    ],
    [
      "industry_name",
      "string",
      "行业名"
    ],
    [
      "stock_name",
      "string",
      "股票名"
    ]
  ],
  "stock_disclosure_feed_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "category",
      "string",
      "资讯类型：news、announcement、roadshow"
    ],
    [
      "issue_date",
      "datetime/string",
      "发布时间或公告日期；路演通常为空"
    ],
    [
      "title",
      "string",
      "标题"
    ],
    [
      "source",
      "string",
      "来源；路演通常为空"
    ],
    [
      "detail_table",
      "string",
      "详情来源表"
    ],
    [
      "detail_id",
      "string",
      "记录 ID；路演通常为空"
    ],
    [
      "type_code",
      "string",
      "公告类型码；非公告通常为空"
    ],
    [
      "type_name",
      "string",
      "公告类型名；非公告通常为空"
    ],
    [
      "url",
      "string",
      "PDF、新闻或活动链接；源端无链接时为空"
    ],
    [
      "summary",
      "string",
      "摘要；源端无摘要时为空"
    ],
    [
      "start_date",
      "date/string",
      "路演开始日期；非路演为空"
    ],
    [
      "start_time",
      "time/string",
      "路演开始时间；非路演为空"
    ],
    [
      "end_time",
      "time/string",
      "路演结束时间；非路演为空"
    ]
  ],
  "stock_event_drivers_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "event_date",
      "date/string",
      "事件创建日期"
    ],
    [
      "event_name",
      "string",
      "事件名称，不等同于涨停原因"
    ],
    [
      "detail_id",
      "string",
      "事件详情 ID"
    ],
    [
      "event_nature",
      "string",
      "事件性质"
    ],
    [
      "creation_change_pct",
      "number",
      "创建日涨跌幅，单位：%"
    ],
    [
      "has_detail",
      "boolean",
      "是否有详情正文"
    ],
    [
      "detail_title",
      "string",
      "详情标题；include_detail=true 时补充"
    ],
    [
      "detail_text",
      "string",
      "详情正文；include_detail=true 时补充"
    ]
  ],
  "stock_topic_exposure_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "topic_type",
      "string",
      "题材类型：sector 板块题材、theme 主题题材"
    ],
    [
      "created_date",
      "date/string",
      "创建日期"
    ],
    [
      "topic_name",
      "string",
      "题材名称"
    ],
    [
      "relevance",
      "number",
      "关联度，源端评价分值"
    ],
    [
      "selected_date",
      "date/string",
      "入选或更新日期；源端可能为空"
    ],
    [
      "reason",
      "string",
      "入选原因或栏目内容"
    ],
    [
      "topic_id",
      "string",
      "题材 ID"
    ],
    [
      "group_code",
      "string",
      "源端分组类别码；主题题材可能为空"
    ]
  ],
  "concept_related_boards_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "board_market",
      "string",
      "板块市场"
    ],
    [
      "board_code",
      "string",
      "板块代码"
    ],
    [
      "board_name",
      "string",
      "板块名称"
    ],
    [
      "change_pct",
      "number",
      "涨幅，单位：%"
    ],
    [
      "limit_up_count",
      "integer",
      "涨停数"
    ]
  ],
  "concept_constituents_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "exchange",
      "string",
      "AxData 交易所代码：SSE、SZSE 或 BSE"
    ],
    [
      "market_code",
      "string",
      "市场代码"
    ],
    [
      "name",
      "string",
      "股票名称"
    ],
    [
      "change_pct",
      "number",
      "涨幅，单位：%"
    ],
    [
      "last_price",
      "number",
      "现价，单位：元"
    ]
  ],
  "concept_capital_flow_tdx": [
    [
      "board_name",
      "string",
      "题材或行业名"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "main_amount",
      "number",
      "主力资金"
    ],
    [
      "main_buy_amount",
      "number",
      "主买资金"
    ],
    [
      "avg_main_amount",
      "number",
      "平均主力资金"
    ],
    [
      "avg_main_buy_amount",
      "number",
      "平均主买资金"
    ]
  ],
  "concept_control_series_tdx": [
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "control_ratio_pct",
      "number",
      "主力控盘比例，单位：%"
    ],
    [
      "board_code",
      "string",
      "所属板块代码"
    ],
    [
      "board_name",
      "string",
      "所属板块名称"
    ],
    [
      "rank",
      "integer",
      "排名"
    ]
  ],
  "concept_control_ranking_tdx": [
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "exchange",
      "string",
      "AxData 交易所代码：SSE、SZSE 或 BSE"
    ],
    [
      "rank",
      "integer",
      "排名"
    ],
    [
      "market_code",
      "integer",
      "市场代码"
    ],
    [
      "symbol",
      "string",
      "股票代码"
    ],
    [
      "name",
      "string",
      "股票名称"
    ],
    [
      "control_ratio_pct",
      "number",
      "控盘比例，单位：%"
    ]
  ],
  "concept_constituent_comparison_tdx": [
    [
      "rank",
      "integer",
      "排名"
    ],
    [
      "market_code",
      "integer",
      "市场代码"
    ],
    [
      "symbol",
      "string",
      "股票代码"
    ],
    [
      "name",
      "string",
      "股票简称"
    ],
    [
      "report_period",
      "date/string",
      "财务数据报告期；compare_type=financial 时返回"
    ],
    [
      "change_pct",
      "number",
      "涨幅，单位：%"
    ],
    [
      "change_pct_3d",
      "number",
      "3 日涨幅，单位：%"
    ],
    [
      "change_pct_5d",
      "number",
      "5 日涨幅，单位：%"
    ],
    [
      "change_pct_20d",
      "number",
      "20 日涨幅，单位：%"
    ],
    [
      "change_pct_60d",
      "number",
      "60 日涨幅，单位：%"
    ],
    [
      "total_market_cap",
      "number",
      "总市值"
    ],
    [
      "float_market_cap",
      "number",
      "流通市值"
    ],
    [
      "revenue",
      "number",
      "营业收入"
    ],
    [
      "net_profit",
      "number",
      "归母净利润"
    ],
    [
      "revenue_yoy_pct",
      "number",
      "营收同比，单位：%"
    ],
    [
      "net_profit_yoy_pct",
      "number",
      "归母净利润同比，单位：%"
    ]
  ],
  "stock_valuation_metrics_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "pe_ttm",
      "number",
      "PE(TTM)"
    ],
    [
      "pe_percentile",
      "number",
      "PE 百分位"
    ],
    [
      "pb_mrq",
      "number",
      "PB(MRQ)"
    ],
    [
      "pb_percentile",
      "number",
      "PB 百分位"
    ],
    [
      "pcf_ttm",
      "number",
      "市现率(TTM)"
    ],
    [
      "pcf_percentile",
      "number",
      "市现率百分位"
    ],
    [
      "ps_ttm",
      "number",
      "市销率(TTM)"
    ],
    [
      "ps_percentile",
      "number",
      "市销率百分位"
    ],
    [
      "peg",
      "number",
      "PEG"
    ],
    [
      "float_market_cap",
      "number",
      "流通市值"
    ],
    [
      "total_market_cap",
      "number",
      "总市值"
    ]
  ],
  "stock_valuation_series_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "metric",
      "string",
      "指标"
    ],
    [
      "value",
      "number",
      "指标值"
    ],
    [
      "percentile",
      "number",
      "历史百分位"
    ]
  ],
  "stock_valuation_band_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "date",
      "date/string",
      "日期"
    ],
    [
      "band_value_1",
      "number",
      "估值通道原始值 1"
    ],
    [
      "band_value_2",
      "number",
      "估值通道原始值 2"
    ],
    [
      "band_value_3",
      "number",
      "估值通道原始值 3"
    ],
    [
      "total_count",
      "integer",
      "样本总数"
    ],
    [
      "min_value",
      "number",
      "最小值"
    ],
    [
      "mid_value",
      "number",
      "中位值"
    ]
  ],
  "stock_return_calendar_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "symbol",
      "string",
      "交易所原始六位代码"
    ],
    [
      "year",
      "string",
      "年份"
    ],
    [
      "month_1_pct",
      "number",
      "1 月涨跌幅，单位：%"
    ],
    [
      "month_2_pct",
      "number",
      "2 月涨跌幅，单位：%"
    ],
    [
      "month_3_pct",
      "number",
      "3 月涨跌幅，单位：%"
    ],
    [
      "month_4_pct",
      "number",
      "4 月涨跌幅，单位：%"
    ],
    [
      "month_5_pct",
      "number",
      "5 月涨跌幅，单位：%"
    ],
    [
      "month_6_pct",
      "number",
      "6 月涨跌幅，单位：%"
    ],
    [
      "month_7_pct",
      "number",
      "7 月涨跌幅，单位：%"
    ],
    [
      "month_8_pct",
      "number",
      "8 月涨跌幅，单位：%"
    ],
    [
      "month_9_pct",
      "number",
      "9 月涨跌幅，单位：%"
    ],
    [
      "month_10_pct",
      "number",
      "10 月涨跌幅，单位：%"
    ],
    [
      "month_11_pct",
      "number",
      "11 月涨跌幅，单位：%"
    ],
    [
      "month_12_pct",
      "number",
      "12 月涨跌幅，单位：%"
    ],
    [
      "year_pct",
      "number",
      "年度涨跌幅，单位：%"
    ]
  ],
  "stock_market_rankings_tdx": [
    [
      "instrument_id",
      "string",
      "AxData 统一证券代码，例如 000001.SZ"
    ],
    [
      "rank",
      "integer",
      "排名"
    ],
    [
      "rank_change",
      "number",
      "排名变化"
    ],
    [
      "symbol",
      "string",
      "股票代码"
    ],
    [
      "name",
      "string",
      "证券简称"
    ],
    [
      "exchange",
      "string",
      "AxData 交易所代码：SSE、SZSE 或 BSE"
    ],
    [
      "market_code",
      "string",
      "市场代码"
    ],
    [
      "updated_time",
      "datetime/string",
      "更新时间"
    ]
  ]
};

const f10ExampleParamCatalog: Record<string, F10ParamsObject> = {
  "stock_ipo_listing_profile_tdx": {
    "code": "000034.SZ"
  },
  "stock_index_constituent_changes_tdx": {
    "code": "000034.SZ"
  },
  "stock_company_profile_tdx": {
    "code": "000001.SZ"
  },
  "stock_business_composition_tdx": {
    "code": "000001.SZ"
  },
  "stock_financial_statement_tdx": {
    "code": "000034.SZ"
  },
  "stock_financial_diagnosis_tdx": {
    "code": "000034.SZ"
  },
  "stock_forecast_consensus_tdx": {
    "code": "000001.SZ"
  },
  "stock_dividend_history_tdx": {
    "code": "000001.SZ"
  },
  "stock_dividend_metrics_tdx": {
    "code": "000001.SZ"
  },
  "stock_equity_financing_events_tdx": {
    "code": "000034.SZ",
    "event_type": "placement"
  },
  "stock_private_placement_allocations_tdx": {
    "code": "000034.SZ"
  },
  "stock_shareholder_change_plans_tdx": {
    "code": "000034.SZ"
  },
  "stock_northbound_holding_tdx": {
    "code": "000001.SZ"
  },
  "stock_margin_trading_tdx": {
    "code": "000001.SZ"
  },
  "stock_chip_distribution_tdx": {
    "code": "000001.SZ"
  },
  "stock_research_reports_tdx": {
    "code": "000001.SZ",
    "count": 5
  },
  "stock_analyst_rating_tdx": {
    "code": "000001.SZ"
  },
  "stock_institution_holding_tdx": {
    "code": "000001.SZ"
  },
  "stock_governance_guarantees_tdx": {
    "code": "000034.SZ",
    "count": 5
  },
  "stock_violation_cases_tdx": {
    "code": "600519.SH"
  },
  "stock_regulatory_actions_tdx": {
    "code": "000034.SZ",
    "count": 5
  },
  "stock_score_summary_tdx": {
    "code": "000001.SZ"
  },
  "stock_disclosure_feed_tdx": {
    "code": "000034.SZ",
    "category": "announcement",
    "count": 5
  },
  "stock_event_drivers_tdx": {
    "code": "000001.SZ",
    "start_date": "20150101",
    "end_date": "20190212",
    "include_detail": true
  },
  "stock_topic_exposure_tdx": {
    "code": "000001.SZ",
    "topic_type": "theme"
  },
  "concept_related_boards_tdx": {
    "code": "000001.SZ"
  },
  "concept_constituents_tdx": {
    "concept_code": "881386",
    "count": 5
  },
  "concept_capital_flow_tdx": {
    "concept_code": "2817",
    "count": 5
  },
  "concept_control_series_tdx": {
    "code": "000001.SZ",
    "count": 5
  },
  "concept_control_ranking_tdx": {
    "concept_code": "2817",
    "count": 5
  },
  "concept_constituent_comparison_tdx": {
    "code": "000001.SZ",
    "concept_code": "2817",
    "compare_type": "return",
    "sort_by": "zdf"
  },
  "stock_valuation_metrics_tdx": {
    "code": "000001.SZ",
    "count": 5
  },
  "stock_valuation_series_tdx": {
    "code": "000001.SZ",
    "metric": "pe",
    "start_date": "20260601",
    "end_date": "20260605",
    "count": 5
  },
  "stock_valuation_band_tdx": {
    "code": "000001.SZ",
    "metric": "pe",
    "count": 5
  },
  "stock_return_calendar_tdx": {
    "code": "000001.SZ",
    "year": "2026"
  },
  "stock_market_rankings_tdx": {
    "code": "000001.SZ",
    "scope": "market",
    "count": 5
  }
};

const f10SampleRows: Record<string, Array<Record<string, string | number | boolean | null>>> = {
  "stock_ipo_listing_profile_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "stock_type": "A股",
      "list_date": "19940509",
      "issue_method": "申请表抽签限额认购",
      "issue_system": "核准制",
      "par_value": 1.0,
      "issue_price": 5.2,
      "issue_volume": 4680.0,
      "raised_amount": 24336.0,
      "net_raised_amount": 23390.2,
      "first_open": 7.2,
      "first_close": 6.76,
      "lead_underwriter": "巨田证券有限责任公司",
      "sponsor": "巨田证券有限责任公司"
    }
  ],
  "stock_index_constituent_changes_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20241129",
      "change_direction": "调入",
      "index_name": "中证500",
      "publish_date_change_pct": 1.9496101,
      "effective_date": "20241216",
      "effective_date_change_pct": -1.9343494
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20241129",
      "change_direction": "调出",
      "index_name": "中证1000",
      "publish_date_change_pct": 1.9496101,
      "effective_date": "20241216",
      "effective_date_change_pct": -1.9343494
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20240827",
      "change_direction": "调入",
      "index_name": "中证A500",
      "publish_date_change_pct": -3.7938144,
      "effective_date": "20240923",
      "effective_date_change_pct": -1.0534846
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20231211",
      "change_direction": "调入",
      "index_name": "深证成指",
      "publish_date_change_pct": 0.3059039,
      "effective_date": "20231211",
      "effective_date_change_pct": 0.3059039
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20220613",
      "change_direction": "调出",
      "index_name": "深证成指",
      "publish_date_change_pct": -0.520156,
      "effective_date": "20220613",
      "effective_date_change_pct": -0.520156
    }
  ],
  "stock_company_profile_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "stock_type": "A股",
      "list_date": "19910403",
      "issue_method": "公开招募",
      "issue_system": "核准制",
      "par_value": 1.0,
      "issue_price": 40.0,
      "issue_volume": 67.5,
      "raised_amount": 2700.0,
      "net_raised_amount": 2700.0,
      "first_open": 49.0,
      "first_close": 49.0,
      "lead_underwriter": "巨田证券有限责任公司",
      "sponsor": "华润深国投信托有限公司",
      "publish_date": null,
      "change_direction": null,
      "index_name": null,
      "publish_date_change_pct": null,
      "effective_date": null,
      "effective_date_change_pct": null
    }
  ],
  "stock_business_composition_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20251231",
      "dimension": "按地区",
      "item_order": 3,
      "item_name": "总部",
      "revenue": 71518000000.0,
      "revenue_ratio_pct": 54.41031,
      "cost": 17740000000.0,
      "cost_ratio_pct": 22.16558,
      "gross_profit": 53778000000.0,
      "profit_ratio_pct": 58.470236,
      "gross_margin_pct": 75.195056
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20251231",
      "dimension": "按地区",
      "item_order": 3,
      "item_name": "南区",
      "revenue": 20116000000.0,
      "revenue_ratio_pct": 15.304088,
      "cost": 6677000000.0,
      "cost_ratio_pct": 8.342704,
      "gross_profit": 13439000000.0,
      "profit_ratio_pct": 14.611579,
      "gross_margin_pct": 66.807516
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20251231",
      "dimension": "按地区",
      "item_order": 3,
      "item_name": "东区",
      "revenue": 20018000000.0,
      "revenue_ratio_pct": 15.229531,
      "cost": 6903000000.0,
      "cost_ratio_pct": 8.625084,
      "gross_profit": 13115000000.0,
      "profit_ratio_pct": 14.25931,
      "gross_margin_pct": 65.516036
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20250630",
      "dimension": "按地区",
      "item_order": 3,
      "item_name": "总部",
      "revenue": 40152000000.0,
      "revenue_ratio_pct": 57.868415,
      "cost": 10615000000.0,
      "cost_ratio_pct": 27.021867,
      "gross_profit": 29537000000.0,
      "profit_ratio_pct": 59.608088,
      "gross_margin_pct": 73.562961
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20250630",
      "dimension": "按地区",
      "item_order": 3,
      "item_name": "南区",
      "revenue": 10043000000.0,
      "revenue_ratio_pct": 14.47431,
      "cost": 2834000000.0,
      "cost_ratio_pct": 7.214317,
      "gross_profit": 7209000000.0,
      "profit_ratio_pct": 14.548353,
      "gross_margin_pct": 71.78134
    }
  ],
  "stock_financial_statement_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20260331",
      "cash": 7272491349.08,
      "trading_financial_assets": 10694020.39,
      "notes_receivable": 219856614.62,
      "accounts_receivable": 14916640292.21,
      "current_assets": 46013120649.9,
      "total_assets": 56061255922.07,
      "short_term_borrowing": 17713176433.65,
      "notes_payable": 4312277988.47,
      "accounts_payable": 9038695772.99,
      "current_liabilities": 38064050322.19,
      "total_liabilities": 44029600032.97,
      "share_capital": 724991225.0,
      "capital_reserve": 5830079325.22,
      "undistributed_profit": 4561524363.43,
      "parent_equity": 11226703805.3,
      "total_equity": 12031655889.1,
      "liabilities_and_equity": 56061255922.07
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "cash": 8309023979.45,
      "trading_financial_assets": 10694052.39,
      "notes_receivable": 612896695.33,
      "accounts_receivable": 13468986434.51,
      "current_assets": 47303583964.92,
      "total_assets": 57149969452.25,
      "short_term_borrowing": 16428537610.37,
      "notes_payable": 5337937958.99,
      "accounts_payable": 12552603613.72,
      "current_liabilities": 39859957395.49,
      "total_liabilities": 45358008559.85,
      "share_capital": 723444335.0,
      "capital_reserve": 5800664373.09,
      "undistributed_profit": 4325531266.05,
      "parent_equity": 11006444067.37,
      "total_equity": 11791960892.4,
      "liabilities_and_equity": 57149969452.25
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20250930",
      "cash": 6574345950.8,
      "trading_financial_assets": 100000575.0,
      "notes_receivable": 416410203.83,
      "accounts_receivable": 11007141088.83,
      "current_assets": 40719006211.83,
      "total_assets": 50371324408.4,
      "short_term_borrowing": 12760730251.33,
      "notes_payable": 6576704010.14,
      "accounts_payable": 7492943614.53,
      "current_liabilities": 33270722439.75,
      "total_liabilities": 38471053455.31,
      "share_capital": 722761206.0,
      "capital_reserve": 5724318043.19,
      "undistributed_profit": 4482990085.62,
      "parent_equity": 11104619693.3,
      "total_equity": 11900270953.09,
      "liabilities_and_equity": 50371324408.4
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20250630",
      "cash": 5346463227.66,
      "trading_financial_assets": 100000547.0,
      "notes_receivable": 278877118.12,
      "accounts_receivable": 13964951278.96,
      "current_assets": 39042429808.14,
      "total_assets": 48445522968.47,
      "short_term_borrowing": 10218616435.92,
      "notes_payable": 7324019170.51,
      "accounts_payable": 9973218378.59,
      "current_liabilities": 31931926906.16,
      "total_liabilities": 36868223718.42,
      "share_capital": 720196154.0,
      "capital_reserve": 5691058265.89,
      "undistributed_profit": 4238340456.74,
      "parent_equity": 10824523688.31,
      "total_equity": 11577299250.05,
      "liabilities_and_equity": 48445522968.47
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20250331",
      "cash": 7309024112.66,
      "trading_financial_assets": 10008329.22,
      "notes_receivable": 72848022.08,
      "accounts_receivable": 11563788329.12,
      "current_assets": 36127959122.58,
      "total_assets": 45221742886.65,
      "short_term_borrowing": 8543020694.85,
      "notes_payable": 6729041993.67,
      "accounts_payable": 8388746623.1,
      "current_liabilities": 28087437947.31,
      "total_liabilities": 33794648593.94,
      "share_capital": 711260675.0,
      "capital_reserve": 5507926129.76,
      "undistributed_profit": 4218478672.68,
      "parent_equity": 10680166711.59,
      "total_equity": 11427094292.71,
      "liabilities_and_equity": 45221742886.65
    }
  ],
  "stock_financial_diagnosis_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "stock_name": "神州数码",
      "compare_group": "云服务",
      "report_period": "881359",
      "rank": 1,
      "rank_change": null,
      "rating_code": 40,
      "score": 3.5,
      "percentile": 4.88,
      "warning_value": 881359.0
    }
  ],
  "stock_forecast_consensus_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "forecast_start_year": 2026,
      "align_flag": 0,
      "eps_year1": 2.166,
      "eps_year2": 2.227,
      "eps_year3": 2.308,
      "net_profit_year1": 4311468.3,
      "net_profit_year2": 4397870.5,
      "net_profit_year3": 4523682.1,
      "revenue_year1": 13224131.6,
      "revenue_year2": 13565032.4,
      "revenue_year3": 13999891.6,
      "forecast_institution_count": 12
    }
  ],
  "stock_dividend_history_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20251231",
      "board_date": "20260321",
      "plan": "10派3.6元(含税)",
      "eps": 2.07,
      "roe_weighted_pct": 9.15,
      "record_date": "20260611",
      "ex_dividend_date": "20260612",
      "progress": "实施方案",
      "progress_code": "036003",
      "payout_ratio_pct": 16.39,
      "target_holder": "全体股东"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20250630",
      "board_date": "20250823",
      "plan": "10派2.36元(含税)",
      "eps": 1.18,
      "roe_weighted_pct": 5.25,
      "record_date": "20251014",
      "ex_dividend_date": "20251015",
      "progress": "实施方案",
      "progress_code": "036003",
      "payout_ratio_pct": 18.42,
      "target_holder": "全体股东"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20241231",
      "board_date": "20250315",
      "plan": "10派3.62元(含税)",
      "eps": 2.15,
      "roe_weighted_pct": 10.08,
      "record_date": "20250611",
      "ex_dividend_date": "20250612",
      "progress": "实施方案",
      "progress_code": "036003",
      "payout_ratio_pct": 15.78,
      "target_holder": "全体股东"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20240630",
      "board_date": "20240816",
      "plan": "10派2.46元(含税)",
      "eps": 1.23,
      "roe_weighted_pct": 5.79,
      "record_date": "20241009",
      "ex_dividend_date": "20241010",
      "progress": "实施方案",
      "progress_code": "036003",
      "payout_ratio_pct": 18.45,
      "target_holder": "全体股东"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "report_period": "20231231",
      "board_date": "20240315",
      "plan": "10派7.19元(含税)",
      "eps": 2.25,
      "roe_weighted_pct": 11.38,
      "record_date": "20240613",
      "ex_dividend_date": "20240614",
      "progress": "实施方案",
      "progress_code": "036003",
      "payout_ratio_pct": 30.04,
      "target_holder": "全体股东"
    }
  ],
  "stock_dividend_metrics_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260615",
      "metric_value": 5.39,
      "benchmark_value": 0.838
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260612",
      "metric_value": 5.3,
      "benchmark_value": 0.836
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260611",
      "metric_value": 5.27,
      "benchmark_value": 0.836
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260610",
      "metric_value": 5.27,
      "benchmark_value": 0.841
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260609",
      "metric_value": 5.35,
      "benchmark_value": 0.841
    }
  ],
  "stock_equity_financing_events_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "event_type": "placement",
      "plan": "本次发行股票价格不低于定价基准日（2015年8月8日）前20个交易日公司股票均价的90%，即7.43元/股。",
      "amount": 219999.9989,
      "price": 7.43,
      "volume": 29609.6903,
      "progress": "非公开发行"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160622",
      "event_type": "placement",
      "plan": "发行价格为不低于定价基准日前20个交易日公司股票交易均价的90%，经商议发行价格为15.73元/股。",
      "amount": 41910.0,
      "price": null,
      "volume": 2664.3353,
      "progress": "已终止"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20171213",
      "event_type": "placement",
      "plan": "购买资产发行价格不低于定价基准日前60个交易日公司股票交易均价的90%。",
      "amount": 374459.65,
      "price": null,
      "volume": 16002.2446,
      "progress": "已终止"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20190429",
      "event_type": "placement",
      "plan": "预留授予价格尚不确定。",
      "amount": null,
      "price": null,
      "volume": 55.6915,
      "progress": "股东大会通过"
    }
  ],
  "stock_private_placement_allocations_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "allocator": "王晓岩",
      "allocated_volume": 64603000.0,
      "subscribed_volume": 64603000.0,
      "allocated_amount": 480000290.0,
      "lock_months": 36.0,
      "institution_type": "特定投资者",
      "unlock_date": "20190301",
      "shareholder_id": "GD069591"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "allocator": "郭为",
      "allocated_volume": 154777803.0,
      "subscribed_volume": 154777803.0,
      "allocated_amount": 1149999076.29,
      "lock_months": 36.0,
      "institution_type": "特定投资者",
      "unlock_date": "20190301",
      "shareholder_id": "GD020109"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "allocator": "王廷月",
      "allocated_volume": 26917900.0,
      "subscribed_volume": 26917900.0,
      "allocated_amount": 199999997.0,
      "lock_months": 36.0,
      "institution_type": "特定投资者",
      "unlock_date": "20190301",
      "shareholder_id": "GD130355"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "allocator": "钱学宁",
      "allocated_volume": 13459000.0,
      "subscribed_volume": 13459000.0,
      "allocated_amount": 100000370.0,
      "lock_months": 36.0,
      "institution_type": "特定投资者",
      "unlock_date": "20190301",
      "shareholder_id": "GD130350"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "event_date": "20160301",
      "allocator": "张明",
      "allocated_volume": 6729500.0,
      "subscribed_volume": 6729500.0,
      "allocated_amount": 50000185.0,
      "lock_months": 36.0,
      "institution_type": "特定投资者",
      "unlock_date": "20190301",
      "shareholder_id": "GD013757"
    }
  ],
  "stock_shareholder_change_plans_tdx": [
    {
      "instrument_id": "600519.SH",
      "symbol": "600519",
      "announcement_date": "20251230",
      "direction": "拟增持",
      "shareholder_name": "中国贵州茅台酒厂（集团）有限责任公司",
      "shareholder_role": "控股股东",
      "planned_volume_upper": null,
      "planned_ratio_upper_pct": null,
      "planned_amount_upper": 3300000000.0,
      "start_date": "20250901",
      "end_date": "20260228",
      "progress": "完成",
      "detail_id": 1075090
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "announcement_date": "20260313",
      "direction": "拟减持",
      "shareholder_name": "陈振坤",
      "shareholder_role": "董事/总裁/董事会秘书",
      "planned_volume_upper": 220937.0,
      "planned_ratio_upper_pct": 0.0305,
      "planned_amount_upper": null,
      "start_date": "20260407",
      "end_date": "20260706",
      "progress": "进行中",
      "detail_id": 1078327
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "announcement_date": "20260313",
      "direction": "拟减持",
      "shareholder_name": "陆明",
      "shareholder_role": "副总裁",
      "planned_volume_upper": 150156.0,
      "planned_ratio_upper_pct": 0.0207,
      "planned_amount_upper": null,
      "start_date": "20260407",
      "end_date": "20260706",
      "progress": "进行中",
      "detail_id": 1078329
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "announcement_date": "20260313",
      "direction": "拟减持",
      "shareholder_name": "潘春雷",
      "shareholder_role": "副总裁",
      "planned_volume_upper": 37500.0,
      "planned_ratio_upper_pct": 0.0052,
      "planned_amount_upper": null,
      "start_date": "20260407",
      "end_date": "20260706",
      "progress": "进行中",
      "detail_id": 1078330
    }
  ],
  "stock_northbound_holding_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "channel_type": "深股通",
      "date": "20260331",
      "holding_ratio_pct": 2.94,
      "holding_volume": 570772048.0,
      "change_volume": -57519101.0,
      "change_pct": -9.1548,
      "close": 11.08
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "channel_type": "深股通",
      "date": "20251231",
      "holding_ratio_pct": 3.23,
      "holding_volume": 628291149.0,
      "change_volume": -79103049.0,
      "change_pct": -11.1823,
      "close": 11.41
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "channel_type": "深股通",
      "date": "20250930",
      "holding_ratio_pct": 3.64,
      "holding_volume": 707394198.0,
      "change_volume": -121720333.0,
      "change_pct": -14.6808,
      "close": 11.34
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "channel_type": "深股通",
      "date": "20250630",
      "holding_ratio_pct": 4.27,
      "holding_volume": 829114531.0,
      "change_volume": 170999878.0,
      "change_pct": 25.9833,
      "close": 12.07
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "channel_type": "深股通",
      "date": "20250331",
      "holding_ratio_pct": 3.39,
      "holding_volume": 658114653.0,
      "change_volume": -88767070.0,
      "change_pct": -11.885,
      "close": 11.26
    }
  ],
  "stock_margin_trading_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260612",
      "margin_net_buy": -149371070.0,
      "margin_balance": 5065914051.0,
      "short_balance": -92900.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260611",
      "margin_net_buy": -7935699.0,
      "margin_balance": 5215285121.0,
      "short_balance": 182500.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260610",
      "margin_net_buy": -84178342.0,
      "margin_balance": 5223220820.0,
      "short_balance": 102700.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260609",
      "margin_net_buy": -47206515.0,
      "margin_balance": 5307399162.0,
      "short_balance": 366400.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260608",
      "margin_net_buy": -35187803.0,
      "margin_balance": 5354605677.0,
      "short_balance": -11800.0
    }
  ],
  "stock_chip_distribution_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260612",
      "profit_ratio_pct": 73.2641,
      "cost90_concentration": 11.9776,
      "cost90_range": "10.32~11.85",
      "cost70_concentration": 7.092,
      "cost70_range": "10.47~11.38"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260611",
      "profit_ratio_pct": 55.4947,
      "cost90_concentration": 11.6482,
      "cost90_range": "10.68~12.21",
      "cost70_concentration": 6.9736,
      "cost70_range": "10.83~11.75"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260610",
      "profit_ratio_pct": 56.3862,
      "cost90_concentration": 11.7248,
      "cost90_range": "10.67~12.21",
      "cost70_concentration": 6.9736,
      "cost70_range": "10.83~11.75"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260609",
      "profit_ratio_pct": 44.6695,
      "cost90_concentration": 11.7248,
      "cost90_range": "10.67~12.21",
      "cost70_concentration": 6.9736,
      "cost70_range": "10.83~11.75"
    }
  ],
  "stock_research_reports_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "rating": "买入",
      "analyst": "林虎",
      "publish_date": "20260611",
      "detail_id": 1636183,
      "title": "平安银行(000001)筑底回升，拐点确立",
      "attachment": "128334E121E313DA66FEFDF5320EAD94"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "rating": "买入",
      "analyst": "刘斐然 朱广越",
      "publish_date": "20260509",
      "detail_id": 1630394,
      "title": "平安银行(000001)2026一季报点评：营收业绩增速均转正，底部位置确立",
      "attachment": "F5DF849ACD33F7FCE41DBAA0A0162285"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "rating": "买入",
      "analyst": "徐凝碧 林加力",
      "publish_date": "20260428",
      "detail_id": 1628447,
      "title": "平安银行(000001)2026年一季报点评：营收利润恢复双增，中收表现亮眼",
      "attachment": "DB24810A1F8F2F9CB96C1F491E297991"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "rating": "增持",
      "analyst": "林宛慧 徐康",
      "publish_date": "20260427",
      "detail_id": 1629769,
      "title": "平安银行(000001)2026年一季报点评：息差企稳，非息亮眼，营收业绩增速回正",
      "attachment": "CB9B4D8304F334E655DFDC11DC299951"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "rating": "买入",
      "analyst": "马鲲鹏 李晨 王欣宇",
      "publish_date": "20260426",
      "detail_id": 1635700,
      "title": "平安银行(000001)转型成效凸显，营收利润回正",
      "attachment": "27D57EBE93EDBC1256F87B498289598F"
    }
  ],
  "stock_analyst_rating_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260611",
      "buy_count": 13,
      "overweight_count": 7,
      "neutral_count": 2,
      "underweight_count": 0,
      "sell_count": 0,
      "target_price": 14.162143,
      "target_price_low": 13.52,
      "target_price_high": 14.62,
      "current_price": 11.06,
      "upside_pct": 32.1880651
    }
  ],
  "stock_institution_holding_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260331",
      "report_period": "2026一季报",
      "institution_holding_ratio_pct": 2.94,
      "close": 11.08
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20251231",
      "report_period": "2025年报",
      "institution_holding_ratio_pct": 3.23,
      "close": 11.41
    }
  ],
  "stock_governance_guarantees_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "guarantor": "神州数码集团股份有限公司子公司",
      "guaranteed_party": "神码澳门离岸",
      "amount": 1233451900.0,
      "currency": "人民币",
      "guarantee_type": "一般保证",
      "is_completed": "否",
      "is_related_party": "是",
      "actual_date": "20250911",
      "term": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "guarantor": "神州数码集团股份有限公司",
      "guaranteed_party": "神码澳门离岸",
      "amount": 1233451900.0,
      "currency": "人民币",
      "guarantee_type": "一般保证",
      "is_completed": "否",
      "is_related_party": "是",
      "actual_date": "20250911",
      "term": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "guarantor": "神州数码集团股份有限公司",
      "guaranteed_party": "神码深圳",
      "amount": 1005809700.0,
      "currency": "人民币",
      "guarantee_type": "连带责任保证",
      "is_completed": "否",
      "is_related_party": "是",
      "actual_date": "20250818",
      "term": 2
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "guarantor": "神州数码集团股份有限公司子公司",
      "guaranteed_party": "北京神州鲲泰",
      "amount": 763003500.0,
      "currency": "人民币",
      "guarantee_type": "连带责任保证",
      "is_completed": "否",
      "is_related_party": "是",
      "actual_date": "20251218",
      "term": 0.5
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "report_period": "20251231",
      "guarantor": "神州数码集团股份有限公司",
      "guaranteed_party": "合肥信创科技",
      "amount": 700000000.0,
      "currency": "人民币",
      "guarantee_type": "连带责任保证",
      "is_completed": "否",
      "is_related_party": "是",
      "actual_date": "20250910",
      "term": 3
    }
  ],
  "stock_violation_cases_tdx": [
    {
      "instrument_id": "600519.SH",
      "symbol": "600519",
      "case_date": "20260313",
      "case_type": "董监高违法违规",
      "publish_date": null,
      "progress": "被留置调查",
      "detail_id": 1002375,
      "decision": null
    }
  ],
  "stock_regulatory_actions_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20220817",
      "target": "上市公司董监高",
      "action": "监管函",
      "content": "关于对叶海强的监管函",
      "link": "http://reportdocs.static.szse.cn/UpFiles/jgsy/gkxx_jgsy_000034174831.pdf"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20110824",
      "target": "姜欣",
      "action": "交易所通报批评",
      "content": "关于对重庆润江基础设施投资有限公司及相关当事人给予处分的决定",
      "link": "http://reportdocs.static.szse.cn/UpFiles/cfwj/2011-09-21_000034677.doc"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20080825",
      "target": "王迎、蔡锡民、张溯、华毛肃、张晓洁、邵华、肖水龙、洪乐平、张小立、梁侠",
      "action": "交易所通报批评",
      "content": "关于对深圳市深信泰丰（集团）股份有限公司及相关当事人给予处分的决定",
      "link": "http://reportdocs.static.szse.cn/UpFiles/cfwj/2008-08-26_000034581.doc"
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "publish_date": "20011108",
      "target": "梁侠、张小立",
      "action": "内部批评",
      "content": "关于对深圳市深信泰丰（集团）股份有限公司高管张小立等予以内部通报批评的决定",
      "link": "http://reportdocs.static.szse.cn/upfiles/cfwj/2002-04-11_0000341214.doc"
    }
  ],
  "stock_score_summary_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "score": 2.732,
      "industry_rank": 5,
      "industry_rank_total": 15,
      "market_rank": 3803,
      "market_rank_total": 5521,
      "market_win_pct": 31.1357,
      "date": "20260615",
      "capital_score": 1.0,
      "fundamental_score": 2.33,
      "news_score": 3.0,
      "theme_score": 5.0,
      "industry_name": "全国性银行",
      "stock_name": "平安银行"
    }
  ],
  "stock_disclosure_feed_tdx": [
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "category": "announcement",
      "issue_date": "20260613",
      "title": "神州数码：关于2025年年度报告的更正公告",
      "source": "深交所",
      "detail_table": "tb_gg_abg",
      "detail_id": "1225367857",
      "type_code": "0127",
      "type_name": "补充及更正",
      "url": "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225367857.pdf",
      "summary": null,
      "start_date": null,
      "start_time": null,
      "end_time": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "category": "announcement",
      "issue_date": "20260613",
      "title": "神州数码：2025年年度报告（更正后）",
      "source": "深交所",
      "detail_table": "tb_gg_abg",
      "detail_id": "1225367858",
      "type_code": "010301",
      "type_name": "年度报告",
      "url": "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225367858.pdf",
      "summary": null,
      "start_date": null,
      "start_time": null,
      "end_time": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "category": "announcement",
      "issue_date": "20260613",
      "title": "神州数码：信永中和会计师事务所（特殊普通合伙）关于神州数码集团股份有限公司2025年年度报告更正的专项说明",
      "source": "深交所",
      "detail_table": "tb_gg_abg",
      "detail_id": "1225367859",
      "type_code": "0129",
      "type_name": "中介机构报告",
      "url": "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225367859.pdf",
      "summary": null,
      "start_date": null,
      "start_time": null,
      "end_time": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "category": "announcement",
      "issue_date": "20260612",
      "title": "神州数码：关于为子公司担保的进展公告",
      "source": "深交所",
      "detail_table": "tb_gg_abg",
      "detail_id": "1225365293",
      "type_code": "0117",
      "type_name": "交易",
      "url": "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225365293.pdf",
      "summary": null,
      "start_date": null,
      "start_time": null,
      "end_time": null
    },
    {
      "instrument_id": "000034.SZ",
      "symbol": "000034",
      "category": "announcement",
      "issue_date": "20260605",
      "title": "神州数码：关于为子公司担保的进展公告",
      "source": "深交所",
      "detail_table": "tb_gg_abg",
      "detail_id": "1225351980",
      "type_code": "0117",
      "type_name": "交易",
      "url": "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225351980.pdf",
      "summary": null,
      "start_date": null,
      "start_time": null,
      "end_time": null
    }
  ],
  "stock_event_drivers_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "event_date": "20150625",
      "event_name": "商业银行75%存贷比取消",
      "detail_id": 2304,
      "event_nature": "利好",
      "creation_change_pct": -1.6534,
      "has_detail": true,
      "detail_title": "事件背景",
      "detail_text": "2015年6月24日，国务院常务会议通过《中华人民共和国商业银行法案修正案(草案)》，草案删除了贷款余额与存款余额比例不得超过75%的规定，将存贷比由法定监管指标转为流动性监测指标。"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "event_date": "20180124",
      "event_name": "贷款利率强势上行或增厚银行业绩",
      "detail_id": 5723,
      "event_nature": "利好",
      "creation_change_pct": -0.0683,
      "has_detail": true,
      "detail_title": "事件背景",
      "detail_text": "昨日银行股强势上涨，全线飘红。究其原因，银行业绩复苏必然是被市场提及的主因，而近期贷款定价走高或将进一步支撑这种逻辑。"
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "event_date": "20190212",
      "event_name": "国务院决定支持商业银行多渠道补充资本金",
      "detail_id": 7721,
      "event_nature": "利好",
      "creation_change_pct": -0.1784,
      "has_detail": true,
      "detail_title": "事件背景",
      "detail_text": "国务院总理李克强主持召开国务院常务会议，决定支持商业银行多渠道补充资本金，增强金融服务实体经济和防风险能力。"
    }
  ],
  "stock_topic_exposure_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20161202",
      "topic_name": "平安保险持股",
      "relevance": 5.0,
      "selected_date": "20260323",
      "reason": "中国平安保险(集团)股份有限公司是公司控股股东",
      "topic_id": "900",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20230829",
      "topic_name": "不可减持(新规)",
      "relevance": 4.0,
      "selected_date": null,
      "reason": "公司近20个交易日内跌破净资产，依照减持新规，控股股东和实际控制人不可减持。",
      "topic_id": "2965",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20130910",
      "topic_name": "优先股",
      "relevance": 5.0,
      "selected_date": "20211108",
      "reason": "公司旗下有优先股平银优01",
      "topic_id": "508",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20130128",
      "topic_name": "农业保险",
      "relevance": 3.0,
      "selected_date": "20211018",
      "reason": "公司有其他业务涉及保险代理服务",
      "topic_id": "361",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20201203",
      "topic_name": "罗素大盘",
      "relevance": 3.0,
      "selected_date": "20210926",
      "reason": "公司符合罗素大盘股标准",
      "topic_id": "2714",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20210814",
      "topic_name": "零售金融业务",
      "relevance": 5.0,
      "selected_date": "20220927",
      "reason": "公司是卓越领先的智能化零售银行",
      "topic_id": "X500101004",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20211022",
      "topic_name": "批发金融业务",
      "relevance": 4.0,
      "selected_date": "20220927",
      "reason": "公司主营业务包括批发金融业务",
      "topic_id": "X500102005",
      "group_code": null
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "topic_type": "theme",
      "created_date": "20220324",
      "topic_name": "汽车金融",
      "relevance": 3.0,
      "selected_date": "20220927",
      "reason": "公司主营业务包括汽车金融业务",
      "topic_id": "X260402006",
      "group_code": null
    }
  ],
  "concept_related_boards_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "881386",
      "board_name": "全国性银行",
      "change_pct": -1.09,
      "limit_up_count": 0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880218",
      "board_name": "深圳板块",
      "change_pct": 0.63,
      "limit_up_count": 7
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880609",
      "board_name": "跨境支付CIPS",
      "change_pct": -0.71,
      "limit_up_count": 1
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880679",
      "board_name": "周期股",
      "change_pct": -0.27,
      "limit_up_count": 2
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880721",
      "board_name": "北上重仓",
      "change_pct": -0.29,
      "limit_up_count": 0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880801",
      "board_name": "基金重仓",
      "change_pct": 0.04,
      "limit_up_count": 1
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880805",
      "board_name": "保险重仓",
      "change_pct": -0.64,
      "limit_up_count": 1
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880821",
      "board_name": "大盘股",
      "change_pct": 0.07,
      "limit_up_count": 1
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880826",
      "board_name": "低市盈率",
      "change_pct": -1.06,
      "limit_up_count": 0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880829",
      "board_name": "低市净率",
      "change_pct": -1.15,
      "limit_up_count": 0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880845",
      "board_name": "高股息股",
      "change_pct": -1.12,
      "limit_up_count": 0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880846",
      "board_name": "破净资产",
      "change_pct": -1.02,
      "limit_up_count": 1
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "board_market": "1",
      "board_code": "880883",
      "board_name": "MSCI成份",
      "change_pct": -0.08,
      "limit_up_count": 1
    }
  ],
  "concept_constituents_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "exchange": "SZSE",
      "market_code": "0",
      "name": "平安银行",
      "change_pct": -0.45,
      "last_price": 11.01
    },
    {
      "instrument_id": "600000.SH",
      "symbol": "600000",
      "exchange": "SSE",
      "market_code": "1",
      "name": "浦发银行",
      "change_pct": 0.0,
      "last_price": 9.53
    },
    {
      "instrument_id": "600015.SH",
      "symbol": "600015",
      "exchange": "SSE",
      "market_code": "1",
      "name": "华夏银行",
      "change_pct": -0.43,
      "last_price": 6.9
    },
    {
      "instrument_id": "600016.SH",
      "symbol": "600016",
      "exchange": "SSE",
      "market_code": "1",
      "name": "民生银行",
      "change_pct": 0.0,
      "last_price": 3.63
    },
    {
      "instrument_id": "600036.SH",
      "symbol": "600036",
      "exchange": "SSE",
      "market_code": "1",
      "name": "招商银行",
      "change_pct": -0.64,
      "last_price": 38.7
    }
  ],
  "concept_capital_flow_tdx": [
    {
      "board_name": "化学制药",
      "date": "20260430",
      "main_amount": -7708566.0,
      "main_buy_amount": -8853812.0,
      "avg_main_amount": -7085495.4,
      "avg_main_buy_amount": -7734552.84
    },
    {
      "board_name": "化学制药",
      "date": "20260506",
      "main_amount": -2188328.25,
      "main_buy_amount": -10129654.0,
      "avg_main_amount": -4462953.86,
      "avg_main_buy_amount": -6449633.2
    },
    {
      "board_name": "化学制药",
      "date": "20260507",
      "main_amount": -103805.75,
      "main_buy_amount": -3092367.5,
      "avg_main_amount": -16312254.56,
      "avg_main_buy_amount": -13359400.42
    },
    {
      "board_name": "化学制药",
      "date": "20260508",
      "main_amount": -1869947.25,
      "main_buy_amount": 1370486.0,
      "avg_main_amount": -10001046.14,
      "avg_main_buy_amount": -26926295.58
    },
    {
      "board_name": "化学制药",
      "date": "20260511",
      "main_amount": 761055.25,
      "main_buy_amount": 5330107.5,
      "avg_main_amount": -8341284.57,
      "avg_main_buy_amount": 5803502.68
    }
  ],
  "concept_control_series_tdx": [
    {
      "date": "20260601",
      "control_ratio_pct": 41.58,
      "board_code": "881386",
      "board_name": "全国性银行",
      "rank": 6
    },
    {
      "date": "20260602",
      "control_ratio_pct": 38.21,
      "board_code": "881386",
      "board_name": "全国性银行",
      "rank": 6
    },
    {
      "date": "20260603",
      "control_ratio_pct": 42.88,
      "board_code": "881386",
      "board_name": "全国性银行",
      "rank": 6
    },
    {
      "date": "20260604",
      "control_ratio_pct": 55.01,
      "board_code": "881386",
      "board_name": "全国性银行",
      "rank": 6
    },
    {
      "date": "20260605",
      "control_ratio_pct": 47.22,
      "board_code": "881386",
      "board_name": "全国性银行",
      "rank": 6
    }
  ],
  "concept_control_ranking_tdx": [
    {
      "date": "20260506",
      "instrument_id": "002102.SZ",
      "exchange": "SZSE",
      "rank": 1,
      "market_code": 0,
      "symbol": "002102",
      "name": "ST能特",
      "control_ratio_pct": 57.8
    },
    {
      "date": "20260506",
      "instrument_id": "000766.SZ",
      "exchange": "SZSE",
      "rank": 2,
      "market_code": 0,
      "symbol": "000766",
      "name": "通化金马",
      "control_ratio_pct": 51.95
    },
    {
      "date": "20260506",
      "instrument_id": "688166.SH",
      "exchange": "SSE",
      "rank": 3,
      "market_code": 1,
      "symbol": "688166",
      "name": "博瑞医药",
      "control_ratio_pct": 47.05
    },
    {
      "date": "20260506",
      "instrument_id": "603538.SH",
      "exchange": "SSE",
      "rank": 4,
      "market_code": 1,
      "symbol": "603538",
      "name": "美诺华",
      "control_ratio_pct": 46.7
    },
    {
      "date": "20260506",
      "instrument_id": "600079.SH",
      "exchange": "SSE",
      "rank": 5,
      "market_code": 1,
      "symbol": "600079",
      "name": "ST人福",
      "control_ratio_pct": 43.35
    }
  ],
  "concept_constituent_comparison_tdx": [
    {
      "rank": 1,
      "market_code": 0,
      "symbol": "301171",
      "name": "易点天下",
      "report_period": null,
      "change_pct": 8.23,
      "change_pct_3d": 0.42,
      "change_pct_5d": -5.71,
      "change_pct_20d": -17.31,
      "change_pct_60d": 4.11,
      "total_market_cap": null,
      "float_market_cap": null,
      "revenue": null,
      "net_profit": null,
      "revenue_yoy_pct": null,
      "net_profit_yoy_pct": null
    },
    {
      "rank": 2,
      "market_code": 0,
      "symbol": "300468",
      "name": "四方精创",
      "report_period": null,
      "change_pct": 7.95,
      "change_pct_3d": 10.44,
      "change_pct_5d": 11.04,
      "change_pct_20d": -9.93,
      "change_pct_60d": -31.3,
      "total_market_cap": null,
      "float_market_cap": null,
      "revenue": null,
      "net_profit": null,
      "revenue_yoy_pct": null,
      "net_profit_yoy_pct": null
    },
    {
      "rank": 3,
      "market_code": 0,
      "symbol": "301316",
      "name": "慧博云通",
      "report_period": null,
      "change_pct": 6.8,
      "change_pct_3d": 1.19,
      "change_pct_5d": -2.75,
      "change_pct_20d": -35.23,
      "change_pct_60d": -15.64,
      "total_market_cap": null,
      "float_market_cap": null,
      "revenue": null,
      "net_profit": null,
      "revenue_yoy_pct": null,
      "net_profit_yoy_pct": null
    },
    {
      "rank": 4,
      "market_code": 0,
      "symbol": "300996",
      "name": "普联软件",
      "report_period": null,
      "change_pct": 6.76,
      "change_pct_3d": 6.96,
      "change_pct_5d": -0.35,
      "change_pct_20d": -8.64,
      "change_pct_60d": -5.41,
      "total_market_cap": null,
      "float_market_cap": null,
      "revenue": null,
      "net_profit": null,
      "revenue_yoy_pct": null,
      "net_profit_yoy_pct": null
    },
    {
      "rank": 5,
      "market_code": 0,
      "symbol": "300773",
      "name": "拉卡拉",
      "report_period": null,
      "change_pct": 6.59,
      "change_pct_3d": 7.63,
      "change_pct_5d": 7.63,
      "change_pct_20d": -8.74,
      "change_pct_60d": -8.5,
      "total_market_cap": null,
      "float_market_cap": null,
      "revenue": null,
      "net_profit": null,
      "revenue_yoy_pct": null,
      "net_profit_yoy_pct": null
    }
  ],
  "stock_valuation_metrics_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260615",
      "pe_ttm": 4.98,
      "pe_percentile": 41.21,
      "pb_mrq": 0.46,
      "pb_percentile": 5.7,
      "pcf_ttm": 1.13,
      "pcf_percentile": 42.69,
      "ps_ttm": 1.61,
      "ps_percentile": 64.66,
      "peg": 0.1,
      "float_market_cap": 214625959936.0,
      "total_market_cap": 214629466112.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260612",
      "pe_ttm": 5.07,
      "pe_percentile": 47.23,
      "pb_mrq": 0.47,
      "pb_percentile": 10.49,
      "pcf_ttm": 1.14,
      "pcf_percentile": 44.43,
      "ps_ttm": 1.64,
      "ps_percentile": 71.84,
      "peg": 0.1,
      "float_market_cap": 218118946816.0,
      "total_market_cap": 218122518528.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260611",
      "pe_ttm": 5.09,
      "pe_percentile": 49.55,
      "pb_mrq": 0.47,
      "pb_percentile": 12.39,
      "pcf_ttm": 1.15,
      "pcf_percentile": 44.92,
      "ps_ttm": 1.65,
      "ps_percentile": 74.15,
      "peg": 0.1,
      "float_market_cap": 219283292160.0,
      "total_market_cap": 219286880256.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260610",
      "pe_ttm": 5.1,
      "pe_percentile": 50.21,
      "pb_mrq": 0.47,
      "pb_percentile": 13.05,
      "pcf_ttm": 1.15,
      "pcf_percentile": 45.0,
      "ps_ttm": 1.65,
      "ps_percentile": 74.65,
      "peg": 0.1,
      "float_market_cap": 219671396352.0,
      "total_market_cap": 219674984448.0
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260609",
      "pe_ttm": 5.02,
      "pe_percentile": 43.93,
      "pb_mrq": 0.47,
      "pb_percentile": 7.35,
      "pcf_ttm": 1.13,
      "pcf_percentile": 43.85,
      "ps_ttm": 1.62,
      "ps_percentile": 67.46,
      "peg": 0.1,
      "float_market_cap": 215984340992.0,
      "total_market_cap": 215987879936.0
    }
  ],
  "stock_valuation_series_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260601",
      "metric": "pe",
      "value": 4.95,
      "percentile": 37.49
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260602",
      "metric": "pe",
      "value": 4.99,
      "percentile": 42.11
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260603",
      "metric": "pe",
      "value": 4.95,
      "percentile": 37.41
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260604",
      "metric": "pe",
      "value": 4.88,
      "percentile": 31.96
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20260605",
      "metric": "pe",
      "value": 4.95,
      "percentile": 36.91
    }
  ],
  "stock_valuation_band_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20250616",
      "band_value_1": 5.239,
      "band_value_2": 11.79,
      "band_value_3": 11.79,
      "total_count": 243,
      "min_value": 4.7567,
      "mid_value": 5.1667
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20250617",
      "band_value_1": 5.2256,
      "band_value_2": 11.76,
      "band_value_3": 11.76,
      "total_count": 243,
      "min_value": 4.7567,
      "mid_value": 5.1667
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20250618",
      "band_value_1": 5.2301,
      "band_value_2": 11.77,
      "band_value_3": 11.77,
      "total_count": 243,
      "min_value": 4.7567,
      "mid_value": 5.1667
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20250619",
      "band_value_1": 5.199,
      "band_value_2": 11.7,
      "band_value_3": 11.7,
      "total_count": 243,
      "min_value": 4.7567,
      "mid_value": 5.1667
    },
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "date": "20250620",
      "band_value_1": 5.2612,
      "band_value_2": 11.84,
      "band_value_3": 11.84,
      "total_count": 243,
      "min_value": 4.7567,
      "mid_value": 5.1667
    }
  ],
  "stock_return_calendar_tdx": [
    {
      "instrument_id": "000001.SZ",
      "symbol": "000001",
      "year": "2026",
      "month_1_pct": -5.0833,
      "month_2_pct": 0.6463,
      "month_3_pct": 1.6514,
      "month_4_pct": 3.7004,
      "month_5_pct": -4.8738,
      "month_6_pct": 3.3852,
      "month_7_pct": 0.0,
      "month_8_pct": 0.0,
      "month_9_pct": 0.0,
      "month_10_pct": 0.0,
      "month_11_pct": 0.0,
      "month_12_pct": 0.0,
      "year_pct": -0.964
    }
  ],
  "stock_market_rankings_tdx": [
    {
      "instrument_id": "002428.SZ",
      "rank": 1,
      "rank_change": -6.0,
      "symbol": "002428",
      "name": "云南锗业",
      "exchange": "SZSE",
      "market_code": "0",
      "updated_time": "20260616"
    },
    {
      "instrument_id": "600522.SH",
      "rank": 2,
      "rank_change": -1.0,
      "symbol": "600522",
      "name": "中天科技",
      "exchange": "SSE",
      "market_code": "1",
      "updated_time": "20260616"
    },
    {
      "instrument_id": "000636.SZ",
      "rank": 3,
      "rank_change": -5.0,
      "symbol": "000636",
      "name": "风华高科",
      "exchange": "SZSE",
      "market_code": "0",
      "updated_time": "20260616"
    },
    {
      "instrument_id": "600110.SH",
      "rank": 4,
      "rank_change": -17.0,
      "symbol": "600110",
      "name": "诺德股份",
      "exchange": "SSE",
      "market_code": "1",
      "updated_time": "20260616"
    },
    {
      "instrument_id": "000725.SZ",
      "rank": 5,
      "rank_change": 4.0,
      "symbol": "000725",
      "name": "京东方Ａ",
      "exchange": "SZSE",
      "market_code": "0",
      "updated_time": "20260616"
    }
  ]
};

const f10CommonCodeParam = ["code", "string/list", "是", "股票代码：支持 000001、000001.SZ、sz000001；批量可传数组或英文逗号分隔字符串"];

const f10CatalogSpecs: F10CatalogSpec[] = [
  {
    id: "stock_ipo_listing_profile_tdx",
    title: "发行上市资料",
    group: "F10数据",
    summary: "查询公司发行上市资料。",
    functionText: "获取发行上市资料",
    key: "instrument_id",
    params: [f10CommonCodeParam],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ"],
      ["symbol", "string", "交易所原始六位代码"],
      ["stock_type", "string", "股票类别"],
      ["list_date", "date/string", "上市日期"],
      ["issue_method", "string", "发行方式"],
      ["issue_system", "string", "发行制度"],
      ["par_value", "number", "每股面值，单位：元"],
      ["issue_price", "number", "发行价格，单位：元"],
      ["issue_volume", "number", "发行数量"],
      ["raised_amount", "number", "实际募资总额"],
      ["net_raised_amount", "number", "实际募资净额"],
      ["first_open", "number", "首日开盘价，单位：元"],
      ["first_close", "number", "首日收盘价，单位：元"],
      ["lead_underwriter", "string", "主承销商"],
      ["sponsor", "string", "上市保荐人"]
    ],
    exampleParams: `code="000034.SZ"`,
    exampleRow: {
      instrument_id: "000034.SZ",
      symbol: "000034",
      stock_type: "A股",
      list_date: "19940509",
      issue_method: "申请表抽签限额认购",
      issue_system: "核准制",
      par_value: 1,
      issue_price: 5.2,
      issue_volume: 4680,
      raised_amount: 24336,
      net_raised_amount: 23390.2,
      first_open: 7.2,
      first_close: 6.76,
      lead_underwriter: "巨田证券有限责任公司",
      sponsor: "巨田证券有限责任公司"
    }
  },
  {
    id: "stock_index_constituent_changes_tdx",
    title: "指数调入调出",
    group: "F10数据",
    summary: "查询股票被指数调入或调出的历史记录。",
    functionText: "获取指数调入调出记录",
    key: "instrument_id,publish_date,index_name",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "起始日期，可选；不传返回全部记录"], ["end_date", "string", "否", "结束日期，可选；不传返回全部记录"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["publish_date", "date/string", "指数调整公布日期"],
      ["change_direction", "string", "指数调入/调出方向"],
      ["index_name", "string", "指数名称"],
      ["publish_date_change_pct", "number", "公布日涨跌幅，单位：%"],
      ["effective_date", "date/string", "指数调整日期"],
      ["effective_date_change_pct", "number", "调整日涨跌幅，单位：%"]
    ],
    exampleParams: `code="000034.SZ"`,
    exampleRow: {
      instrument_id: "000034.SZ",
      symbol: "000034",
      publish_date: "20241129",
      change_direction: "调入",
      index_name: "中证500",
      publish_date_change_pct: 1.9496101,
      effective_date: "20241216",
      effective_date_change_pct: -1.9343494
    }
  },
  {
    id: "stock_business_composition_tdx",
    title: "主营构成",
    group: "F10数据",
    summary: "查询各报告期主营收入、成本、毛利和毛利率。",
    functionText: "获取主营构成明细",
    key: "instrument_id,report_period",
    params: [f10CommonCodeParam, ["period", "string", "否", "报告期，格式 YYYYMMDD；不传时返回全部可用报告期"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["report_period", "date/string", "报告期"],
      ["dimension", "string", "分类方式"],
      ["item_order", "integer", "序号或层级"],
      ["item_name", "string", "主营构成项目"],
      ["revenue", "number", "主营收入"],
      ["revenue_ratio_pct", "number", "收入占比，单位：%"],
      ["cost", "number", "主营成本"],
      ["cost_ratio_pct", "number", "成本占比，单位：%"],
      ["gross_profit", "number", "毛利"],
      ["profit_ratio_pct", "number", "利润占比，单位：%"],
      ["gross_margin_pct", "number", "毛利率，单位：%"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRows: [
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        report_period: "20251231",
        dimension: "按地区",
        item_order: 3,
        item_name: "总部",
        revenue: 71518000000,
        revenue_ratio_pct: 54.41031,
        cost: 17740000000,
        cost_ratio_pct: 22.16558,
        gross_profit: 53778000000,
        profit_ratio_pct: 58.470236,
        gross_margin_pct: 75.195056
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        report_period: "20251231",
        dimension: "按地区",
        item_order: 3,
        item_name: "南区",
        revenue: 20116000000,
        revenue_ratio_pct: 15.304088,
        cost: 6677000000,
        cost_ratio_pct: 8.342704,
        gross_profit: 13439000000,
        profit_ratio_pct: 14.611579,
        gross_margin_pct: 66.807516
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        report_period: "20251231",
        dimension: "按地区",
        item_order: 3,
        item_name: "东区",
        revenue: 20018000000,
        revenue_ratio_pct: 15.229531,
        cost: 6903000000,
        cost_ratio_pct: 8.625084,
        gross_profit: 13115000000,
        profit_ratio_pct: 14.25931,
        gross_margin_pct: 65.516036
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        report_period: "20251231",
        dimension: "按地区",
        item_order: 3,
        item_name: "北区",
        revenue: 13258000000,
        revenue_ratio_pct: 10.086578,
        cost: 5436000000,
        cost_ratio_pct: 6.792113,
        gross_profit: 7822000000,
        profit_ratio_pct: 8.504485,
        gross_margin_pct: 58.998341
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        report_period: "20251231",
        dimension: "按地区",
        item_order: 3,
        item_name: "西区",
        revenue: 5474000000,
        revenue_ratio_pct: 4.164574,
        cost: 2448000000,
        cost_ratio_pct: 3.0587,
        gross_profit: 3026000000,
        profit_ratio_pct: 3.290024,
        gross_margin_pct: 55.279503
      }
    ]
  },
  {
    id: "stock_financial_statement_tdx",
    title: "资产负债表",
    group: "F10数据",
    summary: "查询资产负债表。",
    functionText: "获取资产负债表",
    key: "instrument_id,report_period",
    params: [f10CommonCodeParam],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["report_period", "date/string", "报告期"],
      ["cash", "number", "货币资金"],
      ["current_assets", "number", "流动资产合计"],
      ["total_assets", "number", "资产总计"],
      ["current_liabilities", "number", "流动负债合计"],
      ["total_liabilities", "number", "负债合计"],
      ["share_capital", "number", "实收资本或股本"],
      ["parent_equity", "number", "归母权益合计"],
      ["total_equity", "number", "所有者权益合计"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      report_period: "20260331",
      cash: 127851000000,
      accounts_receivable: 260145000000,
      total_assets: 10879000000,
      current_liabilities: 69183000000
    }
  },
  {
    id: "stock_financial_diagnosis_tdx",
    title: "财务诊断",
    group: "F10数据",
    summary: "查询源端财务能力、预警和评分；这是源端评价，不代表 AxData 自有判断。",
    functionText: "获取源端财务诊断",
    key: "instrument_id,report_period",
    params: [
      f10CommonCodeParam,
      [
        "dimension",
        "string",
        "否",
        "诊断维度：operation 营运能力、profit 盈利能力、growth 成长能力、cashflow 现金流、asset_quality 资产质量、z_score Z值预警、score 综合评分；默认 score"
      ]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["stock_name", "string", "股票简称"],
      ["compare_group", "string", "对比行业或板块"],
      ["report_period", "date/string", "报告期"],
      ["rank", "integer", "个股排名"],
      ["rating_code", "string", "评价等级码"],
      ["score", "number", "源端综合评分"],
      ["percentile", "number", "分位或打败比例"],
      ["warning_value", "number", "Z 值或预警值"]
    ],
    exampleParams: `code="000001.SZ", dimension="score"`,
    note: "该接口返回源端评价或评分，不代表 AxData 自有判断。"
  },
  {
    id: "stock_forecast_consensus_tdx",
    title: "盈利预测",
    group: "F10数据",
    summary: "查询盈利预测统计，包括未来三年预测、历史实际值和预测机构数量。",
    functionText: "获取盈利预测统计",
    key: "instrument_id",
    params: [f10CommonCodeParam],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["forecast_start_year", "integer", "预测起始年份"],
      ["eps_year1", "number", "未来第一年预测每股收益"],
      ["eps_year2", "number", "未来第二年预测每股收益"],
      ["eps_year3", "number", "未来第三年预测每股收益"],
      ["net_profit_year1", "number", "未来第一年预测归母净利润"],
      ["revenue_year1", "number", "未来第一年预测营业收入"],
      ["forecast_institution_count", "integer", "预测机构数量"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      forecast_start_year: 2026,
      eps_year1: 2.166,
      net_profit_year1: 4311468.3,
      forecast_institution_count: 12
    }
  },
  {
    id: "stock_dividend_history_tdx",
    title: "分红历史",
    group: "F10数据",
    summary: "查询历史分红方案、登记日、除权日和方案进度。",
    functionText: "获取分红历史",
    key: "instrument_id,report_period",
    params: [f10CommonCodeParam, ["start_year", "string", "否", "起始年份，可选；不传返回全部记录"], ["end_year", "string", "否", "结束年份，可选；不传返回全部记录"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["report_period", "date/string", "分红年度或报告期"],
      ["plan", "string", "分红方案"],
      ["record_date", "date/string", "股权登记日"],
      ["ex_dividend_date", "date/string", "除权派息日"],
      ["progress", "string", "方案进度"],
      ["payout_ratio_pct", "number", "股利支付率，单位：%"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      report_period: "20251231",
      plan: "10派3.6元(含税)",
      record_date: "20260611",
      ex_dividend_date: "20260612",
      progress: "实施方案",
      payout_ratio_pct: 16.39
    }
  },
  {
    id: "stock_dividend_metrics_tdx",
    title: "分红指标",
    group: "F10数据",
    summary: "查询股息率、股利支付率、派现融资等分红指标。",
    functionText: "获取分红指标",
    key: "instrument_id,date",
    params: [
      f10CommonCodeParam,
      ["metric", "string", "否", "指标：dividend_yield 股息率、payout_ratio 股利支付率、cash_financing 派现融资；默认 dividend_yield"],
      ["view", "string", "否", "展示方式：trend 走势、ranking 排名、summary 总览；不传时 dividend_yield/payout_ratio 默认 trend，cash_financing 默认 summary"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "日期或期间"],
      ["metric_value", "number", "指标值"],
      ["benchmark_value", "number", "对照值"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260612",
      metric_value: 5.3,
      benchmark_value: 0.836
    }
  },
  {
    id: "stock_equity_financing_events_tdx",
    title: "融资事件",
    group: "F10数据",
    summary: "查询增发、配股、股权激励、可转债等融资相关事件。",
    functionText: "获取融资事件",
    key: "instrument_id,event_date",
    params: [
      f10CommonCodeParam,
      ["event_type", "string", "否", "事件类型：placement 增发、rights_issue 配股、incentive 股权激励、convertible_bond 可转债；默认 placement"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["event_date", "date/string", "事件日期"],
      ["event_type", "string", "事件类型"],
      ["plan", "string", "方案或关键条款"],
      ["amount", "number", "融资金额"],
      ["price", "number", "发行、配股、授予或转股价格"],
      ["volume", "number", "发行、配股、授予或债券规模"],
      ["progress", "string", "进度、状态或融资方式"]
    ],
    exampleParams: `code="000034.SZ", event_type="placement"`,
    exampleRow: {
      instrument_id: "000034.SZ",
      event_date: "20160301",
      event_type: "placement",
      amount: 219999.9989,
      price: 7.43,
      volume: 29609.6903,
      progress: "非公开发行"
    }
  },
  {
    id: "stock_private_placement_allocations_tdx",
    title: "增发获配明细",
    group: "F10数据",
    summary: "查询增发获配机构、获配数量和获配金额。",
    functionText: "获取增发获配机构明细",
    key: "instrument_id,event_date,allocator",
    params: [
      f10CommonCodeParam,
      ["event_date", "string", "否", "增发日期，格式 YYYYMMDD 或 YYYY-MM-DD；不传返回全部可用增发日期的获配明细"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["event_date", "date/string", "增发日期"],
      ["allocator", "string", "获配机构"],
      ["allocated_volume", "number", "获配数量，单位：股"],
      ["subscribed_volume", "number", "申购数量，单位：股"],
      ["allocated_amount", "number", "获配金额，单位：元"],
      ["lock_months", "number", "锁定期，单位：月"],
      ["institution_type", "string", "机构类型"],
      ["unlock_date", "date/string", "解禁日期"]
    ],
    exampleParams: `code="000034.SZ"`,
    exampleRow: {
      instrument_id: "000034.SZ",
      event_date: "20160301",
      allocator: "郭为",
      allocated_volume: 154777803,
      subscribed_volume: 154777803,
      allocated_amount: 1149999076.29,
      lock_months: 36,
      institution_type: "特定投资者",
      unlock_date: "20190301"
    }
  },
  {
    id: "stock_shareholder_change_plans_tdx",
    title: "股东增减持",
    group: "F10数据",
    summary: "查询股东增持或减持计划。",
    functionText: "获取股东增减持计划",
    key: "instrument_id,announcement_date,shareholder_name",
    params: [f10CommonCodeParam, ["direction", "string", "否", "方向筛选：increase 增持、decrease 减持；不传返回全部方向"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["announcement_date", "date/string", "最新公告日"],
      ["direction", "string", "变动方向"],
      ["shareholder_name", "string", "股东名称"],
      ["shareholder_role", "string", "股东身份或职务"],
      ["planned_volume_upper", "number", "拟变动数量上限，单位：股"],
      ["planned_ratio_upper_pct", "number", "拟变动上限占总股本比例，单位：%"],
      ["planned_amount_upper", "number", "拟变动资金上限，单位：元；源端未按金额披露时为空"],
      ["start_date", "date/string", "起始变动日期"],
      ["end_date", "date/string", "截止变动日期"],
      ["progress", "string", "进度"]
    ],
    exampleParams: `code="000034.SZ"`,
    exampleRow: {
      instrument_id: "600519.SH",
      announcement_date: "20251230",
      direction: "拟增持",
      shareholder_name: "中国贵州茅台酒厂（集团）有限责任公司",
      shareholder_role: "控股股东",
      planned_amount_upper: 3300000000,
      start_date: "20250901",
      end_date: "20260228",
      progress: "完成"
    }
  },
  {
    id: "stock_northbound_holding_tdx",
    title: "沪深股通持股",
    group: "F10数据",
    summary: "查询沪深股通持股变化序列；不传日期默认返回全部可用记录。",
    functionText: "获取沪深股通持股变化",
    key: "instrument_id,date",
    params: [
      f10CommonCodeParam,
      ["start_date", "string", "否", "起始日期，可选；不传返回全部记录"],
      ["end_date", "string", "否", "结束日期，可选；不传返回全部记录"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["channel_type", "string", "当前持股记录对应的交易通道；有记录的深市标为深股通，沪市标为沪股通"],
      ["date", "date/string", "指标日期"],
      ["holding_ratio_pct", "number", "持股比例，单位：%"],
      ["holding_volume", "number", "持股数量，单位：股"],
      ["change_volume", "number", "变动股数，单位：股"],
      ["change_pct", "number", "较上期变化，单位：%"],
      ["close", "number", "收盘价，单位：元"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      channel_type: "深股通",
      date: "20260331",
      holding_ratio_pct: 2.94,
      holding_volume: 570772048,
      change_volume: -57519101,
      change_pct: -9.1548,
      close: 11.08
    }
  },
  {
    id: "stock_margin_trading_tdx",
    title: "融资融券",
    group: "F10数据",
    summary: "查询源端融资融券统计。",
    functionText: "获取融资融券统计",
    key: "instrument_id,date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "起始日期，可选"], ["end_date", "string", "否", "结束日期，可选"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "日期"],
      ["margin_net_buy", "number", "融资净买入"],
      ["margin_balance", "number", "融资余额"],
      ["short_balance", "number", "融券相关统计"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260611",
      margin_net_buy: -7935699,
      margin_balance: 5215285121,
      short_balance: 182500
    }
  },
  {
    id: "stock_chip_distribution_tdx",
    title: "筹码分布",
    group: "F10数据",
    summary: "查询源端筹码分布统计。",
    functionText: "获取筹码分布统计",
    key: "instrument_id,date",
    params: [
      f10CommonCodeParam,
      ["start_date", "string", "否", "按统计日期过滤的起始日期；不传返回源端本次给出的全部记录"],
      ["end_date", "string", "否", "按统计日期过滤的结束日期；不传返回源端本次给出的全部记录"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["date", "date/string", "统计日期"],
      ["profit_ratio_pct", "number", "获利比例，单位：%"],
      ["cost90_concentration", "number", "90% 成本区间宽窄，数值越小表示筹码成本越集中"],
      ["cost90_range", "string", "覆盖 90% 筹码的估算成本区间"],
      ["cost70_concentration", "number", "70% 成本区间宽窄，数值越小表示核心筹码成本越集中"],
      ["cost70_range", "string", "覆盖 70% 筹码的估算成本区间"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      symbol: "000001",
      date: "20260612",
      profit_ratio_pct: 73.2641,
      cost90_concentration: 11.9776,
      cost90_range: "10.32~11.85",
      cost70_concentration: 7.092,
      cost70_range: "10.47~11.38"
    }
  },
  {
    id: "stock_research_reports_tdx",
    title: "研报列表",
    group: "F10数据",
    summary: "查询公司研究报告列表。",
    functionText: "获取研报列表",
    key: "instrument_id,publish_date,title",
    params: [f10CommonCodeParam, ["rating", "string", "否", "评级筛选：all、buy、overweight、neutral、underweight、sell；默认 all"], ["keyword", "string", "否", "标题关键字"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["rating", "string", "评级类别"],
      ["analyst", "string", "研究员"],
      ["publish_date", "date/string", "撰写日期"],
      ["detail_id", "string", "研报详情 ID"],
      ["title", "string", "研报标题"],
      ["attachment", "string", "研报附件标识"]
    ],
    exampleParams: `code="000001.SZ", rating="all", count=20`,
    exampleRow: {
      instrument_id: "000001.SZ",
      symbol: "000001",
      rating: "买入",
      analyst: "林虎",
      publish_date: "20260611",
      detail_id: 1636183,
      title: "平安银行(000001)筑底回升，拐点确立",
      attachment: "128334E121E313DA66FEFDF5320EAD94"
    }
  },
  {
    id: "stock_analyst_rating_tdx",
    title: "机构评级与目标价",
    group: "F10数据",
    summary: "查询机构评级家数和目标价统计。",
    functionText: "获取机构评级与目标价",
    key: "instrument_id,date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "按评级统计日期过滤的起始日期；不传返回源端本次给出的记录"], ["end_date", "string", "否", "按评级统计日期过滤的结束日期；不传返回源端本次给出的记录"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "评级统计日期"],
      ["buy_count", "integer", "买入家数"],
      ["overweight_count", "integer", "增持家数"],
      ["neutral_count", "integer", "中性家数"],
      ["underweight_count", "integer", "减持家数"],
      ["sell_count", "integer", "卖出家数"],
      ["target_price", "number", "平均目标价"],
      ["target_price_low", "number", "目标价下限"],
      ["target_price_high", "number", "目标价上限"],
      ["current_price", "number", "当前价"],
      ["upside_pct", "number", "上涨空间，单位：%"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260611",
      buy_count: 13,
      overweight_count: 7,
      neutral_count: 2,
      target_price: 14.162143,
      target_price_low: 13.52,
      target_price_high: 14.62,
      current_price: 11.06,
      upside_pct: 32.1880651
    }
  },
  {
    id: "stock_institution_holding_tdx",
    title: "机构持仓",
    group: "F10数据",
    summary: "查询机构持仓比例多期趋势。",
    functionText: "获取机构持仓",
    key: "instrument_id,date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "按报告日期过滤的起始日期；不传返回源端本次给出的全部记录"], ["end_date", "string", "否", "按报告日期过滤的结束日期；不传返回源端本次给出的全部记录"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "报告日期"],
      ["report_period", "string", "报告期名称"],
      ["institution_holding_ratio_pct", "number", "机构持仓比例，单位：%"],
      ["close", "number", "当期收盘价，单位：元"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260331",
      report_period: "2026一季报",
      institution_holding_ratio_pct: 2.94,
      close: 11.08
    }
  },
  {
    id: "stock_governance_guarantees_tdx",
    title: "担保明细",
    group: "F10数据",
    summary: "查询担保方、被担保方、担保金额和担保期限。",
    functionText: "获取担保明细",
    key: "instrument_id,report_period,guarantor",
    params: [f10CommonCodeParam, ["period", "string", "否", "报告期；不传自动取最新可用报告期"], ["count", "integer", "否", "返回条数，默认 20；该接口单期可能有大量明细"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["report_period", "date/string", "报告期"],
      ["guarantor", "string", "担保方"],
      ["guaranteed_party", "string", "被担保方"],
      ["amount", "number", "担保金额"],
      ["currency", "string", "币种"],
      ["guarantee_type", "string", "担保类型"],
      ["is_completed", "string", "是否履行完毕"],
      ["is_related_party", "string", "是否关联交易"],
      ["actual_date", "date/string", "实际发生日"],
      ["term", "number/string", "担保期限，源端原值，可能为数字或空"]
    ],
    exampleParams: `code="000034.SZ", count=3`,
    exampleRow: {
      instrument_id: "000034.SZ",
      report_period: "20251231",
      guarantor: "神州数码集团股份有限公司子公司",
      guaranteed_party: "神码澳门离岸",
      amount: 1233451900,
      currency: "人民币",
      guarantee_type: "一般保证",
      is_completed: "否",
      is_related_party: "是",
      actual_date: "20250911",
      term: null
    }
  },
  {
    id: "stock_violation_cases_tdx",
    title: "违规处理",
    group: "F10数据",
    summary: "查询违规处理和处罚决定。",
    functionText: "获取违规处理",
    key: "instrument_id,publish_date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "按立案日期过滤的起始日期；不传返回源端本次给出的全部记录"], ["end_date", "string", "否", "按立案日期过滤的结束日期；不传返回源端本次给出的全部记录"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["case_date", "date/string", "立案日期"],
      ["case_type", "string", "立案类型"],
      ["publish_date", "date/string", "处罚公布日期，源端可能为空"],
      ["progress", "string", "案情进展"],
      ["detail_id", "string", "违法事实详情 ID"],
      ["decision", "string", "处罚决定，源端可能为空"]
    ],
    exampleParams: `code="600519.SH"`,
    exampleRow: {
      instrument_id: "600519.SH",
      case_date: "20260313",
      case_type: "董监高违法违规",
      progress: "被留置调查",
      detail_id: 1002375
    }
  },
  {
    id: "stock_regulatory_actions_tdx",
    title: "监管措施",
    group: "F10数据",
    summary: "查询监管措施或处罚函件。",
    functionText: "获取监管措施",
    key: "instrument_id,publish_date,target",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "按处罚公布日期过滤的起始日期；不传返回源端本次给出的全部记录"], ["end_date", "string", "否", "按处罚公布日期过滤的结束日期；不传返回源端本次给出的全部记录"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["publish_date", "date/string", "处罚公布日期"],
      ["target", "string", "处罚对象"],
      ["action", "string", "监管措施"],
      ["content", "string", "函件内容"],
      ["link", "string", "链接，源端可能为空"]
    ],
    exampleParams: `code="000034.SZ", count=3`,
    exampleRow: {
      instrument_id: "000034.SZ",
      publish_date: "20220817",
      target: "上市公司董监高",
      action: "监管函",
      content: "关于对叶海强的监管函",
      link: "http://reportdocs.static.szse.cn/UpFiles/jgsy/gkxx_jgsy_000034174831.pdf"
    }
  },
  {
    id: "stock_score_summary_tdx",
    title: "综合评分",
    group: "F10数据",
    summary: "查询源端综合评分、维度评分和排名；这是源端评价，不代表 AxData 自有判断。",
    functionText: "获取源端综合评分",
    key: "instrument_id,date",
    params: [f10CommonCodeParam],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["score", "number", "源端综合评分"],
      ["industry_rank", "integer", "行业排名名次"],
      ["industry_rank_total", "integer", "行业排名总数"],
      ["market_rank", "integer", "A 股市场排名名次"],
      ["market_rank_total", "integer", "A 股市场排名总数"],
      ["market_win_pct", "number", "打败 A 股百分比"],
      ["date", "date/string", "日期"],
      ["capital_score", "number", "资金面评分"],
      ["fundamental_score", "number", "基本面评分"],
      ["news_score", "number", "消息面评分"],
      ["theme_score", "number", "主题面评分"],
      ["industry_name", "string", "行业名"],
      ["stock_name", "string", "股票名"]
    ],
    exampleParams: `code="000001.SZ"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      score: 2.932,
      industry_rank: 11,
      industry_rank_total: 15,
      market_rank: 3028,
      market_rank_total: 5521,
      market_win_pct: 45.173,
      date: "20260616",
      capital_score: 2,
      fundamental_score: 2.33,
      news_score: 3,
      theme_score: 5,
      industry_name: "全国性银行",
      stock_name: "平安银行"
    },
    note: "该接口返回源端评价或评分，不代表 AxData 自有判断。"
  },
  {
    id: "stock_market_rankings_tdx",
    title: "排名明细",
    group: "F10数据",
    summary: "查询市场或行业排名明细。",
    functionText: "获取排名明细",
    key: "rank,instrument_id",
    params: [f10CommonCodeParam, ["scope", "string", "否", "范围：market 全市场排名，industry 为传入股票所属行业内排名；默认 market。建议单只股票调用"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["rank", "integer", "排名"],
      ["rank_change", "number", "排名变化"],
      ["symbol", "string", "股票代码"],
      ["name", "string", "证券简称"],
      ["exchange", "string", "AxData 交易所代码"],
      ["market_code", "string", "市场代码"],
      ["updated_time", "datetime/string", "更新时间"]
    ],
    exampleParams: `code="000001.SZ", scope="market", count=5`,
    exampleRow: {
      instrument_id: "002428.SZ",
      rank: 1,
      rank_change: -6,
      symbol: "002428",
      name: "云南锗业",
      exchange: "SZSE",
      market_code: "0",
      updated_time: "20260616"
    }
  },
  {
    id: "stock_disclosure_feed_tdx",
    title: "新闻公告路演",
    group: "F10数据",
    summary: "查询个股新闻、公告或路演列表；不同类型返回字段会有差异，缺失项返回 null。",
    functionText: "获取新闻公告路演",
    key: "instrument_id,issue_date,title",
    params: [f10CommonCodeParam, ["category", "string", "否", "类型：news 新闻、announcement 公告、roadshow 路演；默认 announcement"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["category", "string", "资讯类型：news、announcement、roadshow"],
      ["issue_date", "datetime/string", "发布时间或公告日期；路演通常为空"],
      ["title", "string", "标题"],
      ["source", "string", "来源；路演通常为空"],
      ["detail_table", "string", "详情来源表"],
      ["detail_id", "string", "记录 ID；路演通常为空"],
      ["type_code", "string", "公告类型码；非公告通常为空"],
      ["type_name", "string", "公告类型名；非公告通常为空"],
      ["url", "string", "PDF、新闻或活动链接；源端无链接时为空"],
      ["summary", "string", "摘要；源端无摘要时为空"],
      ["start_date", "date/string", "路演开始日期；非路演为空"],
      ["start_time", "time/string", "路演开始时间；非路演为空"],
      ["end_time", "time/string", "路演结束时间；非路演为空"]
    ],
    exampleParams: `code="000001.SZ", category="announcement", count=5`,
    exampleRow: {
      instrument_id: "000001.SZ",
      symbol: "000001",
      category: "announcement",
      issue_date: "20260605",
      title: "平安银行：2025年年度权益分派实施公告",
      source: "深交所",
      detail_table: "tb_gg_abg",
      detail_id: "1225352449",
      type_code: "0113",
      type_name: "权益分派与限制出售股份上市",
      url: "http://data.tdx.com.cn/tdxfiles/pdf_abg_sz/202606/1225352449.pdf",
      summary: null,
      start_date: null,
      start_time: null,
      end_time: null
    }
  },
  {
    id: "stock_event_drivers_tdx",
    title: "历史事件关联",
    group: "F10数据",
    summary: "查询个股历史事件关联记录；不是涨停原因库，可选补充详情正文。",
    functionText: "获取历史事件关联",
    key: "instrument_id,event_date,event_name",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "起始日期；按事件创建日期过滤"], ["end_date", "string", "否", "结束日期；按事件创建日期过滤"], ["include_detail", "boolean", "否", "是否补充详情正文，默认 false"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["event_date", "date/string", "事件创建日期"],
      ["event_name", "string", "事件名称，不等同于涨停原因"],
      ["detail_id", "string", "事件详情 ID"],
      ["event_nature", "string", "事件性质"],
      ["creation_change_pct", "number", "创建日涨跌幅，单位：%"],
      ["has_detail", "boolean", "是否有详情正文"],
      ["detail_title", "string", "详情标题；include_detail=true 时补充"],
      ["detail_text", "string", "详情正文；include_detail=true 时补充"]
    ],
    exampleParams: `code="000001.SZ", start_date="20150101", end_date="20190212", include_detail=true`,
    exampleRow: {
      instrument_id: "000001.SZ",
      event_date: "20150625",
      event_name: "商业银行75%存贷比取消",
      detail_id: 2304,
      event_nature: "利好",
      creation_change_pct: -1.6534,
      has_detail: true,
      detail_title: "事件背景",
      detail_text: "2015年6月24日，国务院常务会议通过《中华人民共和国商业银行法案修正案(草案)》，草案删除了贷款余额与存款余额比例不得超过75%的规定。"
    }
  },
  {
    id: "stock_topic_exposure_tdx",
    title: "个股题材",
    group: "短线数据",
    summary: "查询个股所属题材、关联度和入选原因。",
    functionText: "获取个股题材",
    key: "instrument_id,topic_id",
    paramsNote: "不传时间；按 code 和 topic_type 返回该股票当前完整题材列表。",
    params: [f10CommonCodeParam, ["topic_type", "string", "否", "题材类型：sector 板块题材、theme 主题题材；默认 theme"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["topic_type", "string", "题材类型：sector 板块题材、theme 主题题材"],
      ["created_date", "date/string", "创建日期"],
      ["topic_name", "string", "题材名称"],
      ["relevance", "number", "关联度，源端评价分值"],
      ["selected_date", "date/string", "入选或更新日期；源端可能为空"],
      ["reason", "string", "入选原因或栏目内容"],
      ["topic_id", "string", "题材 ID"],
      ["group_code", "string", "源端分组类别码；主题题材可能为空"]
    ],
    exampleParams: `code="000001.SZ", topic_type="theme"`,
    exampleRows: [
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20161202",
        topic_name: "平安保险持股",
        relevance: 5,
        selected_date: "20260323",
        reason: "中国平安保险(集团)股份有限公司是公司控股股东",
        topic_id: "900",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20230829",
        topic_name: "不可减持(新规)",
        relevance: 4,
        selected_date: null,
        reason: "公司近20个交易日内跌破净资产，依照减持新规，控股股东和实际控制人不可减持。",
        topic_id: "2965",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20130910",
        topic_name: "优先股",
        relevance: 5,
        selected_date: "20211108",
        reason: "公司旗下有优先股平银优01",
        topic_id: "508",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20130128",
        topic_name: "农业保险",
        relevance: 3,
        selected_date: "20211018",
        reason: "公司有其他业务涉及保险代理服务",
        topic_id: "361",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20201203",
        topic_name: "罗素大盘",
        relevance: 3,
        selected_date: "20210926",
        reason: "公司符合罗素大盘股标准",
        topic_id: "2714",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20210814",
        topic_name: "零售金融业务",
        relevance: 5,
        selected_date: "20220927",
        reason: "公司是卓越领先的智能化零售银行",
        topic_id: "X500101004",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20211022",
        topic_name: "批发金融业务",
        relevance: 4,
        selected_date: "20220927",
        reason: "公司主营业务包括批发金融业务",
        topic_id: "X500102005",
        group_code: null
      },
      {
        instrument_id: "000001.SZ",
        symbol: "000001",
        topic_type: "theme",
        created_date: "20220324",
        topic_name: "汽车金融",
        relevance: 3,
        selected_date: "20220927",
        reason: "公司主营业务包括汽车金融业务",
        topic_id: "X260402006",
        group_code: null
      }
    ]
  },
  {
    id: "concept_related_boards_tdx",
    title: "相关板块",
    group: "短线数据",
    summary: "查询个股当前关联板块列表。",
    functionText: "获取相关板块",
    key: "board_code",
    paramsNote: "不传时间；按 code 返回该股票当前关联板块列表。",
    params: [f10CommonCodeParam],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["board_market", "string", "板块市场"],
      ["board_code", "string", "板块代码"],
      ["board_name", "string", "板块名称"],
      ["change_pct", "number", "涨幅，单位：%"],
      ["limit_up_count", "integer", "涨停数"]
    ],
    exampleParams: `code="000001.SZ"`
  },
  {
    id: "concept_constituents_tdx",
    title: "板块成分股",
    group: "短线数据",
    summary: "按板块代码查询当前成分股。",
    functionText: "获取板块成分股",
    key: "concept_code,instrument_id",
    paramsNote: "需先用相关板块接口按股票代码查询，取返回的 board_code 填到 concept_code；不传时间，返回当前成分股列表。",
    params: [["concept_code", "string", "是", "板块代码；先用相关板块接口按股票代码查询，取返回的 board_code 填入"], ["count", "integer", "否", "返回前多少只，默认 20，最大 500"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "交易所原始六位代码"],
      ["exchange", "string", "AxData 交易所代码：SSE、SZSE 或 BSE"],
      ["market_code", "string", "市场代码"],
      ["name", "string", "股票名称"],
      ["change_pct", "number", "涨幅，单位：%"],
      ["last_price", "number", "现价，单位：元"]
    ],
    exampleParams: `concept_code="881386", count=5`
  },
  {
    id: "concept_capital_flow_tdx",
    title: "题材资金走势",
    group: "短线数据",
    summary: "按题材或行业 ID 查询主力资金走势。",
    functionText: "获取题材资金走势",
    key: "concept_code,date",
    paramsNote: "按题材或行业 ID 返回资金走势；并非相关板块的 board_code 都可用，部分 ID 可能没有资金走势。",
    params: [["concept_code", "string", "是", "题材或行业 ID；可先从个股题材接口返回的 topic_id 中选择，部分 ID 可能没有资金走势"], ["start_date", "string", "否", "起始日期；按 date 过滤"], ["end_date", "string", "否", "结束日期；按 date 过滤"], ["count", "integer", "否", "返回条数，默认 20，最大 500"]],
    fields: [
      ["board_name", "string", "题材或行业名"],
      ["date", "date/string", "日期"],
      ["main_amount", "number", "主力资金"],
      ["main_buy_amount", "number", "主买资金"],
      ["avg_main_amount", "number", "平均主力资金"],
      ["avg_main_buy_amount", "number", "平均主买资金"]
    ],
    exampleParams: `concept_code="2817", count=5`
  },
  {
    id: "concept_control_series_tdx",
    title: "主力控盘序列",
    group: "F10数据",
    summary: "查询每日主力控盘比例序列。",
    functionText: "获取主力控盘序列",
    key: "date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "起始日期；按 date 过滤"], ["end_date", "string", "否", "结束日期；按 date 过滤"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["date", "date/string", "日期"],
      ["control_ratio_pct", "number", "主力控盘比例，单位：%"],
      ["board_code", "string", "所属板块代码"],
      ["board_name", "string", "所属板块名称"],
      ["rank", "integer", "排名"]
    ],
    exampleParams: `code="000001.SZ", count=5`,
    exampleRow: {
      date: "20260601",
      control_ratio_pct: 41.58,
      board_code: "881386",
      board_name: "全国性银行",
      rank: 6
    }
  },
  {
    id: "concept_control_ranking_tdx",
    title: "控盘榜单",
    group: "F10数据",
    summary: "查询行业或题材按日期返回的控盘榜单；每个日期内通常是前十名。",
    functionText: "获取控盘榜单",
    key: "date,rank",
    paramsNote: "按题材或行业 ID 返回按日期拍平后的控盘榜单；不是相关板块 board_code，部分 ID 可能没有控盘榜单。",
    params: [["concept_code", "string", "是", "题材或行业 ID；可先从个股题材接口返回的 topic_id 中选择，部分 ID 可能没有控盘榜单"], ["count", "integer", "否", "返回前多少条榜单记录，默认 20，最大 500；记录按日期榜单拍平后计数"]],
    fields: [
      ["date", "date/string", "日期"],
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["exchange", "string", "AxData 交易所代码"],
      ["rank", "integer", "排名"],
      ["market_code", "integer", "市场代码"],
      ["symbol", "string", "股票代码"],
      ["name", "string", "股票名称"],
      ["control_ratio_pct", "number", "控盘比例，单位：%"]
    ],
    exampleParams: `concept_code="2817", count=5`,
    exampleRow: {
      date: "20260506",
      instrument_id: "002102.SZ",
      exchange: "SZSE",
      rank: 1,
      market_code: 0,
      symbol: "002102",
      name: "ST能特",
      control_ratio_pct: 57.8
    }
  },
  {
    id: "concept_constituent_comparison_tdx",
    title: "题材内对比",
    group: "F10数据",
    summary: "查询题材内股票涨幅、财务或市值对比。",
    functionText: "获取题材内对比",
    key: "concept_code,rank",
    paramsNote: "return 视图主要返回涨幅字段；financial 视图主要返回财务、市值和报告期字段。",
    params: [f10CommonCodeParam, ["concept_code", "string", "是", "题材 ID"], ["compare_type", "string", "否", "对比类型：return 涨幅，financial 财务；默认 return"], ["sort_by", "string", "否", "源端排序字段，默认 zdf；实测不同字段可能仍按源端默认排序"]],
    fields: [
      ["rank", "integer", "排名"],
      ["market_code", "integer", "市场代码"],
      ["symbol", "string", "股票代码"],
      ["name", "string", "股票简称"],
      ["report_period", "date/string", "财务数据报告期；compare_type=financial 时返回"],
      ["change_pct", "number", "涨幅，单位：%"],
      ["change_pct_3d", "number", "3 日涨幅，单位：%"],
      ["change_pct_5d", "number", "5 日涨幅，单位：%"],
      ["change_pct_20d", "number", "20 日涨幅，单位：%"],
      ["change_pct_60d", "number", "60 日涨幅，单位：%"],
      ["total_market_cap", "number", "总市值"],
      ["float_market_cap", "number", "流通市值"],
      ["revenue", "number", "营业收入"],
      ["net_profit", "number", "归母净利润"],
      ["revenue_yoy_pct", "number", "营收同比，单位：%"],
      ["net_profit_yoy_pct", "number", "归母净利润同比，单位：%"]
    ],
    exampleParams: `code="000001.SZ", concept_code="2817", compare_type="return"`,
    exampleRow: {
      rank: 1,
      market_code: 1,
      symbol: "600577",
      name: "精达股份",
      report_period: null,
      change_pct: 6.45,
      change_pct_3d: -2.2,
      change_pct_5d: -4.7,
      change_pct_20d: -17.91,
      change_pct_60d: -19.34
    }
  },
  {
    id: "stock_valuation_metrics_tdx",
    title: "估值表",
    group: "F10数据",
    summary: "查询估值、市值和估值百分位。",
    functionText: "获取估值表",
    key: "instrument_id,date",
    params: [f10CommonCodeParam, ["start_date", "string", "否", "起始日期；按 date 过滤"], ["end_date", "string", "否", "结束日期；按 date 过滤"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "日期"],
      ["pe_ttm", "number", "PE(TTM)"],
      ["pe_percentile", "number", "PE 百分位"],
      ["pb_mrq", "number", "PB(MRQ)"],
      ["pb_percentile", "number", "PB 百分位"],
      ["pcf_ttm", "number", "市现率(TTM)"],
      ["pcf_percentile", "number", "市现率百分位"],
      ["ps_ttm", "number", "市销率(TTM)"],
      ["ps_percentile", "number", "市销率百分位"],
      ["peg", "number", "PEG"],
      ["float_market_cap", "number", "流通市值"],
      ["total_market_cap", "number", "总市值"]
    ],
    exampleParams: `code="000001.SZ", count=3`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260615",
      pe_ttm: 4.98,
      pe_percentile: 41.21,
      pb_mrq: 0.46,
      pb_percentile: 5.7,
      pcf_ttm: 1.13,
      pcf_percentile: 42.69,
      ps_ttm: 1.61,
      ps_percentile: 64.66,
      peg: 0.1,
      float_market_cap: 214625959936,
      total_market_cap: 214629466112
    }
  },
  {
    id: "stock_valuation_series_tdx",
    title: "单指标估值序列",
    group: "F10数据",
    summary: "查询单个估值指标的历史序列和百分位，适合画 PE/PB/PS/PCF 曲线。",
    functionText: "获取单指标估值序列",
    key: "instrument_id,date,metric",
    params: [f10CommonCodeParam, ["metric", "string", "否", "指标：pe、pb、pcf、ps；默认 pe"], ["start_date", "string", "否", "起始日期；按 date 过滤"], ["end_date", "string", "否", "结束日期；按 date 过滤"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "日期"],
      ["metric", "string", "指标"],
      ["value", "number", "指标值"],
      ["percentile", "number", "历史百分位"]
    ],
    exampleParams: `code="000001.SZ", metric="pe", start_date="20260601", end_date="20260605", count=5`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20260601",
      metric: "pe",
      value: 4.95,
      percentile: 37.49
    }
  },
  {
    id: "stock_valuation_band_tdx",
    title: "PE/PB估值通道",
    group: "F10数据",
    summary: "查询 PE/PB Band 估值通道数据，用于绘制估值带图。",
    functionText: "获取 PE/PB 估值通道",
    key: "instrument_id,date,metric",
    params: [f10CommonCodeParam, ["metric", "string", "否", "指标：pe 或 pb；默认 pe"], ["start_date", "string", "否", "起始日期；按 date 过滤"], ["end_date", "string", "否", "结束日期；按 date 过滤"], ["count", "integer", "否", "返回条数，默认 20"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["date", "date/string", "日期"],
      ["band_value_1", "number", "当前 PE 或 PB 指标值"],
      ["band_value_2", "number", "通道辅助值 2，源端用于绘制 Band"],
      ["band_value_3", "number", "通道辅助值 3，源端用于绘制 Band"],
      ["total_count", "integer", "当前统计区间样本数"],
      ["min_value", "number", "当前统计区间最小值"],
      ["mid_value", "number", "当前统计区间中位值"]
    ],
    exampleParams: `code="000001.SZ", metric="pe", count=3`,
    exampleRow: {
      instrument_id: "000001.SZ",
      date: "20250616",
      band_value_1: 5.239,
      band_value_2: 11.79,
      band_value_3: 11.79,
      total_count: 243,
      min_value: 4.7567,
      mid_value: 5.1667
    }
  },
  {
    id: "stock_return_calendar_tdx",
    title: "月度年度涨跌幅",
    group: "F10数据",
    summary: "按年份汇总股票 1 至 12 月涨跌幅和全年涨跌幅，用于查看历史收益日历。",
    functionText: "获取收益日历",
    key: "instrument_id,year",
    params: [f10CommonCodeParam, ["year", "string", "否", "年份，可选；不传返回全部可用年份"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["year", "string", "年份"],
      ["month_1_pct", "number", "1 月涨跌幅，单位：%"],
      ["month_2_pct", "number", "2 月涨跌幅，单位：%"],
      ["month_3_pct", "number", "3 月涨跌幅，单位：%"],
      ["month_12_pct", "number", "12 月涨跌幅，单位：%"],
      ["year_pct", "number", "年度涨跌幅，单位：%"]
    ],
    exampleParams: `code="000001.SZ", year="2026"`,
    exampleRow: {
      instrument_id: "000001.SZ",
      year: "2026",
      month_1_pct: -5.0833,
      month_2_pct: 0.6463,
      month_3_pct: 1.6514,
      month_12_pct: 0,
      year_pct: -0.964
    }
  }
];

function createF10CatalogItem(spec: F10CatalogSpec): CatalogItem {
  const params = f10ParamCatalog[spec.id] ?? spec.params;
  const fields = f10FieldCatalog[spec.id] ?? spec.fields;
  const catalogExampleParams = f10ExampleParamCatalog[spec.id];
  const defaultParams = Object.fromEntries(
    params
      .filter((param) => param[2] === "是" || ["code", "category", "type"].includes(param[0]))
      .map((param) => {
        if (param[0] === "code") return [param[0], "000034.SZ"];
        if (param[0] === "concept_code") return [param[0], "2945"];
        if (param[0] === "event_date") return [param[0], "20160301"];
        if (param[0] === "category") return [param[0], "announcement"];
        if (param[0] === "type") return [param[0], "listing"];
        return [param[0], "demo"];
      })
  );
  const parsedParams = parseF10ExampleParams(spec.exampleParams);
  const previewParams = spec.curlParams ?? catalogExampleParams ?? parsedParams ?? defaultParams;
  const paramsObject = JSON.stringify(previewParams);
  const paramsExample = buildF10ParamsExample(spec, previewParams);
  const sdkCall = `client.call("${spec.id}", ${f10ParamsToPythonArgs(previewParams)})`;
  const fastApiParams = f10ParamsToFastApiArgs(previewParams);
  const fastApiCallArgs = f10ParamsToFastApiCallArgs(previewParams);
  const sampleRows = f10SampleRows[spec.id] ?? [];
  const sampleColumns = sampleRows.length > 0
    ? fields
        .map((field) => field[0])
        .filter((fieldName) => sampleRows.some((row) => row[fieldName] !== undefined && row[fieldName] !== null))
    : [];
  const dataExamples = sampleRows.length > 0
    ? [
        {
          id: `${spec.id}-sample`,
          title: "返回示例",
          icon: Database,
          note: "以下为真实源端请求样例；实际返回会随源端更新变化。",
          columns: sampleColumns,
          rows: sampleRows.map((row) => sampleColumns.map((column) => valueToDisplay(row[column])))
        }
      ]
    : undefined;
  return {
    id: spec.id,
    group: `通达信/股票数据/${spec.group}`,
    title: spec.title,
    name: spec.id,
    method: "POST",
    path: `/v1/request/${spec.id}`,
    status: "ready",
    icon: FileText,
    cadence: "现用现查",
    key: spec.key,
    limit: "按接口参数返回；默认不写入本地数据层",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: spec.summary,
    description: spec.note ? `${spec.summary} ${spec.note}` : spec.summary,
    overview: [
      ["接口名称", spec.id],
      ["接口功能", spec.functionText]
    ],
    notice: spec.note,
    paramsNote: spec.paramsNote,
    paramsExample,
    params,
    fields,
    dataExamples,
    callModes: tdxSourceRequestCallModes,
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = ${sdkCall}
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = ${sdkCall}
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/${spec.id}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":${paramsObject},"persist":false}'`
  };
}

function buildF10ParamsExample(spec: F10CatalogSpec, singleParams: F10ParamsObject): string {
  if (spec.id === "concept_constituents_tdx") {
    return `# 第一步：按股票查它关联的板块，拿 board_code
boards = client.call("concept_related_boards_tdx", code="000001.SZ")
concept_code = boards.iloc[0]["board_code"]

# 第二步：按板块代码查当前成分股
client.call("concept_constituents_tdx", concept_code=concept_code, count=5)`;
  }

  const singleCall = `client.call("${spec.id}", ${f10ParamsToPythonArgs(singleParams)})`;
  const supportsCodeBatch = spec.params.some((param) => param[0] === "code" && param[1].includes("list"));
  if (!supportsCodeBatch) {
    return singleCall;
  }

  const batchParams = { ...singleParams, code: ["000034.SZ", "000001.SZ"] };
  return `# 单个标的
${singleCall}

# 批量请求多个标的
client.call("${spec.id}", ${f10ParamsToPythonArgs(batchParams)})`;
}

function f10ParamsToPythonArgs(params: F10ParamsObject): string {
  return Object.entries(params)
    .map(([key, value]) => `${key}=${f10ValueToPython(value)}`)
    .join(", ");
}

function f10ParamsToFastApiArgs(params: F10ParamsObject): string {
  return Object.entries(params)
    .map(([key, value]) => `${key}: ${f10FastApiType(value)}`)
    .join(", ");
}

function f10ParamsToFastApiCallArgs(params: F10ParamsObject): string {
  return Object.keys(params)
    .map((key) => `${key}=${key}`)
    .join(", ");
}

function f10FastApiType(value: F10ParamValue): string {
  if (Array.isArray(value)) {
    return "str";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? "int" : "float";
  }
  if (typeof value === "boolean") {
    return "bool";
  }
  return "str";
}

function f10ValueToPython(value: F10ParamValue): string {
  if (Array.isArray(value)) {
    return `[${value.map(f10ValueToPython).join(", ")}]`;
  }
  if (typeof value === "string") {
    return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
  }
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  return String(value);
}

function valueToDisplay(value: string | number | boolean | null | undefined): string {
  if (value === null) return "null";
  if (value === undefined) return "";
  return String(value);
}

function parseF10ExampleParams(exampleParams: string): F10ParamsObject | undefined {
  const params: F10ParamsObject = {};
  const paramPattern = /(\w+)\s*=\s*(\[[^\]]*\]|"[^"]*"|true|false|True|False|-?\d+(?:\.\d+)?)/g;
  for (const match of exampleParams.matchAll(paramPattern)) {
    const rawValue = match[2];
    if (rawValue.startsWith("[")) {
      const values = Array.from(rawValue.matchAll(/"([^"]*)"|true|false|True|False|-?\d+(?:\.\d+)?/g)).map((valueMatch) => {
        const value = valueMatch[0];
        if (value.startsWith("\"")) return value.slice(1, -1);
        if (value === "true" || value === "True") return true;
        if (value === "false" || value === "False") return false;
        return Number(value);
      });
      params[match[1]] = values;
    } else if (rawValue.startsWith("\"")) {
      params[match[1]] = rawValue.slice(1, -1);
    } else if (rawValue === "true" || rawValue === "false" || rawValue === "True" || rawValue === "False") {
      params[match[1]] = rawValue === "true" || rawValue === "True";
    } else {
      params[match[1]] = Number(rawValue);
    }
  }
  return Object.keys(params).length > 0 ? params : undefined;
}

tdxCatalogItems.push(...f10CatalogSpecs.map(createF10CatalogItem));

export const tdxNavGroup: CatalogGroup = {
  title: "通达信",
  keepWhenEmpty: true,
  children: [
    {
      title: "股票数据",
      children: [
        {
          title: "基础数据",
          items: [
            "stock_codes_tdx",
            "stock_st_list_tdx",
            "stock_suspensions_tdx",
            "stock_daily_share_tdx",
            "stock_daily_price_limit_tdx",
            "stock_capital_changes_tdx"
          ]
        },
        {
          title: "实时数据",
          items: [
            "stock_quote_refresh_tdx",
            "stock_realtime_rank_tdx",
            "stock_realtime_snapshot_tdx",
            "stock_order_book_tdx",
            "stock_intraday_buy_sell_strength_tdx",
            "stock_intraday_volume_comparison_tdx"
          ]
        },
        {
          title: "短线数据",
          items: [
            "stock_limit_ladder_tdx",
            "stock_theme_strength_rank_tdx",
            "stock_shortline_indicators_tdx",
            "stock_topic_exposure_tdx",
            "concept_related_boards_tdx",
            "concept_constituents_tdx",
            "concept_capital_flow_tdx"
          ]
        },
        {
          title: "行情数据",
          items: [
            "stock_adj_factor_tdx",
            "stock_intraday_today_tdx",
            "stock_intraday_history_tdx",
            "stock_intraday_recent_history_tdx",
            "stock_trades_today_tdx",
            "stock_trades_history_tdx",
            "stock_kline_second_tdx",
            "stock_kline_minute_tdx",
            "stock_kline_nminute_tdx",
            "stock_kline_daily_tdx",
            "stock_kline_nday_tdx",
            "stock_kline_weekly_tdx",
            "stock_kline_monthly_tdx",
            "stock_kline_quarterly_tdx",
            "stock_kline_yearly_tdx"
          ]
        },
        {
          title: "竞价数据",
          items: [
            "stock_auction_process_tdx",
            "stock_auction_result_tdx",
            "stock_auction_result_history_tdx"
          ]
        },
        {
          title: "财务数据",
          items: [
            "stock_finance_summary_tdx",
            "stock_share_capital_tdx",
            "stock_balance_summary_tdx",
            "stock_profit_cashflow_summary_tdx",
            "stock_finance_profile_tdx"
          ]
        },
        {
          title: "F10数据",
          items: [
            "stock_ipo_listing_profile_tdx",
            "stock_index_constituent_changes_tdx",
            "stock_business_composition_tdx",
            "stock_financial_statement_tdx",
            "stock_financial_diagnosis_tdx",
            "stock_forecast_consensus_tdx",
            "stock_dividend_history_tdx",
            "stock_dividend_metrics_tdx",
            "stock_equity_financing_events_tdx",
            "stock_private_placement_allocations_tdx",
            "stock_shareholder_change_plans_tdx",
            "stock_northbound_holding_tdx",
            "stock_margin_trading_tdx",
            "stock_chip_distribution_tdx",
            "stock_research_reports_tdx",
            "stock_analyst_rating_tdx",
            "stock_institution_holding_tdx",
            "stock_governance_guarantees_tdx",
            "stock_violation_cases_tdx",
            "stock_regulatory_actions_tdx",
            "stock_score_summary_tdx",
            "stock_market_rankings_tdx",
            "stock_disclosure_feed_tdx",
            "stock_event_drivers_tdx",
            "concept_control_series_tdx",
            "concept_control_ranking_tdx",
            "concept_constituent_comparison_tdx",
            "stock_valuation_metrics_tdx",
            "stock_valuation_series_tdx",
            "stock_valuation_band_tdx",
            "stock_return_calendar_tdx"
          ]
        }
      ]
    },
    {
      title: "指数数据",
      keepWhenEmpty: true,
      items: [
        "index_codes_tdx",
        "index_realtime_snapshot_tdx",
        "index_realtime_rank_tdx",
        "index_quote_refresh_tdx",
        "index_kline_tdx",
        "index_intraday_today_tdx",
        "index_intraday_history_tdx"
      ]
    },
    {
      title: "ETF数据",
      keepWhenEmpty: true,
      items: [
        "etf_codes_tdx",
        "etf_realtime_snapshot_tdx",
        "etf_realtime_rank_tdx",
        "etf_kline_tdx",
        "etf_intraday_today_tdx",
        "etf_intraday_history_tdx",
        "etf_trades_today_tdx",
        "etf_trades_history_tdx",
        "etf_auction_process_tdx",
        "etf_auction_result_tdx"
      ]
    },
    {
      title: "基金数据",
      keepWhenEmpty: true,
      items: [
        "fund_codes_tdx",
        "fund_nav_tdx",
        "fund_nav_series_tdx"
      ]
    },
    {
      title: "期货数据",
      keepWhenEmpty: true,
      items: [
        "tdx_ext_markets_tdx",
        "tdx_ext_instruments_tdx",
        "futures_contracts_tdx",
        "futures_realtime_snapshot_tdx",
        "futures_kline_tdx",
        "futures_intraday_today_tdx",
        "futures_intraday_history_tdx",
        "futures_trades_today_tdx",
        "futures_trades_history_tdx"
      ]
    },
    {
      title: "期权数据",
      keepWhenEmpty: true,
      items: [
        "option_contracts_tdx",
        "option_chain_tdx",
        "option_realtime_snapshot_tdx",
        "option_kline_tdx",
        "option_intraday_today_tdx",
        "option_intraday_history_tdx"
      ]
    },
    {
      title: "债券数据",
      keepWhenEmpty: true,
      items: [
        "bond_codes_tdx",
        "bond_realtime_snapshot_tdx",
        "bond_kline_tdx"
      ]
    },
    {
      title: "外汇数据",
      keepWhenEmpty: true,
      items: [
        "fx_codes_tdx",
        "fx_realtime_snapshot_tdx",
        "fx_kline_tdx",
        "fx_intraday_today_tdx",
        "fx_intraday_history_tdx",
        "fx_trades_today_tdx",
        "fx_trades_history_tdx"
      ]
    },
    {
      title: "宏观数据",
      keepWhenEmpty: true,
      items: [
        "macro_indicators_tdx",
        "macro_indicator_snapshot_tdx",
        "macro_indicator_series_tdx"
      ]
    }
  ]
};
