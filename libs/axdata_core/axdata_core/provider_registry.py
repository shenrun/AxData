"""Provider registry for AxData plugin manifests.

This is the first implementation slice of the plugin registry. It supports
in-process built-in providers and manifest objects, with conflict resolution
and trust calculation kept separate from the provider-declared trust value.
Entry-point discovery will be layered on top of this module later.
"""

from __future__ import annotations

import json
import inspect
import re
from dataclasses import dataclass, field, replace
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from .plugins import (
    MANIFEST_FILE_NAME,
    MANIFEST_VERSION,
    PLUGIN_API_VERSION,
    PLUGIN_MANIFEST_FILE_NAME,
    CollectorSpec,
    InterfaceSpec,
    ManifestError,
    PluginStatus,
    PluginTrustLevel,
    ProviderManifest,
    SourceProvider,
    manifest_from_provider,
    validate_manifest,
)

ENTRY_POINT_GROUP = "axdata.providers"
PLUGIN_ENTRY_POINT_GROUP = "axdata.plugins"

TRUST_RANK: Mapping[str, int] = {
    PluginTrustLevel.COMMUNITY.value: 10,
    PluginTrustLevel.UNKNOWN.value: 10,
    PluginTrustLevel.OFFICIAL.value: 30,
}

DEFAULT_ENABLED_ENTRY_POINT_DISTS: Mapping[str, str] = {
    "axdata.source.tdx_external": "axdata-source-tdx",
    "axdata.source.tdx_ext_external": "axdata-source-tdx-ext",
}


@dataclass(frozen=True)
class RegisteredProvider:
    """A provider candidate known to the registry."""

    manifest: ProviderManifest
    status: str
    effective_trust_level: str
    enabled: bool = False
    built_in: bool = False
    error: str = ""
    provider: SourceProvider | None = None
    entry_point: Any | None = None
    _loaded_provider: SourceProvider | None = field(default=None, repr=False, compare=False)

    @property
    def provider_id(self) -> str:
        return self.manifest.identity

    @property
    def source_code(self) -> str:
        if self.manifest.provider is not None:
            return self.manifest.provider.source_code
        return "plugin"

    def load_provider(self) -> SourceProvider | None:
        if self.manifest.provider is None:
            return None
        if self.provider is not None:
            return self.provider
        if self._loaded_provider is not None:
            return self._loaded_provider
        if self.entry_point is None:
            return None
        loaded = self.entry_point.load()
        if inspect.isclass(loaded):
            loaded = loaded()
        if callable(loaded) and not hasattr(loaded, "create_adapter"):
            loaded = loaded()
        _validate_loaded_provider_identity(loaded, self.manifest)
        object.__setattr__(self, "_loaded_provider", loaded)
        return loaded


@dataclass(frozen=True)
class IgnoredPluginCandidate:
    """A discovery candidate that is not a valid AxData plugin."""

    candidate_id: str
    reason: str
    message: str
    entry_point_name: str | None = None
    distribution: str | None = None
    provider_id: str | None = None
    covered_by_provider_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "status": "ignored",
            "reason": self.reason,
            "message": self.message,
            "entry_point_name": self.entry_point_name,
            "distribution": self.distribution,
            "provider_id": self.provider_id,
            "covered_by_provider_id": self.covered_by_provider_id,
        }


@dataclass(frozen=True)
class InterfaceRegistration:
    """Resolved interface route entry."""

    interface: InterfaceSpec
    provider_id: str
    effective_trust_level: str
    built_in: bool


@dataclass(frozen=True)
class CollectorRegistration:
    """Resolved collector capability entry."""

    collector: CollectorSpec
    provider_id: str
    effective_trust_level: str
    built_in: bool


@dataclass(frozen=True)
class ProviderRegistrySnapshot:
    """Immutable view of registry state."""

    providers: Mapping[str, RegisteredProvider]
    interfaces: Mapping[str, InterfaceRegistration]
    collectors: Mapping[str, CollectorRegistration] = field(default_factory=dict)
    ignored_candidates: tuple[IgnoredPluginCandidate, ...] = ()


