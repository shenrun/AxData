import type { LucideIcon } from "lucide-react";

export type ServiceState = "checking" | "online" | "offline";

export type HealthPayload = {
  status?: string;
  version?: string;
  data_root?: string;
  auth_enabled?: boolean;
};

export type RuntimeConfig = {
  api_host?: string;
  api_port?: number;
  api_base?: string;
  local_api_base?: string;
  listen_api_base?: string;
  web_host?: string;
  web_port?: number;
  data_root?: string;
  auth_enabled?: boolean;
  cors_origins?: string[];
  pending_restart?: boolean;
  restart_supported?: boolean;
  restart_unavailable_reason?: string | null;
  runtime_config_path?: string;
  next_start?: {
    api_host?: string;
    api_port?: number;
    web_host?: string;
    web_port?: number;
    error?: string;
  };
};

export type ApiTokenRecord = {
  id: string;
  name: string;
  token?: string | null;
  created_at?: string | null;
  last_used_at?: string | null;
  revoked_at?: string | null;
  active?: boolean;
};

export type GuidanceFields = {
  status_message?: string | null;
  next_action?: string | null;
  action_command?: string | null;
};

export type PluginAbilityFilter = "all" | "source" | "collector";

export type ProviderStatus = {
  provider_id: string;
  source_code: string;
  source_name_zh: string;
  version: string;
  status: string;
  enabled: boolean;
  built_in: boolean;
  install_source?: string;
  provider_kind?: string;
  lifecycle_status?: string;
  can_enable?: boolean;
  can_disable?: boolean;
  can_uninstall?: boolean;
  uninstall_mode?: string | null;
  uninstall_block_reason?: string | null;
  declared_trust_level: string;
  effective_trust_level: string;
  interface_count: number;
  downloader_count: number;
  collector_count?: number;
  dependency_count?: number;
  error?: string;
  description?: string;
  homepage?: string | null;
  license?: string | null;
  interfaces?: string[];
  downloaders?: string[];
  collectors?: string[];
  dependencies?: Array<{
    name: string;
    version_spec?: string | null;
    optional?: boolean;
    source?: string | null;
    wheel?: string | null;
    description?: string;
  }>;
  overridden_interfaces?: string[];
  required_config?: Array<{
    name: string;
    kind: string;
    required?: boolean;
    description?: string;
  }>;
} & GuidanceFields;

export type CollectorStatus = {
  name: string;
  collector_id?: string;
  collector_name: string;
  display_name_zh: string;
  description?: string;
  collector_plugin_id?: string;
  dataset_id?: string | null;
  asset_class?: string;
  category?: string;
  provider_id: string;
  legacy_provider_id?: string | null;
  source_code: string;
  source_name_zh: string;
  declared_trust_level: string;
  effective_trust_level: string;
  built_in: boolean;
  plugin_status: string;
  collector_plugin_status?: string;
  enabled: boolean;
  lifecycle_status?: string;
  is_legacy?: boolean;
  legacy_source?: string | null;
  interfaces: string[];
  downloader_profile?: string | null;
  resource_group: string;
  runner_entry?: string | null;
  expected_layer?: string | null;
  default_schedule: Record<string, unknown>;
  default_params: Record<string, unknown>;
  required_interfaces: string[];
  required_datasets?: string[];
  output: Record<string, unknown>;
  quality?: Record<string, unknown>;
  collector_config_schema?: Record<string, unknown>;
  required_config?: Array<{
    name: string;
    kind: string;
    required?: boolean;
    description?: string;
  }>;
  config_schema?: {
    required_config?: Array<{
      name: string;
      kind: string;
      required?: boolean;
      description?: string;
    }>;
    [key: string]: unknown;
  };
};

export type CollectorPluginGroup = {
  pluginId: string;
  title: string;
  sourceCode?: string;
  sourceNameZh?: string;
  status: string;
  enabled: boolean;
  taskCount: number;
  datasetIds: string[];
  runnerEntryCount: number;
  legacyCount: number;
  items: CollectorStatus[];
};

