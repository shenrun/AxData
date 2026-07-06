import { Activity, BarChart3, BriefcaseBusiness, Building2, CandlestickChart, CircleDollarSign, FileText, Landmark, LineChart, Radio, Table2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { CatalogGroup, CatalogItem, ReferenceSection, TableRow } from "./types";

type RuntimeParameter = {
  name?: unknown;
  dtype?: unknown;
  required?: unknown;
  description?: unknown;
  description_zh?: unknown;
};

const SOURCE_GROUP_ORDER = [
  "通达信",
  "通达信扩展行情",
  "交易所",
  "东方财富",
  "巨潮",
  "腾讯财经",
  "新浪财经",
  "其它"
];

const TDX_ASSET_GROUP_ORDER = [
  "股票数据",
  "指数数据",
  "ETF数据",
  "基金数据",
  "期货数据",
  "期权数据",
  "债券数据",
  "外汇数据",
  "宏观数据",
  "其它数据"
];

const CATEGORY_ORDER = [
  "基础数据",
  "实时数据",
  "短线数据",
  "行情数据",
  "竞价数据",
  "财务数据",
  "F10数据",
  "公告数据",
  "龙虎榜数据",
  "融资融券数据",
  "研报数据",
  "财务报表",
  "交易行为",
  "公告",
  "研报",
  "期货数据",
  "期权数据",
  "基金数据",
  "债券数据",
  "外汇数据",
  "宏观数据",
  "特色数据",
  "其它"
];

type RuntimeField = {
  name?: unknown;
  dtype?: unknown;
  description?: unknown;
  description_zh?: unknown;
};

type RuntimeRequiredConfig = {
  name?: unknown;
  kind?: unknown;
  required?: unknown;
  description?: unknown;
};

type RuntimeReferenceSection = {
  id?: unknown;
  title?: unknown;
  note?: unknown;
  columns?: unknown;
  rows?: unknown;
};

export type RuntimeInterfaceEntry = {
  name?: unknown;
  interface_name?: unknown;
  display_name_zh?: unknown;
  summary_zh?: unknown;
  source_code?: unknown;
  source_name_zh?: unknown;
  category?: unknown;
  request_mode?: unknown;
  first_stage_strategy?: unknown;
  source_ability?: unknown;
  description?: unknown;
  description_zh?: unknown;
  params_note_zh?: unknown;
  params_example_zh?: unknown;
  parameters?: unknown;
  fields?: unknown;
  provider_id?: unknown;
  asset_class?: unknown;
  menu_path?: unknown;
  collection?: unknown;
  enabled?: unknown;
  status_message?: unknown;
  next_action?: unknown;
  action_command?: unknown;
  declared_trust_level?: unknown;
  effective_trust_level?: unknown;
  plugin_status?: unknown;
  required_config?: unknown;
  example?: unknown;
  reference_sections?: unknown;
};

type CatalogTreeNode = {
  title: string;
  items: Set<string>;
  children: Map<string, CatalogTreeNode>;
};

export function mergeRuntimeCatalogItems(
  staticItems: CatalogItem[],
  runtimeEntries: RuntimeInterfaceEntry[]
): CatalogItem[] {
  if (runtimeEntries.length === 0) {
    return staticItems.map(markCatalogOnlyItem);
  }
  const runtimeItems = runtimeEntries.map((entry) => {
    const name = runtimeEntryName(entry);
    return mergeRuntimeCatalogItem(entry, name);
  });
  const runtimeIds = new Set(runtimeItems.map((item) => item.id));
  const staticRuntimeItems = staticItems.filter(
    (item) => !runtimeIds.has(item.id) && shouldKeepStaticRuntimeItem(item)
  );
  return [...runtimeItems, ...staticRuntimeItems];
}

function runtimeEntryName(entry: RuntimeInterfaceEntry) {
  return stringValue(entry.name, stringValue(entry.interface_name, "unknown_interface"));
}

function shouldKeepStaticRuntimeItem(item: CatalogItem): boolean {
  return item.path.startsWith("/v1/stream/");
}

export function runtimeNavGroups(items: CatalogItem[]): CatalogGroup[] {
  const roots = new Map<string, CatalogTreeNode>();
  for (const item of items) {
    addCatalogPath(roots, navigationPathForCatalogItem(item), item.id);
  }

  return sortedCatalogGroups(roots, []);
}

function mergeRuntimeCatalogItem(
  entry: RuntimeInterfaceEntry,
  name: string
): CatalogItem {
  const title = stringValue(entry.display_name_zh, name);
  const sourceName = stringValue(entry.source_name_zh, "数据源");
  const category = stringValue(entry.category, "接口");
  const sourceCode = stringValue(entry.source_code, "unknown");
  const providerId = stringValue(entry.provider_id, "");
  const assetClass = stringValue(entry.asset_class, "");
  const pluginStatus = stringValue(entry.plugin_status, "");
  const effectiveTrust = stringValue(entry.effective_trust_level, "");
  const collection = normalizedCollection(entry.collection);
  const requiredConfig = runtimeRequiredConfig(entry.required_config);
  const params = runtimeParams(entry.parameters);
  const fields = runtimeFields(entry.fields);
  const requestExampleParams = runtimeExampleParams(entry.example);
  const dataExamples = runtimeDataExamples(name, fields, entry);
  const summary = stringValue(entry.summary_zh, stringValue(entry.description_zh, stringValue(entry.description, title)));
  const description = stringValue(entry.description_zh, stringValue(entry.description, summary));
  const sourcePath = runtimeSourcePath(entry, name, sourceName, category, sourceCode, assetClass);
  const group = sourcePath;
  const overview = [
    ["接口名称", name],
    ["Provider", providerId || sourceCode],
    ["源", `${sourceName} / ${sourceCode}`],
    ["资产类型", assetClass || "unknown"],
    ["插件状态", pluginStatus || "unknown"],
    ["信任级别", effectiveTrust || "unknown"],
    ...(requiredConfig.length > 0 ? [["配置提示", requiredConfig.join("；")]] : [])
  ];

  return {
    ...runtimeFallbackItem(name, title, group),
    id: name,
    name,
    title,
    group,
    sourcePath,
    sourceCode,
    sourceNameZh: sourceName,
    assetClass,
    category,
    providerId,
    pluginStatus,
    providerEnabled: typeof entry.enabled === "boolean" ? entry.enabled : pluginStatus === "enabled",
    collectionSupported: collection.supported,
    defaultCollectionProfile: collection.defaultProfile,
    statusMessage: stringValueOrNull(entry.status_message),
    nextAction: stringValueOrNull(entry.next_action),
    actionCommand: stringValueOrNull(entry.action_command),
    requestExampleParams,
    method: "POST",
    path: `/v1/request/${name}`,
    status: pluginStatus === "enabled" ? "ready" : "example",
    icon: iconForRuntimeEntry(entry),
    cadence: "按需调用",
    key: firstField(fields) ?? "按接口定义",
    limit: stringValue(entry.source_ability, "按源端限制"),
    permission: pluginStatus === "enabled" ? "已启用" : pluginStatus || "按 Provider 配置",
    summary,
    description,
    overview,
    params,
    fields,
    dataExamples,
    paramsNote: stringValue(entry.params_note_zh, ""),
    paramsExample: stringValue(entry.params_example_zh, ""),
    sdk: runtimeSdkExample(name, params, requestExampleParams),
    curl: runtimeCurlExample(name, params, requestExampleParams)
  };
}

function markCatalogOnlyItem(item: CatalogItem): CatalogItem {
  if (!item.path.startsWith("/v1/request/")) {
    return item;
  }
  return {
    ...item,
    pluginStatus: item.pluginStatus ?? "missing",
    providerEnabled: false,
    collectionSupported: item.collectionSupported ?? false,
    statusMessage: item.statusMessage ?? "接口仅存在于前端目录；当前 API Registry 未返回该接口。",
    nextAction: item.nextAction ?? "刷新接口目录，或检查对应 Provider 是否已安装、启用、兼容且未冲突。",
    actionCommand: item.actionCommand ?? "axdata plugin list --json",
    status: "example"
  };
}

function runtimeFallbackItem(name: string, title: string, group: string): CatalogItem {
  return {
    id: name,
    group,
    title,
    name,
    method: "POST",
    path: `/v1/request/${name}`,
    status: "ready",
    icon: Table2,
    cadence: "按需调用",
    key: "按接口定义",
    limit: "按源端限制",
    permission: "按 Provider 配置",
    summary: title,
    description: title,
    params: [],
    fields: [],
    sdk: runtimeSdkExample(name, []),
    curl: runtimeCurlExample(name, [])
  };
}

function runtimeSourcePath(
  entry: RuntimeInterfaceEntry,
  name: string,
  sourceName: string,
  category: string,
  sourceCode: string,
  assetClass: string
): string {
  const menuPath = runtimeMenuPath(entry.menu_path);
  if (menuPath.length > 0) {
    return menuPath.join(" / ");
  }
  if (sourceCode.trim().toLowerCase() === "tdx") {
    return tdxFallbackSourcePath(name, sourceName, category, assetClass).join(" / ");
  }
  if (sourceCode.trim().toLowerCase() === "tdx_ext") {
    return [sourceName || "通达信扩展行情", normalizeCategory(category)].filter(Boolean).join(" / ");
  }
  return [sourceName || sourceNameFromCode(sourceCode), normalizeCategory(category)].filter(Boolean).join(" / ");
}

function runtimeMenuPath(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((part) => stringValue(part, ""))
    .filter(Boolean);
}

function splitGroup(group: string) {
  return group.split("/").map((part) => part.trim()).filter(Boolean);
}

function tdxFallbackSourcePath(name: string, sourceName: string, category: string, assetClass: string): string[] {
  return [
    sourceName || "通达信",
    tdxAssetGroup(assetClass, name),
    normalizeCategory(category)
  ];
}

function tdxAssetGroup(assetClass: string, name: string) {
  const normalizedAsset = assetClass.trim().toLowerCase();
  const normalizedName = name.trim().toLowerCase();
  if (normalizedAsset === "stock" || normalizedName.startsWith("stock_") || normalizedName.startsWith("concept_")) {
    return "股票数据";
  }
  if (normalizedAsset === "index" || normalizedName.startsWith("index_")) {
    return "指数数据";
  }
  if (["etf", "fund"].includes(normalizedAsset) || normalizedName.startsWith("etf_")) {
    return "ETF数据";
  }
  return "其它数据";
}

function navigationPathForCatalogItem(item: CatalogItem): string[] {
  const explicitPath = splitGroup(item.group || item.sourcePath || "");
  if (isKnownSourceRoot(explicitPath[0])) {
    return explicitPath;
  }
  const sourceName = item.sourceNameZh || sourceNameFromCode(item.sourceCode ?? "") || "其它";
  const category = normalizeCategory(item.category ?? explicitPath.at(-1) ?? "");
  return category && category !== sourceName ? [sourceName, category] : [sourceName];
}

function addCatalogPath(roots: Map<string, CatalogTreeNode>, rawPath: string[], itemId: string) {
  const path = rawPath.length > 0 ? rawPath : ["其它"];
  let level = roots;
  let node: CatalogTreeNode | undefined;
  for (const title of path) {
    const normalizedTitle = title.trim() || "其它";
    node = level.get(normalizedTitle);
    if (!node) {
      node = { title: normalizedTitle, items: new Set(), children: new Map() };
      level.set(normalizedTitle, node);
    }
    level = node.children;
  }
  node?.items.add(itemId);
}

function sortedCatalogGroups(nodes: Map<string, CatalogTreeNode>, parentPath: string[]): CatalogGroup[] {
  return Array.from(nodes.values())
    .sort((left, right) => compareCatalogNode(left.title, right.title, parentPath))
    .map((node) => {
      const children = sortedCatalogGroups(node.children, [...parentPath, node.title]);
      const items = Array.from(node.items).sort();
      return {
        title: node.title,
        ...(items.length > 0 ? { items } : {}),
        ...(children.length > 0 ? { children } : {})
      };
    });
}

function compareCatalogNode(left: string, right: string, parentPath: string[]) {
  if (parentPath.length === 0) {
    return compareByOrder(left, right, SOURCE_GROUP_ORDER);
  }
  if (parentPath[0] === "通达信" && parentPath.length === 1) {
    return compareByOrder(left, right, TDX_ASSET_GROUP_ORDER);
  }
  return compareByOrder(left, right, CATEGORY_ORDER);
}

function isKnownSourceRoot(root: string | undefined) {
  return Boolean(root && SOURCE_GROUP_ORDER.includes(root));
}

function sourceNameFromCode(sourceCode: string) {
  const sourceMap: Record<string, string> = {
    tdx: "通达信",
    tdx_ext: "通达信扩展行情",
    exchange: "交易所",
    cninfo: "巨潮",
    tencent: "腾讯财经",
    eastmoney: "东方财富",
    sina: "新浪财经"
  };
  return sourceMap[sourceCode.trim().toLowerCase()] ?? "";
}

function normalizeCategory(category: string) {
  return category.trim() || "其它";
}

function compareByOrder(left: string, right: string, order: string[]) {
  const leftIndex = order.indexOf(left);
  const rightIndex = order.indexOf(right);
  if (leftIndex >= 0 || rightIndex >= 0) {
    return (leftIndex >= 0 ? leftIndex : Number.MAX_SAFE_INTEGER) -
      (rightIndex >= 0 ? rightIndex : Number.MAX_SAFE_INTEGER);
  }
  return left.localeCompare(right, "zh-CN");
}

function runtimeParams(value: unknown): TableRow[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((parameter: RuntimeParameter) => [
    stringValue(parameter.name, ""),
    stringValue(parameter.dtype, "string"),
    parameter.required ? "是" : "否",
    stringValue(parameter.description_zh, stringValue(parameter.description, ""))
  ]);
}

function runtimeFields(value: unknown): TableRow[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((field: RuntimeField) => [
    stringValue(field.name, ""),
    stringValue(field.dtype, "string"),
    stringValue(field.description_zh, stringValue(field.description, ""))
  ]);
}

function runtimeRequiredConfig(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const configs = value
    .map((config: RuntimeRequiredConfig) => {
      const name = stringValue(config.name, "");
      if (!name) {
        return "";
      }
      const kind = stringValue(config.kind, "config");
      const required = config.required ? "必填" : "可选";
      const description = stringValue(config.description, "");
      return `${name} (${kind}, ${required})${description ? `：${description}` : ""}`;
    })
    .filter(Boolean);
  if (configs.length === 0) {
    return [];
  }
  return [...configs, "仅用于提示，AxData 不保存、不注入、不代理第三方源凭据"];
}

function runtimeExampleParams(value: unknown): Record<string, unknown> | undefined {
  if (!isPlainObject(value)) {
    return undefined;
  }
  const request = value.request;
  if (!isPlainObject(request)) {
    return undefined;
  }
  if (isPlainObject(request.params)) {
    const params = { ...request.params };
    return Object.keys(params).length > 0 ? params : undefined;
  }
  const params = Object.fromEntries(
    Object.entries(request).filter(([key]) => !["fields", "options", "persist"].includes(key))
  );
  return Object.keys(params).length > 0 ? params : undefined;
}

function runtimeDataExamples(name: string, fields: TableRow[], entry: RuntimeInterfaceEntry): ReferenceSection[] | undefined {
  const referenceSections = runtimeReferenceSections(entry.reference_sections);
  const response = runtimeExampleResponseRows(entry.example);
  if (!response) {
    return referenceSections.length > 0 ? referenceSections : undefined;
  }
  const rows = response.rows;
  const declaredFields = fields.map((field) => field[0]).filter(Boolean);
  const availableFields = new Set(rows.flatMap((row) => Object.keys(row)));
  const declaredColumns = declaredFields.filter((field) => availableFields.has(field));
  const extraColumns = Array.from(availableFields).filter((field) => !declaredColumns.includes(field));
  const columns = declaredColumns.length > 0
    ? [...declaredColumns, ...extraColumns]
    : extraColumns.length > 0
      ? extraColumns
      : declaredFields;
  return [
    ...referenceSections,
    {
      id: `${name}-runtime-example`,
      title: "插件真实样例",
      icon: Table2,
      note: "来自插件接口目录里的静态 example.response；页面打开不会再次请求源端。",
      columns,
      rows: rows.map((row) => columns.map((column) => formatTableCell(row[column])))
    }
  ];
}

function runtimeReferenceSections(value: unknown): ReferenceSection[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const sections: ReferenceSection[] = [];
  for (const section of value as RuntimeReferenceSection[]) {
    const id = stringValue(section.id, "");
    const title = stringValue(section.title, "");
    const columns = runtimeStringList(section.columns);
    const rows = runtimeStringRows(section.rows);
    if (!id || !title || columns.length === 0) {
      continue;
    }
    sections.push({
      id,
      title,
      icon: FileText,
      note: stringValue(section.note, ""),
      columns,
      rows
    });
  }
  return sections;
}

function runtimeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => stringValue(item, "")).filter(Boolean);
}