@dataclass
class ProviderRegistry:
    """Merge provider manifests and build exact interface routes."""

    enabled_provider_ids: set[str] | None = None
    disabled_provider_ids: set[str] | None = None
    provider_overrides: Mapping[str, str] = field(default_factory=dict)
    _providers: dict[str, RegisteredProvider] = field(default_factory=dict)
    _interfaces: dict[str, InterfaceRegistration] = field(default_factory=dict)
    _collectors: dict[str, CollectorRegistration] = field(default_factory=dict)
    _ignored_candidates: list[IgnoredPluginCandidate] = field(default_factory=list)

    def register_builtin_provider(self, provider: SourceProvider, *, enabled: bool | None = None) -> None:
        """Register a built-in provider object without entry-point discovery."""

        manifest = manifest_from_provider(provider)
        manifest = replace(
            manifest,
            provider=replace(
                manifest.provider,
                declared_trust_level=PluginTrustLevel.OFFICIAL.value,
            ),
        )
        self.register_manifest(
            manifest,
            provider=provider,
            built_in=True,
            enabled=enabled,
        )

    def register_manifest(
        self,
        manifest: ProviderManifest,
        *,
        provider: SourceProvider | None = None,
        entry_point: Any | None = None,
        built_in: bool = False,
        enabled: bool | None = None,
    ) -> None:
        """Register one parsed provider manifest."""

        provider_id = manifest.identity
        existing = self._providers.get(provider_id)
        if existing is not None and not _can_replace_provider(
            existing,
            built_in=built_in,
            provider=provider,
            entry_point=entry_point,
        ):
            self._ignore_provider_id_collision(
                manifest,
                existing=existing,
                provider=provider,
                entry_point=entry_point,
            )
            return
        is_enabled = self._is_enabled(provider_id, built_in=built_in, explicit=enabled)
        status = PluginStatus.ENABLED.value if is_enabled else PluginStatus.DISABLED.value
        error = ""

        try:
            self._validate_compatibility(manifest)
            validate_manifest(manifest)
        except ManifestError as exc:
            status = PluginStatus.FAILED.value
            error = str(exc)

        if status != PluginStatus.FAILED and manifest.plugin_api_version != PLUGIN_API_VERSION:
            status = PluginStatus.INCOMPATIBLE.value
            error = (
                f"Unsupported plugin_api_version {manifest.plugin_api_version!r}; "
                f"expected {PLUGIN_API_VERSION!r}."
            )

        registered = RegisteredProvider(
            manifest=manifest,
            status=status,
            effective_trust_level=self._effective_trust(manifest, built_in=built_in),
            enabled=is_enabled and status == PluginStatus.ENABLED.value,
            built_in=built_in,
            error=error,
            provider=provider,
            entry_point=entry_point,
        )
        self._providers[provider_id] = registered
        self._rebuild_interfaces()

    def _ignore_provider_id_collision(
        self,
        manifest: ProviderManifest,
        *,
        existing: RegisteredProvider,
        provider: SourceProvider | None = None,
        entry_point: Any | None = None,
    ) -> None:
        error = (
            f"Duplicate provider_id {manifest.identity!r}; already registered by "
            f"{'built-in' if existing.built_in else 'another'} provider."
        )
        self._ignored_candidates.append(
            IgnoredPluginCandidate(
                candidate_id=_collision_candidate_id(manifest.identity, entry_point=entry_point),
                reason="duplicate_provider_id",
                message=error,
                entry_point_name=_entry_point_name(entry_point),
                distribution=_entry_point_distribution_name(entry_point),
                provider_id=manifest.identity,
                covered_by_provider_id=existing.provider_id,
            )
        )

    def discover_entry_points(self, entry_points: Sequence[Any] | None = None) -> None:
        """Discover external providers through Python entry points.

        Discovery reads the distribution-embedded manifest and intentionally
        does not import the provider module. Import is reserved for future
        call-time adapter creation.
        """

        candidates = list(entry_points) if entry_points is not None else list(_provider_entry_points())
        for entry_point in candidates:
            try:
                manifest = _manifest_from_entry_point(entry_point)
            except Exception as exc:
                self._ignore_entry_point_candidate(entry_point, str(exc))
                continue
            self.register_manifest(
                manifest,
                entry_point=entry_point,
                enabled=self._default_entry_point_enabled(manifest.identity, entry_point),
            )

    def snapshot(self) -> ProviderRegistrySnapshot:
        """Return an immutable registry snapshot."""

        return ProviderRegistrySnapshot(
            providers=dict(self._providers),
            interfaces=dict(self._interfaces),
            collectors=dict(self._collectors),
            ignored_candidates=tuple(self._ignored_candidates),
        )

    def list_providers(self) -> tuple[RegisteredProvider, ...]:
        """Return all registered providers."""

        return tuple(self._providers.values())

    def list_interfaces(self) -> tuple[InterfaceRegistration, ...]:
        """Return resolved, callable interface registrations."""

        return tuple(self._interfaces.values())

    def list_collectors(self) -> tuple[CollectorRegistration, ...]:
        """Return resolved collector capability registrations."""

        return tuple(self._collectors.values())

    def get_interface(self, interface_name: str) -> InterfaceRegistration:
        """Return the resolved route for one interface."""

        return self._interfaces[interface_name]

    def _is_enabled(self, provider_id: str, *, built_in: bool, explicit: bool | None) -> bool:
        if explicit is not None:
            return explicit
        if self.disabled_provider_ids is not None and provider_id in self.disabled_provider_ids:
            return False
        if built_in:
            return True
        return self.enabled_provider_ids is not None and provider_id in self.enabled_provider_ids

    def _validate_compatibility(self, manifest: ProviderManifest) -> None:
        if manifest.manifest_version != MANIFEST_VERSION:
            raise ManifestError(
                f"Unsupported manifest_version {manifest.manifest_version!r}; "
                f"expected {MANIFEST_VERSION!r}."
            )

    def _effective_trust(self, manifest: ProviderManifest, *, built_in: bool) -> str:
        if built_in:
            return PluginTrustLevel.OFFICIAL.value
        # Signature validation is a later phase. Until then, external plugins
        # are always treated as community regardless of declared trust.
        return PluginTrustLevel.COMMUNITY.value

    def _default_entry_point_enabled(self, provider_id: str, entry_point: Any) -> bool | None:
        if self.disabled_provider_ids is not None and provider_id in self.disabled_provider_ids:
            return None
        expected_dist = DEFAULT_ENABLED_ENTRY_POINT_DISTS.get(provider_id)
        if expected_dist is None:
            return None
        actual_dist = _entry_point_distribution_name(entry_point)
        if _normalize_dist_name(actual_dist) != _normalize_dist_name(expected_dist):
            return None
        return True

    def _rebuild_interfaces(self) -> None:
        self._clear_conflicts()
        candidates: dict[str, list[RegisteredProvider]] = {}
        for provider in self._providers.values():
            if provider.status != PluginStatus.ENABLED.value or not provider.enabled:
                continue
            for interface in provider.manifest.interfaces:
                candidates.setdefault(interface.name, []).append(provider)

        resolved: dict[str, InterfaceRegistration] = {}
        interface_conflict_provider_ids: set[str] = set()
        for interface_name, providers in candidates.items():
            winner = self._resolve_interface_conflict(interface_name, providers)
            if winner is None:
                interface_conflict_provider_ids.update(provider.provider_id for provider in providers)
                continue
            for provider in providers:
                if provider.provider_id != winner.provider_id:
                    interface_conflict_provider_ids.add(provider.provider_id)
            interface = next(
                item for item in winner.manifest.interfaces if item.name == interface_name
            )
            resolved[interface_name] = InterfaceRegistration(
                interface=interface,
                provider_id=winner.provider_id,
                effective_trust_level=winner.effective_trust_level,
                built_in=winner.built_in,
            )

        self._interfaces = resolved
        self._mark_conflicts(
            interface_conflict_provider_ids,
            error="Interface name conflict; disable one provider or configure an override.",
        )
        self._rebuild_collectors()

    def _rebuild_collectors(self) -> None:
        candidates: dict[str, list[RegisteredProvider]] = {}
        for provider in self._providers.values():
            if provider.status != PluginStatus.ENABLED.value or not provider.enabled:
                continue
            for collector in provider.manifest.collectors:
                candidates.setdefault(collector.name, []).append(provider)

        resolved: dict[str, CollectorRegistration] = {}
        collector_conflict_provider_ids: set[str] = set()
        for collector_name, providers in candidates.items():
            winner = self._resolve_collector_conflict(providers)
            if winner is None:
                collector_conflict_provider_ids.update(provider.provider_id for provider in providers)
                continue
            for provider in providers:
                if provider.provider_id != winner.provider_id:
                    collector_conflict_provider_ids.add(provider.provider_id)
            collector = next(item for item in winner.manifest.collectors if item.name == collector_name)
            resolved[collector_name] = CollectorRegistration(
                collector=collector,
                provider_id=winner.provider_id,
                effective_trust_level=winner.effective_trust_level,
                built_in=winner.built_in,
            )
        self._collectors = resolved
        self._mark_conflicts(
            collector_conflict_provider_ids,
            error="Collector conflict; disable one plugin or rename the collector.",
        )

    def _resolve_collector_conflict(
        self,
        providers: Iterable[RegisteredProvider],
    ) -> RegisteredProvider | None:
        provider_list = list(providers)
        if len(provider_list) == 1:
            return provider_list[0]
        ranked = sorted(
            provider_list,
            key=lambda provider: (
                TRUST_RANK.get(provider.effective_trust_level, 0),
                1 if provider.built_in else 0,
            ),
            reverse=True,
        )
        best = ranked[0]
        tied = [
            provider
            for provider in ranked
            if TRUST_RANK.get(provider.effective_trust_level, 0)
            == TRUST_RANK.get(best.effective_trust_level, 0)
            and provider.built_in == best.built_in
        ]
        if len(tied) > 1:
            return None
        return best

    def _clear_conflicts(self) -> None:
        for provider_id, provider in list(self._providers.items()):
            if provider.status == PluginStatus.CONFLICT.value:
                self._providers[provider_id] = replace(
                    provider,
                    status=PluginStatus.ENABLED.value if provider.enabled else PluginStatus.DISABLED.value,
                    error="",
                )

    def _resolve_interface_conflict(
        self,
        interface_name: str,
        providers: Iterable[RegisteredProvider],
    ) -> RegisteredProvider | None:
        provider_list = list(providers)
        if len(provider_list) == 1:
            return provider_list[0]

        override_provider_id = self.provider_overrides.get(interface_name)
        if override_provider_id:
            for provider in provider_list:
                if provider.provider_id == override_provider_id:
                    return provider

        ranked = sorted(
            provider_list,
            key=lambda provider: (
                TRUST_RANK.get(provider.effective_trust_level, 0),
                1 if provider.built_in else 0,
            ),
            reverse=True,
        )
        best = ranked[0]
        tied = [
            provider
            for provider in ranked
            if TRUST_RANK.get(provider.effective_trust_level, 0)
            == TRUST_RANK.get(best.effective_trust_level, 0)
            and provider.built_in == best.built_in
        ]
        if len(tied) > 1:
            return None
        return best

    def _mark_conflicts(self, provider_ids: set[str], *, error: str) -> None:
        for provider_id in provider_ids:
            provider = self._providers.get(provider_id)
            if provider is None or provider.status in {
                PluginStatus.FAILED.value,
                PluginStatus.INCOMPATIBLE.value,
                PluginStatus.DISABLED.value,
            }:
                continue
            self._providers[provider_id] = replace(
                provider,
                status=PluginStatus.CONFLICT.value,
                error=error,
            )

    def _ignore_entry_point_candidate(self, entry_point: Any, error: str) -> None:
        self._ignored_candidates.append(
            IgnoredPluginCandidate(
                candidate_id=_entry_point_candidate_id(entry_point),
                reason=_ignored_candidate_reason(error),
                message=error,
                entry_point_name=_entry_point_name(entry_point),
                distribution=_entry_point_distribution_name(entry_point),
            )
        )


