import { useState } from "react";
import { Check, ChevronDown, Filter } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { CatalogItem, CollectorPluginGroup, ResolvedCatalogGroup, SidebarGroup, SourceFilterOption } from "../types";
import { compactCollectorTaskTitle } from "../utils";

export function DataCatalogSidebar({
  activeId,
  emptyText,
  groups,
  heading,
  icon: Icon,
  onSelect,
  onSourceFilterChange,
  sourceFilter = "all",
  sourceOptions = []
}: {
  activeId: string;
  emptyText: string;
  groups: ResolvedCatalogGroup[];
  heading: string;
  icon: LucideIcon;
  onSelect: (id: string) => void;
  onSourceFilterChange?: (sourceCode: string) => void;
  sourceFilter?: string;
  sourceOptions?: SourceFilterOption[];
}) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [isSourceFilterExpanded, setIsSourceFilterExpanded] = useState(false);
  const activeSourceOption =
    sourceOptions.find((option) => option.code === sourceFilter) ?? sourceOptions[0];

  function toggleGroup(key: string) {
    setExpandedGroups((current) => ({
      ...current,
      [key]: !current[key]
    }));
  }

  function renderCatalogGroup(group: ResolvedCatalogGroup, level: number) {
    const isExpanded = Boolean(expandedGroups[group.key]);
    const isCollapsed = !isExpanded;

    return (
      <section className={`tree-group tree-level-${level}`} key={group.key}>
        <button
          aria-expanded={!isCollapsed}
          className={
            isCollapsed
              ? `tree-group-toggle tree-level-${level} collapsed`
              : `tree-group-toggle tree-level-${level}`
          }
          onClick={() => toggleGroup(group.key)}
          type="button"
        >
          <ChevronDown size={15} />
          <span>{group.title}</span>
        </button>

        {!isCollapsed ? (
          <div className={`tree-children tree-level-${level}`} role="group" aria-label={`${group.title}目录`}>
            {group.children.map((child) => renderCatalogGroup(child, level + 1))}
            {group.docs.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  className={
                    item.id === activeId
                      ? `tree-item tree-level-${level + 1} active`
                      : `tree-item tree-level-${level + 1}`
                  }
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  type="button"
                >
                  <Icon size={17} />
                  <span>
                    <strong>{item.title}</strong>
                    <small>{item.name}</small>
                  </span>
                  <em>{item.method}</em>
                </button>
              );
            })}
            {group.isEmpty ? (
              <p className={`tree-empty tree-level-${level + 1}`}>待添加接口</p>
            ) : null}
          </div>
        ) : null}
      </section>
    );
  }

  function selectSourceFilter(sourceCode: string) {
    onSourceFilterChange?.(sourceCode);
    setIsSourceFilterExpanded(false);
  }

  return (
    <aside className="doc-sidebar" aria-label={heading}>
      <div className="sidebar-heading">
        <Icon size={18} />
        <span>{heading}</span>
      </div>

      {onSourceFilterChange && sourceOptions.length > 1 ? (
        <div className="source-filter" aria-label="数据源筛选">
          <button
            aria-expanded={isSourceFilterExpanded}
            className="source-filter-summary"
            onClick={() => setIsSourceFilterExpanded((current) => !current)}
            type="button"
          >
            <span className="source-filter-current">
              <strong>{activeSourceOption?.code === "all" ? "全部接口" : activeSourceOption?.label}</strong>
              <em>{activeSourceOption?.count ?? 0}</em>
            </span>
            <span className="source-filter-action">
              <Filter size={13} />
              <span>筛选</span>
              <ChevronDown size={14} />
            </span>
          </button>

          {isSourceFilterExpanded ? (
            <div className="source-filter-options" role="group" aria-label="选择数据源">
              {sourceOptions.map((option) => (
                <button
                  aria-pressed={option.code === sourceFilter}
                  className={option.code === sourceFilter ? "active" : ""}
                  key={option.code}
                  onClick={() => selectSourceFilter(option.code)}
                  type="button"
                >
                  <span>{option.code === "all" ? "全部接口" : option.label}</span>
                  <em>{option.count}</em>
                  {option.code === sourceFilter ? <Check size={13} /> : null}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="catalog-tree">
        {groups.map((group) => renderCatalogGroup(group, 0))}

        {groups.length === 0 ? (
          <p className="empty-state">{emptyText}</p>
        ) : null}
      </div>
    </aside>
  );
}

export function CollectorSidebar({
  activeId,
  activePluginId,
  emptyText,
  groups,
  heading,
  icon: Icon,
  onSelect
}: {
  activeId: string;
  activePluginId: string;
  emptyText: string;
  groups: CollectorPluginGroup[];
  heading: string;
  icon: LucideIcon;
  onSelect: (id: string) => void;
}) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  function toggleGroup(pluginId: string) {
    setExpandedGroups((current) => ({
      ...current,
      [pluginId]: !(current[pluginId] ?? pluginId === activePluginId)
    }));
  }

  return (
    <aside className="doc-sidebar" aria-label={heading}>
      <div className="sidebar-heading">
        <Icon size={18} />
        <span>{heading}</span>
      </div>

      <div className="catalog-tree collector-plugin-tree">
        {groups.map((group) => {
          const isExpanded = expandedGroups[group.pluginId] ?? group.pluginId === activePluginId;
          return (
            <section className="tree-group collector-plugin-group" key={group.pluginId}>
              <button
                aria-expanded={isExpanded}
                className={isExpanded ? "tree-group-toggle tree-level-0" : "tree-group-toggle tree-level-0 collapsed"}
                onClick={() => toggleGroup(group.pluginId)}
                type="button"
              >
                <ChevronDown size={15} />
                <span className="collector-plugin-toggle-label">
                  <strong>{group.title}</strong>
                  <small>{group.pluginId}</small>
                </span>
                <em>{group.taskCount}</em>
              </button>

              {isExpanded ? (
                <div className="tree-children tree-level-0" role="group" aria-label={`${group.title}采集任务`}>
                  {group.items.map((item) => {
                    const itemId = item.collector_id || item.collector_name || item.name;
                    const itemTitle = compactCollectorTaskTitle(item.display_name_zh, itemId);
                    return (
                      <button
                        className={itemId === activeId ? "tree-item tree-level-1 active" : "tree-item tree-level-1"}
                        key={itemId}
                        onClick={() => onSelect(itemId)}
                        type="button"
                      >
                        <Icon size={17} />
                        <span>
                          <strong>{itemTitle}</strong>
                          <small>{item.dataset_id || itemId}</small>
                        </span>
                        <em>{item.is_legacy ? "旧式" : "任务"}</em>
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </section>
          );
        })}

        {groups.length === 0 ? (
          <p className="empty-state">{emptyText}</p>
        ) : null}
      </div>
    </aside>
  );
}

export function InfoSidebar({
  activeId,
  groups,
  heading,
  icon: Icon,
  onSelect
}: {
  activeId: string;
  groups: SidebarGroup[];
  heading: string;
  icon: LucideIcon;
  onSelect: (id: string) => void;
}) {
  return (
    <aside className="doc-sidebar" aria-label={heading}>
      <div className="sidebar-heading">
        <Icon size={18} />
        <span>{heading}</span>
      </div>

      <div className="catalog-tree">
        {groups.map((group) => (
          <section className="tree-group" key={group.title}>
            <h2>{group.title}</h2>
            {group.items.map((item) => {
              const ItemIcon = item.icon;
              return (
                <button
                  className={item.id === activeId ? "tree-item active" : "tree-item"}
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  type="button"
                >
                  <ItemIcon size={17} />
                  <span>
                    <strong>{item.title}</strong>
                    {item.subtitle ? <small>{item.subtitle}</small> : null}
                  </span>
                  {item.badge ? <em>{item.badge}</em> : null}
                </button>
              );
            })}
          </section>
        ))}
      </div>
    </aside>
  );
}