function runtimeStringRows(value: unknown): TableRow[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(Array.isArray)
    .map((row) => row.map((cell) => formatTableCell(cell)));
}

function runtimeExampleResponseRows(value: unknown): { rows: Array<Record<string, unknown>> } | undefined {
  if (!isPlainObject(value)) {
    return undefined;
  }
  const response = value.response;
  if (Array.isArray(response)) {
    return { rows: response.filter(isPlainObject) };
  }
  if (!isPlainObject(response)) {
    return undefined;
  }
  const data = response.data;
  if (Array.isArray(data)) {
    return { rows: data.filter(isPlainObject) };
  }
  return undefined;
}

function normalizedCollection(value: unknown): { supported: boolean; defaultProfile: string | null } {
  if (value && typeof value === "object" && "supported" in value) {
    const collection = value as { supported?: unknown; default_profile?: unknown };
    return {
      supported: Boolean(collection.supported),
      defaultProfile: stringValueOrNull(collection.default_profile)
    };
  }
  return { supported: false, defaultProfile: null };
}

function iconForRuntimeEntry(entry: RuntimeInterfaceEntry): LucideIcon {
  const sourceCode = stringValue(entry.source_code, "");
  const assetClass = stringValue(entry.asset_class, "");
  const name = runtimeEntryName(entry);
  if (sourceCode === "cninfo") return FileText;
  if (sourceCode === "exchange") return Landmark;
  if (sourceCode === "tencent" || sourceCode === "eastmoney" || sourceCode === "sina") return Radio;
  if (assetClass === "index") return LineChart;
  if (assetClass === "etf" || assetClass === "fund") return BriefcaseBusiness;
  if (assetClass === "bond") return CircleDollarSign;
  if (assetClass === "fx") return BarChart3;
  if (name.includes("kline")) return CandlestickChart;
  if (name.includes("realtime")) return Activity;
  return Building2;
}