def _provider_entry_points() -> tuple[Any, ...]:
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return tuple(
            [
                *entry_points.select(group=PLUGIN_ENTRY_POINT_GROUP),
                *entry_points.select(group=ENTRY_POINT_GROUP),
            ]
        )
    return tuple(
        [
            *entry_points.get(PLUGIN_ENTRY_POINT_GROUP, ()),
            *entry_points.get(ENTRY_POINT_GROUP, ()),
        ]
    )


def _can_replace_provider(
    existing: RegisteredProvider,
    *,
    built_in: bool,
    provider: SourceProvider | None,
    entry_point: Any | None,
) -> bool:
    if existing.built_in and not built_in:
        return (
            existing.provider is None
            and existing.entry_point is None
            and provider is not None
            and entry_point is None
        )
    if existing.entry_point is not None and built_in:
        return True
    if entry_point is not None and existing.entry_point is not None:
        return existing.entry_point is entry_point
    if provider is not None and existing.provider is not None:
        return existing.provider is provider
    return existing.built_in == built_in and entry_point is None


def _collision_candidate_id(provider_id: str, *, entry_point: Any | None = None) -> str:
    if entry_point is not None:
        return f"duplicate:{provider_id}:{_entry_point_candidate_id(entry_point)}"
    return f"duplicate:{provider_id}"


