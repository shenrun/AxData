import { CalendarDays, Info, ListChecks } from "lucide-react";
import type { CatalogGroup, CatalogItem, SourceContractSpec } from "../../types";

export const exchangeSourceContracts: SourceContractSpec[] = [
  {
    id: "stock_trade_calendar_exchange",
    interfaceName: "stock_trade_calendar_exchange",
    title: "交易日历",
    group: "基础数据",
    cadence: "现用现查",
    key: "cal_date",
    summary: "从深交所官方交易日历返回指定日期范围内的开闭市信息。",
    params: [
      ["year", "integer/string", "否", "年份，例如 2026；传 start_date/end_date 时优先按日期范围查询"],
      ["start_date", "string", "否", "开始日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["end_date", "string", "否", "结束日期，YYYYMMDD 或 YYYY-MM-DD"]
    ],
    fields: [
      ["cal_date", "date/string", "自然日期，格式 YYYYMMDD"],
      ["is_open", "boolean", "是否交易日"],
      ["pretrade_date", "date/string", "上一个交易日；非交易日也返回最近上一交易日"],
      ["next_trade_date", "date/string", "下一个交易日；非交易日也返回最近下一交易日"]
    ]
  },
  {
    id: "stock_historical_list_exchange",
    interfaceName: "stock_historical_list_exchange",
    title: "历史股票列表",
    group: "基础数据",
    cadence: "现用现查",
    key: "trade_date + instrument_id",
    summary: "按交易所官方上市日期和退市日期计算一个或多个日期仍处于上市生命周期内的股票列表。",
    params: [
      ["trade_date", "string/list", "否", "目标日期或日期列表，YYYYMMDD 或 YYYY-MM-DD"],
      ["start_date", "string", "否", "连续日期范围的开始日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["end_date", "string", "否", "连续日期范围的结束日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["exchange", "string/list", "否", "交易所筛选：SSE、SZSE、BSE；不传默认全部"]
    ],
    fields: [
      ["trade_date", "date/string", "本行对应的目标日期，格式 YYYYMMDD"],
      ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ、600000.SH、430047.BJ"],
      ["symbol", "string", "交易所原始证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["market", "string", "市场板块，例如主板、创业板、科创板、北交所"],
      ["list_date", "date/string", "上市日期，格式 YYYYMMDD"],
      ["delist_date", "date/string", "退市日期；未退市为空"],
      ["listing_status", "string", "上市状态：listed 或 delisted"]
    ]
  },
  {
    id: "stock_basic_info_exchange",
    interfaceName: "stock_basic_info_exchange",
    title: "股票基础信息",
    group: "基础数据",
    cadence: "现用现查",
    key: "instrument_id",
    summary: "返回交易所官方当前股票基础资料；不传参数默认全部支持交易所。",
    params: [
      ["exchange", "string/list", "否", "交易所筛选：SSE、SZSE、BSE；不传默认全部"],
      ["code", "string/list", "否", "股票代码筛选，例如 000001、000001.SZ、sz000001；支持列表或逗号分隔"],
      ["name", "string/list", "否", "证券简称筛选，精确匹配；支持列表或逗号分隔"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码，例如 000001.SZ、600000.SH、430047.BJ"],
      ["symbol", "string", "证券代码，不带交易所后缀，例如 000001"],
      ["exchange", "string", "交易所代码，建议值为 SSE、SZSE、BSE"],
      ["asset_type", "string", "资产类型，本接口固定为 stock"],
      ["name", "string", "证券简称"],
      ["security_full_name", "string", "证券全称；上交所通常提供，其他交易所可能为空"],
      ["market_code", "string", "市场板块代码；上交所、北交所可能提供，没有时为空"],
      ["market", "string", "市场板块名称，例如主板、创业板、科创板、北交所"],
      ["industry_code", "string", "行业代码；上交所通常提供，其他交易所可能为空"],
      ["industry", "string", "行业名称；各交易所口径不同，源端提供时返回"],
      ["region_code", "string", "地区代码；上交所通常提供，其他交易所可能为空"],
      ["region", "string", "地区名称；上交所、北交所可能提供，没有时为空"],
      ["company_code", "string", "公司代码；上交所通常提供，其他交易所可能为空"],
      ["company_short_name", "string", "公司简称；上交所通常提供，其他交易所可能为空"],
      ["company_full_name", "string", "公司法定全称；上交所通常提供，其他交易所可能为空"],
      ["company_short_name_en", "string", "公司英文简称；上交所、北交所可能提供，没有时为空"],
      ["company_full_name_en", "string", "公司英文全称；上交所通常提供，其他交易所可能为空"],
      ["listing_status", "string", "上市状态，建议值 listed、delisted、suspended、unknown"],
      ["list_date", "date/string", "上市日期，格式 YYYYMMDD"],
      ["delist_date", "date/string", "退市日期，未退市为空"],
      ["total_share", "float64", "总股本，单位：亿股；深交所、北交所通常提供，上交所当前列表可能为空"],
      ["float_share", "float64", "流通股本，单位：亿股；深交所、北交所通常提供，上交所当前列表可能为空"],
      ["is_profit", "string", "是否尚未盈利；深交所可能提供，没有时为空"],
      ["is_vie", "string", "是否具有协议控制架构；深交所可能提供，没有时为空"],
      ["has_weighted_voting_rights", "string", "是否具有表决权差异安排；深交所可能提供，没有时为空"],
      ["sponsor", "string", "保荐机构或主办券商；北交所通常提供，其他交易所可能为空"],
      ["share_report_date", "date/string", "股本数据报告日期，格式 YYYYMMDD；北交所通常提供，其他交易所可能为空"]
    ]
  }
];

export const exchangeCatalogItems: CatalogItem[] = [
  {
    id: "stock_trade_calendar_exchange",
    group: "交易所",
    title: "交易日历",
    name: "stock_trade_calendar_exchange",
    method: "POST",
    path: "/v1/request/stock_trade_calendar_exchange",
    status: "ready",
    icon: CalendarDays,
    cadence: "现用现查",
    key: "cal_date",
    limit: "按日期范围返回；不传日期时默认当前自然年",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "从深交所官方交易日历返回指定日期范围内的开闭市信息。",
    description: "不传日期时默认返回当前自然年；传 year 返回全年；传 start_date/end_date 返回指定范围。",
    overview: [
      ["接口名称", "stock_trade_calendar_exchange"],
      ["接口功能", "获取交易日历"]
    ],
    paramsNote: "日期优先级：start_date/end_date > year > 当前自然年。",
    paramsExample: `# 指定日期范围
client.call(
    "stock_trade_calendar_exchange",
    start_date="20260617",
    end_date="20260622",
)

# 指定年份
client.call("stock_trade_calendar_exchange", year=2026)

# 不传日期，默认当前自然年
client.call("stock_trade_calendar_exchange")`,
    params: exchangeSourceContracts[0].params,
    fieldColumns: ["字段", "类型", "说明"],
    fields: exchangeSourceContracts[0].fields,
    dataExamples: [
      {
        id: "trade-calendar-example",
        title: "返回示例",
        icon: CalendarDays,
        columns: ["cal_date", "is_open", "pretrade_date", "next_trade_date"],
        rows: [
          ["20260617", "true", "20260616", "20260618"],
          ["20260618", "true", "20260617", "20260622"],
          ["20260619", "false", "20260618", "20260622"],
          ["20260622", "true", "20260618", "20260623"]
        ]
      }
    ],
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "stock_trade_calendar_exchange",
    start_date="20260617",
    end_date="20260622",
)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call(
    "stock_trade_calendar_exchange",
    start_date="20260617",
    end_date="20260622",
)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_trade_calendar_exchange" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"start_date":"20260617","end_date":"20260622"},"persist":false}'`
  },
  {
    id: "stock_basic_info_exchange",
    group: "交易所",
    title: "股票基础信息",
    name: "stock_basic_info_exchange",
    method: "POST",
    path: "/v1/request/stock_basic_info_exchange",
    status: "ready",
    icon: Info,
    cadence: "现用现查",
    key: "instrument_id",
    limit: "不传参数默认返回全部支持交易所的当前股票基础资料",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "返回交易所官方当前股票基础资料；不传参数默认全部支持交易所。",
    description: "用于查看交易所官方当前股票基础资料，例如名称、板块、行业、地区、上市日期和股本信息；这是当前列表口径，不表示历史某天状态。",
    overview: [
      ["接口名称", "stock_basic_info_exchange"],
      ["接口功能", "获取股票基础信息"]
    ],
    paramsNote: "这是当前官方股票基础资料接口；不传参数默认返回全部支持交易所。不同交易所公开字段不完全一致，源端未提供的字段返回空值。",
    paramsExample: `# 查询单只股票
client.call("stock_basic_info_exchange", code="000001.SZ")

# 按交易所查询
client.call("stock_basic_info_exchange", exchange="SZSE")

# 批量查询
client.call(
    "stock_basic_info_exchange",
    code=["000001.SZ", "600000.SH"],
)`,
    params: exchangeSourceContracts[2].params,
    fieldColumns: ["字段", "类型", "说明"],
    fields: exchangeSourceContracts[2].fields,
    dataExamples: [
      {
        id: "stock-basic-info-example",
        title: "返回示例",
        icon: Info,
        columns: ["instrument_id", "symbol", "exchange", "name", "market", "industry", "list_date", "total_share", "float_share", "listing_status"],
        rows: [
          ["000001.SZ", "000001", "SZSE", "平安银行", "主板", "J 金融业", "19910403", "194.05918198", "194.05685028", "listed"],
          ["600000.SH", "600000", "SSE", "浦发银行", "主板", "金融业", "19991110", "", "", "listed"]
        ]
      }
    ],
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call("stock_basic_info_exchange", code="000001.SZ")
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("stock_basic_info_exchange", code="000001.SZ")
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_basic_info_exchange" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"code":"000001.SZ"},"persist":false}'`
  },
  {
    id: "stock_historical_list_exchange",
    group: "交易所",
    title: "历史股票列表",
    name: "stock_historical_list_exchange",
    method: "POST",
    path: "/v1/request/stock_historical_list_exchange",
    status: "ready",
    icon: ListChecks,
    cadence: "现用现查",
    key: "trade_date + instrument_id",
    limit: "按交易所官方列表返回指定日期的股票池",
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: "按交易所官方上市日期和退市日期计算一个或多个日期仍处于上市生命周期内的股票列表。",
    description: "传 trade_date 返回单日或多个指定日期的股票池；传 start_date/end_date 返回连续日期范围；可用 exchange 限定 SSE、SZSE 或 BSE。",
    overview: [
      ["接口名称", "stock_historical_list_exchange"],
      ["接口功能", "获取历史股票列表"]
    ],
    paramsNote: "判断规则：上市日期不晚于目标日期，且未退市或退市日期不早于目标日期；trade_date 和 start_date/end_date 二选一。",
    paramsExample: `# 指定日期和交易所
client.call(
    "stock_historical_list_exchange",
    trade_date="20240102",
    exchange="SZSE",
)

# 批量指定多个日期
client.call(
    "stock_historical_list_exchange",
    trade_date=["20240102", "20240103"],
    exchange="SZSE",
)

# 指定连续日期范围
client.call(
    "stock_historical_list_exchange",
    start_date="20240102",
    end_date="20240105",
)`,
    params: exchangeSourceContracts[1].params,
    fieldColumns: ["字段", "类型", "说明"],
    fields: exchangeSourceContracts[1].fields,
    dataExamples: [
      {
        id: "historical-stock-list-example",
        title: "返回示例",
        icon: ListChecks,
        columns: ["trade_date", "instrument_id", "symbol", "exchange", "name", "market", "list_date", "delist_date", "listing_status"],
        rows: [
          ["20240102", "000001.SZ", "000001", "SZSE", "平安银行", "主板", "19910403", "", "listed"],
          ["20240102", "000005.SZ", "000005", "SZSE", "ST星源", "", "19901210", "20240426", "delisted"]
        ]
      }
    ],
    sdk: `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "stock_historical_list_exchange",
    trade_date="20240102",
    exchange="SZSE",
)
print(df)`,
    remoteSdk: `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call(
    "stock_historical_list_exchange",
    trade_date="20240102",
    exchange="SZSE",
)
print(df)`,
    curl: `curl -X POST "http://127.0.0.1:8666/v1/request/stock_historical_list_exchange" \\
  -H "Content-Type: application/json" \\
  -d '{"params":{"trade_date":"20240102","exchange":"SZSE"},"persist":false}'`
  }
];

export const exchangeNavGroup: CatalogGroup = {
  title: "交易所",
  keepWhenEmpty: true,
  items: ["stock_trade_calendar_exchange", "stock_historical_list_exchange", "stock_basic_info_exchange"]
};
