import { useCallback, useEffect, useMemo, useState } from "react";
import type { KeyboardEvent } from "react";
import { BookOpen, Code2, Database, Download, Search, ServerCog, type LucideIcon } from "lucide-react";

import { DEFAULT_API_BASE } from "./config";
import { apiFetch } from "./api";
import {
  catalogItems,
  emptyCatalogItem,
  manualGroups,
  manualPages,
  sectionMeta,
  sectionNav,
  settingGroups,
  settingPages
} from "./data/catalog";
import { CollectorSidebar, DataCatalogSidebar, InfoSidebar } from "./components/sidebars";
import { InfoPageView, RuntimePanel, StatusIcon, serviceLabel } from "./components/common";
import { MarkdownDocument } from "./components/MarkdownDocument";
import { DataBrowserPage } from "./pages/DataBrowserPage";
import { DataInterfacesPage } from "./pages/DataInterfacesPage";
import { DiagnosticsPage, PluginManagementPage, SettingsPage, ToolsPage } from "./pages/ToolsPage";
import axdataDevelopmentStandardsMarkdown from "../../../docs/axdata-development-standards.md?raw";
import axpPackagingGuideMarkdown from "../../../docs/axp-packaging-guide.md?raw";
import collectorPluginDevelopmentMarkdown from "../../../docs/collector-plugin-development.md?raw";
import datasetAndDuckdbMarkdown from "../../../docs/dataset-and-duckdb.md?raw";
import pluginInstallManagementMarkdown from "../../../docs/plugin-install-management.md?raw";
import pluginDevelopmentMarkdown from "../../../docs/plugin-development.md?raw";
import sourceProviderDevelopmentMarkdown from "../../../docs/source-provider-development.md?raw";
import uiStandardsMarkdown from "../../../docs/ui-standards.md?raw";
import { mergeRuntimeCatalogItems, runtimeNavGroups } from "./runtimeCatalog";
import type { RuntimeInterfaceEntry } from "./runtimeCatalog";
import type {
  ActiveSection,
  CatalogItem,
  CollectorStatus,
  CollectorPluginGroup,
  HealthPayload,
  InfoPage,
  ProviderStatus,
  RuntimeConfig,
  ServiceState
} from "./types";
import {
  compactCollectorPluginTitle,
  compactCollectorTaskTitle,
  resolveCatalogGroups,
  sourceFilterOptions
} from "./utils";