export type AxpWheelInfo = {
  path: string;
  file_name: string;
  size: number;
  sha256: string;
  checksum_status: string;
};

export type AxpDependencyStatus = {
  name: string;
  version_spec?: string | null;
  optional?: boolean;
  source?: string | null;
  declared_wheel?: string | null;
  status: string;
  installed_version?: string | null;
  bundled_wheel?: string | null;
  bundled_version?: string | null;
  requirement?: string | null;
  message?: string;
  blocking?: boolean;
};

export type AxpPreview = {
  provider_id: string;
  source_code: string;
  source_name_zh: string;
  version: string;
  declared_trust_level: string;
  effective_trust_level: string;
  status_after_install: string;
  manifest_source?: string;
  interfaces?: string[];
  downloaders?: string[];
  collectors?: string[];
  dependencies?: Array<{
    name: string;
    version_spec?: string | null;
    optional?: boolean;
    source?: string | null;
    wheel?: string | null;
    description?: string;
  }>;
  dependency_status?: AxpDependencyStatus[];
  missing_dependencies?: AxpDependencyStatus[];
  unsatisfied_dependencies?: AxpDependencyStatus[];
  bundled_dependency_wheels?: string[];
  can_install_offline?: boolean;
  interface_count?: number;
  downloader_count?: number;
  collector_count?: number;
  dependency_count?: number;
  dependency_status_count?: number;
  wheels: AxpWheelInfo[];
  warnings?: string[];
};

export type AxpInstallResult = {
  provider_id: string;
  install_root: string;
  site_packages: string;
  installed_wheels: string[];
  enabled: boolean;
  replaced?: boolean;
  installed_dependency_requirements?: string[];
  status_after_install: string;
  preview: AxpPreview;
  provider?: ProviderStatus | null;
};

export type InstalledPlugin = {
  provider_id: string;
  source_code: string;
  name: string;
  source_name_zh?: string;
  version: string;
  installed_path: string;
  install_root: string;
  site_packages: string;
  installed_at: string;
  installed_wheels: string[];
  wheel_files?: string[];
  enabled: boolean;
  status: string;
  effective_trust_level: string;
  built_in: boolean;
  install_source?: string;
  provider_kind?: string;
  lifecycle_status?: string;
  can_enable?: boolean;
  can_disable?: boolean;
  can_uninstall?: boolean;
  uninstall_mode?: string | null;
  uninstall_block_reason?: string | null;
  interfaces: string[];
  downloaders: string[];
  collectors?: string[];
  dependencies?: Array<Record<string, unknown>>;
  interface_count: number;
  downloader_count: number;
  collector_count?: number;
  dependency_count?: number;
  error?: string;
} & GuidanceFields;

export type LocalDiagnosticCheck = {
  category: string;
  name: string;
  status: "ok" | "warning" | "error" | "skip" | string;
  message?: string;
  path?: string;
  exists?: boolean;
  writable?: boolean;
  available?: boolean;
  version?: string | null;
  host?: string;
  port?: number;
  occupied?: boolean;
};

