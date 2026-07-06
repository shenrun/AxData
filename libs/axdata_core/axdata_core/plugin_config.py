"""Provider enable/disable configuration for AxData."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

PLUGIN_CONFIG_VERSION = 1
PLUGIN_CONFIG_FILE_NAME = "plugins.json"


class PluginConfigError(ValueError):
    """Raised when plugin configuration cannot be parsed or written."""


@dataclass(frozen=True)
class PluginConfig:
    """AxData-owned Provider enablement configuration.

    Installing a Python distribution only makes a Provider discoverable. This
    config decides whether AxData should actually include it in catalog and
    route resolution.
    """

    enabled_provider_ids: tuple[str, ...] = ()
    disabled_provider_ids: tuple[str, ...] = ()
    removed_provider_ids: tuple[str, ...] = ()
    provider_overrides: Mapping[str, str] = field(default_factory=dict)
    version: int = PLUGIN_CONFIG_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "enabled_provider_ids": sorted(set(self.enabled_provider_ids)),
            "disabled_provider_ids": sorted(set(self.disabled_provider_ids)),
            "removed_provider_ids": sorted(set(self.removed_provider_ids)),
            "provider_overrides": dict(sorted(self.provider_overrides.items())),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PluginConfig":
        version = data.get("version", PLUGIN_CONFIG_VERSION)
        if version != PLUGIN_CONFIG_VERSION:
            raise PluginConfigError(
                f"Unsupported plugin config version {version!r}; expected {PLUGIN_CONFIG_VERSION!r}."
            )
        return cls(
            version=PLUGIN_CONFIG_VERSION,
            enabled_provider_ids=_string_tuple(
                data.get("enabled_provider_ids", ()),
                "enabled_provider_ids",
            ),
            disabled_provider_ids=_string_tuple(
                data.get("disabled_provider_ids", ()),
                "disabled_provider_ids",
            ),
            removed_provider_ids=_string_tuple(
                data.get("removed_provider_ids", ()),
                "removed_provider_ids",
            ),
            provider_overrides=_string_mapping(
                data.get("provider_overrides", {}),
                "provider_overrides",
            ),
        )

    def enable(self, provider_id: str) -> "PluginConfig":
        provider_id = _clean_provider_id(provider_id)
        enabled = set(self.enabled_provider_ids)
        disabled = set(self.disabled_provider_ids)
        removed = set(self.removed_provider_ids)
        enabled.add(provider_id)
        disabled.discard(provider_id)
        removed.discard(provider_id)
        return PluginConfig(
            enabled_provider_ids=tuple(sorted(enabled)),
            disabled_provider_ids=tuple(sorted(disabled)),
            removed_provider_ids=tuple(sorted(removed)),
            provider_overrides=dict(self.provider_overrides),
            version=self.version,
        )

    def disable(self, provider_id: str) -> "PluginConfig":
        provider_id = _clean_provider_id(provider_id)
        enabled = set(self.enabled_provider_ids)
        disabled = set(self.disabled_provider_ids)
        enabled.discard(provider_id)
        disabled.add(provider_id)
        return PluginConfig(
            enabled_provider_ids=tuple(sorted(enabled)),
            disabled_provider_ids=tuple(sorted(disabled)),
            removed_provider_ids=self.removed_provider_ids,
            provider_overrides=dict(self.provider_overrides),
            version=self.version,
        )

    def remove(self, provider_id: str) -> "PluginConfig":
        provider_id = _clean_provider_id(provider_id)
        enabled = set(self.enabled_provider_ids)
        disabled = set(self.disabled_provider_ids)
        removed = set(self.removed_provider_ids)
        enabled.discard(provider_id)
        disabled.add(provider_id)
        removed.add(provider_id)
        return PluginConfig(
            enabled_provider_ids=tuple(sorted(enabled)),
            disabled_provider_ids=tuple(sorted(disabled)),
            removed_provider_ids=tuple(sorted(removed)),
            provider_overrides=dict(self.provider_overrides),
            version=self.version,
        )

    def set_override(self, interface_name: str, provider_id: str | None) -> "PluginConfig":
        interface_name = str(interface_name or "").strip()
        if not interface_name:
            raise PluginConfigError("interface_name is required for provider override.")
        overrides = dict(self.provider_overrides)
        if provider_id is None or str(provider_id).strip() == "":
            overrides.pop(interface_name, None)
        else:
            overrides[interface_name] = _clean_provider_id(provider_id)
        return PluginConfig(
            enabled_provider_ids=self.enabled_provider_ids,
            disabled_provider_ids=self.disabled_provider_ids,
            removed_provider_ids=self.removed_provider_ids,
            provider_overrides=overrides,
            version=self.version,
        )


def plugin_config_path(
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> Path:
    """Return the resolved plugin configuration path."""

    if path is not None:
        return Path(path).expanduser().resolve()

    env_path = os.getenv("AXDATA_PLUGIN_CONFIG_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()

    root = Path(data_root or os.getenv("AXDATA_DATA_DIR", "data")).expanduser().resolve()
    return root.parent / "metadata" / PLUGIN_CONFIG_FILE_NAME


def load_plugin_config(
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> PluginConfig:
    """Load Provider enablement config, returning defaults when absent."""

    config_path = plugin_config_path(data_root=data_root, path=path)
    if not config_path.exists():
        return PluginConfig()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginConfigError(f"Invalid plugin config JSON at {config_path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise PluginConfigError(f"Plugin config at {config_path} must be a JSON object.")
    return PluginConfig.from_dict(payload)


def save_plugin_config(
    config: PluginConfig,
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> Path:
    """Persist Provider enablement config with an atomic replace."""

    config_path = plugin_config_path(data_root=data_root, path=path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = config_path.with_name(f".{config_path.name}.tmp")
    text = json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n"
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(config_path)
    return config_path


def enable_provider(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> PluginConfig:
    """Enable one Provider in AxData config and persist it."""

    config = load_plugin_config(data_root=data_root, path=path).enable(provider_id)
    save_plugin_config(config, data_root=data_root, path=path)
    return config


def disable_provider(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> PluginConfig:
    """Disable one Provider in AxData config and persist it."""

    config = load_plugin_config(data_root=data_root, path=path).disable(provider_id)
    save_plugin_config(config, data_root=data_root, path=path)
    return config


def remove_provider(
    provider_id: str,
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> PluginConfig:
    """Mark one preinstalled Provider as removed from the current AxData runtime."""

    config = load_plugin_config(data_root=data_root, path=path).remove(provider_id)
    save_plugin_config(config, data_root=data_root, path=path)
    return config


def set_provider_override(
    interface_name: str,
    provider_id: str | None,
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> PluginConfig:
    """Set or clear an interface-level Provider override."""

    config = load_plugin_config(data_root=data_root, path=path).set_override(interface_name, provider_id)
    save_plugin_config(config, data_root=data_root, path=path)
    return config


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise PluginConfigError(f"{field_name} must be an array of strings.")
    normalized = []
    for item in value:
        if not isinstance(item, str):
            raise PluginConfigError(f"{field_name} must contain only strings.")
        item = item.strip()
        if item:
            normalized.append(item)
    return tuple(sorted(set(normalized)))


def _string_mapping(value: Any, field_name: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise PluginConfigError(f"{field_name} must be an object.")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise PluginConfigError(f"{field_name} must map strings to strings.")
        key = key.strip()
        item = item.strip()
        if key and item:
            normalized[key] = item
    return normalized


def _clean_provider_id(provider_id: str) -> str:
    value = str(provider_id or "").strip()
    if not value:
        raise PluginConfigError("provider_id is required.")
    return value