function runtimeSdkExample(name: string, params: TableRow[], exampleParams?: Record<string, unknown>) {
  const firstParam = params.find((row) => row[2] === "是")?.[0];
  const exampleEntries = Object.entries(exampleParams ?? {});
  const paramLine = exampleEntries.length > 0
    ? exampleEntries.map(([key, value]) => `    ${key}=${formatPythonLiteral(value)},`).join("\n")
    : firstParam
      ? `    ${firstParam}=\"000001.SZ\",`
      : "";
  return `import axdata as ax

client = ax.AxDataClient()
df = client.call(
    "${name}",
${paramLine}
)
print(df.head())`;
}

function runtimeCurlExample(name: string, params: TableRow[], exampleParams?: Record<string, unknown>) {
  const firstParam = params.find((row) => row[2] === "是")?.[0];
  const paramsJson = JSON.stringify(exampleParams ?? (firstParam ? { [firstParam]: "000001.SZ" } : {}));
  return `curl -X POST http://127.0.0.1:8666/v1/request/${name} \\
  -H "Content-Type: application/json" \\
  -d '{"params":${paramsJson},"fields":null}'`;
}

function firstField(fields: TableRow[]) {
  return fields[0]?.[0];
}

function stringValue(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function stringValueOrNull(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function formatTableCell(value: unknown): string {
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

function formatPythonLiteral(value: unknown): string {
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  if (Array.isArray(value)) {
    return `[${value.map(formatPythonLiteral).join(", ")}]`;
  }
  if (value === null || value === undefined) {
    return "None";
  }
  return JSON.stringify(value);
}