def _entry_point_candidate_id(entry_point: Any) -> str:
    raw_name = str(getattr(entry_point, "name", "unknown") or "unknown").lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw_name).strip("_")
    if not normalized or not normalized[0].isalpha():
        normalized = f"plugin_{normalized or 'unknown'}"
    return f"entry_point.{normalized}"


def _entry_point_name(entry_point: Any | None) -> str | None:
    if entry_point is None:
        return None
    return str(getattr(entry_point, "name", "") or "") or None


def _entry_point_distribution_name(entry_point: Any | None) -> str | None:
    if entry_point is None:
        return None
    distribution = getattr(entry_point, "dist", None)
    if distribution is None:
        return None
    metadata_obj = getattr(distribution, "metadata", {}) or {}
    get = getattr(metadata_obj, "get", None)
    if callable(get):
        value = get("Name") or get("name")
        return str(value) if value else None
    return None


def _normalize_dist_name(value: str | None) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def _ignored_candidate_reason(error: str) -> str:
    lower_error = error.lower()
    if "does not include" in lower_error and (
        PLUGIN_MANIFEST_FILE_NAME in lower_error or MANIFEST_FILE_NAME in lower_error
    ):
        return "missing_manifest"
    if "has no distribution" in lower_error or "has no file list" in lower_error:
        return "invalid_entry_point"
    if "manifest" in lower_error:
        return "invalid_manifest"
    return "discovery_error"


