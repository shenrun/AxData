import { BarChart3, BookOpenText, FileSearch, Landmark, Newspaper, ReceiptText } from "lucide-react";
import type { CatalogGroup, CatalogItem, SourceContractSpec } from "../../types";

export const externalSourceContracts: SourceContractSpec[] = [
  {
    id: "cninfo_announcements",
    interfaceName: "cninfo_announcements",
    title: "公告列表",
    group: "公告数据",
    cadence: "现用现查",
    key: "announcement_id",
    summary: "按股票和日期范围临时获取巨潮公告元信息。",
    params: [
      ["code", "string/list", "是", "股票代码：支持 000001、000001.SZ、sh600000 或列表"],
      ["start_date", "string", "否", "开始日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["end_date", "string", "否", "结束日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["page", "integer", "否", "页码，默认 1"],
      ["limit", "integer", "否", "每页条数，默认 30，最大 100"]
    ],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "六位证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["announcement_id", "string", "公告 ID"],
      ["title", "string", "公告标题"],
      ["publish_date", "date/string", "公告发布日期，格式 YYYYMMDD"],
      ["file_type", "string", "附件类型，例如 PDF"],
      ["file_size_kb", "float64", "附件大小，单位：KB"],
      ["download_url", "string", "PDF 下载地址"]
    ]
  },
  {
    id: "cninfo_announcement_detail",
    interfaceName: "cninfo_announcement_detail",
    title: "公告PDF元信息",
    group: "公告数据",
    cadence: "现用现查",
    key: "announcement_id",
    summary: "确认巨潮公告 PDF 的文件类型、大小和下载地址；不解析正文。",
    params: [
      ["announcement_id", "string", "否", "公告 ID"],
      ["url", "string", "是", "公告 PDF 路径或完整 URL"],
      ["title", "string", "否", "可选公告标题，用于透传"]
    ],
    fields: [
      ["announcement_id", "string", "公告 ID"],
      ["title", "string", "公告标题；传入时返回"],
      ["content_type", "string", "文件类型，例如 application/pdf"],
      ["file_size_bytes", "integer", "文件大小，单位：字节"],
      ["download_url", "string", "PDF 下载地址"]
    ]
  },
  {
    id: "tencent_realtime_snapshot",
    interfaceName: "tencent_realtime_snapshot",
    title: "实时快照",
    group: "行情数据",
    cadence: "现用现查",
    key: "instrument_id",
    summary: "临时获取腾讯财经快照，覆盖 A 股、指数和 ETF 的确认字段。",
    params: [["code", "string/list", "是", "证券代码：支持 000001.SZ、600000.SH、920000.BJ、000001.SH、510050.SH 或列表"]],
    fields: [
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "六位证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["asset_type", "string", "资产类型：stock、index、etf"],
      ["name", "string", "证券简称"],
      ["quote_time", "datetime/string", "源端行情时间，格式 YYYYMMDDHHMMSS"],
      ["last_price", "float64", "最新价，单位：元或指数点"],
      ["pre_close", "float64", "昨收价，单位：元或指数点"],
      ["open", "float64", "开盘价，单位：元或指数点"],
      ["high", "float64", "最高价，单位：元或指数点"],
      ["low", "float64", "最低价，单位：元或指数点"],
      ["change", "float64", "涨跌额，单位：元或指数点"],
      ["change_pct", "float64", "涨跌幅，百分比数值"],
      ["volume", "float64", "成交量，沿用源端口径"],
      ["amount", "float64", "成交额，单位：元"],
      ["turnover_rate", "float64", "换手率，百分比数值；指数可能为空"],
      ["pe_dynamic", "float64", "动态市盈率；不适用时为空"],
      ["pb", "float64", "市净率；不适用时为空"],
      ["total_market_value", "float64", "总市值，单位：亿元"],
      ["float_market_value", "float64", "流通市值，单位：亿元"],
      ["limit_up_price", "float64", "涨停价；不适用时为空"],
      ["limit_down_price", "float64", "跌停价；不适用时为空"],
      ["currency", "string", "币种"]
    ]
  },
  {
    id: "eastmoney_dragon_tiger_daily",
    interfaceName: "eastmoney_dragon_tiger_daily",
    title: "龙虎榜每日汇总",
    group: "龙虎榜数据",
    cadence: "现用现查",
    key: "trade_date + instrument_id",
    summary: "低频获取东方财富龙虎榜每日汇总，金额单位为元。",
    params: [
      ["trade_date", "string", "是", "交易日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["page", "integer", "否", "页码，默认 1"],
      ["limit", "integer", "否", "每页条数，默认 50，最大 200"]
    ],
    fields: [
      ["trade_date", "date/string", "交易日期，格式 YYYYMMDD"],
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "六位证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["reason", "string", "上榜原因"],
      ["close_price", "float64", "收盘价，单位：元"],
      ["change_pct", "float64", "涨跌幅，百分比数值"],
      ["turnover_rate", "float64", "换手率，百分比数值"],
      ["buy_amount", "float64", "龙虎榜买入额，单位：元"],
      ["sell_amount", "float64", "龙虎榜卖出额，单位：元"],
      ["net_buy_amount", "float64", "龙虎榜净买入额，单位：元"],
      ["total_amount", "float64", "龙虎榜成交额，单位：元"],
      ["market", "string", "交易市场标签"]
    ]
  },
  {
    id: "eastmoney_margin_trading",
    interfaceName: "eastmoney_margin_trading",
    title: "融资融券明细",
    group: "融资融券数据",
    cadence: "现用现查",
    key: "trade_date + instrument_id",
    summary: "低频获取单股融资融券明细，金额单位为元，融券数量单位为股。",
    params: [
      ["code", "string", "是", "股票代码：支持 000001、000001.SZ"],
      ["start_date", "string", "否", "开始日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["end_date", "string", "否", "结束日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["page", "integer", "否", "页码，默认 1"],
      ["limit", "integer", "否", "每页条数，默认 50，最大 200"]
    ],
    fields: [
      ["trade_date", "date/string", "交易日期，格式 YYYYMMDD"],
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "六位证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["market", "string", "交易市场标签"],
      ["close_price", "float64", "收盘价，单位：元"],
      ["change_pct", "float64", "涨跌幅，百分比数值"],
      ["margin_balance", "float64", "融资余额，单位：元"],
      ["margin_buy_amount", "float64", "融资买入额，单位：元"],
      ["margin_repay_amount", "float64", "融资偿还额，单位：元"],
      ["margin_net_buy_amount", "float64", "融资净买入额，单位：元"],
      ["short_balance", "float64", "融券余额，单位：元"],
      ["short_sell_volume", "float64", "融券卖出量，单位：股"],
      ["short_repay_volume", "float64", "融券偿还量，单位：股"],
      ["short_net_sell_volume", "float64", "融券净卖出量，单位：股"],
      ["total_balance", "float64", "融资融券余额，单位：元"],
      ["market_value", "float64", "总市值，单位：元"]
    ]
  },
  {
    id: "eastmoney_research_reports",
    interfaceName: "eastmoney_research_reports",
    title: "个股研报列表",
    group: "研报数据",
    cadence: "现用现查",
    key: "report_id",
    summary: "低频获取个股研报列表元信息；不抓取 PDF 正文。",
    params: [
      ["code", "string", "是", "股票代码：支持 000001、000001.SZ"],
      ["start_date", "string", "否", "开始发布日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["end_date", "string", "否", "结束发布日期，YYYYMMDD 或 YYYY-MM-DD"],
      ["page", "integer", "否", "页码，默认 1"],
      ["limit", "integer", "否", "每页条数，默认 20，最大 100"]
    ],
    fields: [
      ["report_id", "string", "研报 ID"],
      ["instrument_id", "string", "AxData 统一证券代码"],
      ["symbol", "string", "六位证券代码"],
      ["exchange", "string", "交易所代码：SSE、SZSE、BSE"],
      ["name", "string", "证券简称"],
      ["title", "string", "研报标题"],
      ["publish_date", "date/string", "发布日期，格式 YYYYMMDD"],
      ["org_name", "string", "研究机构"],
      ["rating", "string", "评级"],
      ["rating_change", "string", "评级变动源端值"],
      ["researcher", "string", "研究员"],
      ["eps_forecast_this_year", "float64", "本年度 EPS 预测，单位：元/股"],
      ["pe_forecast_this_year", "float64", "本年度 PE 预测，倍"],
      ["file_size_kb", "float64", "附件大小，单位：KB"],
      ["page_count", "integer", "附件页数"]
    ]
  }
];

const examples: Record<string, Array<Record<string, string>>> = {
  cninfo_announcements: [
    {
      instrument_id: "000001.SZ",
      symbol: "000001",
      exchange: "SZSE",
      name: "平安银行",
      announcement_id: "1218968511",
      title: "关联交易公告",
      publish_date: "20240123",
      file_type: "PDF",
      file_size_kb: "156",
      download_url: "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF"
    }
  ],
  cninfo_announcement_detail: [
    {
      announcement_id: "1218968511",
      title: "",
      content_type: "application/pdf",
      file_size_bytes: "158287",
      download_url: "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF"
    }
  ],
  tencent_realtime_snapshot: [
    {
      instrument_id: "000001.SZ",
      symbol: "000001",
      exchange: "SZSE",
      asset_type: "stock",
      name: "平安银行",
      quote_time: "20260622144633",
      last_price: "10.64",
      pre_close: "10.52",
      change_pct: "1.14",
      amount: "1273923383",
      turnover_rate: "0.62",
      currency: "CNY"
    }
  ],
  eastmoney_dragon_tiger_daily: [
    {
      trade_date: "20240102",
      instrument_id: "000595.SZ",
      symbol: "000595",
      exchange: "SZSE",
      name: "*ST宝实",
      reason: "连续三个交易日内，涨幅偏离值累计达到20%的证券",
      close_price: "5.7",
      change_pct: "10.0386",
      buy_amount: "79387344",
      sell_amount: "41045941.7",
      net_buy_amount: "38341402.3"
    }
  ],
  eastmoney_margin_trading: [
    {
      trade_date: "20240105",
      instrument_id: "000001.SZ",
      symbol: "000001",
      exchange: "SZSE",
      name: "平安银行",
      margin_balance: "5105063089",
      margin_buy_amount: "266715372",
      margin_net_buy_amount: "-59044659",
      short_balance: "106309509",
      total_balance: "5211372598"
    }
  ],
  eastmoney_research_reports: [
    {
      report_id: "AP202410221640398395",
      instrument_id: "000001.SZ",
      symbol: "000001",
      exchange: "SZSE",
      name: "平安银行",
      title: "2024年三季报点评：零售业务调优结构，存款成本持续改善",
      publish_date: "20241022",
      org_name: "东兴证券股份有限公司",
      rating: "买入",
      researcher: "林瑾璐,田馨宇"
    }
  ]
};

const icons: Record<string, typeof Newspaper> = {
  cninfo_announcements: Newspaper,
  cninfo_announcement_detail: FileSearch,
  tencent_realtime_snapshot: BarChart3,
  eastmoney_dragon_tiger_daily: Landmark,
  eastmoney_margin_trading: ReceiptText,
  eastmoney_research_reports: BookOpenText
};

export const externalCatalogItems: CatalogItem[] = externalSourceContracts.map((contract) => {
  const rows = examples[contract.id] ?? [];
  const columns = contract.fields.map((field) => field[0]).filter((field) => rows.some((row) => row[field] !== undefined));
  return {
    id: contract.id,
    group: `${sourceGroupTitle(contract.id)}/${contract.group}`,
    title: contract.title,
    name: contract.interfaceName,
    method: "POST",
    path: `/v1/request/${contract.interfaceName}`,
    status: "ready",
    icon: icons[contract.id] ?? FileSearch,
    cadence: contract.cadence,
    key: contract.key,
    limit: externalLimit(contract.id),
    permission: "本机自用可直接请求；开放给局域网时再配置 token",
    summary: contract.summary,
    description: externalDescription(contract.id),
    overview: [
      ["接口名称", contract.interfaceName],
      ["接口功能", contract.title],
    ],
    paramsNote: externalParamsNote(contract.id),
    paramsExample: externalParamsExample(contract.interfaceName),
    params: contract.params,
    fieldColumns: ["字段", "类型", "说明"],
    fields: contract.fields,
    dataExamples: rows.length
      ? [
          {
            id: `${contract.id}-example`,
            title: "真实返回样例",
            icon: icons[contract.id] ?? FileSearch,
            columns,
            rows: rows.map((row) => columns.map((column) => row[column] ?? ""))
          }
        ]
      : undefined,
    sdk: externalSdkExample(contract.interfaceName),
    remoteSdk: externalRemoteSdkExample(contract.interfaceName),
    curl: externalCurlExample(contract.interfaceName)
  };
});

export const cninfoNavGroup: CatalogGroup = {
  title: "巨潮",
  keepWhenEmpty: true,
  items: ["cninfo_announcements", "cninfo_announcement_detail"]
};

export const tencentNavGroup: CatalogGroup = {
  title: "腾讯财经",
  keepWhenEmpty: true,
  items: ["tencent_realtime_snapshot"]
};

export const eastmoneyNavGroup: CatalogGroup = {
  title: "东方财富",
  keepWhenEmpty: true,
  items: ["eastmoney_dragon_tiger_daily", "eastmoney_margin_trading", "eastmoney_research_reports"]
};

export const sinaNavGroup: CatalogGroup = {
  title: "新浪财经",
  keepWhenEmpty: true,
  items: []
};

function sourceGroupTitle(id: string) {
  if (id.startsWith("cninfo_")) return "巨潮";
  if (id.startsWith("tencent_")) return "腾讯财经";
  if (id.startsWith("eastmoney_")) return "东方财富";
  return "新浪财经";
}

function externalLimit(id: string) {
  if (id.startsWith("eastmoney_")) return "低频请求；默认串行，遇到源端空结果返回空表";
  if (id.startsWith("cninfo_")) return "按股票和日期分页返回；详情接口只返回 PDF 元信息";
  return "按传入代码返回；指数和 ETF 的估值字段可能为空";
}

function externalDescription(id: string) {
  if (id === "cninfo_announcement_detail") return "这个接口只确认 PDF 文件类型、大小和下载地址，不解析 PDF 正文。";
  if (id === "tencent_realtime_snapshot") return "这个接口返回源端快照时间；价格单位为元或指数点，比例字段是百分比数值。";
  if (id.startsWith("eastmoney_")) return "这个接口只保留已确认字段；金额字段单位为元，遇到源端空结果返回空表。";
  return "这个接口返回公告元信息和 PDF 下载地址。";
}

function externalParamsNote(id: string) {
  if (id === "cninfo_announcement_detail") return "url 可以传完整 PDF 地址，也可以传巨潮返回的相对路径。";
  return "不传 fields 时返回上方全部字段；临时调用只查一次。";
}

function externalParamsExample(interfaceName: string) {
  return `client.call("${interfaceName}", ${exampleArgs(interfaceName)})`;
}

function externalSdkExample(interfaceName: string) {
  return `import axdata as ax

client = ax.AxDataClient()
df = client.call("${interfaceName}", ${exampleArgs(interfaceName)})
print(df)`;
}

function externalRemoteSdkExample(interfaceName: string) {
  return `import axdata as ax

client = ax.AxDataClient(api_base="http://服务器IP:8666")
df = client.call("${interfaceName}", ${exampleArgs(interfaceName)})
print(df)`;
}

function externalCurlExample(interfaceName: string) {
  return `curl -X POST "http://127.0.0.1:8666/v1/request/${interfaceName}" \\
  -H "Content-Type: application/json" \\
  -d '{"params":${JSON.stringify(exampleParams(interfaceName))},"persist":false}'`;
}

function exampleArgs(interfaceName: string) {
  const params = exampleParams(interfaceName);
  return Object.entries(params)
    .map(([key, value]) => `${key}=${formatPythonValue(value)}`)
    .join(", ");
}

function exampleParams(interfaceName: string): Record<string, unknown> {
  if (interfaceName === "cninfo_announcements") return { code: "000001.SZ", start_date: "20240101", end_date: "20240131", limit: 3 };
  if (interfaceName === "cninfo_announcement_detail") return { announcement_id: "1218968511", url: "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF" };
  if (interfaceName === "tencent_realtime_snapshot") return { code: ["000001.SZ", "600000.SH"] };
  if (interfaceName === "eastmoney_dragon_tiger_daily") return { trade_date: "20240102", limit: 5 };
  if (interfaceName === "eastmoney_margin_trading") return { code: "000001.SZ", start_date: "20240102", end_date: "20240105", limit: 5 };
  if (interfaceName === "eastmoney_research_reports") return { code: "000001.SZ", start_date: "20240101", end_date: "20241231", limit: 5 };
  return { code: "000001.SZ", statement_type: "income", year: 2024, limit: 2 };
}

function formatPythonValue(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(formatPythonValue).join(", ")}]`;
  if (typeof value === "string") return `"${value}"`;
  return String(value);
}
