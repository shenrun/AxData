import type { ReactNode } from "react";
import { Activity, AlertCircle, CheckCircle2, Code2, ServerCog, Table2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { HealthPayload, InfoPage, RuntimeConfig, ServiceState, TableRow } from "../types";
import { columnsForRows, formatAuthState } from "../utils";

export function RuntimePanel({
  apiBase,
  health,
  lastChecked,
  runtimeConfig
}: {
  apiBase: string;
  health: HealthPayload | null;
  lastChecked: string;
  runtimeConfig: RuntimeConfig | null;
}) {
  return (
    <aside className="runtime-panel">
      <div className="panel-title">
        <ServerCog size={18} />
        <strong>后端服务状态</strong>
      </div>
      <dl className="runtime-list">
        <div>
          <dt>后端地址</dt>
          <dd>{apiBase}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>{health?.status ?? "未连接"}</dd>
        </div>
        <div>
          <dt>后端端口</dt>
          <dd>{runtimeConfig?.api_port ?? "unknown"}</dd>
        </div>
        <div>
          <dt>网页端口</dt>
          <dd>{runtimeConfig?.web_port ?? "unknown"}</dd>
        </div>
        <div>
          <dt>鉴权</dt>
          <dd>{formatAuthState(runtimeConfig)}</dd>
        </div>
        <div>
          <dt>上次检查</dt>
          <dd>{lastChecked}</dd>
        </div>
      </dl>
    </aside>
  );
}

export function InfoPageView({
  aside,
  children,
  lead,
  page,
  showCode = true,
  showReadyBadge = true,
  showDetails = true
}: {
  aside?: ReactNode;
  children?: ReactNode;
  lead?: ReactNode;
  page: InfoPage;
  showCode?: boolean;
  showReadyBadge?: boolean;
  showDetails?: boolean;
}) {
  const Icon = page.icon;

  return (
    <>
      <section className={aside ? "doc-hero" : "doc-hero single"}>
        <div className="doc-heading">
          <div className="endpoint-line">
            <span className="section-eyebrow">{page.eyebrow}</span>
            {showReadyBadge ? (
              <span className="ready-badge">
                <CheckCircle2 size={15} />
                示例
              </span>
            ) : null}
          </div>

          <div className="title-row">
            <span className="title-icon">
              <Icon size={26} />
            </span>
            <h1>{page.title}</h1>
          </div>
          {page.summary ? <p>{page.summary}</p> : null}

          {page.facts.length > 0 ? (
            <dl className="summary-list">
              {page.facts.map((row) => (
                <div key={row.join(":")}>
                  <dt>{row[0]}</dt>
                  <dd>{row.slice(1).join(" / ")}</dd>
                </div>
              ))}
            </dl>
          ) : null}
        </div>

        {aside}
      </section>

      {lead}

      {showDetails && page.details.length > 0 ? (
        <section className="doc-section">
          <div className="section-title">
            <Table2 size={20} />
            <h2>详情</h2>
          </div>
          <DataTable columns={columnsForRows(page.details)} rows={page.details} />
        </section>
      ) : null}

      {showCode && page.code ? (
        <section className="doc-section">
          <div className="section-title">
            <Code2 size={20} />
            <h2>{page.codeTitle ?? "示例代码"}</h2>
          </div>
          <CodeBlock code={page.code} language={page.codeLanguage ?? "bash / py"} />
        </section>
      ) : null}

      {children}
    </>
  );
}

export function DataTable({ columns, rows }: { columns: string[]; rows: TableRow[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.join(":")}>
              {row.map((cell, index) => (
                <td key={`${cell}-${index}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CodeBlock({ code, language }: { code: string; language: string }) {
  return (
    <div className="code-block">
      <span>{language}</span>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

export function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="metric">
      <Icon size={18} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function StatusIcon({ state }: { state: ServiceState }) {
  if (state === "online") {
    return <CheckCircle2 size={17} />;
  }
  if (state === "offline") {
    return <AlertCircle size={17} />;
  }
  return <Activity size={17} />;
}

export function serviceLabel(state: ServiceState) {
  if (state === "online") {
    return "后端已连接";
  }
  if (state === "offline") {
    return "后端未连接";
  }
  return "检查中";
}
