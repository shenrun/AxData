import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const python = process.platform === "win32"
  ? join(repoRoot, ".venv", "Scripts", "python.exe")
  : join(repoRoot, ".venv", "bin", "python");

const tempDir = mkdtempSync(join(tmpdir(), "axdata-web-catalog-"));

try {
  const runtimeEnv = runtimeCatalogEnv(tempDir);
  const runtimeEntries = loadRuntimeEntries(runtimeEnv);
  const entriesPath = join(tempDir, "runtime-entries.json");
  const entryPath = join(tempDir, "check-runtime-catalog.ts");
  const bundlePath = join(tempDir, "check-runtime-catalog.mjs");
  writeFileSync(entriesPath, JSON.stringify(runtimeEntries), "utf8");
  writeFileSync(entryPath, checkSource(entryPath, entriesPath), "utf8");

  const buildArgs = [
    "--prefix",
    join(repoRoot, "apps", "web"),
    "exec",
    "esbuild",
    "--",
    entryPath,
    "--bundle",
    "--platform=node",
    "--format=esm",
    `--outfile=${bundlePath}`,
    "--log-level=warning"
  ];
  const build = spawnSync(npmCommand(), npmArgs(buildArgs), {
    cwd: repoRoot,
    encoding: "utf8"
  });
  if (build.error) {
    throw build.error;
  }
  if (build.stdout) {
    process.stdout.write(build.stdout);
  }
  if (build.stderr) {
    process.stderr.write(build.stderr);
  }
  if (build.status !== 0) {
    process.exit(build.status ?? 1);
  }

  const result = spawnSync("node", [bundlePath], {
    cwd: repoRoot,
    encoding: "utf8"
  });
  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
} finally {
  rmSync(tempDir, { recursive: true, force: true });
}

function runtimeCatalogEnv(rootDir) {
  const dataDir = join(rootDir, "data");
  const metadataDir = join(rootDir, "metadata");
  const pluginRoot = join(rootDir, "plugins");
  const pluginConfigPath = join(metadataDir, "plugins.json");
  mkdirSync(metadataDir, { recursive: true });
  writeFileSync(pluginConfigPath, JSON.stringify({
    version: 1,
    enabled_provider_ids: ["axdata.source.tdx_external"],
    disabled_provider_ids: [],
    provider_overrides: {}
  }), "utf8");
  return {
    ...process.env,
    AXDATA_DATA_DIR: dataDir,
    AXDATA_PLUGIN_CONFIG_PATH: pluginConfigPath,
    AXDATA_PLUGIN_INSTALL_ROOT: pluginRoot
  };
}

function loadRuntimeEntries(env) {
  const code = [
    "import json",
    "from axdata_core.provider_catalog import list_registry_interface_dicts",
    "print(json.dumps(list(list_registry_interface_dicts()), ensure_ascii=True))"
  ].join("\n");
  const result = spawnSync(python, ["-c", code], {
    cwd: repoRoot,
    env,
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024
  });
  if (result.status !== 0) {
    if (result.stdout) {
      process.stdout.write(result.stdout);
    }
    if (result.stderr) {
      process.stderr.write(result.stderr);
    }
    throw new Error("failed to load runtime interface registry");
  }
  return JSON.parse(result.stdout);
}

