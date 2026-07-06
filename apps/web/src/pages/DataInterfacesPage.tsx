import { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Code2,
  Database,
  RefreshCw,
  ServerCog,
  SlidersHorizontal,
  Table2
} from "lucide-react";
import type { CatalogItem, ReferenceSection } from "../types";
import { sdkModes } from "../data/catalog";
import { CodeBlock, DataTable } from "../components/common";

export function DataInterfacesPage({ activeDoc }: {
  activeDoc: CatalogItem;
}) {
  const ActiveIcon = activeDoc.icon;
  const isSourceDirect = activeDoc.path.startsWith("/v1/request/");
  const isStream = activeDoc.path.startsWith("/v1/stream/");
  const isRuntimeInterface = isSourceDirect || isStream;
  const isReferenceOnly = activeDoc.path.startsWith("/docs/");
  const summary = interfaceSummary(activeDoc.summary);
  const overviewRows = interfaceOverviewRows(activeDoc, isSourceDirect, isStream);

  return (
    <>
      <section className="doc-hero single">
        <div className="doc-heading">
          {!isRuntimeInterface ? (
            <div className="endpoint-line">
              <span className="section-eyebrow">{isReferenceOnly ? "记录页面" : "SDK 方法"}</span>
              <code>{activeDoc.name}</code>
              {!isReferenceOnly ? (
                <>
                  <span className={`method-badge ${activeDoc.method.toLowerCase()}`}>
                    {activeDoc.method}
                  </span>
                  <code>{activeDoc.path}</code>
                </>
              ) : null}
              <span className={activeDoc.status === "ready" ? "ready-badge" : "ready-badge example"}>
                <CheckCircle2 size={15} />
                {isReferenceOnly ? "记录" : activeDoc.status === "ready" ? "已实现" : "示例"}
              </span>
            </div>
          ) : null}

          <div className="title-row">
            <span className="title-icon">
              <ActiveIcon size={26} />
            </span>
            <h1>{activeDoc.title}</h1>
            {activeDoc.sourceNameZh || activeDoc.sourceCode ? (
              <span className="source-badge" title={activeDoc.sourcePath ?? activeDoc.sourceNameZh ?? activeDoc.sourceCode}>
                {activeDoc.sourceNameZh ?? activeDoc.sourceCode}
              </span>
            ) : null}
          </div>
          {summary ? <p>{summary}</p> : null}

          <dl className="summary-list">
            {overviewRows.map((row) => (
              <div key={row.join(":")}>
                <dt>{row[0]}</dt>
                <dd>{row.slice(1).join(" / ")}</dd>
              </div>
            ))}
            {activeDoc.notice ? (
              <InterfaceNotice notice={activeDoc.notice} />
            ) : null}
          </dl>
        </div>
      </section>

      {!isRuntimeInterface && !isReferenceOnly ? (
        <section className="doc-section">
          <div className="section-title">
            <Code2 size={20} />
            <h2>调用方式</h2>
          </div>
          <SdkModeGrid />
        </section>
      ) : null}

      <section className="doc-section" id="api-reference">
        <div className="section-title">
          <Table2 size={20} />
          <h2>输入参数</h2>
        </div>
        {activeDoc.paramsNote ? <p className="guide-note">{activeDoc.paramsNote}</p> : null}
        <DataTable columns={["名称", "类型", "必填", "描述"]} rows={activeDoc.params} />
        {activeDoc.paramsExample ? (
          <div className="params-example">
            <CodeBlock code={activeDoc.paramsExample} language="py" />
          </div>
        ) : null}
      </section>

      <section className="doc-section" id="data-dictionary">
        <div className="section-title">
          <Database size={20} />
          <h2>返回字段</h2>
        </div>
        <DataTable columns={activeDoc.fieldColumns ?? ["字段", "类型", "说明"]} rows={activeDoc.fields} />
      </section>

      {activeDoc.dataExamples?.map((section) => {
        const SectionIcon = section.icon;
        return (
          <section className="doc-section" id={section.id} key={section.id}>
            <div className="section-title">
              <SectionIcon size={20} />
              <h2>{section.title}</h2>
            </div>
            {section.note ? <p className="guide-note">{section.note}</p> : null}
            <DataTable columns={section.columns} rows={section.rows} />
          </section>
        );
      })}

      {!isReferenceOnly ? (
        <InterfaceCallExamplesSection activeDoc={activeDoc} isSourceDirect={isSourceDirect} isStream={isStream} />
      ) : null}

      {isSourceDirect ? (
        <section className="doc-section">
          <div className="section-title">
            <RefreshCw size={20} />
            <h2>请求预览</h2>
          </div>
          <SourceRequestPreviewPanel
            activeDoc={activeDoc}
          />
        </section>
      ) : null}

      {isStream ? (
        <section className="doc-section">
          <div className="section-title">
            <Activity size={20} />
            <h2>推送样例</h2>
          </div>
          <StaticStreamPreviewPanel />
        </section>
      ) : null}

      {activeDoc.interfaceExamples?.map((section) => {
        const SectionIcon = section.icon;
        return (
          <section className="doc-section" id={section.id} key={section.id}>
            <div className="section-title">
              <SectionIcon size={20} />
              <h2>{section.title}</h2>
            </div>
            {section.note ? <p className="guide-note">{section.note}</p> : null}
            <DataTable columns={section.columns} rows={section.rows} />
          </section>
        );
      })}

      {activeDoc.guides?.map((guide) => {
        const GuideIcon = guide.icon;
        return (
          <section className="doc-section" id={guide.id} key={guide.id}>
            <div className="section-title">
              <GuideIcon size={20} />
              <h2>{guide.title}</h2>
            </div>
            {guide.note ? <p className="guide-note">{guide.note}</p> : null}
            <DataTable columns={guide.columns} rows={guide.rows} />
          </section>
        );
      })}

      {supportsTdxExecutionOptions(activeDoc) ? (
        <TdxAdvancedExecutionOptions activeDoc={activeDoc} />
      ) : null}
    </>
  );
}

export function InterfaceNotice({ notice }: { notice: string }) {
  const separatorIndex = notice.indexOf("：");
  const label = separatorIndex >= 0 ? notice.slice(0, separatorIndex) : "提示";
  const content = separatorIndex >= 0 ? notice.slice(separatorIndex + 1) : notice;
  const rules = content
    .trim()
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [market, ...patterns] = line.split(/\s+/);
      return { market, patterns: patterns.join(" ") };
    });

  return (
    <div>
      <dt>{label}</dt>
      <dd className="interface-rule-list">
      {rules.length > 0 ? (
        <>
          {rules.map((rule) => (
            <span className="interface-rule-item" key={rule.market}>
              <span>{rule.market}</span>
              <code>{rule.patterns}</code>
            </span>
          ))}
        </>
      ) : (
        content.trim()
      )}
      </dd>
    </div>
  );
}

function defaultOverviewRows(activeDoc: CatalogItem, isSourceDirect: boolean) {
  const rows = [
    ["接口名称", activeDoc.name],
    ["频率", activeDoc.cadence],
    ["主键字段", activeDoc.key],
    ["限制", activeDoc.limit],
    ["权限", activeDoc.permission]
  ];
  if (!isSourceDirect) {
    rows.splice(1, 0, ["调用方式", `${activeDoc.method} ${activeDoc.path}`]);
  }
  if (isSourceDirect) {
    rows.push(["调用方式", "临时调用"]);
  }
  return rows;
}

function interfaceSummary(summary: string) {
  return summary
    .replace(/[；;，,]?\s*临时调用默认不保存到本地。?/g, "")
    .replace(/[；;，,]?\s*默认不保存到本地。?/g, "")
    .trim();
}

function interfaceOverviewRows(activeDoc: CatalogItem, isSourceDirect: boolean, isStream: boolean) {
  const rows = (activeDoc.overview ?? defaultOverviewRows(activeDoc, isSourceDirect)).filter((row) => {
    const label = row[0];
    return label !== "相关采集器" && label !== "保存方式" && label !== "调用路径" && label !== "接口类型";
  });
  if (!isSourceDirect && !isStream) {
    return rows;
  }
  const typeLabel = isSourceDirect
    ? "临时请求（HTTP POST，查一次返回一次）"
    : "实时流（本地 SDK stream 或远程 WebSocket，持续推送）";
  return [["接口类型", typeLabel], ["调用路径", activeDoc.path], ...rows];
}

function InterfaceCallExamplesSection({
  activeDoc,
  isSourceDirect,
  isStream
}: {
  activeDoc: CatalogItem;
  isSourceDirect: boolean;
  isStream: boolean;
}) {
  const cliCommand = isSourceDirect ? recommendedCliCommand(activeDoc) : null;
  const remoteSdkCode = remoteSdkExampleFor(activeDoc);
  const httpApiCode = httpApiWithToken(activeDoc.curl);
  const transportTitle = isStream ? "WebSocket" : "HTTP API";

  return (
    <section className="doc-section" id={activeDoc.callModes?.id ?? "call-examples"}>
      <div className="section-title">
        <Code2 size={20} />
        <h2>调用方式</h2>
      </div>
      {activeDoc.callModes ? (
        <>
          {activeDoc.callModes.note ? <p className="guide-note">{activeDoc.callModes.note}</p> : null}
          <DataTable columns={activeDoc.callModes.columns} rows={activeDoc.callModes.rows} />
        </>
      ) : null}
      <div className="code-grid call-examples-grid">
        <div>
          <div className="section-title">
            <Code2 size={20} />
            <h2>本地 SDK 示例</h2>
          </div>
          <CodeBlock code={activeDoc.sdk} language="py" />
        </div>
        {remoteSdkCode ? (
          <div>
            <div className="section-title">
              <ServerCog size={20} />
              <h2>远程 SDK 示例</h2>
            </div>
            <p className="guide-note compact">只有远程服务开启鉴权时才需要 token；本地 SDK 不需要。</p>
            <CodeBlock code={remoteSdkCode} language="py" />
          </div>
        ) : null}
        <div>
          <div className="section-title">
            <Activity size={20} />
            <h2>{transportTitle}</h2>
          </div>
          <p className="guide-note compact">远程 HTTP/API 示例使用服务端地址；token 只属于开启鉴权的 AxData API。</p>
          <CodeBlock code={httpApiCode} language="bash" />
        </div>
        {cliCommand ? (
          <div>
            <div className="section-title">
              <Code2 size={20} />
              <h2>CLI 命令</h2>
            </div>
            <CodeBlock code={cliCommand} language="bash" />
          </div>
        ) : null}
      </div>
    </section>
  );
}

function recommendedCliCommand(activeDoc: CatalogItem) {
  const params = JSON.stringify(sampleParamsFromCurl(activeDoc.curl) ?? sampleParamsForInterface(activeDoc));
  return `axdata request ${activeDoc.name} --params '${params}' --json`;
}

function sampleParamsFromCurl(curl: string): Record<string, unknown> | null {
  const dataMatch = curl.match(/-d\s+['"](.+?)['"]/s);
  if (!dataMatch) {
    return null;
  }
  try {
    const body = JSON.parse(dataMatch[1]);
    return isPlainObject(body) && isPlainObject(body.params) && Object.keys(body.params).length > 0
      ? body.params
      : null;
  } catch {
    return null;
  }
}

function remoteSdkExampleFor(activeDoc: CatalogItem) {
  if (activeDoc.remoteSdk) {
    return remoteSdkWithToken(activeDoc.remoteSdk);
  }
  if (!activeDoc.sdk.includes("AxDataClient()")) {
    return null;
  }
  return remoteSdkWithToken(
    activeDoc.sdk.replace(
      "AxDataClient()",
      'AxDataClient(api_base="http://服务器IP:8666")'
    )
  );
}

function remoteSdkWithToken(code: string) {
  return code.replace(/AxDataClient\(([^)]*api_base=[^)]*)\)/g, (match, args: string) => {
    if (args.includes("token=")) {
      return match;
    }
    return `AxDataClient(${args}, token="axd_...")`;
  });
}

function httpApiWithToken(code: string) {
  const remoteCode = code
    .replace(/http:\/\/127\.0\.0\.1:8666/g, "http://服务器IP:8666")
    .replace(/ws:\/\/127\.0\.0\.1:8666/g, "ws://服务器IP:8666");
  if (!remoteCode.includes("curl ") || remoteCode.includes("Authorization: Bearer")) {
    return withWebSocketToken(remoteCode);
  }
  const withHeader = remoteCode.replace(
    /(\n\s*)-H "Content-Type:/,
    '$1-H "Authorization: Bearer axd_..." \\\n$1-H "Content-Type:'
  );
  return withWebSocketToken(withHeader);
}

