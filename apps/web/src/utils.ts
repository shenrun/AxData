import { catalogItems } from "./data/catalog";
import type {
  CatalogGroup,
  CatalogItem,
  IngestionPlan,
  ResolvedCatalogGroup,
  RuntimeConfig,
  SourceFilterOption,
  TableRow
} from "./types";

const SOURCE_FILTER_ORDER = ["tdx", "exchange", "eastmoney", "cninfo", "tencent", "sina"];

export function matchesCatalogItem(item: CatalogItem, normalizedQuery: string) {
  if (!normalizedQuery) {
    return true;
  }
  const haystack = [
    item.group,
    item.sourceNameZh,
    item.sourceCode,
    item.title,
    item.name,
    item.path,
    item.summary,
    ...item.fields.flat(),
    ...item.params.flat()
  ].join(" ").toLowerCase();
  return haystack.includes(normalizedQuery);
}

export function sourceFilterOptions(items: CatalogItem[]): SourceFilterOption[] {
  const bySource = new Map<string, { label: string; count: number }>();
  for (const item of items) {
    const code = item.sourceCode ?? "";
    if (!code) {
      continue;
    }
    const existing = bySource.get(code);
    if (existing) {
      existing.count += 1;
    } else {
      bySource.set(code, {
        label: item.sourceNameZh || code,
        count: 1
      });
    }
  }
  return [
    { code: "all", label: "全部", count: items.length },
    ...Array.from(bySource.entries())
      .sort(([leftCode, left], [rightCode, right]) =>
        compareSourceFilterOption(leftCode, left.label, rightCode, right.label)
      )
      .map(([code, option]) => ({ code, ...option }))
  ];
}

export function compactCollectorTaskTitle(title: string | null | undefined, fallback = "") {
  const value = String(title || fallback || "").trim();
  if (value.length > 2 && value.endsWith("采集")) {
    return value.slice(0, -"采集".length);
  }
  return value;
}

export function compactCollectorPluginTitle(title: string | null | undefined, fallback = "") {
  const value = String(title || fallback || "").trim();
  if (value.length > 4 && value.endsWith("采集插件")) {
    return value.slice(0, -"采集插件".length);
  }
  return value;
}

function compareSourceFilterOption(
  leftCode: string,
  leftLabel: string,
  rightCode: string,
  rightLabel: string
) {
  const leftIndex = SOURCE_FILTER_ORDER.indexOf(leftCode);
  const rightIndex = SOURCE_FILTER_ORDER.indexOf(rightCode);
  if (leftIndex >= 0 || rightIndex >= 0) {
    return (leftIndex >= 0 ? leftIndex : Number.MAX_SAFE_INTEGER) -
      (rightIndex >= 0 ? rightIndex : Number.MAX_SAFE_INTEGER);
  }
  return leftLabel.localeCompare(rightLabel, "zh-CN");
}

export function makeExampleIngestionPlan(item: CatalogItem): IngestionPlan {
  return {
    id: item.id,
    task: `${item.name}.sync`,
    schedule: "每天 22:00",
    timezone: "Asia/Shanghai",
    mode: "按接口口径增量采集",
    writePolicy: "raw 每次保存；staging 标准化；core 按主键覆盖或追加",
    output: `data/core/${item.name}.parquet`,
    status: "example",
    summary: `${item.title} 的采集配置会和接口目录保持一致。后续接入真实数据后，这里用于管理口径、调度、清洗规则、写入策略和质量检查。`,
    inputs: [
      [item.name, item.title, `data/core/${item.name}.parquet`, "Parquet"],
      ["字段契约", item.key, "AxData schema", "表结构"],
      ["调度窗口", "交易日晚间刷新", "每天 22:00", "Asia/Shanghai"]
    ],
    pipeline: [
      ["raw", "保存原始响应或原始文件", "用于本地追溯和重放"],
      ["staging", "字段对齐、类型转换、日期标准化", `统一到 ${item.name} schema`],
      ["core", "写入标准口径文件", `data/core/${item.name}.parquet`],
      ["quality", "执行非空、重复、日期范围和主键校验", "异常进入任务日志"]
    ],
    settings: [
      ["enabled", "false", "真实数据接入前默认关闭"],
      ["schedule", "0 22 * * *", "每天 22:00"],
      ["timezone", "Asia/Shanghai", "本地交易时区"],
      ["interface", item.name, "接口名就是口径"],
      ["output", `data/core/${item.name}.parquet`, "core 层标准文件"],
      ["write_mode", "upsert", "按表主键写入"]
    ],
    code: `task: ${item.name}.sync
schedule: "0 22 * * *"
timezone: Asia/Shanghai
enabled: false
interface: ${item.name}
write:
  raw: always
  staging: normalize
  core: data/core/${item.name}.parquet
quality:
  primary_key: "${item.key}"`
  };
}

export function resolveCatalogGroups(
  groups: CatalogGroup[],
  normalizedQuery: string,
  items: CatalogItem[] = catalogItems,
  parentKey = "",
  parentMatched = false
): ResolvedCatalogGroup[] {
  const catalogById = new Map(items.map((item) => [item.id, item]));
  return groups
    .map((group) => {
      const key = parentKey ? `${parentKey}/${group.title}` : group.title;
      const groupMatched = parentMatched || !normalizedQuery || group.title.toLowerCase().includes(normalizedQuery);
      const docs = (group.items ?? [])
        .map((id) => catalogById.get(id))
        .filter((item): item is CatalogItem => Boolean(item))
        .filter((item) => groupMatched || matchesCatalogItem(item, normalizedQuery));
      const children = resolveCatalogGroups(group.children ?? [], normalizedQuery, items, key, groupMatched);

      return {
        title: group.title,
        key,
        docs,
        children,
        isEmpty: docs.length === 0 && children.length === 0
      };
    })
    .filter((group, index) => {
      const sourceGroup = groups[index];
      const keepEmpty =
        Boolean(sourceGroup.keepWhenEmpty) &&
        (!normalizedQuery || sourceGroup.title.toLowerCase().includes(normalizedQuery));
      return group.docs.length > 0 || group.children.length > 0 || keepEmpty;
    });
}

export function columnsForRows(rows: TableRow[]) {
  const columnCount = Math.max(2, ...rows.map((row) => row.length));
  if (columnCount === 2) {
    return ["项目", "说明"];
  }
  if (columnCount === 3) {
    return ["项目", "说明", "备注"];
  }
  return ["项目", "说明", "补充", "状态"];
}

export function formatAuthState(config: RuntimeConfig | null) {
  if (!config) {
    return "unknown";
  }
  return config.auth_enabled ? "enabled" : "local open";
}