function checkSource(entryPath, entriesPath) {
  const normalizedEntriesPath = entriesPath.replaceAll("\\", "\\\\");
  const normalizedToolsPagePath = join(repoRoot, "apps", "web", "src", "pages", "ToolsPage.tsx").replaceAll("\\", "\\\\");
  const catalogImport = relativeImport(entryPath, join(repoRoot, "apps", "web", "src", "data", "catalog", "index.ts"));
  const runtimeCatalogImport = relativeImport(entryPath, join(repoRoot, "apps", "web", "src", "runtimeCatalog.ts"));
  return `
import { readFileSync } from "node:fs";
import { catalogItems } from "${catalogImport}";
import { mergeRuntimeCatalogItems, runtimeNavGroups } from "${runtimeCatalogImport}";

const runtimeEntries = JSON.parse(readFileSync("${normalizedEntriesPath}", "utf8"));
const toolsPageSource = readFileSync("${normalizedToolsPagePath}", "utf8");
const items = mergeRuntimeCatalogItems(catalogItems, runtimeEntries);
const navGroups = runtimeNavGroups(items);
const errors = [];
const runtimeIds = runtimeEntries.map((entry) => entry.name);
const itemIds = items.map((item) => item.id);
const navIds = collectNavIds(navGroups);
const navIdSet = new Set(navIds);
const runtimeIdSet = new Set(runtimeIds);
const staticStreamIds = items
  .filter((item) => item.path?.startsWith("/v1/stream/"))
  .map((item) => item.id);
const staticStreamIdSet = new Set(staticStreamIds);
const duplicateIds = duplicates(navIds);
const missingIds = runtimeIds.filter((id) => !navIdSet.has(id));
const extraIds = navIds.filter((id) => !runtimeIdSet.has(id) && !staticStreamIdSet.has(id));
const topGroups = navGroups.map((group) => group.title);
const englishOnlySummaries = items
  .filter((item) => item.path?.startsWith("/v1/request/"))
  .filter((item) => hasLatin(item.summary) && !hasCjk(item.summary))
  .map((item) => item.id);

assert(runtimeEntries.length >= 100, "expected at least 100 runtime interfaces, got " + runtimeEntries.length);
assert(items.length === runtimeEntries.length + staticStreamIds.length, "catalog item count does not match runtime entries plus static stream items");
assert(new Set(itemIds).size === itemIds.length, "catalog items contain duplicate ids");
assert(navIds.length === runtimeIds.length + staticStreamIds.length, "nav item count does not match runtime entries plus static stream items");
assert(duplicateIds.length === 0, "nav contains duplicate ids: " + duplicateIds.join(", "));
assert(missingIds.length === 0, "nav is missing runtime ids: " + missingIds.join(", "));
assert(extraIds.length === 0, "nav contains non-runtime/non-stream ids: " + extraIds.join(", "));
assert(englishOnlySummaries.length === 0, "runtime summaries must be Chinese display text, got English-only summaries: " + englishOnlySummaries.join(", "));

for (const source of ["通达信", "交易所", "东方财富", "巨潮", "腾讯财经", "新浪财报"]) {
  assert(topGroups.includes(source), "missing source root: " + source);
}
for (const oldRoot of ["股票", "ETF", "指数", "公告与研报", "财务与 F10", "短线与主题", "实时与盘口"]) {
  assert(!topGroups.includes(oldRoot), "old business root still present: " + oldRoot);
}

const tdx = navGroups.find((group) => group.title === "通达信");
assert(Boolean(tdx), "missing TDX root");
const tdxChildren = tdx?.children?.map((group) => group.title) ?? [];
for (const assetGroup of ["股票数据", "指数数据", "ETF数据"]) {
  assert(tdxChildren.includes(assetGroup), "missing TDX asset group: " + assetGroup);
}

const stockData = tdx?.children?.find((group) => group.title === "股票数据");
const stockCategories = stockData?.children?.map((group) => group.title) ?? [];
for (const category of ["实时数据", "短线数据", "行情数据", "竞价数据", "财务数据", "F10数据"]) {
  assert(stockCategories.includes(category), "missing TDX stock category: " + category);
}

assert(Boolean(findPath(navGroups, ["通达信", "指数数据", "实时数据"], "index_realtime_snapshot_tdx")), "missing TDX index realtime path");
assert(Boolean(findPath(navGroups, ["通达信", "指数数据", "行情数据"], "index_kline_tdx")), "missing TDX index market path");
assert(Boolean(findPath(navGroups, ["通达信", "ETF数据", "实时数据"], "etf_realtime_snapshot_tdx")), "missing TDX ETF realtime path");
assert(Boolean(findPath(navGroups, ["通达信", "ETF数据", "行情数据"], "etf_kline_tdx")), "missing TDX ETF market path");
assert(Boolean(findPath(navGroups, ["通达信", "ETF数据", "竞价数据"], "etf_auction_process_tdx")), "missing TDX ETF auction path");
assert(Boolean(findPath(navGroups, ["东方财富", "研报数据"], "eastmoney_research_reports")), "missing Eastmoney source/category path");
assert(Boolean(findPath(navGroups, ["交易所", "基础数据"], "stock_trade_calendar_exchange")), "missing Exchange source/category path");

const sampleItems = Object.fromEntries(items
  .filter((item) => [
    "stock_kline_daily_tdx",
    "index_realtime_snapshot_tdx",
    "stock_intraday_today_tdx",
    "etf_auction_process_tdx",
    "stock_trade_calendar_exchange",
    "cninfo_announcements",
    "eastmoney_research_reports"
  ].includes(item.id))
  .map((item) => [item.id, item]));
assert(sampleItems.stock_kline_daily_tdx?.sourcePath === "通达信 / 股票数据 / 行情数据", "TDX stock sourcePath was not restored");
assert(sampleItems.index_realtime_snapshot_tdx?.sourcePath === "通达信 / 指数数据 / 实时数据", "TDX index sourcePath was not restored");
assert(sampleItems.etf_auction_process_tdx?.sourcePath === "通达信 / ETF数据 / 竞价数据", "TDX ETF sourcePath was not restored");
assert(sampleItems.eastmoney_research_reports?.sourceNameZh === "东方财富", "sourceNameZh was not preserved");
assert(sampleItems.eastmoney_research_reports?.sourceCode === "eastmoney", "sourceCode was not preserved");
assert(sampleItems.stock_kline_daily_tdx?.collectionSupported === true, "collectable TDX item did not keep collectionSupported");
assert(sampleItems.stock_intraday_today_tdx?.collectionSupported === false, "source-only TDX item should not be collectable");
assert(sampleItems.stock_intraday_today_tdx?.pluginStatus === "enabled", "source-only TDX item did not keep plugin status");
assert(Boolean(sampleItems.stock_kline_daily_tdx) && !("callModes" in sampleItems.stock_kline_daily_tdx), "runtime request item kept old static callModes");
assert(Boolean(sampleItems.stock_trade_calendar_exchange) && !("remoteSdk" in sampleItems.stock_trade_calendar_exchange), "runtime request item kept old static remoteSdk");
assert(sampleItems.cninfo_announcements?.summary === "按股票和日期范围临时获取巨潮公告元信息。", "built-in cninfo display summary was not projected");
assert(sampleItems.stock_trade_calendar_exchange?.paramsExample?.includes('client.call("stock_trade_calendar_exchange", year=2026)'), "built-in exchange params example was not projected");
assert(!toolsPageSource.includes("../data/catalog/tdx"), "collector page imported old static TDX catalog");
assert(!toolsPageSource.includes("../data/catalog/exchange"), "collector page imported old static exchange catalog");
assert(!toolsPageSource.includes("SOURCE_CATALOG_ITEMS"), "collector page kept old static source catalog lookup");

if (errors.length > 0) {
  for (const error of errors) {
    console.error("web runtime catalog validation failed:", error);
  }
  process.exit(1);
}

console.log(JSON.stringify({
  entryCount: runtimeEntries.length,
  itemCount: items.length,
  navItemCount: navIds.length,
  duplicateCount: duplicateIds.length,
  missingCount: missingIds.length,
  staticStreamIds,
  topGroups,
  tdxChildren,
  stockCategories
}, null, 2));

function assert(condition, message) {
  if (!condition) {
    errors.push(message);
  }
}

function collectNavIds(groups) {
  return groups.flatMap((group) => [
    ...(group.items ?? []),
    ...collectNavIds(group.children ?? [])
  ]);
}

function duplicates(values) {
  const seen = new Set();
  const repeated = new Set();
  for (const value of values) {
    if (seen.has(value)) {
      repeated.add(value);
    }
    seen.add(value);
  }
  return Array.from(repeated).sort();
}

function hasCjk(value) {
  return /[\u4e00-\u9fff]/.test(String(value ?? ""));
}

function hasLatin(value) {
  return /[A-Za-z]/.test(String(value ?? ""));
}

function findPath(groups, path, itemId) {
  const [head, ...tail] = path;
  const group = groups.find((candidate) => candidate.title === head);
  if (!group) {
    return null;
  }
  if (tail.length === 0) {
    return (group.items ?? []).includes(itemId) ? group : null;
  }
  return findPath(group.children ?? [], tail, itemId);
}
`;
}

function relativeImport(fromFile, toFile) {
  const specifier = relative(dirname(fromFile), toFile).replaceAll("\\", "/");
  return specifier.startsWith(".") ? specifier : `./${specifier}`;
}

function npmCommand() {
  return process.platform === "win32" ? "cmd.exe" : "npm";
}

function npmArgs(args) {
  if (process.platform === "win32") {
    return ["/d", "/s", "/c", "npm", ...args];
  }
  return args;
}