def _manifest_from_entry_point(entry_point: Any) -> ProviderManifest:
    distribution = getattr(entry_point, "dist", None)
    if distribution is None:
        raise ManifestError(f"Entry point {getattr(entry_point, 'name', '<unknown>')} has no distribution.")
    raw = _read_manifest_from_distribution(distribution, entry_point=entry_point)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"AxData plugin manifest is not valid JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ManifestError("AxData plugin manifest must contain a JSON object.")
    return ProviderManifest.from_dict(payload)


def _read_manifest_from_distribution(distribution: Any, *, entry_point: Any | None = None) -> str:
    files = distribution.files
    if files is None:
        editable_raw = _read_editable_manifest_from_distribution(
            distribution,
            files=(),
            entry_point=entry_point,
        )
        if editable_raw is not None:
            return editable_raw
        raise ManifestError(f"Distribution {distribution.metadata.get('Name', '<unknown>')} has no file list.")
    candidates: list[tuple[int, Any]] = []
    for item in files:
        normalized = str(item).replace("\\", "/")
        if normalized.endswith(PLUGIN_MANIFEST_FILE_NAME):
            candidates.append((0, item))
        elif normalized.endswith(MANIFEST_FILE_NAME):
            candidates.append((1, item))
    if candidates:
        _priority, item = sorted(candidates, key=lambda candidate: (candidate[0], str(candidate[1])))[0]
        located = distribution.locate_file(item)
        return located.read_text(encoding="utf-8")
    editable_raw = _read_editable_manifest_from_distribution(
        distribution,
        files=files,
        entry_point=entry_point,
    )
    if editable_raw is not None:
        return editable_raw
    raise ManifestError(
        f"Distribution {distribution.metadata.get('Name', '<unknown>')} does not include "
        f"{PLUGIN_MANIFEST_FILE_NAME} or {MANIFEST_FILE_NAME}."
    )