function App() {
  const initialCollectorRoute = readInitialCollectorRoute();
  const [activeSection, setActiveSection] = useState<ActiveSection>(initialCollectorRoute ? "tools" : "manual");
  const [activeManualId, setActiveManualId] = useState("quickstart");
  const [activeId, setActiveId] = useState(initialCollectorRoute?.collectorId ?? "stock_codes_tdx");
  const [activeSettingId, setActiveSettingId] = useState("access");
  const [query, setQuery] = useState("");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [highlightedSuggestionIndex, setHighlightedSuggestionIndex] = useState(0);
  const [serviceState, setServiceState] = useState<ServiceState>("checking");
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [runtimeConfig, setRuntimeConfig] = useState<RuntimeConfig | null>(null);
  const [providerStatuses, setProviderStatuses] = useState<ProviderStatus[]>([]);
  const [collectorCatalog, setCollectorCatalog] = useState<CollectorStatus[]>([]);
  const [activeCollectorPluginId, setActiveCollectorPluginId] = useState(initialCollectorRoute?.pluginId ?? "");
  const [runtimeInterfaceEntries, setRuntimeInterfaceEntries] = useState<RuntimeInterfaceEntry[]>([]);
  const [sourceFilter, setSourceFilter] = useState("all");
  const apiBase = DEFAULT_API_BASE;
  const [lastChecked, setLastChecked] = useState("--");

  const effectiveCatalogItems = useMemo(
    () => mergeRuntimeCatalogItems(catalogItems, runtimeInterfaceEntries),
    [runtimeInterfaceEntries]
  );
  const effectiveNavGroups = useMemo(
    () => runtimeNavGroups(effectiveCatalogItems),
    [effectiveCatalogItems]
  );
  const activeDoc = useMemo(
    () => effectiveCatalogItems.find((item) => item.id === activeId) ?? emptyCatalogItem,
    [activeId, effectiveCatalogItems]
  );
  const activeManualPage = useMemo(
    () => manualPages.find((item) => item.id === activeManualId) ?? manualPages[0],
    [activeManualId]
  );
  const activeSettingPage = useMemo(
    () => settingPages.find((item) => item.id === activeSettingId) ?? settingPages[0],
    [activeSettingId]
  );
  const filteredGroups = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const sourceFilteredItems = sourceFilter === "all"
      ? effectiveCatalogItems
      : effectiveCatalogItems.filter((item) => item.sourceCode === sourceFilter);
    return resolveCatalogGroups(effectiveNavGroups, normalizedQuery, sourceFilteredItems);
  }, [effectiveCatalogItems, effectiveNavGroups, query, sourceFilter]);
  const interfaceSourceOptions = useMemo(
    () => sourceFilterOptions(effectiveCatalogItems),
    [effectiveCatalogItems]
  );
  const collectorItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return collectorCatalog
      .filter((item) => matchesCollectorItem(item, normalizedQuery))
      .sort(compareCollectorCatalogItems);
  }, [collectorCatalog, query]);
  const collectorPluginGroups = useMemo(
    () => buildCollectorPluginGroups(collectorItems),
    [collectorItems]
  );
  const fullCollectorPluginGroups = useMemo(
    () => buildCollectorPluginGroups([...collectorCatalog].sort(compareCollectorCatalogItems)),
    [collectorCatalog]
  );
  const activeToolsDoc = useMemo(() => {
    const activeInCatalog = collectorCatalog.find((item) => collectorId(item) === activeId);
    if (activeInCatalog) {
      return activeInCatalog;
    }
    const activePluginGroup = collectorPluginGroups.find((group) => group.pluginId === activeCollectorPluginId);
    return activePluginGroup?.items[0] ?? collectorItems[0] ?? collectorCatalog[0] ?? null;
  }, [activeCollectorPluginId, activeId, collectorCatalog, collectorItems, collectorPluginGroups]);
  const activeToolsPluginGroup = useMemo(() => {
    const activePluginId = activeToolsDoc ? collectorPluginId(activeToolsDoc) : activeCollectorPluginId;
    return fullCollectorPluginGroups.find((group) => group.pluginId === activePluginId) ?? fullCollectorPluginGroups[0] ?? null;
  }, [activeCollectorPluginId, activeToolsDoc, fullCollectorPluginGroups]);

  const searchSuggestions = useMemo(() => {
    const sourceFilteredItems = sourceFilter === "all" || activeSection === "tools"
      ? effectiveCatalogItems
      : effectiveCatalogItems.filter((item) => item.sourceCode === sourceFilter);
    return activeSection === "tools"
      ? buildCollectorSearchSuggestions(query, collectorCatalog)
      : buildSearchSuggestions(query, sourceFilteredItems);
  }, [activeSection, collectorCatalog, effectiveCatalogItems, query, sourceFilter]);

  const showSearchSuggestions =
    (activeSection === "interfaces" || activeSection === "tools") &&
    isSearchFocused &&
    query.trim().length > 0;

  useEffect(() => {
    setHighlightedSuggestionIndex(0);
  }, [query]);

  useEffect(() => {
    const controller = new AbortController();

    async function checkHealth(signal?: AbortSignal) {
      setServiceState("checking");
      try {
        const response = await apiFetch(`${apiBase}/health`, {
          signal,
          headers: { Accept: "application/json" }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = (await response.json()) as HealthPayload;
        setHealth(data);

        try {
          const configResponse = await apiFetch(`${apiBase}/v1/config`, {
            signal,
            headers: { Accept: "application/json" }
          });
          if (configResponse.ok) {
            const payload = (await configResponse.json()) as { data?: RuntimeConfig } & RuntimeConfig;
            setRuntimeConfig(payload.data ?? payload);
          } else {
            setRuntimeConfig(null);
          }
        } catch {
          setRuntimeConfig(null);
        }
        setServiceState("online");
      } catch {
        if (!signal?.aborted) {
          setHealth(null);
          setRuntimeConfig(null);
          setServiceState("offline");
        }
      } finally {
        if (!signal?.aborted) {
          setLastChecked(new Intl.DateTimeFormat("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
          }).format(new Date()));
        }
      }
    }

    checkHealth(controller.signal);
    const timer = window.setInterval(() => checkHealth(controller.signal), 30000);

    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [apiBase]);

  const refreshRuntimeStatus = useCallback(async () => {
    try {
      const [healthResponse, configResponse] = await Promise.all([
        apiFetch(`${apiBase}/health`, { headers: { Accept: "application/json" } }),
        apiFetch(`${apiBase}/v1/config`, { headers: { Accept: "application/json" } })
      ]);
      if (healthResponse.ok) {
        setHealth((await healthResponse.json()) as HealthPayload);
      }
      if (configResponse.ok) {
        const payload = (await configResponse.json()) as { data?: RuntimeConfig } & RuntimeConfig;
        setRuntimeConfig(payload.data ?? payload);
      }
      setServiceState(healthResponse.ok ? "online" : "offline");
      setLastChecked(new Intl.DateTimeFormat("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }).format(new Date()));
    } catch {
      setHealth(null);
      setRuntimeConfig(null);
      setServiceState("offline");
    }
  }, [apiBase]);

  const loadRuntimeCatalogs = useCallback(async (signal?: AbortSignal) => {
    try {
      const interfacesResponse = await apiFetch(`${apiBase}/v1/request/interfaces`, {
        signal,
        headers: { Accept: "application/json" }
      });
      if (interfacesResponse.ok) {
        const payload = await interfacesResponse.json();
        setRuntimeInterfaceEntries(Array.isArray(payload.data) ? payload.data : []);
      } else {
        setRuntimeInterfaceEntries([]);
      }

      const providersResponse = await apiFetch(`${apiBase}/v1/plugins/providers`, {
        signal,
        headers: { Accept: "application/json" }
      });
      if (providersResponse.ok) {
        const payload = await providersResponse.json();
        setProviderStatuses(Array.isArray(payload.data) ? payload.data : []);
      } else {
        setProviderStatuses([]);
      }

      const response = await apiFetch(`${apiBase}/v1/plugins/collectors`, {
        signal,
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json();
      const rows = Array.isArray(payload.data) ? payload.data : [];
      setCollectorCatalog(rows);
    } catch {
      if (!signal?.aborted) {
        setRuntimeInterfaceEntries([]);
        setProviderStatuses([]);
        setCollectorCatalog([]);
      }
    }
  }, [apiBase]);

  useEffect(() => {
    const controller = new AbortController();

    loadRuntimeCatalogs(controller.signal);
    return () => controller.abort();
  }, [loadRuntimeCatalogs]);

  useEffect(() => {
    if (activeSection !== "tools" || !activeToolsDoc) {
      return;
    }
    syncCollectorRoute(collectorPluginId(activeToolsDoc), collectorId(activeToolsDoc));
  }, [activeSection, activeToolsDoc]);

  function selectSection(section: ActiveSection) {
    setActiveSection(section);
    if (section === "interfaces" && !effectiveCatalogItems.some((item) => item.id === activeId)) {
      setActiveId(effectiveCatalogItems[0]?.id ?? emptyCatalogItem.id);
    }
    if (section === "tools" && !collectorCatalog.some((item) => collectorId(item) === activeId)) {
      const activePluginCollector = activeCollectorPluginId
        ? collectorCatalog.find((item) => collectorPluginId(item) === activeCollectorPluginId)
        : null;
      const firstCollector = activePluginCollector ?? collectorCatalog[0];
      if (firstCollector) {
        setActiveId(collectorId(firstCollector));
        setActiveCollectorPluginId(collectorPluginId(firstCollector));
      }
    }
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function openCollectorFromPlugin(pluginId?: string, collectorItemId?: string) {
    const pluginCollector = pluginId
      ? collectorCatalog.find((item) => collectorPluginId(item) === pluginId)
      : null;
    const explicitCollector = collectorItemId
      ? collectorCatalog.find((item) => collectorId(item) === collectorItemId)
      : null;
    const fallbackCollector = pluginCollector ?? collectorCatalog[0];
    const nextCollector = explicitCollector ?? fallbackCollector;
    const nextId = nextCollector ? collectorId(nextCollector) : "";
    if (nextId) {
      setActiveId(nextId);
    }
    if (pluginId) {
      setActiveCollectorPluginId(pluginId);
    } else if (nextCollector) {
      setActiveCollectorPluginId(collectorPluginId(nextCollector));
    }
    setActiveSection("tools");
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function selectInterfaceSuggestion(itemId: string) {
    setActiveSection(activeSection === "tools" ? "tools" : "interfaces");
    setActiveId(itemId);
    setQuery("");
    setIsSearchFocused(false);
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function selectSearchSuggestion(suggestion: SearchSuggestion) {
    setActiveId(suggestion.id);
    if (activeSection === "tools") {
      const collector = collectorCatalog.find((item) => collectorId(item) === suggestion.id);
      if (collector) {
        setActiveCollectorPluginId(collectorPluginId(collector));
      }
    }
    setQuery("");
    setIsSearchFocused(false);
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function applySourceFilter(nextSourceFilter: string) {
    setSourceFilter(nextSourceFilter);
    if (nextSourceFilter === "all") {
      return;
    }
    const activeStillVisible = effectiveCatalogItems.some(
      (item) => item.id === activeId && item.sourceCode === nextSourceFilter
    );
    if (!activeStillVisible) {
      const nextItem = effectiveCatalogItems.find((item) => item.sourceCode === nextSourceFilter);
      if (nextItem) {
        setActiveId(nextItem.id);
      }
    }
  }

  function handleSearchKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!showSearchSuggestions || searchSuggestions.length === 0) {
      if (event.key === "Escape") {
        setIsSearchFocused(false);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightedSuggestionIndex((current) =>
        Math.min(current + 1, searchSuggestions.length - 1)
      );
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedSuggestionIndex((current) => Math.max(current - 1, 0));
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      const selected = searchSuggestions[Math.min(highlightedSuggestionIndex, searchSuggestions.length - 1)];
      selectSearchSuggestion(selected);
      return;
    }

    if (event.key === "Escape") {
      setIsSearchFocused(false);
    }
  }

  const section = sectionMeta[activeSection];
  const SectionIcon = section.icon;
  const hasSidebar =
    activeSection === "manual" ||
    activeSection === "interfaces" ||
    activeSection === "tools" ||
    activeSection === "settings";

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#top"
          aria-label="AxData home"
          onClick={(event) => {
            event.preventDefault();
            selectSection("manual");
          }}
        >
          <span className="brand-mark">
            <Database size={26} strokeWidth={2.4} />
          </span>
          <span>
            <strong>AxData</strong>
            <small>开源量化数据库</small>
          </span>
        </a>

        {activeSection === "interfaces" || activeSection === "tools" ? (
          <div
            className="top-search-shell"
            onBlur={(event) => {
              const nextTarget = event.relatedTarget;
              if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
                setIsSearchFocused(false);
              }
            }}
            onFocus={() => setIsSearchFocused(true)}
          >
            <label className="top-search" htmlFor="global-search">
              <Search size={20} />
              <input
                aria-autocomplete="list"
                aria-controls="global-search-suggestions"
                aria-expanded={showSearchSuggestions}
                id="global-search"
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="搜索接口、SDK 方法、字段、表名"
                value={query}
              />
            </label>
            {showSearchSuggestions ? (
              <div
                className="search-suggestions"
                id="global-search-suggestions"
                role="listbox"
              >
                {searchSuggestions.length > 0 ? (
                  searchSuggestions.map((suggestion, index) => {
                    const SuggestionIcon = suggestion.icon;
                    return (
                      <button
                        aria-selected={index === highlightedSuggestionIndex}
                        className={
                          index === highlightedSuggestionIndex
                            ? "search-suggestion active"
                            : "search-suggestion"
                        }
                        key={suggestion.id}
                        onClick={() => selectSearchSuggestion(suggestion)}
                        onMouseDown={(event) => event.preventDefault()}
                        role="option"
                        type="button"
                      >
                          <SuggestionIcon size={16} />
                          <span>
                          <strong>{suggestion.title}</strong>
                          <small>{suggestion.name}</small>
                        </span>
                        <em>{suggestion.group}</em>
                      </button>
                    );
                  })
                ) : (
                  <div className="search-suggestion-empty">没有匹配的接口</div>
                )}
              </div>
            ) : null}
          </div>
        ) : (
          <div className="topbar-context">
            <SectionIcon size={17} />
            <span>{section.title}</span>
          </div>
        )}

        <nav className="topnav" aria-label="Primary navigation">
          {sectionNav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                aria-current={item.id === activeSection ? "page" : undefined}
                className={item.id === activeSection ? "active" : ""}
                key={item.id}
                onClick={() => selectSection(item.id)}
                type="button"
              >
                <Icon size={16} />
                <span>{item.title}</span>
              </button>
            );
          })}
        </nav>

        <div className={`service-chip ${serviceState}`}>
          <StatusIcon state={serviceState} />
          <span>{serviceLabel(serviceState)}</span>
        </div>
      </header>

      <div className={hasSidebar ? "workbench" : "workbench no-sidebar"} id="top">
        {activeSection === "manual" ? (
          <InfoSidebar
            activeId={activeManualPage.id}
            groups={manualGroups}
            heading="开始"
            icon={BookOpen}
            onSelect={setActiveManualId}
          />
        ) : null}
        {activeSection === "interfaces" ? (
          <DataCatalogSidebar
            activeId={activeDoc.id}
            emptyText="没有匹配的接口"
            groups={filteredGroups}
            heading="接口目录"
            icon={Code2}
            onSelect={setActiveId}
            onSourceFilterChange={applySourceFilter}
            sourceFilter={sourceFilter}
            sourceOptions={interfaceSourceOptions}
          />
        ) : null}
        {activeSection === "tools" ? (
          <CollectorSidebar
            activeId={activeToolsDoc ? collectorId(activeToolsDoc) : ""}
            activePluginId={activeToolsPluginGroup?.pluginId ?? ""}
            emptyText="当前没有可用采集任务"
            groups={collectorPluginGroups}
            heading="采集"
            icon={Download}
            onSelect={(collectorItemId) => {
              const collector = collectorCatalog.find((item) => collectorId(item) === collectorItemId);
              if (collector) {
                setActiveCollectorPluginId(collectorPluginId(collector));
              }
              setActiveId(collectorItemId);
            }}
          />
        ) : null}
        {activeSection === "settings" ? (
          <InfoSidebar
            activeId={activeSettingPage.id}
            groups={settingGroups}
            heading="配置"
            icon={ServerCog}
            onSelect={setActiveSettingId}
          />
        ) : null}

        <main className="doc-main">
          {activeSection === "manual" ? (
            <InfoPageView
              aside={
                <RuntimePanel
                  apiBase={apiBase}
                  health={health}
                  lastChecked={lastChecked}
                  runtimeConfig={runtimeConfig}
                />
              }
              lead={shouldShowArchitectureDiagram(activeManualPage.id) ? <AxDataArchitectureDiagram /> : undefined}
              page={activeManualPage}
            >
              {activeManualPage.markdownDoc ? (
                <section className="doc-section markdown-section">
                  <MarkdownDocument source={manualMarkdownSource(activeManualPage.markdownDoc)} />
                </section>
              ) : null}
            </InfoPageView>
          ) : null}
          {activeSection === "interfaces" ? (
            <DataInterfacesPage activeDoc={activeDoc} />
          ) : null}
          {activeSection === "data" ? (
            <DataBrowserPage apiBase={apiBase} onOpenCollector={() => selectSection("tools")} />
          ) : null}
          {activeSection === "tools" ? (
            <ToolsPage
              activeCollector={activeToolsDoc}
              activePluginId={activeToolsPluginGroup?.pluginId ?? activeCollectorPluginId}
              activePluginGroup={activeToolsPluginGroup}
              apiBase={apiBase}
              health={health}
              runtimeCatalogItems={effectiveCatalogItems}
            />
          ) : null}
          {activeSection === "plugins" ? (
            <PluginManagementPage
              apiBase={apiBase}
              collectorCatalog={collectorCatalog}
              onOpenCollector={openCollectorFromPlugin}
              onRuntimeCatalogRefresh={() => loadRuntimeCatalogs()}
              providerStatuses={providerStatuses}
            />
          ) : null}
          {activeSection === "diagnostics" ? (
            <DiagnosticsPage apiBase={apiBase} health={health} runtimeConfig={runtimeConfig} />
          ) : null}
          {activeSection === "settings" ? (
            <SettingsPage
              apiBase={apiBase}
              health={health}
              onRuntimeConfigRefresh={refreshRuntimeStatus}
              page={activeSettingPage}
              runtimeConfig={runtimeConfig}
            />
          ) : null}
        </main>
      </div>
    </div>
  );
}

function manualMarkdownSource(doc: NonNullable<InfoPage["markdownDoc"]>) {
  const docs: Record<NonNullable<InfoPage["markdownDoc"]>, string> = {
    "axdata-development-standards": axdataDevelopmentStandardsMarkdown,
    "plugin-development": pluginDevelopmentMarkdown,
    "source-provider-development": sourceProviderDevelopmentMarkdown,
    "collector-plugin-development": collectorPluginDevelopmentMarkdown,
    "dataset-and-duckdb": datasetAndDuckdbMarkdown,
    "ui-standards": uiStandardsMarkdown,
    "axp-packaging-guide": axpPackagingGuideMarkdown,
    "plugin-install-management": pluginInstallManagementMarkdown
  };
  return docs[doc];
}

function shouldShowArchitectureDiagram(manualPageId: string) {
  return ["quickstart", "architecture", "plugin-development"].includes(manualPageId);
}

function AxDataArchitectureDiagram() {
  return (
    <section className="doc-section architecture-diagram-section" aria-label="AxData 架构图">
      <div className="section-title">
        <Database size={20} />
        <h2>结构图</h2>
      </div>
      <div className="architecture-diagram">
        <div className="architecture-layer">
          <div className="architecture-layer-title">上游来源</div>
          <div className="architecture-row architecture-row-sources">
            <div className="architecture-node source">
              <strong>数据源 Provider</strong>
              <span>声明接口、参数、字段、真实样例和 Adapter</span>
            </div>
            <div className="architecture-node source">
              <strong>本地文件 / 外部服务</strong>
              <span>通达信、交易所、东财、巨潮、CSV、团队自有源</span>
            </div>
          </div>
        </div>

        <div className="architecture-arrow architecture-arrow-wide">↓</div>

        <div className="architecture-split">
          <div className="architecture-lane source-lane">
            <div className="architecture-lane-title">接口临时查询</div>
            <div className="architecture-node registry">
              <strong>ProviderRegistry</strong>
              <span>接口目录和 source_request 路由</span>
            </div>
            <div className="architecture-arrow">↓</div>
            <div className="architecture-node call">
              <strong>源端直取</strong>
              <span>SDK call / HTTP request / Web 接口页调试</span>
            </div>
            <div className="architecture-arrow">↓</div>
            <div className="architecture-node endpoint">
              <strong>即时返回</strong>
              <span>给调用方看结果，不写 data/core</span>
            </div>
            <div className="architecture-note">查一次就是查一次，默认不入库、不创建任务</div>
          </div>

          <div className="architecture-lane collector-lane">
            <div className="architecture-lane-title">采集入库</div>
            <div className="architecture-node registry">
              <strong>CollectorRegistry</strong>
              <span>CollectorSpec / runner_entry / dataset output</span>
            </div>
            <div className="architecture-arrow">↓</div>
            <div className="architecture-node runner">
              <strong>Collector Runner</strong>
              <span>排队、进度、日志、重试、质量规则</span>
            </div>
            <div className="architecture-arrow">↓</div>
            <div className="architecture-node storage">
              <strong>Writer / Quality</strong>
              <span>按数据集声明写文件并记录质量结果</span>
            </div>
            <div className="architecture-note">手动采集或交易日定时采集；采集器独立于接口 Provider</div>
          </div>
        </div>

        <div className="architecture-arrow architecture-arrow-wide">↓</div>
        <div className="architecture-layer">
          <div className="architecture-layer-title">本地数据资产</div>
          <div className="architecture-row architecture-row-data">
            <div className="architecture-node storage">
              <strong>Parquet 主数据</strong>
              <span>data/raw、staging、core、factor；长期事实源</span>
            </div>
            <div className="architecture-node query">
              <strong>DuckDB 查询层</strong>
              <span>直接读 Parquet；查询缓存可删除、可重建</span>
            </div>
            <div className="architecture-node metadata">
              <strong>metadata / logs</strong>
              <span>任务、运行记录、质量摘要、诊断信息</span>
            </div>
          </div>
        </div>

        <div className="architecture-arrow architecture-arrow-wide">↓</div>
        <div className="architecture-layer">
          <div className="architecture-layer-title">使用入口</div>
          <div className="architecture-row architecture-row-users">
            <div className="architecture-node user">
              <strong>本地 Python SDK</strong>
              <span>AxDataClient() 直接用本机数据和本机插件</span>
            </div>
            <div className="architecture-node user">
              <strong>远程 SDK / HTTP API</strong>
              <span>api_base 指向服务器；需要时传 AxData token</span>
            </div>
            <div className="architecture-node user">
              <strong>Web / CLI</strong>
              <span>本机管理、接口调试、采集控制和诊断</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

type SearchSuggestion = {
  id: string;
  title: string;
  name: string;
  group: string;
  icon: LucideIcon;
  score: number;
};

function readInitialCollectorRoute() {
  if (typeof window === "undefined") {
    return null;
  }
  const params = new URLSearchParams(window.location.search);
  const hashText = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : window.location.hash;
  const hashParams = new URLSearchParams(hashText.startsWith("?") ? hashText.slice(1) : hashText);
  const section = params.get("section") || hashParams.get("section");
  const pluginId = params.get("plugin") || hashParams.get("plugin") || "";
  const collectorId = params.get("collector") || hashParams.get("collector") || "";
  if (section !== "tools" && !pluginId && !collectorId) {
    return null;
  }
  return { pluginId, collectorId };
}

function syncCollectorRoute(pluginId: string, collectorItemId: string) {
  if (typeof window === "undefined") {
    return;
  }
  const url = new URL(window.location.href);
  url.searchParams.set("section", "tools");
  url.searchParams.set("plugin", pluginId);
  url.searchParams.set("collector", collectorItemId);
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

function buildSearchSuggestions(
  query: string,
  items: CatalogItem[]
): SearchSuggestion[] {
  const normalizedQuery = normalizeSearchValue(query);
  if (!normalizedQuery) {
    return [];
  }
  return items
    .map((item) => ({
      id: item.id,
      title: item.title,
      name: item.name,
      group: item.group,
      icon: item.icon,
      score: scoreCatalogItem(item, normalizedQuery)
    }))
    .filter((suggestion) => suggestion.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return left.name.localeCompare(right.name);
    })
    .slice(0, 8);
}

function buildCollectorSearchSuggestions(query: string, collectors: CollectorStatus[]): SearchSuggestion[] {
  const normalizedQuery = normalizeSearchValue(query);
  if (!normalizedQuery) {
    return [];
  }
  return collectors
    .map((item) => ({
      id: collectorId(item),
      title: compactCollectorTaskTitle(item.display_name_zh, collectorId(item)),
      name: collectorId(item),
      group: item.collector_plugin_id || item.provider_id || "collector",
      icon: Download,
      score: scoreCollectorItem(item, normalizedQuery)
    }))
    .filter((suggestion) => suggestion.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return left.name.localeCompare(right.name);
    })
    .slice(0, 8);
}

function matchesCollectorItem(item: CollectorStatus, normalizedQuery: string) {
  if (!normalizedQuery) {
    return true;
  }
  return collectorSearchText(item).includes(normalizedQuery);
}

function compareCollectorCatalogItems(left: CollectorStatus, right: CollectorStatus) {
  const leftPlugin = collectorPluginId(left);
  const rightPlugin = collectorPluginId(right);
  if (leftPlugin !== rightPlugin) {
    return leftPlugin.localeCompare(rightPlugin);
  }
  return collectorId(left).localeCompare(collectorId(right));
}

function buildCollectorPluginGroups(items: CollectorStatus[]): CollectorPluginGroup[] {
  const grouped = new Map<string, CollectorStatus[]>();
  items.forEach((item) => {
    const pluginId = collectorPluginId(item);
    grouped.set(pluginId, [...(grouped.get(pluginId) ?? []), item]);
  });

  return [...grouped.entries()]
    .map(([pluginId, pluginItems]) => {
      const sortedItems = [...pluginItems].sort((left, right) => collectorId(left).localeCompare(collectorId(right)));
      const statuses = sortedItems.map((item) => item.collector_plugin_status || item.plugin_status || "enabled");
      const enabled = sortedItems.some((item) => item.enabled);
      return {
        pluginId,
        title: collectorPluginTitle(pluginId, sortedItems),
        sourceCode: firstText(sortedItems.map((item) => item.source_code)),
        sourceNameZh: firstText(sortedItems.map((item) => item.source_name_zh)),
        status: collectorPluginGroupStatus(statuses),
        enabled,
        taskCount: sortedItems.length,
        datasetIds: uniqueText(sortedItems.map((item) => item.dataset_id || "")),
        runnerEntryCount: sortedItems.filter((item) => Boolean(item.runner_entry)).length,
        legacyCount: sortedItems.filter((item) => item.is_legacy).length,
        items: sortedItems
      };
    })
    .sort((left, right) => left.pluginId.localeCompare(right.pluginId));
}

function collectorId(item: CollectorStatus) {
  return item.collector_id || item.collector_name || item.name;
}

function collectorPluginId(item: CollectorStatus) {
  return item.collector_plugin_id || item.provider_id || "unknown";
}

function collectorPluginTitle(pluginId: string, items: CollectorStatus[]) {
  if (pluginId === "axdata.collector.tdx") {
    return "通达信";
  }
  const sourceName = firstText(items.map((item) => item.source_name_zh));
  if (sourceName && sourceName !== "plugin") {
    return compactCollectorPluginTitle(sourceName);
  }
  return pluginId === "unknown" ? "未知" : pluginId;
}

function collectorPluginGroupStatus(statuses: string[]) {
  if (statuses.some((status) => ["failed", "incompatible", "conflict"].includes(status))) {
    return statuses.find((status) => ["failed", "incompatible", "conflict"].includes(status)) || "failed";
  }
  if (statuses.some((status) => ["disabled", "missing", "uninstalled"].includes(status))) {
    return statuses.find((status) => ["disabled", "missing", "uninstalled"].includes(status)) || "disabled";
  }
  if (statuses.some((status) => status === "installed")) {
    return "installed";
  }
  return statuses[0] || "enabled";
}

function firstText(values: Array<string | null | undefined>) {
  return values.find((value) => String(value || "").trim()) || undefined;
}

function uniqueText(values: Array<string | null | undefined>) {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
}

function collectorSearchText(item: CollectorStatus) {
  return [
    item.display_name_zh,
    collectorId(item),
    item.collector_plugin_id,
    item.dataset_id,
    item.provider_id,
    item.source_name_zh,
    item.source_code,
    item.asset_class,
    item.category,
    item.resource_group,
    item.description
  ].join(" ").toLowerCase();
}

function scoreCollectorItem(item: CollectorStatus, query: string) {
  const id = normalizeSearchValue(collectorId(item));
  const title = normalizeSearchValue(item.display_name_zh || "");
  const plugin = normalizeSearchValue(item.collector_plugin_id || item.provider_id || "");
  const dataset = normalizeSearchValue(item.dataset_id || "");
  const allText = collectorSearchText(item);

  let score = 0;
  score = Math.max(score, scoreTextMatch(id, query, 1000, 900, 760));
  score = Math.max(score, scoreTextMatch(title, query, 920, 840, 700));
  score = Math.max(score, scoreTextMatch(plugin, query, 560, 460, 360));
  score = Math.max(score, scoreTextMatch(dataset, query, 540, 440, 340));
  score = Math.max(score, scoreTextMatch(allText, query, 0, 0, 160));

  const terms = query.split(/\s+/).filter(Boolean);
  if (terms.length > 1 && terms.every((term) => allText.includes(term))) {
    score += 80 + terms.length * 12;
  }
  return score;
}

function scoreCatalogItem(item: CatalogItem, query: string) {
  const title = normalizeSearchValue(item.title);
  const name = normalizeSearchValue(item.name);
  const group = normalizeSearchValue(item.group);
  const source = normalizeSearchValue(`${item.sourceNameZh ?? ""} ${item.sourceCode ?? ""}`);
  const path = normalizeSearchValue(item.path);
  const summary = normalizeSearchValue(item.summary);
  const fieldText = normalizeSearchValue(item.fields.flat().join(" "));
  const paramText = normalizeSearchValue(item.params.flat().join(" "));
  const allText = [title, name, group, source, path, summary, fieldText, paramText].join(" ");

  let score = 0;
  score = Math.max(score, scoreTextMatch(name, query, 1000, 900, 760));
  score = Math.max(score, scoreTextMatch(title, query, 920, 840, 700));
  score = Math.max(score, scoreTextMatch(group, query, 520, 430, 360));
  score = Math.max(score, scoreTextMatch(source, query, 500, 410, 340));
  score = Math.max(score, scoreTextMatch(path, query, 480, 390, 320));
  score = Math.max(score, scoreTextMatch(summary, query, 0, 0, 180));
  score = Math.max(score, scoreTextMatch(fieldText, query, 0, 0, 150));
  score = Math.max(score, scoreTextMatch(paramText, query, 0, 0, 130));

  const terms = query.split(/\s+/).filter(Boolean);
  if (terms.length > 1 && terms.every((term) => allText.includes(term))) {
    score += 80 + terms.length * 12;
  }

  if (score === 0 && (isSubsequence(query, name) || isSubsequence(query, title))) {
    score = 60;
  }

  return score;
}

function scoreTextMatch(text: string, query: string, exact: number, prefix: number, contains: number) {
  if (!text || !query) {
    return 0;
  }
  if (exact > 0 && text === query) {
    return exact;
  }
  if (prefix > 0 && text.startsWith(query)) {
    return prefix;
  }
  if (contains > 0 && text.includes(query)) {
    return contains;
  }
  return 0;
}

function normalizeSearchValue(value: string) {
  return value.trim().toLowerCase();
}

function isSubsequence(query: string, text: string) {
  if (!query || query.length > text.length) {
    return false;
  }
  let queryIndex = 0;
  for (const char of text) {
    if (char === query[queryIndex]) {
      queryIndex += 1;
      if (queryIndex === query.length) {
        return true;
      }
    }
  }
  return false;
}

export default App;
