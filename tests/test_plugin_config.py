from __future__ import annotations

import json

import pytest

from axdata_core.plugin_config import (
    PLUGIN_CONFIG_FILE_NAME,
    PluginConfig,
    PluginConfigError,
    disable_provider,
    enable_provider,
    load_plugin_config,
    plugin_config_path,
    save_plugin_config,
    set_provider_override,
)


def test_plugin_config_defaults_to_axdata_metadata_next_to_data_root(tmp_path) -> None:
    data_root = tmp_path / "data"

    assert plugin_config_path(data_root=data_root) == tmp_path / "metadata" / PLUGIN_CONFIG_FILE_NAME
    assert load_plugin_config(data_root=data_root) == PluginConfig()


def test_plugin_config_round_trips_enable_disable_and_overrides(tmp_path) -> None:
    data_root = tmp_path / "data"

    config = PluginConfig().enable("axdata.source.demo")
    config = config.disable("axdata.source.tdx")
    config = config.set_override("demo_snapshot", "axdata.source.demo")
    path = save_plugin_config(config, data_root=data_root)

    assert path == tmp_path / "metadata" / "plugins.json"
    assert load_plugin_config(data_root=data_root) == config
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "version": 1,
        "enabled_provider_ids": ["axdata.source.demo"],
        "disabled_provider_ids": ["axdata.source.tdx"],
        "removed_provider_ids": [],
        "provider_overrides": {"demo_snapshot": "axdata.source.demo"},
    }


def test_enable_and_disable_helpers_persist_changes(tmp_path) -> None:
    data_root = tmp_path / "data"

    enable_provider("axdata.source.community", data_root=data_root)
    disable_provider("axdata.source.tdx", data_root=data_root)
    set_provider_override("demo_snapshot", "axdata.source.community", data_root=data_root)

    config = load_plugin_config(data_root=data_root)

    assert config.enabled_provider_ids == ("axdata.source.community",)
    assert config.disabled_provider_ids == ("axdata.source.tdx",)
    assert config.provider_overrides == {"demo_snapshot": "axdata.source.community"}


def test_plugin_config_rejects_invalid_json_shape(tmp_path) -> None:
    path = tmp_path / "plugins.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(PluginConfigError, match="JSON object"):
        load_plugin_config(path=path)