def _read_editable_manifest_from_distribution(
    distribution: Any,
    *,
    files: Sequence[Any],
    entry_point: Any | None,
) -> str | None:
    """Read a manifest from a local editable install without importing provider code."""

    project_root = _editable_project_root(distribution, files=files)
    if project_root is None:
        return None
    package_paths = _manifest_package_paths(distribution, files=files, entry_point=entry_point)
    candidates: list[Path] = [
        project_root / PLUGIN_MANIFEST_FILE_NAME,
        project_root / MANIFEST_FILE_NAME,
    ]
    for package_path in package_paths:
        candidates.extend(
            [
                project_root / package_path / PLUGIN_MANIFEST_FILE_NAME,
                project_root / package_path / MANIFEST_FILE_NAME,
                project_root / "src" / package_path / PLUGIN_MANIFEST_FILE_NAME,
                project_root / "src" / package_path / MANIFEST_FILE_NAME,
            ]
        )
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        except OSError:
            continue
    return None


def _editable_project_root(distribution: Any, *, files: Sequence[Any]) -> Path | None:
    raw = _distribution_file_text(distribution, files=files, file_name="direct_url.json")
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping):
        return None
    dir_info = payload.get("dir_info")
    if not isinstance(dir_info, Mapping) or dir_info.get("editable") is not True:
        return None
    url = str(payload.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None
    path = url2pathname(unquote(parsed.path or ""))
    if parsed.netloc:
        path = f"//{parsed.netloc}/{path.lstrip('/')}"
    root = Path(path).expanduser()
    if root.exists():
        return root.resolve()
    return None


def _manifest_package_paths(
    distribution: Any,
    *,
    files: Sequence[Any],
    entry_point: Any | None,
) -> tuple[Path, ...]:
    names: list[str] = []
    raw_top_level = _distribution_file_text(distribution, files=files, file_name="top_level.txt")
    if raw_top_level:
        names.extend(line.strip() for line in raw_top_level.splitlines() if line.strip())
    entry_point_value = str(getattr(entry_point, "value", "") or "")
    module_name = entry_point_value.split(":", 1)[0].split("[", 1)[0].strip()
    if module_name:
        parts = [part for part in module_name.split(".") if part]
        if parts:
            names.append(parts[0])
            if len(parts) > 1:
                names.append(".".join(parts[:-1]))
    paths: list[Path] = []
    seen: set[str] = set()
    for name in names:
        normalized = re.sub(r"[^A-Za-z0-9_.]+", "", name).strip(".")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        paths.append(Path(*normalized.split(".")))
    return tuple(paths)


def _distribution_file_text(distribution: Any, *, files: Sequence[Any], file_name: str) -> str | None:
    for item in files:
        normalized = str(item).replace("\\", "/")
        if normalized == file_name or normalized.endswith(f"/{file_name}"):
            try:
                return distribution.locate_file(item).read_text(encoding="utf-8")
            except Exception:
                return None
    read_text = getattr(distribution, "read_text", None)
    if callable(read_text):
        try:
            raw = read_text(file_name)
        except Exception:
            return None
        return raw if isinstance(raw, str) else None
    return None


def _validate_loaded_provider_identity(provider: Any, manifest: ProviderManifest) -> None:
    if manifest.provider is None:
        raise ManifestError(f"Manifest {manifest.identity!r} does not declare a provider.")
    provider_id = getattr(provider, "provider_id", None)
    if provider_id != manifest.provider.provider_id:
        raise ManifestError(
            f"Loaded provider_id {provider_id!r} does not match manifest provider_id "
            f"{manifest.provider.provider_id!r}."
        )
    plugin_api_version = getattr(provider, "plugin_api_version", None)
    if plugin_api_version != manifest.plugin_api_version:
        raise ManifestError(
            f"Loaded provider plugin_api_version {plugin_api_version!r} does not match "
            f"manifest plugin_api_version {manifest.plugin_api_version!r}."
        )