export type LocalDiagnosticsPayload = {
  summary?: {
    status?: "ok" | "warning" | "error" | string;
    ok?: number;
    warning?: number;
    error?: number;
  };
  python?: Record<string, unknown>;
  axdata?: Record<string, unknown>;
  config?: RuntimeConfig & {
    raw_dir?: string;
    staging_dir?: string;
    core_dir?: string;
    factor_dir?: string;
    metadata_root?: string;
    cache_root?: string;
    logs_root?: string;
    plugin_config_path?: string;
    plugin_dir?: string;
    plugin_site_packages?: string;
    collector_store_path?: string;
    web_base?: string;
  };
  checks?: LocalDiagnosticCheck[];
  dependencies?: LocalDiagnosticCheck[];
  registry?: {
    loaded?: boolean;
    provider_count?: number;
    enabled_provider_count?: number;
    interface_count?: number;
    collector_count?: number;
    status_counts?: Record<string, number>;
  };
  plugins?: {
    providers?: Array<ProviderStatus>;
    installed?: Array<InstalledPlugin>;
    installed_count?: number;
    enabled_provider_ids?: string[];
    disabled_provider_ids?: string[];
    failed_provider_ids?: string[];
  };
  tdx?: Record<string, unknown>;
  ports?: LocalDiagnosticCheck[];
  collector?: Record<string, unknown>;
  real_source_smoke?: Record<string, unknown>;
  next_actions?: string[];
};

export type TableRow = string[];

export type ReferenceSection = {
  id: string;
  title: string;
  icon: LucideIcon;
  note?: string;
  columns: string[];
  rows: TableRow[];
};

export type CatalogItem = {
  id: string;
  group: string;
  sourcePath?: string;
  sourceCode?: string;
  sourceNameZh?: string;
  assetClass?: string;
  category?: string;
  providerId?: string;
  pluginStatus?: string;
  providerEnabled?: boolean;
  collectionSupported?: boolean;
  defaultCollectionProfile?: string | null;
  statusMessage?: string | null;
  nextAction?: string | null;
  actionCommand?: string | null;
  requestExampleParams?: Record<string, unknown>;
  title: string;
  name: string;
  method: "GET" | "POST" | "WS";
  path: string;
  status: "ready" | "example";
  icon: LucideIcon;
  cadence: string;
  key: string;
  limit: string;
  permission: string;
  summary: string;
  description: string;
  overview?: TableRow[];
  notice?: string;
  guides?: ReferenceSection[];
  paramsNote?: string;
  paramsExample?: string;
  params: TableRow[];
  fields: TableRow[];
  fieldColumns?: string[];
  callModes?: ReferenceSection;
  interfaceExamples?: ReferenceSection[];
  dataExamples?: ReferenceSection[];
  sdk: string;
  remoteSdk?: string;
  curl: string;
};

export type CatalogGroup = {
  title: string;
  items?: string[];
  children?: CatalogGroup[];
  keepWhenEmpty?: boolean;
};

export type ResolvedCatalogGroup = {
  title: string;
  key: string;
  docs: CatalogItem[];
  children: ResolvedCatalogGroup[];
  isEmpty: boolean;
};

export type SourceFilterOption = {
  code: string;
  label: string;
  count: number;
};

export type ActiveSection =
  | "manual"
  | "interfaces"
  | "data"
  | "tools"
  | "plugins"
  | "diagnostics"
  | "settings";

export type SidebarItem = {
  id: string;
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
};

export type SidebarGroup = {
  title: string;
  items: SidebarItem[];
};

export type InfoPage = SidebarItem & {
  eyebrow: string;
  summary: string;
  facts: TableRow[];
  details: TableRow[];
  code?: string;
  codeTitle?: string;
  codeLanguage?: string;
  manualMode?: "default" | "markdown";
  markdownDoc?:
    | "axdata-development-standards"
    | "plugin-development"
    | "source-provider-development"
    | "collector-plugin-development"
    | "dataset-and-duckdb"
    | "ui-standards"
    | "axp-packaging-guide"
    | "plugin-install-management";
};

export type IngestionPlan = {
  id: string;
  task: string;
  schedule: string;
  timezone: string;
  mode: string;
  writePolicy: string;
  output: string;
  status: "enabled" | "example";
  summary: string;
  inputs: TableRow[];
  pipeline: TableRow[];
  settings: TableRow[];
  code: string;
};

export type SourceContractSpec = {
  id: string;
  interfaceName: string;
  title: string;
  group: string;
  cadence: string;
  key: string;
  summary: string;
  params: TableRow[];
  fields: TableRow[];
};