function withWebSocketToken(code: string) {
  if (!code.includes("ws://") || code.includes("token=")) {
    return code;
  }
  return code.replace(/(ws:\/\/服务器IP:8666\/[^\s`"']+)/, "$1?token=axd_...");
}

function sampleParamsForInterface(activeDoc: CatalogItem): Record<string, unknown> {
  if (activeDoc.requestExampleParams && Object.keys(activeDoc.requestExampleParams).length > 0) {
    return activeDoc.requestExampleParams;
  }
  const examples: Record<string, Record<string, unknown>> = {
    stock_realtime_snapshot_tdx: { code: "000001.SZ" },
    stock_realtime_rank_tdx: { category: "a_share", count: 3 },
    stock_order_book_tdx: { code: "000001.SZ" },
    index_realtime_snapshot_tdx: { code: "000001.SH" },
    index_realtime_rank_tdx: { sort: "change_pct", count: 5 },
    index_kline_tdx: { code: "000001.SH", period: "day", count: 20 },
    etf_realtime_snapshot_tdx: { code: "510050.SH" },
    etf_realtime_rank_tdx: { sort: "change_pct", count: 5 },
    etf_kline_tdx: { code: "510050.SH", period: "day", count: 20 },
    concept_constituents_tdx: { concept_code: "881386", count: 5 },
    stock_intraday_today_tdx: { code: "000001.SZ" },
    stock_intraday_history_tdx: { code: "000001.SZ", trade_date: "20260519" },
    stock_intraday_recent_history_tdx: { code: "000001.SZ", trade_date: "20260519" },
    stock_intraday_buy_sell_strength_tdx: { code: "000001.SZ" },
    stock_intraday_volume_comparison_tdx: { code: "000001.SZ" },
    stock_trades_today_tdx: { code: "000001.SZ" },
    stock_trades_history_tdx: { code: "000001.SZ", trade_date: "20260511" },
    stock_auction_process_tdx: { code: "000988.SZ" },
    stock_auction_result_tdx: { code: "000001.SZ" },
    stock_auction_result_history_tdx: { code: "000001.SZ", trade_date: "20260511" },
    stock_finance_summary_tdx: { code: "000001.SZ" },
    stock_finance_profile_tdx: { code: "000001.SZ" },
    index_intraday_today_tdx: { code: "000001.SH" },
    index_intraday_history_tdx: { code: "000001.SH", trade_date: "20260617" },
    etf_intraday_today_tdx: { code: "510050.SH" },
    etf_trades_today_tdx: { code: "510050.SH" },
    cninfo_announcements: { code: "000001.SZ", limit: 5 },
    cninfo_announcement_detail: { url: "https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF" },
    eastmoney_market_index_realtime: { scope: "default", limit: 6 },
    eastmoney_stock_realtime_snapshot: { code: "000001.SZ" },
    eastmoney_sector_realtime: { sector_type: "industry", limit: 5 },
    eastmoney_sector_constituents: { sector_code: "BK1033", limit: 5 },
    eastmoney_stock_sector_belong: { code: "000001.SZ" },
    eastmoney_limit_up_pool: { trade_date: "20260514" },
    eastmoney_limit_down_pool: { trade_date: "20260514" },
    eastmoney_yesterday_limit_up_pool: { trade_date: "20260514" },
    eastmoney_stock_changes: { change_type: "8201" },
    eastmoney_stock_change_detail: { code: "000001.SZ", trade_date: "20260514" },
    eastmoney_dragon_tiger_daily: { trade_date: "20260511", limit: 5 },
    eastmoney_margin_trading: { code: "000001.SZ", limit: 5 },
    eastmoney_research_reports: { code: "000001.SZ", limit: 5 },
    cls_market_wind_stocks: { plate_code: "cls80198" },
    cls_sector_popular_stocks: { plate_code: "cls80025" },
    cls_sector_rotation: { days: 4 },
    cls_stock_timeline: { code: "002664.SZ" },
    cls_stock_kline: { code: "002664.SZ", limit: 5 },
    cls_news_telegraph: { category: "important", limit: 5 },
    kph_market_emotion: { trade_date: "20260513" },
    kph_sector_ranking: { trade_date: "20260513", sector_type: "selected" },
    kph_sector_constituents_history: { plate_id: "801001", trade_date: "20260513" },
    kph_limit_up_history: { trade_date: "20260513" },
    kph_limit_down_history: { trade_date: "20260513" },
    kph_wind_vane_history: { trade_date: "20260513" },
    kph_limit_ladder: { trade_date: "20260513" },
    kph_market_review_events: { trade_date: "20260513", limit: 5 },
    kph_limit_resumption_history: { trade_date: "20260513", limit: 5 },
    tencent_realtime_snapshot: { code: "000001.SZ" },
    stock_trade_calendar_exchange: { start_date: "20260617", end_date: "20260622" },
    stock_historical_list_exchange: { trade_date: "20240102", exchange: "SZSE" },
    stock_basic_info_exchange: { code: ["000001.SZ", "600000.SH"] }
  };
  if (examples[activeDoc.name]) {
    return examples[activeDoc.name];
  }
  const params: Record<string, unknown> = {};
  for (const row of activeDoc.params) {
    if (row[2] !== "是") {
      continue;
    }
    params[row[0]] = sampleValueForParam(row[0], activeDoc);
  }
  return params;
}

function sampleValueForParam(paramName: string, activeDoc: CatalogItem): unknown {
  if (paramName === "code") {
    if (activeDoc.assetClass === "index") return "000001.SH";
    if (activeDoc.assetClass === "etf") return "510050.SH";
    return "000001.SZ";
  }
  if (paramName.includes("date")) return "20260511";
  if (paramName.includes("count") || paramName.includes("limit")) return 5;
  if (paramName.includes("concept")) return "881386";
  if (paramName.includes("exchange")) return "SSE";
  return "demo";
}

function SourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  return <StaticSourceRequestPreviewPanel activeDoc={activeDoc} />;
}

function StaticSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const pluginExample = pluginResponseExample(activeDoc);
  const hasPluginExample = Boolean(pluginExample);
  const rows = catalogPreviewRows(pluginExample);
  const params = sampleParamsFromCurl(activeDoc.curl) ?? sampleParamsForInterface(activeDoc);
  const sdkCode = buildLivePreviewSdkCode(activeDoc.name, params);
  const resultColumns = staticPreviewColumns(activeDoc, rows);
  const hasRows = rows.length > 0;

  return (
    <div className="source-preview-panel">
      <div className={`source-preview-status ${hasPluginExample ? "example" : "unconfigured"}`}>
        <Code2 size={17} />
        <span>{sourcePreviewStatusText(rows.length, hasPluginExample)}</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">真实样例快照</div>
          {hasRows ? (
            <DataTable
              columns={resultColumns}
              rows={rows.map((row) => resultColumns.map((column) => formatPreviewCell(row[column])))}
            />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>{sourcePreviewEmptyText(hasPluginExample)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StaticStreamPreviewPanel() {
  const rows = QUOTE_STREAM_SNAPSHOT_MESSAGE.data;
  const columns = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这是 2026-07-04 17:12 非交易时段实测抓到的静态样例；页面打开不会连接 WebSocket。这里不传 fields，所以 data 行展示默认行情字段；如调用方传入 fields，才会只返回指定列。</span>
      </div>
      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">订阅消息</div>
          <CodeBlock code={JSON.stringify(QUOTE_STREAM_SUBSCRIBE_MESSAGE, null, 2)} language="json" />
        </div>
        <div>
          <div className="source-preview-label">订阅确认</div>
          <CodeBlock code={JSON.stringify(QUOTE_STREAM_SUBSCRIBED_MESSAGE, null, 2)} language="json" />
        </div>
        <div>
          <div className="source-preview-label">初始快照</div>
          <CodeBlock code={JSON.stringify(QUOTE_STREAM_SNAPSHOT_MESSAGE, null, 2)} language="json" />
        </div>
        <div>
          <div className="source-preview-label">增量更新为空</div>
          <CodeBlock code={JSON.stringify(QUOTE_STREAM_EMPTY_UPDATE_MESSAGE, null, 2)} language="json" />
        </div>
      </div>
      <div className="source-preview-label">初始快照里的 data 行，默认字段</div>
      <DataTable
        columns={columns}
        rows={rows.map((row) => columns.map((column) => formatPreviewCell(row[column])))}
      />
    </div>
  );
}

function TradeCalendarSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    start_date="20260617",
    end_date="20260622",
)
print(df)`;
  const rows = PREVIEW_TRADE_CALENDAR_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求深交所官方交易日历，返回指定日期范围内的开闭市信息。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function HistoricalStockListSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    trade_date="20240102",
    exchange="SZSE",
)
print(df)`;
  const rows = PREVIEW_HISTORICAL_STOCK_LIST_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求交易所官方股票生命周期数据，返回一个或多个日期仍处于上市生命周期内的股票列表。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function StockBasicInfoSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code=["000001.SZ", "600000.SH"],
)
print(df)`;
  const rows = PREVIEW_STOCK_BASIC_INFO_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求交易所官方当前股票基础资料。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function ExternalSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = activeDoc.dataExamples?.[0];
  const exampleRows = example?.rows ?? [];
  const resultColumns = example?.columns ?? [];
  const sdkCode = activeDoc.sdk;

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里展示已实测的真实样例；实际调用会请求对应源端，并按上方返回字段输出。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          {exampleRows.length > 0 ? (
            <DataTable columns={resultColumns} rows={exampleRows} />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>这个接口暂未放置样例。</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function IndexSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = activeDoc.dataExamples?.[0];
  const exampleRows = example?.rows ?? [];
  const hasExample = exampleRows.length > 0;
  const resultColumns = example?.columns ?? [];
  const sdkCode = activeDoc.sdk;

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求通达信指数数据，并按上方返回字段输出。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          {hasExample ? (
            <DataTable columns={resultColumns} rows={exampleRows} />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>暂未放置真实返回样例；实际调用会请求源端并按上方返回字段输出。</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EtfSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = activeDoc.dataExamples?.[0];
  const exampleRows = example?.rows ?? [];
  const hasExample = exampleRows.length > 0;
  const resultColumns = example?.columns ?? [];
  const sdkCode = activeDoc.sdk;

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求通达信 ETF 数据，并按上方返回字段输出。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          {hasExample ? (
            <DataTable columns={resultColumns} rows={exampleRows} />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>暂未放置真实返回样例；实际调用会请求源端并按上方返回字段输出。</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StockSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const [filter, setFilter] = useState<PreviewFilter>("scope");
  const [mode, setMode] = useState<PreviewMode>("single");
  const previewConfig = buildPreviewConfig(activeDoc.id, filter, mode);
  const sdkCode = buildPreviewSdkCode(activeDoc.name, previewConfig.sdkArgs);
  const resultRows = previewExampleRows(activeDoc.id, filter, previewConfig.value);
  const resultColumns = previewColumns(activeDoc, resultRows);

  useEffect(() => {
    setFilter("scope");
    setMode("single");
  }, [activeDoc.id]);

  return (
    <div className="source-preview-panel">
      <div className="preview-controls">
        <div>
          <div className="source-preview-label">筛选字段</div>
          <div className="segmented-control">
            {PREVIEW_FILTERS.map((option) => (
              <button
                className={filter === option.value ? "active" : ""}
                key={option.value}
                onClick={() => {
                  setFilter(option.value);
                  setMode("single");
                }}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="source-preview-label">查询方式</div>
          <div className="segmented-control">
            {PREVIEW_MODES.map((option) => (
              <button
                className={mode === option.value ? "active" : ""}
                key={option.value}
                onClick={() => setMode(option.value)}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用时会按参数返回最新数据。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable columns={resultColumns} rows={resultRows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))} />
        </div>
      </div>
    </div>
  );
}

function F10SourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = activeDoc.dataExamples?.[0];
  const exampleRows = example?.rows ?? [];
  const hasExample = exampleRows.length > 0;
  const resultColumns = example?.columns ?? [];
  const sdkCode = activeDoc.sdk;
  const previewNote = activeDoc.paramsNote
    ? `这里只是示例预览，不发起真实请求；实际调用${activeDoc.paramsNote}`
    : "这里只是示例预览，不发起真实请求；实际调用会请求当前资料接口，并按上方返回字段输出。";

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>{previewNote}</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          {hasExample ? (
            <DataTable columns={resultColumns} rows={exampleRows} />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>暂未放置真实返回样例；实际调用会请求源端并按上方返回字段输出。</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function OrderBookSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
)
print(df)`;
  const rows = PREVIEW_ORDER_BOOK_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求当前五档盘口，返回买一到买五、卖一到卖五的价格和量。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function DailyShareSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
)
print(df)`;
  const rows = PREVIEW_DAILY_SHARE_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用默认返回全量股票，会请求财务快照并读取盘前统计资源，返回每日股本字段。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function DailyPriceLimitSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
)
print(df)`;
  const rows = PREVIEW_DAILY_PRICE_LIMIT_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用不传日期时默认返回全量股票，会请求快照昨收并按交易日历计算涨停价、跌停价。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function RealtimeSnapshotSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code=["000001.SZ", "600000.SH"],
)
print(df)`;
  const rows = PREVIEW_REALTIME_SNAPSHOT_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求当前行情快照，返回价格、成交量额、内外盘、买一卖一和盘中指标。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function RealtimeRankSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    category="a_share",
    sort="change_pct",
    count=80,
)
print(df)`;
  const rows = PREVIEW_REALTIME_RANK_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用默认返回前 80 条，传 count="all" 时取完整当前榜单。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

const LIMIT_LADDER_PREVIEW_COLUMNS = [
  "trade_date",
  "ladder_level",
  "limit_board_text",
  "instrument_id",
  "name",
  "last_price",
  "change_pct",
  "limit_status",
  "amount",
  "seal_amount",
  "seal_to_amount_ratio",
  "free_float_market_value",
  "primary_theme",
  "secondary_themes",
  "year_limit_up_days",
  "symbol",
  "exchange",
  "pre_close",
  "limit_up_price"
];

const LIMIT_LADDER_PREVIEW_TSV_COLUMNS = [
  "trade_date",
  "ladder_level",
  "limit_board_text",
  "instrument_id",
  "name",
  "last_price",
  "change_pct",
  "limit_status",
  "amount",
  "seal_amount",
  "seal_to_amount_ratio",
  "free_float_market_value",
  "top_theme_summary",
  "year_limit_up_days",
  "symbol",
  "exchange",
  "pre_close",
  "limit_up_price"
];

function LimitLadderSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
)
print(df)`;
  const rows = PREVIEW_LIMIT_LADDER_ROWS;
  const resultColumns = LIMIT_LADDER_PREVIEW_COLUMNS.filter((column) => activeDoc.fields.some((field) => field[0] === column));

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是静态示例预览，不发起真实请求；题材字段按当前过滤规则展示。实际调用会请求当前涨幅榜、统计资源和 F10 题材，返回当前连板天梯。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function TdxExtSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = activeDoc.dataExamples?.[0];
  const exampleRows = example?.rows ?? [];
  const hasExample = exampleRows.length > 0;
  const resultColumns = example?.columns ?? [];

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>以下预览来自本机扩展资产目录或源端请求的真实样例；实际调用会按当前本机环境返回同类字段。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={activeDoc.sdk} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          {hasExample ? (
            <DataTable columns={resultColumns} rows={exampleRows} />
          ) : (
            <div className="source-preview-status unconfigured">
              <Database size={17} />
              <span>暂未放置真实返回样例；实际调用会按上方返回字段输出。</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ThemeStrengthRankSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
)
print(df)`;
  const rows = PREVIEW_THEME_STRENGTH_RANK_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；示例为主板 count=5 的真实返回样例。实际调用会请求当前涨停池并按题材强度返回排行。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function AuctionProcessSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000988.SZ",
)
print(df)`;
  const rows = PREVIEW_AUCTION_PROCESS_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求竞价明细，返回开盘段和收盘段的价格、撮合量、未撮合量和方向原始值。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function AuctionResultSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const isHistory = activeDoc.id === "stock_auction_result_history_tdx";
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",${isHistory ? '\n    trade_date="20260511",' : ""}
)
print(df)`;
  const rows = isHistory ? PREVIEW_AUCTION_RESULT_HISTORY_ROWS : PREVIEW_AUCTION_RESULT_TODAY_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>{isHistory ? "这里只是示例预览，不发起真实请求；实际调用会请求指定交易日成交明细，并筛选 09:25 那笔作为历史竞价结果。" : "这里只是示例预览，不发起真实请求；实际调用会请求当日成交明细，并筛选 09:25 那笔作为竞价结果。"}</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function AuctionIndicatorsSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="002971.SZ",
)
print(df)`;
  const rows = PREVIEW_AUCTION_INDICATOR_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求实时快照、日 K、财务快照，并读取本地统计资源计算短线指标。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function KlineSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const preview = klinePreviewConfig(activeDoc.id);
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
${preview.sdkArgs.map((line) => `    ${line}`).join("\n")}
)
print(df)`;
  const rows = klinePreviewRows(preview.period);
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际使用时通常通过 Python SDK 调用，返回的是所选标的的全量 K 线序列。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function CapitalChangesSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
    category="xdxr",
)
print(df)`;
  const rows = PREVIEW_CAPITAL_CHANGE_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求股本变迁记录，作为复权因子计算的原始依据。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function AdjFactorSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
    adjust="qfq",
)
print(df)`;
  const rows = PREVIEW_ADJ_FACTOR_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求 TDX 股本变迁事件和未复权日 K 后计算每日因子，和 TDX 自带复权 K 可能存在口径误差。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function IntradayHistorySourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
    trade_date="20260519",
)
print(df)`;
  const rows = PREVIEW_INTRADAY_HISTORY_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求指定交易日的历史分时点，返回价格、分钟成交量和昨收价。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function IntradayRecentHistorySourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
    trade_date="20260519",
)
print(df)`;
  const rows = PREVIEW_INTRADAY_RECENT_HISTORY_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求近期历史分时图，返回分时价格、分时均价、分钟成交量、昨收价和开盘价。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function IntradayTodaySourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
)
print(df)`;
  const rows = PREVIEW_INTRADAY_TODAY_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求当前交易日分时点，返回分时价格、分时均价和分钟成交量。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function IntradaySubchartSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const isVolumeComparison = activeDoc.id === "stock_intraday_volume_comparison_tdx";
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",
)
print(df)`;
  const rows = isVolumeComparison ? PREVIEW_INTRADAY_VOLUME_COMPARISON_ROWS : PREVIEW_INTRADAY_BUY_SELL_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>{isVolumeComparison ? "这里只是示例预览，不发起真实请求；示例数值取自一次实测，实际调用会请求当前分时副图成交对比，返回今日成交量、昨日成交量、变动量和变动比例。" : "这里只是示例预览，不发起真实请求；示例数值取自一次实测，实际调用会返回请求时刻 TDX 当前分时副图里的委买和委卖序列。"}</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function TradeDetailsSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const isHistory = activeDoc.id === "stock_trades_history_tdx";
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code="000001.SZ",${isHistory ? '\n    trade_date="20260511",' : ""}
)
print(df)`;
  const rows = isHistory ? PREVIEW_TRADE_HISTORY_ROWS : PREVIEW_TRADE_TODAY_ROWS;
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>{isHistory ? "这里只是示例预览，不发起真实请求；实际调用会请求指定交易日成交明细，返回成交价、成交量、成交笔数和方向。" : "这里只是示例预览，不发起真实请求；实际调用会请求当前交易日成交明细，返回成交价、成交量、成交笔数和方向。"}</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

function FinanceSourceRequestPreviewPanel({ activeDoc }: { activeDoc: CatalogItem }) {
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
    code=["000001.SZ", "600000.SH", "300750.SZ"],
)
print(df)`;
  const rows = financePreviewRows(activeDoc.id);
  const resultColumns = previewColumns(activeDoc, rows);

  return (
    <div className="source-preview-panel">
      <div className="source-preview-status example">
        <Code2 size={17} />
        <span>这里只是示例预览，不发起真实请求；实际调用会请求 TDX 财务信息快照，返回当前接口对应的财务字段。</span>
      </div>

      <div className="source-preview-grid">
        <div>
          <div className="source-preview-label">SDK 调用</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        <div>
          <div className="source-preview-label">返回结果示例</div>
          <DataTable
            columns={resultColumns}
            rows={rows.map((row) => resultColumns.map((column) => String(row[column] ?? "")))}
          />
        </div>
      </div>
    </div>
  );
}

type PreviewFilter = "name" | "code" | "scope";
type PreviewMode = "single" | "batch";

const PREVIEW_FILTERS: Array<{ label: string; value: PreviewFilter }> = [
  { label: "name", value: "name" },
  { label: "code", value: "code" },
  { label: "scope", value: "scope" }
];

const PREVIEW_MODES: Array<{ label: string; value: PreviewMode }> = [
  { label: "单个", value: "single" },
  { label: "批量", value: "batch" }
];

function buildPreviewConfig(interfaceId: string, filter: PreviewFilter, mode: PreviewMode) {
  const isSuspensionList = interfaceId === "stock_suspensions_tdx";
  const isStList = interfaceId === "stock_st_list_tdx";
  const values = {
    name: isSuspensionList
      ? mode === "single" ? "*ST国华" : ["*ST国华", "天津港"]
      : isStList
        ? mode === "single" ? "*ST国华" : ["*ST国华", "ST能特", "*ST天龙"]
      : mode === "single" ? "平安银行" : ["浦发银行", "平安银行", "宁德时代", "中芯国际", "九号公司"],
    code: isSuspensionList
      ? mode === "single" ? "000004.SZ" : ["000004.SZ", "600717.SH"]
      : isStList
        ? mode === "single" ? "000004.SZ" : ["000004.SZ", "002102.SZ", "300029.SZ"]
      : mode === "single" ? "000001.SZ" : ["600000.SH", "000001.SZ", "300750.SZ", "688981.SH", "689009.SH"],
    scope: mode === "single" ? "all" : ["main", "star", "chinext", "bse", "cdr"]
  };
  const value = values[filter];
  return {
    value,
    sdkArgs: previewSdkArgs(filter, value)
  };
}

function formatPythonValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  if (Array.isArray(value)) {
    return `[${value.map(formatPythonValue).join(", ")}]`;
  }
  if (value === null || value === undefined) {
    return "None";
  }
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return JSON.stringify(String(value));
}

function previewSdkArgs(filter: PreviewFilter, value: string | string[]) {
  return [`${filter}=${formatPythonValue(value)},`];
}

function buildPreviewSdkCode(interfaceName: string, sdkArgs: string[]) {
  const formattedArgs = sdkArgs.map((arg) => `    ${arg}`).join("\n");
  return `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${interfaceName}",
${formattedArgs}
)
print(df)`;
}

function buildLivePreviewSdkCode(interfaceName: string, params: Record<string, unknown>) {
  const formattedArgs = Object.entries(params)
    .map(([key, value]) => `    ${key}=${formatPythonValue(value)},`)
    .join("\n");
  return `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${interfaceName}"${formattedArgs ? `,\n${formattedArgs}` : ""}
)
print(df)`;
}

function staticPreviewColumns(activeDoc: CatalogItem, rows: Array<Record<string, unknown>>) {
  const declaredFields = activeDoc.fields
    .map((field) => field[0])
    .filter((field): field is string => Boolean(field));
  const extraFields = Array.from(new Set(rows.flatMap((row) => Object.keys(row))))
    .filter((field) => !declaredFields.includes(field));
  return declaredFields.length > 0 ? [...declaredFields, ...extraFields] : extraFields;
}

function pluginResponseExample(activeDoc: CatalogItem): ReferenceSection | undefined {
  return activeDoc.dataExamples?.find((section) => (
    section.id === `${activeDoc.name}-runtime-example` || section.title === "插件真实样例"
  ));
}

function catalogPreviewRows(example: ReferenceSection | undefined): Array<Record<string, unknown>> {
  if (!example || example.columns.length === 0 || example.rows.length === 0) {
    return [];
  }
  return example.rows.map((row) => {
    const record: Record<string, unknown> = {};
    example.columns.forEach((column, index) => {
      record[column] = row[index] ?? "";
    });
    return record;
  });
}

function sourcePreviewStatusText(displayedRows: number, hasPluginExample: boolean) {
  if (!hasPluginExample) {
    return "插件没有提供静态真实样例快照；这里不再用假数据冒充真实返回。";
  }
  if (displayedRows === 0) {
    return "插件提供了静态真实样例快照；生成时源端返回 0 条。页面打开不会再次请求源端。";
  }
  return `插件静态真实样例：展示 ${displayedRows} 条，来自插件接口目录 example.response。页面打开不会再次请求源端。`;
}

function sourcePreviewEmptyText(hasPluginExample: boolean) {
  return hasPluginExample
    ? "插件静态样例生成时源端返回 0 条。"
    : "插件还没有提供静态真实样例。";
}

function formatPreviewCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

const QUOTE_STREAM_SUBSCRIBE_MESSAGE = {
  op: "subscribe",
  id: "doc_sample_full_fields",
  params: {
    code: ["000001.SZ", "600000.SH"],
    interval_ms: 3000,
    initial_snapshot: true
  }
};

const QUOTE_STREAM_SUBSCRIBED_MESSAGE = {
  type: "subscribed",
  stream: "stock_quote_refresh_tdx",
  request_id: "doc_sample_full_fields",
  subscription_id: "sub_bb1bb8c5d455",
  server_time: "2026-07-04T17:12:07+08:00",
  data: {
    code: ["000001.SZ", "600000.SH"],
    fields: null,
    interval_ms: 3000,
    initial_snapshot: true
  }
};

const QUOTE_STREAM_SNAPSHOT_MESSAGE: {
  type: string;
  stream: string;
  request_id: string;
  subscription_id: string;
  server_time: string;
  data: Array<Record<string, unknown>>;
} = {
  type: "snapshot",
  stream: "stock_quote_refresh_tdx",
  request_id: "doc_sample_full_fields",
  subscription_id: "sub_bb1bb8c5d455",
  server_time: "2026-07-04T17:12:09+08:00",
  data: [
    {
      instrument_id: "000001.SZ",
      symbol: "000001",
      tdx_code: "sz000001",
      exchange: "SZSE",
      last_price: 10.29,
      pre_close: 10.28,
      open: 10.29,
      high: 10.4,
      low: 10.18,
      change: 0.01,
      change_pct: 0.097276,
      open_change_pct: 0.097276,
      high_change_pct: 1.167315,
      low_change_pct: -0.972763,
      amplitude_pct: 2.140078,
      average_price: 10.294945,
      average_change_pct: 0.145379,
      drawdown_pct: 1.070039,
      attack_pct: 1.070039,
      volume: 863326,
      current_volume: 7895,
      amount: 888789376.0,
      inside_volume: 442777,
      outside_volume: 420550,
      inside_outside_ratio: 1.052852,
      open_amount: 11215100.0,
      open_amount_ratio_pct: 1.26184,
      bid1_price: 10.29,
      bid1_volume: 1518,
      ask1_price: 10.3,
      ask1_volume: 489,
      locked_amount: 1562022.0,
      bid1_ask1_volume_diff: 1029,
      bid1_ask1_balance_pct: 51.270553,
      rise_speed: 0.0,
      short_turnover: 0.02,
      min2_amount: 8123968.0,
      opening_rush: 0.0,
      vol_rise_speed: 0.84701,
      entrust_ratio: -47.246376,
      activity: 4453
    },
    {
      instrument_id: "600000.SH",
      symbol: "600000",
      tdx_code: "sh600000",
      exchange: "SSE",
      last_price: 8.69,
      pre_close: 8.7,
      open: 8.69,
      high: 8.82,
      low: 8.59,
      change: -0.01,
      change_pct: -0.114943,
      open_change_pct: -0.114943,
      high_change_pct: 1.37931,
      low_change_pct: -1.264368,
      amplitude_pct: 2.643678,
      average_price: 8.693178,
      average_change_pct: -0.078414,
      drawdown_pct: 1.494253,
      attack_pct: 1.149425,
      volume: 695133,
      current_volume: 3884,
      amount: 604291520.0,
      inside_volume: 408109,
      outside_volume: 287024,
      inside_outside_ratio: 1.421864,
      open_amount: 3695900.0,
      open_amount_ratio_pct: 0.611609,
      bid1_price: 8.69,
      bid1_volume: 802,
      ask1_price: 8.7,
      ask1_volume: 5163,
      locked_amount: 696938.0,
      bid1_ask1_volume_diff: -4361,
      bid1_ask1_balance_pct: -73.109807,
      rise_speed: 0.0,
      short_turnover: 0.01,
      min2_amount: 3375168.0,
      opening_rush: -0.1,
      vol_rise_speed: 0.684328,
      entrust_ratio: -36.462738,
      activity: 4149
    }
  ]
};

const QUOTE_STREAM_EMPTY_UPDATE_MESSAGE = {
  type: "update",
  stream: "stock_quote_refresh_tdx",
  subscription_id: "sub_bb1bb8c5d455",
  server_time: "2026-07-04T17:12:15+08:00",
  data: []
};

const PREVIEW_SAMPLE_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    name: "浦发银行",
    market: "主板"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    name: "平安银行",
    market: "主板"
  },
  {
    instrument_id: "300750.SZ",
    symbol: "300750",
    tdx_code: "sz300750",
    exchange: "SZSE",
    name: "宁德时代",
    market: "创业板"
  },
  {
    instrument_id: "688981.SH",
    symbol: "688981",
    tdx_code: "sh688981",
    exchange: "SSE",
    name: "中芯国际",
    market: "科创板"
  },
  {
    instrument_id: "920000.BJ",
    symbol: "920000",
    tdx_code: "bj920000",
    exchange: "BSE",
    name: "安徽凤凰",
    market: "北交所"
  },
  {
    instrument_id: "689009.SH",
    symbol: "689009",
    tdx_code: "sh689009",
    exchange: "SSE",
    name: "九号公司",
    market: "CDR"
  }
];

const PREVIEW_SUSPENSION_SAMPLE_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000004.SZ",
    symbol: "000004",
    tdx_code: "sz000004",
    exchange: "SZSE",
    name: "*ST国华",
    market: "主板"
  },
  {
    instrument_id: "600717.SH",
    symbol: "600717",
    tdx_code: "sh600717",
    exchange: "SSE",
    name: "天津港",
    market: "主板"
  },
  {
    instrument_id: "688121.SH",
    symbol: "688121",
    tdx_code: "sh688121",
    exchange: "SSE",
    name: "卓然股份",
    market: "科创板"
  },
  {
    instrument_id: "300029.SZ",
    symbol: "300029",
    tdx_code: "sz300029",
    exchange: "SZSE",
    name: "*ST天龙",
    market: "创业板"
  }
];

const PREVIEW_ST_SAMPLE_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000004.SZ",
    symbol: "000004",
    tdx_code: "sz000004",
    exchange: "SZSE",
    name: "*ST国华",
    market: "主板",
    st_type: "*ST"
  },
  {
    instrument_id: "002102.SZ",
    symbol: "002102",
    tdx_code: "sz002102",
    exchange: "SZSE",
    name: "ST能特",
    market: "主板",
    st_type: "ST"
  },
  {
    instrument_id: "300029.SZ",
    symbol: "300029",
    tdx_code: "sz300029",
    exchange: "SZSE",
    name: "*ST天龙",
    market: "创业板",
    st_type: "*ST"
  }
];

const PREVIEW_HISTORICAL_STOCK_LIST_ROWS: Array<Record<string, string>> = [
  {
    trade_date: "20240102",
    instrument_id: "000001.SZ",
    symbol: "000001",
    exchange: "SZSE",
    name: "平安银行",
    market: "主板",
    list_date: "19910403",
    delist_date: "",
    listing_status: "listed"
  },
  {
    trade_date: "20240102",
    instrument_id: "000005.SZ",
    symbol: "000005",
    exchange: "SZSE",
    name: "ST星源",
    market: "",
    list_date: "19901210",
    delist_date: "20240426",
    listing_status: "delisted"
  }
];

const PREVIEW_STOCK_BASIC_INFO_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    exchange: "SZSE",
    asset_type: "stock",
    name: "平安银行",
    security_full_name: "",
    market_code: "",
    market: "主板",
    industry_code: "",
    industry: "J 金融业",
    region_code: "",
    region: "",
    company_code: "",
    company_short_name: "",
    company_full_name: "",
    company_short_name_en: "",
    company_full_name_en: "",
    listing_status: "listed",
    list_date: "19910403",
    delist_date: "",
    total_share: "194.05918198",
    float_share: "194.05685028",
    is_profit: "-",
    is_vie: "-",
    has_weighted_voting_rights: "-",
    sponsor: "",
    share_report_date: ""
  },
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    exchange: "SSE",
    asset_type: "stock",
    name: "浦发银行",
    security_full_name: "浦发银行",
    market_code: "1",
    market: "主板",
    industry_code: "J",
    industry: "金融业",
    region_code: "310000",
    region: "上海市",
    company_code: "600000",
    company_short_name: "浦发银行",
    company_full_name: "上海浦东发展银行股份有限公司",
    company_short_name_en: "SPD BANK",
    company_full_name_en: "Shanghai Pudong Development Bank Co.,Ltd.",
    listing_status: "listed",
    list_date: "19991110",
    delist_date: "",
    total_share: "",
    float_share: "",
    is_profit: "",
    is_vie: "",
    has_weighted_voting_rights: "",
    sponsor: "",
    share_report_date: ""
  }
];

const PREVIEW_DAILY_SHARE_ROWS: Array<Record<string, string>> = [
  {
    trade_date: "20260615",
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    total_share: "19405918750",
    float_share: "19405601250",
    free_float_share_z: "8160481200",
    finance_updated_date: "20260425",
    share_source: "finance_snapshot+tdxstat"
  }
];

const PREVIEW_DAILY_PRICE_LIMIT_ROWS: Array<Record<string, string>> = [
  {
    trade_date: "20260622",
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    name: "平安银行",
    name_flag: "",
    pre_close_trade_date: "20260618",
    pre_close: "10.14",
    pre_close_source: "tdx_realtime_snapshot",
    limit_up_price: "11.15",
    limit_down_price: "9.13",
    limit_ratio_pct: "10",
    limit_rule: "main_10pct",
    limit_status: "normal"
  }
];

const PREVIEW_TRADE_CALENDAR_ROWS: Array<Record<string, string>> = [
  {
    cal_date: "20260617",
    is_open: "true",
    pretrade_date: "20260616",
    next_trade_date: "20260618"
  },
  {
    cal_date: "20260618",
    is_open: "true",
    pretrade_date: "20260617",
    next_trade_date: "20260622"
  },
  {
    cal_date: "20260619",
    is_open: "false",
    pretrade_date: "20260618",
    next_trade_date: "20260622"
  },
  {
    cal_date: "20260622",
    is_open: "true",
    pretrade_date: "20260618",
    next_trade_date: "20260623"
  }
];

const PREVIEW_ORDER_BOOK_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    level: "1",
    bid_price: "10.13",
    bid_volume: "320",
    ask_price: "10.14",
    ask_volume: "428"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    level: "2",
    bid_price: "10.12",
    bid_volume: "118",
    ask_price: "10.15",
    ask_volume: "260"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    level: "3",
    bid_price: "10.11",
    bid_volume: "94",
    ask_price: "10.16",
    ask_volume: "136"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    level: "4",
    bid_price: "10.10",
    bid_volume: "87",
    ask_price: "10.17",
    ask_volume: "92"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    level: "5",
    bid_price: "10.09",
    bid_volume: "66",
    ask_price: "10.18",
    ask_volume: "71"
  }
];

const PREVIEW_REALTIME_SNAPSHOT_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    last_price: "10.14",
    pre_close: "10.28",
    open: "10.13",
    high: "10.20",
    low: "10.08",
    change: "-0.14",
    change_pct: "-1.361868",
    open_change_pct: "-1.459144",
    high_change_pct: "-0.778210",
    low_change_pct: "-1.945525",
    amplitude_pct: "1.167315",
    average_price: "10.140000",
    average_change_pct: "-1.361868",
    drawdown_pct: "0.583658",
    attack_pct: "0.583658",
    volume: "1000",
    current_volume: "15",
    amount: "1014000",
    inside_volume: "400",
    outside_volume: "600",
    inside_outside_ratio: "0.666667",
    open_amount: "10000",
    open_amount_ratio_pct: "0.986193",
    bid1_price: "10.13",
    bid1_volume: "320",
    ask1_price: "10.14",
    ask1_volume: "428",
    locked_amount: "324160",
    bid1_ask1_volume_diff: "-108",
    bid1_ask1_balance_pct: "-14.438503",
    rise_speed: "0.21",
    short_turnover: "0.08",
    min2_amount: "320000",
    opening_rush: "0.12",
    vol_rise_speed: "1.25",
    entrust_ratio: "18.5",
    activity: "11"
  },
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    last_price: "8.42",
    pre_close: "8.39",
    open: "8.40",
    high: "8.45",
    low: "8.38",
    change: "0.03",
    change_pct: "0.357568",
    open_change_pct: "0.119190",
    high_change_pct: "0.715137",
    low_change_pct: "-0.119190",
    amplitude_pct: "0.834327",
    average_price: "8.420000",
    average_change_pct: "0.357569",
    drawdown_pct: "0.357569",
    attack_pct: "0.476758",
    volume: "2100",
    current_volume: "22",
    amount: "1768200",
    inside_volume: "920",
    outside_volume: "1180",
    inside_outside_ratio: "0.779661",
    open_amount: "182000",
    open_amount_ratio_pct: "10.292953",
    bid1_price: "8.42",
    bid1_volume: "610",
    ask1_price: "8.43",
    ask1_volume: "430",
    locked_amount: "513620",
    bid1_ask1_volume_diff: "180",
    bid1_ask1_balance_pct: "17.307692",
    rise_speed: "0.05",
    short_turnover: "0.03",
    min2_amount: "510000",
    opening_rush: "0.04",
    vol_rise_speed: "0.92",
    entrust_ratio: "9.6",
    activity: "22"
  }
];

const PREVIEW_REALTIME_RANK_ROWS: Array<Record<string, string>> = PREVIEW_REALTIME_SNAPSHOT_ROWS.map((row, index) => ({
  rank: String(index + 1),
  ...row
}));

const PREVIEW_LIMIT_LADDER_TSV = `
20260617	3	3天3板	000777.SZ	中核科技	21.86	10.015098	sealed	1701761920.0	78418378.0	0.046081	6097663376.0	国企改革（20|3|5） 罗素大盘（10|3|3） 央企改革（10|3|2）	9	000777	SZSE	19.87	21.86
20260617	3	7天4板	002080.SZ	中材科技	82.41	9.99733	sealed	6698619904.0	11685738.0	0.001744	54987990090.0	国企改革（20|3|5） 罗素大盘（10|3|3） 央企改革（10|3|2）	16	002080	SZSE	74.92	82.41
20260617	3	7天4板	600110.SH	诺德股份	17.22	10.031949	sealed	279370304.0	599269776.0	2.145073	20956502364.0	不可减持(新规)（15|3|7） 比亚迪概念（9|3|2） 宁德时代概念（7|3|3）	21	600110	SSE	15.65	17.22
20260617	3	5天4板	600353.SH	旭光电子	38.19	9.99424	sealed	1113021696.0	492463869.0	0.442457	18374698410.0	华为概念（15|3|4） 定向增发（8|3|3） 成渝特区（2|3|1）	13	600353	SSE	34.72	38.19
20260617	3	8天5板	603186.SH	华正新材	226.67	10.001941	sealed	3603072256.0	35383187.0	0.00982	22374663701.0	华为概念（15|3|4） 境外知名投行持股（14|3|2） 定向增发（8|3|3）	14	603186	SSE	206.06	226.67
20260617	3	3天3板	603618.SH	杭电股份	51.73	9.993621	sealed	1575478528.0	96124686.0	0.061013	16915963476.999998	境外知名投行持股（14|3|2） 高盛持股（13|3|1） 光纤概念（4|3|1）	27	603618	SSE	47.03	51.73
20260617	3	3天3板	601636.SH	旗滨集团	8.67	10.025381	sealed	563774080.0	201098049.0	0.3567	16129069770.0	罗素大盘（10|3|3） 医疗器械概念（4|3|1） 平板玻璃（3|3|1）	3	601636	SSE	7.88	8.67
20260617	3	7天5板	603002.SH	宏昌电子	23.2	10.004742	sealed	1801844480.0	47003200.0	0.026086	12334182560.0	比亚迪概念（9|3|2） 覆铜板（3|3|3） AMD概念（2|3|1）	12	603002	SSE	21.09	23.2
20260617	3	7天4板	002741.SZ	光华科技	39.44	10.013947	sealed	806009472.0	191524584.0	0.237621	11584249752.0	宁德时代概念（7|3|3） 富士康概念（4|3|1） 电商概念（2|3|1）	9	002741	SZSE	35.85	39.44
20260617	3	3天3板	603115.SH	海星股份	119.94	9.996332	sealed	531354656.0	27466260.0	0.051691	10301694576.0		24	603115	SSE	109.04	119.94
20260617	2	2天2板	600192.SH	长城电工	8.35	10.013175	sealed	243748928.0	26805170.0	0.10997	2230624845.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 最近闪拉（3|3|2）	15	600192	SSE	7.59	8.35
20260617	2	2天2板	002989.SZ	中天精装	33.97	10.006477	sealed	739530560.0	5747724.0	0.007772	3306520905.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 精装修（2|2|1）	9	002989	SZSE	30.88	33.97
20260617	2	2天2板	600397.SH	江钨装备	18.36	10.005992	sealed	2570234368.0	727056.0	0.000283	11024698968.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 定向增发（8|3|3）	12	600397	SSE	16.69	18.36
20260617	2	2天2板	600186.SH	莲花控股	14.66	9.977494	sealed	2988177408.0	57489190.0	0.019239	21009423386.0	不可减持(新规)（15|3|7） 参股券商（2|2|1） 调味品（1|2|1）	13	600186	SSE	13.33	14.66
20260617	2	2天2板	002141.SZ	贤丰控股	4.28	10.025707	sealed	687193152.0	35181600.0	0.051196	3084355464.0	不可减持(新规)（15|3|7） 广东自贸区（2|2|1） 横琴新区（2|2|1）	11	002141	SZSE	3.89	4.28
20260617	2	2天2板	000679.SZ	大连友谊	7.35	10.02994	sealed	157769152.0	28306320.0	0.179416	1884540000.0	不可减持(新规)（15|3|7） 东亚自贸（2|2|1） 区域性百货（1|2|1）	3	000679	SZSE	6.68	7.35
20260617	2	2天2板	603773.SH	沃格光电	166.13	9.998014	sealed	1950594944.0	280792926.0	0.143952	23081902844.0	华为概念（15|3|4） 3D玻璃（3|2|1） 光电玻璃加工（2|2|1）	24	603773	SSE	151.03	166.13
20260617	2	2天2板	603989.SH	艾华集团	37.73	10.0	sealed	547646656.0	66857560.0	0.122082	5141897222.0	华为概念（15|3|4） 罗素中盘（5|2|1） 电容（2|2|1）	9	603989	SSE	34.3	37.73
20260617	2	2天2板	600615.SH	鑫源智造	11.04	9.960159	sealed	151346560.0	1590864.0	0.010511	1739917248.0		3	600615	SSE	10.04	11.04
20260617	1	1天1板	000725.SZ	京东方Ａ	6.71	10.0	sealed	12134264832.0	1441334169.0	0.118782	205229831609.0	国企改革（20|3|5） 华为概念（15|3|4） 罗素大盘（10|3|3）	4	000725	SZSE	6.1	6.71
20260617	1	1天1板	002916.SZ	深南电路	444.27	10.000495	sealed	5194632704.0	493894959.0	0.095078	105878515254.0	国企改革（20|3|5） 华为概念（15|3|4） 罗素大盘（10|3|3）	12	002916	SZSE	403.88	444.27
20260617	1	7天3板	000811.SZ	冰轮环境	36.52	10.0	sealed	347706336.0	315795744.0	0.908225	22624731624.000004	国企改革（20|3|5） 东亚自贸（2|2|1） 黄河三角（2|1|0）	13	000811	SZSE	33.2	36.52
20260617	1	1天1板	601117.SH	中国化学	8.22	10.040161	sealed	1503337088.0	243469002.0	0.161952	28364388210.000004	国企改革（20|3|5） 不可减持(新规)（15|3|7） 罗素大盘（10|3|3）	2	601117	SSE	7.47	8.22
20260617	1	1天1板	600552.SH	凯盛科技	24.13	9.981768	sealed	1581555456.0	181141497.0	0.114534	16119650768.0	国企改革（20|3|5） 华为概念（15|3|4） 境外知名投行持股（14|3|2）	6	600552	SSE	21.94	24.13
20260617	1	3天2板	600026.SH	中远海能	19.69	10.0	sealed	2028316800.0	99314391.0	0.048964	31620688847.000004	国企改革（20|3|5） 央企改革（10|3|2） 财报高增长（7|1|0）	8	600026	SSE	17.9	19.69
20260617	1	1天1板	600876.SH	凯盛新能	9.42	10.046729	sealed	71922224.0	98053722.0	1.36333	1434427674.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 境外知名投行持股（14|3|2）	5	600876	SSE	8.56	9.42
20260617	1	1天1板	600707.SH	彩虹股份	12.66	9.991312	sealed	2643923968.0	89698632.0	0.033926	16410085698.0	国企改革（20|3|5） 面板（4|1|0） 全息概念（3|1|0）	10	600707	SSE	11.51	12.66
20260617	1	1天1板	000050.SZ	深天马Ａ	9.14	9.987966	sealed	520988416.0	63469988.0	0.121826	12489258858.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 华为概念（15|3|4）	1	000050	SZSE	8.31	9.14
20260617	1	6天3板	600378.SH	昊华科技	63.8	10.0	sealed	6959652864.0	59442460.0	0.008541	30775027360.0	国企改革（20|3|5） 央企改革（10|3|2） 财报高增长（7|1|0）	5	600378	SSE	58.0	63.8
20260617	1	1天1板	603637.SH	镇海股份	18.27	9.99398	sealed	162183392.0	55076742.0	0.339595	3435600420.0	国企改革（20|3|5） 境外知名投行持股（14|3|2） 高盛持股（13|3|1）	5	603637	SSE	16.61	18.27
20260617	1	3天2板	600237.SH	铜峰电子	12.56	9.982487	sealed	912731328.0	51755992.0	0.056705	5940277120.0	国企改革（20|3|5） 宁德时代概念（7|3|3） 柔性直流输电（2|3|1）	8	600237	SSE	11.42	12.56
20260617	1	3天2板	000823.SZ	超声电子	22.11	10.0	sealed	1496065152.0	51472080.0	0.034405	9314268645.0	国企改革（20|3|5） 比亚迪概念（9|3|2） 人民币贬值受益（6|1|0）	6	000823	SZSE	20.1	22.11
20260617	1	9天5板	002254.SZ	泰和新材	18.58	10.005921	sealed	2011525888.0	45725380.0	0.022732	10072630476.0	国企改革（20|3|5） 罗素中盘（5|2|1） 光纤概念（4|3|1）	10	002254	SZSE	16.89	18.58
20260617	1	1天1板	600676.SH	交运股份	7.03	10.015649	sealed	126086048.0	24671082.0	0.195669	3879852079.0	国企改革（20|3|5） 不可减持(新规)（15|3|7） 比亚迪概念（9|3|2）	9	600676	SSE	6.39	7.03
20260617	1	1天1板	002491.SZ	通鼎互联	28.71	10.0	sealed	5178287616.0	142728894.0	0.027563	22248840339.0	不可减持(新规)（15|3|7） 境外知名投行持股（14|3|2） 高盛持股（13|3|1）	22	002491	SZSE	26.1	28.71
20260617	1	1天1板	002579.SZ	中京电子	18.47	10.005956	sealed	1707542272.0	125644022.0	0.073582	7688348058.0	不可减持(新规)（15|3|7） 华为概念（15|3|4） 境外知名投行持股（14|3|2）	15	002579	SZSE	16.79	18.47
20260617	1	3天2板	603261.SH	立航科技	40.7	10.0	sealed	89424928.0	41786690.0	0.467282	1072440930.0	不可减持(新规)（15|3|7） 高盛持股（13|3|1） 最近闪拉（3|3|2）	21	603261	SSE	37.0	40.7
20260617	1	1天1板	000695.SZ	滨海能源	14.47	10.038023	sealed	358874176.0	15080634.0	0.042022	2410835124.0	不可减持(新规)（15|3|7） 境外知名投行持股（14|3|2） 高盛持股（13|3|1）	10	000695	SZSE	13.15	14.47
20260617	1	1天1板	603929.SH	亚翔集成	232.18	10.001421	sealed	2165250816.0	138402498.0	0.06392	19717189960.0	华为概念（15|3|4） 财报高增长（7|1|0） 并购基金（5|3|1）	25	603929	SSE	211.07	232.18
20260617	1	1天1板	000100.SZ	TCL科技	5.12	10.107527	sealed	10656098304.0	103544320.0	0.009717	94925788160.0	华为概念（15|3|4） 罗素大盘（10|3|3） 比亚迪概念（9|3|2）	1	000100	SZSE	4.65	5.12
20260617	1	1天1板	002938.SZ	鹏鼎控股	119.01	10.000924	sealed	7448793088.0	91459185.0	0.012278	75264244695.0	华为概念（15|3|4） 罗素大盘（10|3|3） 人民币贬值受益（6|1|0）	12	002938	SZSE	108.19	119.01
20260617	1	3天2板	002106.SZ	莱宝高科	14.78	9.970238	sealed	604070912.0	88391790.0	0.146327	7476152620.0	华为概念（15|3|4） 央企改革（10|3|2） 定向增发（8|3|3）	3	002106	SZSE	13.44	14.78
20260617	1	1天1板	002906.SZ	华阳集团	28.9	10.01142	sealed	318343168.0	81558690.0	0.256197	6536535530.0	华为概念（15|3|4） 比亚迪概念（9|3|2） 宁德时代概念（7|3|3）	1	002906	SZSE	26.27	28.9
20260617	1	5天2板	603324.SH	盛剑科技	39.18	9.994385	sealed	539087744.0	58773918.0	0.109025	2083188846.0	华为概念（15|3|4） 境外知名投行持股（14|3|2） 宁德时代概念（7|3|3）	6	603324	SSE	35.62	39.18
20260617	1	1天1板	603976.SH	正川股份	27.7	10.007943	sealed	148771184.0	133381040.0	0.896552	1205548320.0	境外知名投行持股（14|3|2） 高盛持股（13|3|1） 医疗器械概念（4|3|1）	4	603976	SSE	25.18	27.7
20260617	1	1天1板	001339.SZ	智微智能	115.39	10.0	sealed	1544304000.0	66556952.0	0.043098	9564988653.0	境外知名投行持股（14|3|2） 高盛持股（13|3|1） 定向增发（8|3|3）	7	001339	SZSE	104.9	115.39
20260617	1	3天2板	603458.SH	勘设股份	14.72	10.014948	sealed	527364928.0	61690048.0	0.116978	4079836416.0	境外知名投行持股（14|3|2） 摩根中国A股基金持股（6|1|0） 西部大开发（3|1|0）	8	603458	SSE	13.38	14.72
20260617	1	1天1板	002828.SZ	贝肯能源	9.77	10.022523	sealed	208380032.0	56712896.0	0.272161	1705179594.0	境外知名投行持股（14|3|2） 高盛持股（13|3|1） 煤化工（4|3|1）	9	002828	SZSE	8.88	9.77
20260617	1	1天1板	002404.SZ	嘉欣丝绸	6.84	9.967846	sealed	176257664.0	29195856.0	0.165643	2042372016.0	境外知名投行持股（14|3|2） 高盛持股（13|3|1） 集成电路（8|1|0）	4	002404	SZSE	6.22	6.84
20260617	1	1天1板	001282.SZ	三联锻造	21.18	10.025974	sealed	257027056.0	61875252.0	0.240734	1345027428.0	高盛持股（13|3|1） 比亚迪概念（9|3|2） 小鹏汽车概念（3|1|0）	4	001282	SZSE	19.25	21.18
20260617	1	1天1板	603285.SH	键邦股份	50.58	10.00435	sealed	187149216.0	31824936.0	0.170051	3150972144.0	高盛持股（13|3|1） 涂料（2|1|0） 赛克（1|1|0）	9	603285	SSE	45.98	50.58
20260617	1	1天1板	603986.SH	兆易创新	586.04	10.000751	sealed	31598895104.0	923657644.0	0.029231	356917875132.0	罗素大盘（10|3|3） 集成电路（8|1|0） 财报高增长（7|1|0）	10	603986	SSE	532.76	586.04
20260617	1	1天1板	002201.SZ	九鼎新材	12.76	10.0	sealed	729626176.0	38567100.0	0.052859	5032711156.0	比亚迪概念（9|3|2） 境外主权基金持股（3|1|0） 阿布扎比投资局持股（3|1|0）	16	002201	SZSE	11.6	12.76
20260617	1	1天1板	002161.SZ	远 望 谷	6.26	10.017575	sealed	280800960.0	74134676.0	0.264011	3837468266.0	定向增发（8|3|3） 集成电路（8|1|0） 射频识别（1|1|0）	4	002161	SZSE	5.69	6.26
20260617	1	1天1板	000672.SZ	上峰材料	19.03	10.0	sealed	839488192.0	7598679.0	0.009052	7738526664.0	集成电路（8|1|0） 罗素中盘（5|2|1） 西部大开发（3|1|0）	9	000672	SZSE	17.3	19.03
20260617	1	1天1板	001326.SZ	联域股份	74.03	10.0	sealed	200625552.0	28708834.0	0.143097	1544510099.0	人民币贬值受益（6|1|0） 绿色照明（2|2|1）	8	001326	SZSE	67.3	74.03
20260617	1	1天1板	002918.SZ	蒙娜丽莎	12.53	10.00878	sealed	319472576.0	52146101.0	0.163226	1759877343.0	精装修（2|2|1） 杭州亚运会（1|1|0） 建筑陶瓷（1|1|0）	10	002918	SZSE	11.39	12.53
20260617	1	1天1板	603488.SH	展鹏科技	13.18	10.016694	sealed	499045856.0	1286368.0	0.002578	2422644796.0	换电（2|1|0） 电梯（1|1|0）	8	603488	SSE	11.98	13.18
20260617	1	1天1板	001223.SZ	欧克科技	49.83	10.0	sealed	244981328.0	138826380.0	0.566681	1629082224.0	智能制造装备（1|1|0）	10	001223	SZSE	45.3	49.83
20260617	1	7天3板	600176.SH	中国巨石	54.6	9.991942	sealed	7036662784.0	271045320.0	0.038519	114686377260.0		8	600176	SSE	49.64	54.6
20260617	1	1天1板	603601.SH	再升科技	15.77	9.972106	sealed	2490928384.0	118183534.0	0.047446	11640500917.0		28	603601	SSE	14.34	15.77
20260617	1	1天1板	603283.SH	赛腾股份	63.06	9.994767	sealed	1981130112.0	78881754.0	0.039817	13809824700.0		5	603283	SSE	57.33	63.06
20260617	1	1天1板	603139.SH	康惠股份	44.13	9.995015	sealed	228514576.0	41852892.0	0.183152	2229933030.0		6	603139	SSE	40.12	44.13
20260617	1	1天1板	600579.SH	中化装备	7.5	9.970674	sealed	141947728.0	27927000.0	0.196741	1360205250.0		7	600579	SSE	6.82	7.5
20260617	1	1天1板	603880.SH	南卫股份	8.06	9.959072	sealed	57982904.0	15954770.0	0.275163	1229001696.0		3	603880	SSE	7.33	8.06
20260617	1	1天1板	600673.SH	东阳光	35.89	9.990806	sealed	5115895296.0	6625294.0	0.001295	50652364525.0		10	600673	SSE	32.63	35.89
20260617	1	9天4板	603020.SH	爱普股份	13.89	9.976247	sealed	413910144.0	2562705.0	0.006191	3271838115.0		6	603020	SSE	12.63	13.89
20260617	1	1天1板	000955.SZ	欣龙控股	4.63	9.976247	sealed	194279696.0	153384.0	0.00079	1882545962.0		8	000955	SZSE	4.21	4.63
`;

const PREVIEW_LIMIT_LADDER_ROWS: Array<Record<string, string>> = PREVIEW_LIMIT_LADDER_TSV.trim().split("\n").map((line) => {
  const values = line.split("\t");
  const legacyRow = Object.fromEntries(LIMIT_LADDER_PREVIEW_TSV_COLUMNS.map((column, index) => [column, values[index] ?? ""]));
  return {
    ...legacyRow,
    primary_theme: previewPrimaryTheme(legacyRow.top_theme_summary),
    secondary_themes: previewSecondaryThemes(legacyRow.top_theme_summary)
  };
});

function previewPrimaryTheme(summary: string | undefined) {
  const names = previewThemeNames(summary);
  return names[0] ?? "";
}

function previewSecondaryThemes(summary: string | undefined) {
  const names = previewThemeNames(summary);
  return names.slice(1, 4).join("+");
}

function previewThemeNames(summary: string | undefined) {
  return String(summary ?? "")
    .split(/\s+/)
    .map((item, index) => previewThemeItem(item, index))
    .filter((item): item is PreviewThemeItem => item !== null)
    .filter((item) => !previewThemeIsNoise(item.name))
    .sort((left, right) =>
      right.limitUpCount - left.limitUpCount ||
      right.highestBoard - left.highestBoard ||
      right.lianbanCount - left.lianbanCount ||
      left.index - right.index
    )
    .map((item) => item.name);
}

type PreviewThemeItem = {
  name: string;
  limitUpCount: number;
  highestBoard: number;
  lianbanCount: number;
  index: number;
};

function previewThemeItem(value: string, index: number): PreviewThemeItem | null {
  const text = String(value ?? "").trim();
  if (!text) {
    return null;
  }
  const match = text.match(/^(.*?)（(\d+)\|(\d+)\|(\d+)）$/);
  if (!match) {
    return {
      name: text.replace(/（.*$/, "").trim(),
      limitUpCount: 0,
      highestBoard: 0,
      lianbanCount: 0,
      index
    };
  }
  return {
    name: match[1].trim(),
    limitUpCount: Number(match[2] ?? 0),
    highestBoard: Number(match[3] ?? 0),
    lianbanCount: Number(match[4] ?? 0),
    index
  };
}

function previewThemeIsNoise(name: string) {
  const keywords = [
    "不可减持",
    "持股",
    "罗素",
    "MSCI",
    "富时",
    "标普",
    "沪股通",
    "深股通",
    "融资融券",
    "转融券",
    "国企改革",
    "国资改革",
    "央企改革",
    "参股券商",
    "参股新三板",
    "最近闪拉",
    "定向增发",
    "并购基金",
    "财报",
    "证金",
    "汇金",
    "社保基金",
    "养老金"
  ];
  return keywords.some((keyword) => name.toUpperCase().includes(keyword.toUpperCase()));
}

const PREVIEW_THEME_STRENGTH_RANK_ROWS: Array<Record<string, string>> = [
  {
    rank: "1",
    trade_date: "20260618",
    topic_type: "theme",
    topic_name: "不可减持(新规)",
    topic_id: "2965",
    theme_strength_score: "2255",
    limit_up_count: "22",
    highest_ladder_level: "3",
    lianban_stock_count: "5",
    first_board_count: "17",
    leader_instrument_id: "002141.SZ",
    leader_name: "贤丰控股",
    leader_ladder_level: "3",
    leader_limit_board_text: "3天3板",
    leader_seal_amount: "213785958",
    seal_amount_sum: "3927163397",
    amount_sum: "18376688992",
    top_stock_summary: "贤丰控股（3天3板） 中天精装（3天3板） 通鼎互联（2天2板） 中京电子（2天2板） 立航科技（4天3板）"
  },
  {
    rank: "2",
    trade_date: "20260618",
    topic_type: "theme",
    topic_name: "境外知名投行持股",
    topic_id: "2519",
    theme_strength_score: "1335",
    limit_up_count: "13",
    highest_ladder_level: "2",
    lianban_stock_count: "3",
    first_board_count: "10",
    leader_instrument_id: "002491.SZ",
    leader_name: "通鼎互联",
    leader_ladder_level: "2",
    leader_limit_board_text: "2天2板",
    leader_seal_amount: "319368540",
    seal_amount_sum: "1750304674",
    amount_sum: "12347801640",
    top_stock_summary: "通鼎互联（2天2板） 中京电子（2天2板） 智微智能（2天2板） 晋拓股份（1天1板） 抚顺特钢（1天1板）"
  },
  {
    rank: "3",
    trade_date: "20260618",
    topic_type: "theme",
    topic_name: "华为概念",
    topic_id: "1075",
    theme_strength_score: "1155",
    limit_up_count: "11",
    highest_ladder_level: "4",
    lianban_stock_count: "3",
    first_board_count: "8",
    leader_instrument_id: "600353.SH",
    leader_name: "旭光电子",
    leader_ladder_level: "4",
    leader_limit_board_text: "6天5板",
    leader_seal_amount: "469323117",
    seal_amount_sum: "4387498863",
    amount_sum: "18287416904",
    top_stock_summary: "旭光电子（6天5板） 艾华集团（3天3板） 中京电子（2天2板） 光迅科技（4天2板） 卓郎智能（4天3板）"
  },
  {
    rank: "4",
    trade_date: "20260618",
    topic_type: "theme",
    topic_name: "高盛持股",
    topic_id: "3031",
    theme_strength_score: "1140",
    limit_up_count: "11",
    highest_ladder_level: "2",
    lianban_stock_count: "4",
    first_board_count: "7",
    leader_instrument_id: "002491.SZ",
    leader_name: "通鼎互联",
    leader_ladder_level: "2",
    leader_limit_board_text: "2天2板",
    leader_seal_amount: "319368540",
    seal_amount_sum: "1268297363",
    amount_sum: "8703460032",
    top_stock_summary: "通鼎互联（2天2板） 中京电子（2天2板） 智微智能（2天2板） 立航科技（4天3板） 华森制药（1天1板）"
  },
  {
    rank: "5",
    trade_date: "20260618",
    topic_type: "theme",
    topic_name: "国企改革",
    topic_id: "2978",
    theme_strength_score: "1040",
    limit_up_count: "10",
    highest_ladder_level: "3",
    lianban_stock_count: "2",
    first_board_count: "8",
    leader_instrument_id: "002989.SZ",
    leader_name: "中天精装",
    leader_ladder_level: "3",
    leader_limit_board_text: "3天3板",
    leader_seal_amount: "52695437",
    seal_amount_sum: "4889527118",
    amount_sum: "20411634912",
    top_stock_summary: "中天精装（3天3板） 冰轮环境（8天4板） 光迅科技（4天2板） 江西铜业（4天2板） 祥龙电业（1天1板）"
  }
];

const PREVIEW_AUCTION_PROCESS_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000988.SZ",
    symbol: "000988",
    tdx_code: "sz000988",
    exchange: "SZSE",
    auction_time: "09:15:00",
    auction_index: "0",
    price: "152.800003",
    matched_volume: "157",
    matched_amount_estimated: "2398960.047913",
    unmatched_volume: "11",
    unmatched_amount_estimated: "168080.003357",
    unmatched_direction: "1"
  },
  {
    instrument_id: "000988.SZ",
    symbol: "000988",
    tdx_code: "sz000988",
    exchange: "SZSE",
    auction_time: "09:15:09",
    auction_index: "1",
    price: "153.350006",
    matched_volume: "508",
    matched_amount_estimated: "7790180.310059",
    unmatched_volume: "7",
    unmatched_amount_estimated: "107345.004272",
    unmatched_direction: "-1"
  },
  {
    instrument_id: "000988.SZ",
    symbol: "000988",
    tdx_code: "sz000988",
    exchange: "SZSE",
    auction_time: "14:57:09",
    auction_index: "82",
    price: "150.210007",
    matched_volume: "321",
    matched_amount_estimated: "4821741.224670",
    unmatched_volume: "18",
    unmatched_amount_estimated: "270378.012085",
    unmatched_direction: "1"
  },
  {
    instrument_id: "000988.SZ",
    symbol: "000988",
    tdx_code: "sz000988",
    exchange: "SZSE",
    auction_time: "14:59:51",
    auction_index: "87",
    price: "150.600006",
    matched_volume: "719",
    matched_amount_estimated: "10828140.438843",
    unmatched_volume: "22",
    unmatched_amount_estimated: "331320.013428",
    unmatched_direction: "-1"
  }
];

const PREVIEW_AUCTION_RESULT_TODAY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    auction_time: "09:25",
    trade_index: "1",
    price: "10.86",
    volume: "1200",
    amount: "1303200.0",
    order_count: "28"
  }
];

const PREVIEW_AUCTION_RESULT_HISTORY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260511",
    auction_time: "09:25",
    auction_datetime: "2026-05-11T09:25:00+08:00",
    trade_index: "1",
    price: "10.86",
    volume: "1200",
    amount: "1303200.0",
    order_count: "28"
  }
];

const PREVIEW_AUCTION_INDICATOR_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "002971.SZ",
    symbol: "002971",
    tdx_code: "sz002971",
    exchange: "SZSE",
    stats_date: "20260612",
    open_price: "55.76",
    pre_close: "50.69",
    open_change_pct: "10.001973",
    open_amount: "121491000",
    open_volume_hand: "21788.199426",
    open_volume_ratio: "17.55",
    open_turnover_z: "1.895",
    open_prev_amount_ratio: "3.653",
    auction_prev_volume_ratio: "0.6548",
    opening_rush: "6.01",
    open_prev_seal_ratio: "2677.25",
    prev_amount: "3325475300",
    prev_seal_amount: "4537900",
    prev2_seal_amount: "186197000",
    prev_open_volume_hand: "33272",
    prev_open_amount: "182996000",
    float_shares: "114984000",
    float_market_value: "6520440000",
    free_float_shares: "114984000",
    free_float_market_value: "6520440000",
    seal_amount: "453790000",
    seal_to_amount_ratio: "0.18",
    seal_to_float_ratio: "6.96",
    seal_prev_ratio: "100",
    limit_stat_days: "7",
    limit_up_count_in_stat_days: "5",
    limit_board_text: "7天5板",
    limit_up_streak_days: "4",
    year_limit_up_days: "13"
  }
];

function klinePreviewConfig(interfaceId: string) {
  const configs: Record<string, { period: string; sdkArgs: string[] }> = {
    stock_kline_second_tdx: {
      period: "5s",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],', "seconds=5,"]
    },
    stock_kline_minute_tdx: {
      period: "1m",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],', 'period="1m",']
    },
    stock_kline_nminute_tdx: {
      period: "10m",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],', "minutes=10,"]
    },
    stock_kline_daily_tdx: {
      period: "day",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],']
    },
    stock_kline_nday_tdx: {
      period: "45d",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],', "days=45,"]
    },
    stock_kline_weekly_tdx: {
      period: "week",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],']
    },
    stock_kline_monthly_tdx: {
      period: "month",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],']
    },
    stock_kline_quarterly_tdx: {
      period: "quarter",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],']
    },
    stock_kline_yearly_tdx: {
      period: "year",
      sdkArgs: ['code=["000001.SZ", "600000.SH"],']
    }
  };
  return configs[interfaceId] ?? configs.stock_kline_second_tdx;
}

function klinePreviewRows(period: string): Array<Record<string, string>> {
  return PREVIEW_KLINE_ROWS.map((row) => ({ ...row, period }));
}

const PREVIEW_KLINE_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "2026-05-19T13:39:50+08:00",
    period: "5s",
    open: "10.13",
    high: "10.15",
    low: "10.12",
    close: "10.14",
    volume: "120.0",
    amount: "121680.0"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "2026-05-19T13:39:55+08:00",
    period: "5s",
    open: "10.14",
    high: "10.16",
    low: "10.13",
    close: "10.15",
    volume: "96.0",
    amount: "97440.0"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "2026-05-19T13:40:00+08:00",
    period: "5s",
    open: "10.15",
    high: "10.17",
    low: "10.14",
    close: "10.16",
    volume: "132.0",
    amount: "134112.0"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "2026-05-19T13:40:05+08:00",
    period: "5s",
    open: "10.16",
    high: "10.16",
    low: "10.13",
    close: "10.13",
    volume: "88.0",
    amount: "89144.0"
  },
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    trade_time: "2026-05-19T13:39:50+08:00",
    period: "5s",
    open: "8.42",
    high: "8.43",
    low: "8.41",
    close: "8.42",
    volume: "210.0",
    amount: "176820.0"
  },
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    trade_time: "2026-05-19T13:39:55+08:00",
    period: "5s",
    open: "8.42",
    high: "8.44",
    low: "8.42",
    close: "8.43",
    volume: "184.0",
    amount: "155112.0"
  },
  {
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    trade_time: "2026-05-19T13:40:00+08:00",
    period: "5s",
    open: "8.43",
    high: "8.43",
    low: "8.41",
    close: "8.41",
    volume: "226.0",
    amount: "190066.0"
  }
];

const PREVIEW_INTRADAY_HISTORY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T09:31:00+08:00",
    minute_index: "0",
    price: "10.13",
    volume: "120",
    prev_close: "10.08"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T09:32:00+08:00",
    minute_index: "1",
    price: "10.15",
    volume: "80",
    prev_close: "10.08"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T11:30:00+08:00",
    minute_index: "119",
    price: "10.22",
    volume: "96",
    prev_close: "10.08"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T13:01:00+08:00",
    minute_index: "120",
    price: "10.19",
    volume: "105",
    prev_close: "10.08"
  }
];

const PREVIEW_INTRADAY_RECENT_HISTORY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T09:31:00+08:00",
    time_label: "09:31",
    minute_index: "0",
    price: "10.13",
    avg_price: "10.115",
    volume: "120",
    prev_close: "10.08",
    open_price: "10.12"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T09:32:00+08:00",
    time_label: "09:32",
    minute_index: "1",
    price: "10.15",
    avg_price: "10.128",
    volume: "80",
    prev_close: "10.08",
    open_price: "10.12"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T11:30:00+08:00",
    time_label: "11:30",
    minute_index: "119",
    price: "10.22",
    avg_price: "10.176",
    volume: "96",
    prev_close: "10.08",
    open_price: "10.12"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260519",
    trade_time: "2026-05-19T13:01:00+08:00",
    time_label: "13:01",
    minute_index: "120",
    price: "10.19",
    avg_price: "10.1772",
    volume: "105",
    prev_close: "10.08",
    open_price: "10.12"
  }
];

const PREVIEW_INTRADAY_TODAY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    time_label: "09:31",
    minute_index: "0",
    price: "10.86",
    avg_price: "10.8417",
    volume: "120"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    time_label: "09:32",
    minute_index: "1",
    price: "10.88",
    avg_price: "10.8427",
    volume: "80"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    time_label: "11:30",
    minute_index: "119",
    price: "10.92",
    avg_price: "10.8751",
    volume: "96"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    time_label: "13:01",
    minute_index: "120",
    price: "10.89",
    avg_price: "10.8768",
    volume: "105"
  }
];

const PREVIEW_INTRADAY_BUY_SELL_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "09:30",
    minute_index: "0",
    bid_order: "10326",
    ask_order: "4866"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "09:31",
    minute_index: "1",
    bid_order: "6321",
    ask_order: "20068"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "10:55",
    minute_index: "85",
    bid_order: "12397",
    ask_order: "27555"
  }
];

const PREVIEW_INTRADAY_VOLUME_COMPARISON_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "09:30",
    minute_index: "0",
    today_volume: "105984",
    yesterday_volume: "44100",
    volume_change: "61884",
    volume_change_pct: "140.326531"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "09:31",
    minute_index: "1",
    today_volume: "126062",
    yesterday_volume: "87433",
    volume_change: "38629",
    volume_change_pct: "44.181259"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    minute_time: "10:04",
    minute_index: "34",
    today_volume: "557963",
    yesterday_volume: "415016",
    volume_change: "142947",
    volume_change_pct: "34.443732"
  }
];

const PREVIEW_TRADE_TODAY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "14:08",
    trade_index: "0",
    price: "10.86",
    volume: "89",
    order_count: "9",
    side: "buy"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "14:08",
    trade_index: "1",
    price: "10.86",
    volume: "22",
    order_count: "5",
    side: "buy"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_time: "14:08",
    trade_index: "2",
    price: "10.85",
    volume: "86",
    order_count: "8",
    side: "sell"
  }
];

const PREVIEW_TRADE_HISTORY_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260511",
    trade_time: "14:12",
    trade_datetime: "2026-05-11T14:12:00+08:00",
    trade_index: "0",
    price: "10.86",
    volume: "89",
    order_count: "9",
    side: "buy"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260511",
    trade_time: "14:13",
    trade_datetime: "2026-05-11T14:13:00+08:00",
    trade_index: "1",
    price: "10.85",
    volume: "86",
    order_count: "8",
    side: "sell"
  },
  {
    instrument_id: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20260511",
    trade_time: "14:13",
    trade_datetime: "2026-05-11T14:13:00+08:00",
    trade_index: "2",
    price: "10.86",
    volume: "64",
    order_count: "5",
    side: "neutral"
  }
];

const PREVIEW_ADJ_FACTOR_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    ts_code: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20240531",
    adj_factor: "0.825"
  },
  {
    instrument_id: "000001.SZ",
    ts_code: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20240603",
    adj_factor: "1"
  },
  {
    instrument_id: "000001.SZ",
    ts_code: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    trade_date: "20240604",
    adj_factor: "1"
  }
];

const PREVIEW_CAPITAL_CHANGE_ROWS: Array<Record<string, string>> = [
  {
    instrument_id: "000001.SZ",
    ts_code: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    event_date: "20240614",
    category_raw: "1",
    category_name: "除权除息",
    c1: "7.19",
    c2: "0",
    c3: "0",
    c4: "0"
  },
  {
    instrument_id: "000001.SZ",
    ts_code: "000001.SZ",
    symbol: "000001",
    tdx_code: "sz000001",
    exchange: "SZSE",
    event_date: "20241010",
    category_raw: "1",
    category_name: "除权除息",
    c1: "2.46",
    c2: "0",
    c3: "0",
    c4: "0"
  },
  {
    instrument_id: "600300.SH",
    ts_code: "600300.SH",
    symbol: "600300",
    tdx_code: "sh600300",
    exchange: "SSE",
    event_date: "20010104",
    category_raw: "5",
    category_name: "股本变化",
    c1: "5000",
    c2: "33000",
    c3: "9200",
    c4: "33000"
  }
];

const PREVIEW_FINANCE_BASE_ROW: Record<string, string> = {
  instrument_id: "000001.SZ",
  symbol: "000001",
  tdx_code: "sz000001",
  exchange: "SZSE",
  updated_date: "20260425",
  ipo_date: "19910403",
  total_share: "19405918750",
  float_share: "19405601250",
  state_share: "0",
  founder_legal_person_share: "0",
  legal_person_share: "0",
  b_share: "0",
  h_share: "0",
  shareholder_count: "457610",
  eps: "0.67",
  bps: "23.91",
  total_assets: "35277000000",
  current_assets: "1000000",
  fixed_assets: "2000000",
  intangible_assets: "3000000",
  current_liabilities: "4000000",
  long_term_liabilities: "5000000",
  capital_reserve: "6000000",
  net_assets: "7000000",
  accounts_receivable: "9000000",
  inventory: "14000000",
  revenue: "35277000000",
  main_business_profit: "8000000",
  operating_profit: "10000000",
  investment_income: "11000000",
  operating_cashflow: "12000000",
  total_cashflow: "13000000",
  total_profit: "15000000",
  after_tax_profit: "16000000",
  net_profit: "14523000000",
  undistributed_profit: "17000000",
  province_raw: "18",
  province_name: "深圳",
  province_board_name: "深圳板块",
  province_board_code: "880218",
  industry_raw: "101",
  tdx_industry_code: "T1001",
  tdx_industry_name: "银行",
  tdx_industry_path: "金融 / 银行",
  tdx_research_industry_code: "X500102",
  tdx_research_industry_name: "股份制银行",
  tdx_research_industry_path: "银行 / 全国性银行 / 股份制银行"
};

const PREVIEW_FINANCE_ROWS: Array<Record<string, string>> = [
  PREVIEW_FINANCE_BASE_ROW,
  {
    ...PREVIEW_FINANCE_BASE_ROW,
    instrument_id: "600000.SH",
    symbol: "600000",
    tdx_code: "sh600000",
    exchange: "SSE",
    updated_date: "20260430",
    ipo_date: "19991110",
    total_share: "29352108000",
    float_share: "29352108000",
    shareholder_count: "338420",
    eps: "0.72",
    bps: "22.68",
    total_assets: "9238500000000",
    net_assets: "665900000000",
    revenue: "173540000000",
    net_profit: "42120000000",
    operating_cashflow: "91860000000",
    province_raw: "9",
    province_name: "天津",
    province_board_name: "天津板块",
    province_board_code: "880209",
    industry_raw: "101",
    tdx_industry_code: "T1001",
    tdx_industry_name: "银行",
    tdx_industry_path: "金融 / 银行",
    tdx_research_industry_code: "X500102",
    tdx_research_industry_name: "股份制银行",
    tdx_research_industry_path: "银行 / 全国性银行 / 股份制银行"
  },
  {
    ...PREVIEW_FINANCE_BASE_ROW,
    instrument_id: "300750.SZ",
    symbol: "300750",
    tdx_code: "sz300750",
    exchange: "SZSE",
    updated_date: "20260424",
    ipo_date: "20180611",
    total_share: "4400470000",
    float_share: "3897800000",
    shareholder_count: "252180",
    eps: "11.23",
    bps: "58.46",
    total_assets: "731250000000",
    net_assets: "257250000000",
    revenue: "400920000000",
    net_profit: "44120000000",
    operating_cashflow: "68230000000",
    province_raw: "13",
    province_name: "福建",
    province_board_name: "福建板块",
    province_board_code: "880213",
    industry_raw: "335",
    tdx_industry_code: "T0908",
    tdx_industry_name: "电气设备",
    tdx_industry_path: "工业 / 电气设备",
    tdx_research_industry_code: "X450103",
    tdx_research_industry_name: "锂电池",
    tdx_research_industry_path: "新能源 / 电池 / 锂电池"
  }
];

const FINANCE_INTERFACE_IDS = new Set([
  "stock_finance_summary_tdx",
  "stock_share_capital_tdx",
  "stock_balance_summary_tdx",
  "stock_profit_cashflow_summary_tdx",
  "stock_finance_profile_tdx"
]);

function isFinanceInterface(interfaceId: string) {
  return FINANCE_INTERFACE_IDS.has(interfaceId);
}

function isF10CatalogInterface(activeDoc: CatalogItem) {
  return activeDoc.sourceCode === "tdx" && activeDoc.category === "F10数据";
}

const TDX_TOPIC_WORKER_INTERFACE_IDS = new Set([
  "stock_limit_ladder_tdx",
  "stock_theme_strength_rank_tdx"
]);

const TDX_EXT_LOCAL_INTERFACE_IDS = new Set([
  "tdx_ext_markets_tdx",
  "tdx_ext_instruments_tdx",
  "futures_contracts_tdx",
  "option_contracts_tdx",
  "fund_codes_tdx",
  "fund_nav_tdx",
  "bond_codes_tdx",
  "fx_codes_tdx",
  "macro_indicators_tdx",
]);

const TDX_EXT_REMOTE_INTERFACE_IDS = new Set([
  "futures_realtime_snapshot_tdx",
  "futures_kline_tdx",
  "futures_intraday_today_tdx",
  "futures_intraday_history_tdx",
  "futures_trades_today_tdx",
  "futures_trades_history_tdx",
  "option_chain_tdx",
  "option_realtime_snapshot_tdx",
  "option_kline_tdx",
  "option_intraday_today_tdx",
  "option_intraday_history_tdx",
  "fund_nav_series_tdx",
  "bond_realtime_snapshot_tdx",
  "bond_kline_tdx",
  "fx_realtime_snapshot_tdx",
  "fx_kline_tdx",
  "fx_intraday_today_tdx",
  "fx_intraday_history_tdx",
  "fx_trades_today_tdx",
  "fx_trades_history_tdx",
  "macro_indicator_snapshot_tdx",
  "macro_indicator_series_tdx"
]);

function tdxExecutionOptionKind(activeDoc: CatalogItem): "quote" | "f10" | "f10_topic" | "tdx_ext" | null {
  if (!activeDoc.path.startsWith("/v1/request/")) {
    return null;
  }
  if (TDX_TOPIC_WORKER_INTERFACE_IDS.has(activeDoc.id)) {
    return "f10_topic";
  }
  if (TDX_EXT_REMOTE_INTERFACE_IDS.has(activeDoc.id)) {
    return "tdx_ext";
  }
  if (TDX_EXT_LOCAL_INTERFACE_IDS.has(activeDoc.id)) {
    return null;
  }
  if (isF10CatalogInterface(activeDoc) || activeDoc.id === "stock_topic_exposure_tdx") {
    return activeDoc.params.some((param) => param[0] === "code") ? "f10" : null;
  }
  if (
    activeDoc.sourceCode === "tdx" &&
    ["stock", "index", "etf"].includes(activeDoc.assetClass ?? "")
  ) {
    return "quote";
  }
  return null;
}

function isTdxExtInterface(interfaceId: string) {
  return TDX_EXT_LOCAL_INTERFACE_IDS.has(interfaceId) || TDX_EXT_REMOTE_INTERFACE_IDS.has(interfaceId);
}

function isExternalSourceInterface(interfaceId: string) {
  return (
    interfaceId.startsWith("cninfo_") ||
    interfaceId.startsWith("tencent_") ||
    interfaceId.startsWith("eastmoney_") ||
    interfaceId.startsWith("sina_")
  );
}

function supportsTdxExecutionOptions(activeDoc: CatalogItem) {
  return tdxExecutionOptionKind(activeDoc) !== null;
}

type AdvancedOptionEntry = [string, number | string | boolean];

type TdxAdvancedRecommendation = {
  sourceServerCount: number;
  connectionsPerServer: number;
  reason: string;
  label?: string;
  optionEntries?: AdvancedOptionEntry[];
  extraRows?: string[][];
};

function TdxAdvancedExecutionOptions({ activeDoc }: { activeDoc: CatalogItem }) {
  const example = tdxAdvancedExecutionExample(activeDoc);
  const kind = tdxExecutionOptionKind(activeDoc);
  const recommendation = tdxAdvancedOptionsRecommendation(activeDoc, kind);
  const optionEntries: AdvancedOptionEntry[] = recommendation.optionEntries ?? [
    ["source_server_count", recommendation.sourceServerCount],
    ["connections_per_server", recommendation.connectionsPerServer]
  ];
  const sdkOptionLines = optionEntries.map(([key, value]) => `        "${key}": ${formatPythonLiteral(value)},`).join("\n");
  const curlOptions = Object.fromEntries(optionEntries);
  const sessionSource = kind === "tdx_ext" ? "tdx_ext" : "tdx";
  const showSessionExample = kind === "quote" || kind === "tdx_ext";
  const optionRows: string[][] = [
    ["推荐并发", recommendation.label ?? `${recommendation.sourceServerCount} × ${recommendation.connectionsPerServer}`, recommendation.reason],
    ...optionEntries.map(([key, value]) => [key, String(value), optionDescription(key)]),
    ...(recommendation.extraRows ?? [])
  ];
  const sdkCode = `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${activeDoc.name}",
${example.pythonParamLines}
    options={
${sdkOptionLines}
    },
)
print(df)`;
  const sessionCode = `import axdata as ax

client = ax.AxDataClient()

with client.session(
    source="${sessionSource}",
    source_server_count=${recommendation.sourceServerCount},
    connections_per_server=${recommendation.connectionsPerServer},
) as session:
    df = session.call(
        "${activeDoc.name}",
${example.pythonParamLines}
    )
print(df)`;
  const curlCode = `curl -X POST "http://127.0.0.1:8666/v1/request/${activeDoc.name}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "params": ${example.jsonParams},
    "options": ${JSON.stringify(curlOptions, null, 6).replace(/\n/g, "\n    ")},
    "persist": false
  }'`;

  return (
    <section className="doc-section advanced-options-section" id="advanced-execution-options">
      <div className="section-title">
        <SlidersHorizontal size={20} />
        <h2>高级选项</h2>
      </div>
      <p className="guide-note">
        不填也能用；单次请求可以传 options。盘中反复请求实时快照、榜单、盘口或扩展行情时，用本地 session 复用 TDX 长连接池。
      </p>
      <DataTable
        columns={["项目", "建议", "说明"]}
        rows={optionRows}
      />
      <div className="advanced-options-grid">
        <div>
          <div className="source-preview-label">Python SDK</div>
          <CodeBlock code={sdkCode} language="py" />
        </div>
        {showSessionExample ? (
          <div>
            <div className="source-preview-label">高频本地 session</div>
            <CodeBlock code={sessionCode} language="py" />
          </div>
        ) : null}
        <div>
          <div className="source-preview-label">网页/其他语言桥接</div>
          <CodeBlock code={curlCode} language="bash" />
        </div>
      </div>
    </section>
  );
}

function tdxAdvancedOptionsRecommendation(
  activeDoc: CatalogItem,
  kind: "quote" | "f10" | "f10_topic" | "tdx_ext" | null
): TdxAdvancedRecommendation {
  const recommendations: Record<string, TdxAdvancedRecommendation> = {
    stock_codes_tdx: {
      sourceServerCount: 1,
      connectionsPerServer: 3,
      reason: "这个接口主要按沪、深、北三个市场拆分扫描，1 台服务器 3 条连接刚好覆盖三路任务。"
    },
    stock_st_list_tdx: {
      sourceServerCount: 1,
      connectionsPerServer: 3,
      reason: "先拿完整股票池再筛 ST / *ST，瓶颈和最新股票列表一致，推荐 1 × 3。"
    },
    stock_suspensions_tdx: {
      sourceServerCount: 4,
      connectionsPerServer: 2,
      reason: "和采集一致：一开始就创建 4 × 2 连接池；前段股票池只有沪、深、北三路，天然用不满，后段批量停牌状态检查会吃满并发。",
      extraRows: [
        ["股票池阶段", "最多 3 路", "扫描沪、深、北三个市场；不需要单独配置。"],
        ["停牌状态阶段", "4 × 2", "批量查停牌状态，批大小 80。"]
      ]
    },
    stock_daily_share_tdx: {
      sourceServerCount: 4,
      connectionsPerServer: 2,
      reason: "和采集一致：创建 4 × 2 连接池；前段扫描股票池只用到沪、深、北三路，后段财务快照批量使用同一个连接池。",
      extraRows: [
        ["股票池阶段", "最多 3 路", "扫描沪、深、北三个市场；不需要单独配置。"],
        ["财务快照阶段", "4 × 2", "按每批 80 只股票读取财务快照。"]
      ]
    },
    stock_daily_price_limit_tdx: {
      sourceServerCount: 4,
      connectionsPerServer: 2,
      reason: "用户只传一次 options；接口内部会先拿股票池，再批量请求实时快照并计算涨跌停价格。"
    },
    stock_capital_changes_tdx: {
      sourceServerCount: 8,
      connectionsPerServer: 2,
      reason: "股本变迁是逐票事件请求，任务更多，推荐用 8 台快服务器、每台 2 条连接。"
    },
    stock_limit_ladder_tdx: {
      sourceServerCount: 1,
      connectionsPerServer: 1,
      label: "题材查询 6 线程",
      optionEntries: [
        ["f10_topic_workers", 6],
        ["f10_topic_refill_workers", 6],
        ["f10_topic_refill_rounds", 1]
      ],
      reason: "和采集一致：主体天梯列表一次可取，耗时主要在逐票补题材；首轮用 6 个 F10 worker 查询，只有题材为空时才用 6 个 worker 补漏 1 轮。"
    },
    stock_theme_strength_rank_tdx: {
      sourceServerCount: 1,
      connectionsPerServer: 1,
      label: "题材查询 6 线程",
      optionEntries: [
        ["f10_topic_workers", 6],
        ["f10_topic_refill_workers", 6],
        ["f10_topic_refill_rounds", 1]
      ],
      reason: "和采集一致：题材强度排行复用连板池，耗时主要在逐票补题材；首轮用 6 个 F10 worker 查询，只有题材为空时才用 6 个 worker 补漏 1 轮。"
    }
  };
  if (kind === "f10") {
    return {
      sourceServerCount: 1,
      connectionsPerServer: 1,
      label: "F10 查询 6 worker",
      optionEntries: [["f10_workers", 6]],
      reason: "F10 不是普通行情长连接；这个选项只在一次传多只 code 时并发查询，单只股票不会明显加速。"
    };
  }
  if (kind === "tdx_ext") {
    return {
      sourceServerCount: 2,
      connectionsPerServer: 2,
      label: "拓展行情连接 2 × 2",
      reason: "拓展行情使用独立连接池；K线、分时、逐笔和多合约快照这类多品种请求才会并发，本地缓存列表不会显示高级选项。",
      extraRows: [
        ["适用场景", "多品种/多合约", "多个品种、多个合约或多页请求可以拆开请求。"],
        ["单品种请求", "保持可用", "只有一个 code 时即使传 options，也不会为了并发增加复杂度。"]
      ]
    };
  }
  return (
    recommendations[activeDoc.name] ?? {
      sourceServerCount: 1,
      connectionsPerServer: 1,
      reason: "默认保持单连接，只有全量、批量或逐票拆分明显的接口才建议手动提高并发。"
    }
  );
}

function optionDescription(key: string) {
  if (key === "source_server_count") {
    return "使用前几个已启用且测速排序靠前的源端服务器；普通行情和拓展行情会各自选择自己的服务器表";
  }
  if (key === "connections_per_server") {
    return "每个服务器同时打开几条连接；F10 接口不使用这个选项";
  }
  if (key === "f10_workers") {
    return "批量 code 时同时查询多少只股票的 F10 数据";
  }
  if (key === "f10_topic_workers") {
    return "第一轮同时查询多少只股票的 F10 题材信息";
  }
  if (key === "f10_topic_refill_workers") {
    return "第一轮没取到题材的股票，用多少 worker 再查一次";
  }
  if (key === "f10_topic_refill_rounds") {
    return "题材补漏轮数；1 表示首轮有漏时最多补一次，没有漏就不会补";
  }
  return "本次请求的执行选项";
}

function tdxAdvancedExecutionExample(activeDoc: CatalogItem) {
  const paramNames = new Set(activeDoc.params.map((param) => param[0]));
  const pythonArgs: string[] = [];
  const jsonParams: Record<string, unknown> = {};
  const kind = tdxExecutionOptionKind(activeDoc);

  if (paramNames.has("code")) {
    const codes = advancedExampleCodes(activeDoc, kind);
    pythonArgs.push(`code=${formatPythonLiteral(codes)}`);
    jsonParams.code = codes;
  } else if (paramNames.has("scope")) {
    pythonArgs.push(`scope="all"`);
    jsonParams.scope = "all";
  }

  if (activeDoc.id === "option_chain_tdx") {
    pythonArgs.push(`product_code="AP"`);
    pythonArgs.push(`contract_month="202610"`);
    jsonParams.product_code = "AP";
    jsonParams.contract_month = "202610";
  }

  if (paramNames.has("category") && activeDoc.id === "stock_realtime_rank_tdx") {
    pythonArgs.push(`category="a_share"`);
    jsonParams.category = "a_share";
  }
  if (paramNames.has("sort")) {
    pythonArgs.push(`sort="change_pct"`);
    jsonParams.sort = "change_pct";
  }
  if (paramNames.has("count")) {
    pythonArgs.push(`count=80`);
    jsonParams.count = 80;
  }
  if (paramNames.has("seconds")) {
    pythonArgs.push(`seconds=5`);
    jsonParams.seconds = 5;
  }
  if (paramNames.has("minutes")) {
    pythonArgs.push(`minutes=10`);
    jsonParams.minutes = 10;
  }
  if (paramNames.has("days")) {
    pythonArgs.push(`days=45`);
    jsonParams.days = 45;
  }
  if (paramNames.has("trade_date") && activeDoc.params.some((param) => param[0] === "trade_date" && param[2] === "是")) {
    pythonArgs.push(`trade_date="20260618"`);
    jsonParams.trade_date = "20260618";
  }

  const pythonParamLines = pythonArgs.length > 0
    ? pythonArgs.map((arg) => `    ${arg},`).join("\n")
    : `    # 正常输入参数照旧写在这里`;
  const jsonParamText = JSON.stringify(jsonParams, null, 6).replace(/\n/g, "\n    ");
  return { pythonParamLines, jsonParams: jsonParamText };
}

function advancedExampleCodes(activeDoc: CatalogItem, kind: "quote" | "f10" | "f10_topic" | "tdx_ext" | null) {
  if (kind === "tdx_ext") {
    if (activeDoc.id.startsWith("option_")) {
      return ["AP2610-C-10000.CZCE", "AP2610-P-10000.CZCE"];
    }
    if (activeDoc.id.startsWith("fx_")) {
      return ["USDCNY.FX", "EURUSD.FX"];
    }
    if (activeDoc.id.startsWith("bond_")) {
      return ["10YGB.BOND", "1YGB.BOND"];
    }
    if (activeDoc.id.startsWith("macro_")) {
      return ["1_GDP.MACRO", "1_CPI.MACRO"];
    }
    if (activeDoc.id.startsWith("fund_")) {
      return ["159007.FUND", "110022.FUND"];
    }
    return ["IC2606.CFFEX", "IF2606.CFFEX"];
  }
  if (activeDoc.assetClass === "etf") {
    return ["510050.SH", "510300.SH"];
  }
  if (activeDoc.assetClass === "index") {
    return ["000001.SH", "399001.SZ"];
  }
  return ["000001.SZ", "600000.SH"];
}

function formatPythonLiteral(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => formatPythonLiteral(item)).join(", ")}]`;
  }
  if (typeof value === "string") {
    return `"${value}"`;
  }
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  return String(value);
}

function financePreviewRows(_interfaceId: string): Array<Record<string, string>> {
  return PREVIEW_FINANCE_ROWS;
}

const SCOPE_MARKETS: Record<string, string[]> = {
  all: ["主板", "科创板", "创业板", "北交所", "CDR"],
  main: ["主板"],
  star: ["科创板"],
  chinext: ["创业板"],
  bse: ["北交所"],
  cdr: ["CDR"]
};

function previewColumns(activeDoc: CatalogItem, rows: Array<Record<string, string>>) {
  const preferred = activeDoc.fields.map((field) => field[0]);
  const available = new Set(rows.flatMap((row) => Object.keys(row)));
  const columns = preferred.filter((column) => available.has(column));
  return columns.length > 0 ? columns : preferred.slice(0, 6);
}

function previewExampleRows(interfaceId: string, filter: PreviewFilter, value: string | string[]) {
  const sampleRows =
    interfaceId === "stock_suspensions_tdx"
      ? PREVIEW_SUSPENSION_SAMPLE_ROWS
      : interfaceId === "stock_st_list_tdx"
        ? PREVIEW_ST_SAMPLE_ROWS
        : PREVIEW_SAMPLE_ROWS;
  const values = Array.isArray(value) ? value : [value];

  if (filter === "name") {
    return values.flatMap((name) => sampleRows.filter((row) => row.name === name));
  }

  if (filter === "code") {
    return values.flatMap((code) => sampleRows.filter((row) => previewRowMatchesCode(row, code)));
  }

  const markets = values.flatMap((scope) => SCOPE_MARKETS[scope] ?? []);
  if (interfaceId === "stock_st_list_tdx") {
    const rows = sampleRows.filter((row) => markets.includes(row.market));
    return rows.length > 0 ? rows : sampleRows;
  }
  return pickRowsByMarket(sampleRows, markets);
}

function previewRowMatchesCode(row: Record<string, string>, code: string) {
  const normalized = code.trim().toLowerCase();
  return [row.instrument_id, row.symbol, row.tdx_code].some((candidate) => candidate.toLowerCase() === normalized);
}

function pickRowsByMarket(rows: Array<Record<string, string>>, markets: string[]) {
  const selected: Array<Record<string, string>> = [];
  for (const market of markets) {
    const row = rows.find((item) => item.market === market);
    if (row) {
      selected.push(row);
    }
  }
  return selected.length > 0 ? selected : rows.slice(0, markets.length);
}

function SdkModeGrid() {
  return (
    <div className="sdk-mode-grid">
      {sdkModes.map((mode) => {
        const ModeIcon = mode.icon;
        return (
          <article className="sdk-mode-card" key={mode.id}>
            <div className="sdk-mode-title">
              <ModeIcon size={18} />
              <strong>{mode.title}</strong>
              <span>{mode.badge}</span>
            </div>
            <p>{mode.summary}</p>
            <dl>
              {mode.facts.map((row) => (
                <div key={row.join(":")}>
                  <dt>{row[0]}</dt>
                  <dd>{row[1]}</dd>
                </div>
              ))}
            </dl>
          </article>
        );
      })}
    </div>
  );
}
