from __future__ import annotations

from dataclasses import replace
import json

from axdata_core.plugins import (
    CollectorSpec,
    InterfaceSpec,
    PluginInfo,
    PluginStatus,
    PluginTrustLevel,
    ProviderInfo,
    ProviderManifest,
)
from axdata_core.provider_registry import ProviderRegistry


def _interface(
    name: str,
    *,
    source_code: str = "demo",
    source_name_zh: str = "示例",
) -> InterfaceSpec:
    return InterfaceSpec(
        name=name,
        display_name_zh=name,
        source_code=source_code,
        source_name_zh=source_name_zh,
        asset_class="stock",
    )


def _manifest(
    provider_id: str,
    *,
    interface_name: str = "demo_snapshot",
    declared_trust_level: str = PluginTrustLevel.COMMUNITY.value,
    plugin_api_version: str = "1.0",
    manifest_version: str = "1.0",
) -> ProviderManifest:
    return ProviderManifest(
        manifest_version=manifest_version,
        plugin_api_version=plugin_api_version,
        provider=ProviderInfo(
            provider_id=provider_id,
            source_code="demo",
            source_name_zh="示例",
            version="0.1.0",
            declared_trust_level=declared_trust_level,
        ),
        interfaces=(_interface(interface_name),),
    )


class _BuiltinProvider:
    provider_id = "axdata.source.builtin"
    source_code = "builtin"
    source_name_zh = "内置"
    version = "0.1.0"
    plugin_api_version = "1.0"

    def interfaces(self):
        return (
            _interface(
                "demo_snapshot",
                source_code=self.source_code,
                source_name_zh=self.source_name_zh,
            ),
        )

    def create_adapter(self, options=None):
        raise AssertionError("registry must not create adapters while listing")

    def downloader_profiles(self):
        return ()


def test_builtin_provider_defaults_enabled_and_official() -> None:
    registry = ProviderRegistry()

    registry.register_builtin_provider(_BuiltinProvider())

    snapshot = registry.snapshot()
    provider = snapshot.providers["axdata.source.builtin"]
    route = snapshot.interfaces["demo_snapshot"]

    assert provider.status == PluginStatus.ENABLED.value
    assert provider.enabled is True
    assert provider.effective_trust_level == PluginTrustLevel.OFFICIAL.value
    assert provider.manifest.provider.declared_trust_level == PluginTrustLevel.OFFICIAL.value
    assert route.provider_id == "axdata.source.builtin"


def test_external_manifest_defaults_disabled() -> None:
    registry = ProviderRegistry()

    registry.register_manifest(_manifest("axdata.source.community"))

    snapshot = registry.snapshot()
    provider = snapshot.providers["axdata.source.community"]

    assert provider.status == PluginStatus.DISABLED.value
    assert provider.enabled is False
    assert snapshot.interfaces == {}


def test_external_self_declared_official_is_downgraded_to_community() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.community"})

    registry.register_manifest(
        _manifest(
            "axdata.source.community",
            declared_trust_level=PluginTrustLevel.OFFICIAL.value,
        )
    )

    provider = registry.snapshot().providers["axdata.source.community"]

    assert provider.manifest.provider.declared_trust_level == PluginTrustLevel.OFFICIAL.value
    assert provider.effective_trust_level == PluginTrustLevel.COMMUNITY.value


def test_builtin_wins_over_external_same_interface() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.community"})

    registry.register_builtin_provider(_BuiltinProvider())
    registry.register_manifest(_manifest("axdata.source.community"))

    snapshot = registry.snapshot()

    assert snapshot.interfaces["demo_snapshot"].provider_id == "axdata.source.builtin"
    assert snapshot.providers["axdata.source.community"].status == PluginStatus.CONFLICT.value
    assert snapshot.providers["axdata.source.builtin"].status == PluginStatus.ENABLED.value


def test_two_enabled_community_providers_with_same_interface_both_conflict() -> None:
    registry = ProviderRegistry(
        enabled_provider_ids={"axdata.source.a", "axdata.source.b"},
    )

    registry.register_manifest(_manifest("axdata.source.a"))
    registry.register_manifest(_manifest("axdata.source.b"))

    snapshot = registry.snapshot()

    assert "demo_snapshot" not in snapshot.interfaces
    assert snapshot.providers["axdata.source.a"].status == PluginStatus.CONFLICT.value
    assert snapshot.providers["axdata.source.b"].status == PluginStatus.CONFLICT.value
    assert "Interface name conflict" in snapshot.providers["axdata.source.a"].error


def test_different_provider_ids_with_same_interface_still_conflict() -> None:
    registry = ProviderRegistry(
        enabled_provider_ids={"axdata.source.left", "axdata.source.right"},
    )

    registry.register_manifest(_manifest("axdata.source.left", interface_name="shared_snapshot"))
    registry.register_manifest(_manifest("axdata.source.right", interface_name="shared_snapshot"))

    snapshot = registry.snapshot()

    assert set(snapshot.providers) == {"axdata.source.left", "axdata.source.right"}
    assert snapshot.ignored_candidates == ()
    assert "shared_snapshot" not in snapshot.interfaces
    assert snapshot.providers["axdata.source.left"].status == PluginStatus.CONFLICT.value
    assert snapshot.providers["axdata.source.right"].status == PluginStatus.CONFLICT.value


def test_override_resolves_community_conflict() -> None:
    registry = ProviderRegistry(
        enabled_provider_ids={"axdata.source.a", "axdata.source.b"},
        provider_overrides={"demo_snapshot": "axdata.source.b"},
    )

    registry.register_manifest(_manifest("axdata.source.a"))
    registry.register_manifest(_manifest("axdata.source.b"))

    snapshot = registry.snapshot()

    assert snapshot.interfaces["demo_snapshot"].provider_id == "axdata.source.b"
    assert snapshot.providers["axdata.source.a"].status == PluginStatus.CONFLICT.value
    assert snapshot.providers["axdata.source.b"].status == PluginStatus.ENABLED.value


def test_bad_manifest_version_is_failed() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.bad"})

    registry.register_manifest(
        _manifest("axdata.source.bad", manifest_version="2.0"),
    )

    provider = registry.snapshot().providers["axdata.source.bad"]

    assert provider.status == PluginStatus.FAILED.value
    assert "manifest_version" in provider.error


def test_bad_plugin_api_version_is_incompatible() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.bad"})

    registry.register_manifest(
        _manifest("axdata.source.bad", plugin_api_version="9.0"),
    )

    provider = registry.snapshot().providers["axdata.source.bad"]

    assert provider.status == PluginStatus.INCOMPATIBLE.value
    assert "plugin_api_version" in provider.error


def test_disabled_provider_does_not_participate_in_conflict() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.enabled"})

    registry.register_manifest(_manifest("axdata.source.enabled"))
    registry.register_manifest(_manifest("axdata.source.disabled"))

    snapshot = registry.snapshot()

    assert snapshot.interfaces["demo_snapshot"].provider_id == "axdata.source.enabled"
    assert snapshot.providers["axdata.source.disabled"].status == PluginStatus.DISABLED.value


def test_builtin_provider_can_be_disabled_by_axdata_config() -> None:
    registry = ProviderRegistry(disabled_provider_ids={"axdata.source.builtin"})

    registry.register_builtin_provider(_BuiltinProvider())

    snapshot = registry.snapshot()
    provider = snapshot.providers["axdata.source.builtin"]

    assert provider.status == PluginStatus.DISABLED.value
    assert provider.enabled is False
    assert snapshot.interfaces == {}


def test_replacing_manifest_rebuilds_routes() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.demo"})

    registry.register_manifest(_manifest("axdata.source.demo", interface_name="old_name"))
    registry.register_manifest(
        replace(
            _manifest("axdata.source.demo", interface_name="new_name"),
            provider=ProviderInfo(
                provider_id="axdata.source.demo",
                source_code="demo",
                source_name_zh="示例",
                version="0.2.0",
            ),
        )
    )

    snapshot = registry.snapshot()

    assert "old_name" not in snapshot.interfaces
    assert snapshot.interfaces["new_name"].provider_id == "axdata.source.demo"


def test_external_manifest_cannot_replace_existing_builtin_provider_id() -> None:
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.builtin"})

    registry.register_builtin_provider(_BuiltinProvider())
    registry.register_manifest(
        _manifest("axdata.source.builtin", interface_name="external_takeover"),
        entry_point=object(),
    )

    snapshot = registry.snapshot()

    assert snapshot.providers["axdata.source.builtin"].built_in is True
    assert snapshot.providers["axdata.source.builtin"].status == PluginStatus.ENABLED.value
    assert snapshot.interfaces["demo_snapshot"].provider_id == "axdata.source.builtin"
    assert "external_takeover" not in snapshot.interfaces


def test_second_entry_point_with_same_provider_id_is_ignored_not_replaced(tmp_path) -> None:
    first_manifest = _manifest("axdata.source.external", interface_name="first_snapshot")
    second_manifest = _manifest("axdata.source.external", interface_name="second_snapshot")
    first_manifest_path = tmp_path / "first" / "axdata-provider.json"
    second_manifest_path = tmp_path / "second" / "axdata-provider.json"
    first_manifest_path.parent.mkdir()
    second_manifest_path.parent.mkdir()
    first_manifest_path.write_text(json.dumps(first_manifest.to_dict()), encoding="utf-8")
    second_manifest_path.write_text(json.dumps(second_manifest.to_dict()), encoding="utf-8")

    class FakeDistribution:
        def __init__(self, name, manifest_path):
            self.metadata = {"Name": name}
            self.files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        def __init__(self, name, dist):
            self.name = name
            self.dist = dist

        def load(self):  # pragma: no cover - discovery must not import
            raise AssertionError("registry discovery must not import provider entry point")

    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points(
        [
            FakeEntryPoint("first", FakeDistribution("first-source", first_manifest_path)),
            FakeEntryPoint("second", FakeDistribution("second-source", second_manifest_path)),
        ]
    )

    snapshot = registry.snapshot()

    assert snapshot.providers["axdata.source.external"].status == PluginStatus.ENABLED.value
    assert snapshot.interfaces["first_snapshot"].provider_id == "axdata.source.external"
    assert "second_snapshot" not in snapshot.interfaces
    assert "duplicate:axdata.source.external" not in snapshot.providers
    assert len(snapshot.ignored_candidates) == 1
    duplicate = snapshot.ignored_candidates[0]
    assert duplicate.reason == "duplicate_provider_id"
    assert duplicate.provider_id == "axdata.source.external"
    assert duplicate.covered_by_provider_id == "axdata.source.external"
    assert duplicate.entry_point_name == "second"
    assert duplicate.distribution == "second-source"
    assert "Duplicate provider_id" in duplicate.message


def test_entry_point_discovery_reads_embedded_manifest_without_import(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "pkg" / "axdata-provider.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()

        def load(self):  # pragma: no cover - this must not be called
            raise AssertionError("registry discovery must not import provider entry point")

    registry = ProviderRegistry()
    registry.discover_entry_points([FakeEntryPoint()])

    snapshot = registry.snapshot()
    provider = snapshot.providers["axdata.source.external"]

    assert provider.status == PluginStatus.DISABLED.value
    assert provider.enabled is False
    assert provider.provider is None
    assert snapshot.interfaces == {}


def test_entry_point_discovery_reads_editable_manifest_without_import(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    project_root = tmp_path / "project"
    manifest_path = project_root / "src" / "external_pkg" / "axdata-provider.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    dist_root = tmp_path / "external_pkg-0.1.0.dist-info"
    dist_root.mkdir()
    (dist_root / "direct_url.json").write_text(
        json.dumps({"dir_info": {"editable": True}, "url": project_root.as_uri()}),
        encoding="utf-8",
    )
    (dist_root / "top_level.txt").write_text("external_pkg\n", encoding="utf-8")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [
            dist_root.relative_to(tmp_path) / "direct_url.json",
            dist_root.relative_to(tmp_path) / "top_level.txt",
        ]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        value = "external_pkg.provider:provider"
        dist = FakeDistribution()

        def load(self):  # pragma: no cover - this must not be called
            raise AssertionError("editable manifest discovery must not import provider entry point")

    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([FakeEntryPoint()])

    snapshot = registry.snapshot()

    assert snapshot.providers["axdata.source.external"].status == PluginStatus.ENABLED.value
    assert snapshot.interfaces["external_snapshot"].provider_id == "axdata.source.external"


def test_enabled_entry_point_manifest_participates_in_routes(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()

    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([FakeEntryPoint()])

    snapshot = registry.snapshot()

    assert snapshot.providers["axdata.source.external"].status == PluginStatus.ENABLED.value
    assert snapshot.interfaces["external_snapshot"].provider_id == "axdata.source.external"


def test_entry_point_provider_load_is_cached_after_first_call(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeProvider:
        provider_id = "axdata.source.external"
        source_code = "external"
        source_name_zh = "外部"
        version = "0.1.0"
        plugin_api_version = "1.0"

        def interfaces(self):
            return ()

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

        def downloader_profiles(self):
            return ()

    provider_object = FakeProvider()

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()
        load_count = 0

        def load(self):
            self.load_count += 1
            return provider_object

    entry_point = FakeEntryPoint()
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([entry_point])

    registered = registry.snapshot().providers["axdata.source.external"]

    assert entry_point.load_count == 0
    assert registered.load_provider() is provider_object
    assert registered.load_provider() is provider_object
    assert entry_point.load_count == 1


def test_entry_point_provider_factory_load_is_cached_after_first_call(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeProvider:
        provider_id = "axdata.source.external"
        plugin_api_version = "1.0"

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    provider_object = FakeProvider()

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()
        load_count = 0
        factory_count = 0

        def load(self):
            self.load_count += 1

            def factory():
                self.factory_count += 1
                return provider_object

            return factory

    entry_point = FakeEntryPoint()
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([entry_point])

    registered = registry.snapshot().providers["axdata.source.external"]

    assert entry_point.load_count == 0
    assert entry_point.factory_count == 0
    assert registered.load_provider() is provider_object
    assert registered.load_provider() is provider_object
    assert entry_point.load_count == 1
    assert entry_point.factory_count == 1


def test_entry_point_provider_class_is_instantiated_and_cached(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeProvider:
        provider_id = "axdata.source.external"
        plugin_api_version = "1.0"
        instance_count = 0

        def __init__(self):
            type(self).instance_count += 1

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()
        load_count = 0

        def load(self):
            self.load_count += 1
            return FakeProvider

    entry_point = FakeEntryPoint()
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([entry_point])

    registered = registry.snapshot().providers["axdata.source.external"]
    first = registered.load_provider()
    second = registered.load_provider()

    assert isinstance(first, FakeProvider)
    assert second is first
    assert entry_point.load_count == 1
    assert FakeProvider.instance_count == 1


def test_entry_point_provider_failed_load_is_not_cached(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeProvider:
        provider_id = "axdata.source.external"
        plugin_api_version = "1.0"

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    provider_object = FakeProvider()

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()
        load_count = 0

        def load(self):
            self.load_count += 1
            if self.load_count == 1:
                raise RuntimeError("temporary import failure")
            return provider_object

    entry_point = FakeEntryPoint()
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([entry_point])

    registered = registry.snapshot().providers["axdata.source.external"]

    try:
        registered.load_provider()
    except RuntimeError as exc:
        assert "temporary import failure" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("first load should fail")

    assert registered.load_provider() is provider_object
    assert registered.load_provider() is provider_object
    assert entry_point.load_count == 2


def test_entry_point_loaded_provider_id_must_match_manifest(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class WrongProvider:
        provider_id = "axdata.source.other"
        plugin_api_version = "1.0"

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    class CorrectProvider:
        provider_id = "axdata.source.external"
        plugin_api_version = "1.0"

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()
        load_count = 0

        def load(self):
            self.load_count += 1
            return WrongProvider() if self.load_count == 1 else CorrectProvider()

    entry_point = FakeEntryPoint()
    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([entry_point])
    registered = registry.snapshot().providers["axdata.source.external"]

    try:
        registered.load_provider()
    except Exception as exc:
        assert "does not match manifest provider_id" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("mismatched provider_id should fail")

    assert isinstance(registered.load_provider(), CorrectProvider)
    assert entry_point.load_count == 2


def test_entry_point_loaded_plugin_api_version_must_match_manifest(tmp_path) -> None:
    manifest = _manifest("axdata.source.external", interface_name="external_snapshot")
    manifest_path = tmp_path / "axdata-provider.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class WrongProvider:
        provider_id = "axdata.source.external"
        plugin_api_version = "2.0"

        def create_adapter(self, options=None):
            raise AssertionError("adapter creation is not part of provider loading")

    class FakeDistribution:
        metadata = {"Name": "axdata-source-external"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "external"
        dist = FakeDistribution()

        def load(self):
            return WrongProvider()

    registry = ProviderRegistry(enabled_provider_ids={"axdata.source.external"})
    registry.discover_entry_points([FakeEntryPoint()])
    registered = registry.snapshot().providers["axdata.source.external"]

    try:
        registered.load_provider()
    except Exception as exc:
        assert "does not match manifest plugin_api_version" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("mismatched plugin_api_version should fail")


def test_entry_point_without_manifest_is_ignored() -> None:
    class FakeDistribution:
        metadata = {"Name": "broken-source"}
        files = []

        def locate_file(self, item):  # pragma: no cover
            raise AssertionError("no files should be located")

    class FakeEntryPoint:
        name = "broken"
        dist = FakeDistribution()

    registry = ProviderRegistry()
    registry.discover_entry_points([FakeEntryPoint()])

    snapshot = registry.snapshot()

    assert "entry_point.broken" not in snapshot.providers
    assert len(snapshot.ignored_candidates) == 1
    candidate = snapshot.ignored_candidates[0]
    assert candidate.candidate_id == "entry_point.broken"
    assert candidate.reason == "missing_manifest"
    assert candidate.entry_point_name == "broken"
    assert candidate.distribution == "broken-source"
    assert "axdata-plugin.json" in candidate.message
    assert "axdata-provider.json" in candidate.message


def test_ignored_entry_point_candidate_id_is_manifest_safe() -> None:
    class FakeDistribution:
        metadata = {"Name": "broken-source"}
        files = []

        def locate_file(self, item):  # pragma: no cover
            raise AssertionError("no files should be located")

    class FakeEntryPoint:
        name = "123 Broken:Plugin"
        dist = FakeDistribution()

    registry = ProviderRegistry()
    registry.discover_entry_points([FakeEntryPoint()])

    snapshot = registry.snapshot()
    candidate = snapshot.ignored_candidates[0]

    assert "entry_point.plugin_123_broken_plugin" not in snapshot.providers
    assert candidate.candidate_id == "entry_point.plugin_123_broken_plugin"
    assert candidate.reason == "missing_manifest"


def test_collector_only_manifest_can_be_discovered_without_provider(tmp_path) -> None:
    manifest = ProviderManifest(
        plugin=PluginInfo(
            plugin_id="axdata.plugin.close_refresh",
            name_zh="收盘刷新",
            version="0.1.0",
        ),
        provider=None,
        interfaces=(),
        collectors=(
            CollectorSpec(
                name="close.refresh.daily",
                display_name_zh="收盘刷新",
                interfaces=("stock_codes_tdx",),
                downloader_profile="tdx.stock_codes.latest",
                resource_group="tdx.quote",
                default_params={"scope": "all"},
            ),
        ),
    )
    manifest_path = tmp_path / "pkg" / "axdata-plugin.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")

    class FakeDistribution:
        metadata = {"Name": "axdata-close-refresh"}
        files = [manifest_path.relative_to(tmp_path)]

        def locate_file(self, item):
            return tmp_path / item

    class FakeEntryPoint:
        name = "close_refresh"
        dist = FakeDistribution()

        def load(self):  # pragma: no cover
            raise AssertionError("collector-only manifest discovery must not import plugin")

    registry = ProviderRegistry(enabled_provider_ids={"axdata.plugin.close_refresh"})
    registry.discover_entry_points([FakeEntryPoint()])
    snapshot = registry.snapshot()

    plugin = snapshot.providers["axdata.plugin.close_refresh"]
    assert plugin.status == PluginStatus.ENABLED.value
    assert plugin.provider_id == "axdata.plugin.close_refresh"
    assert plugin.source_code == "plugin"
    assert snapshot.interfaces == {}
    assert snapshot.collectors["close.refresh.daily"].provider_id == "axdata.plugin.close_refresh"


def test_two_enabled_collector_plugins_with_same_collector_both_conflict() -> None:
    def collector_manifest(plugin_id: str) -> ProviderManifest:
        return ProviderManifest(
            plugin=PluginInfo(
                plugin_id=plugin_id,
                name_zh=plugin_id,
                version="0.1.0",
            ),
            provider=None,
            interfaces=(),
            collectors=(
                CollectorSpec(
                    name="close.refresh.daily",
                    display_name_zh="收盘刷新",
                    interfaces=("stock_codes_tdx",),
                    resource_group="tdx.quote",
                ),
            ),
        )

    registry = ProviderRegistry(
        enabled_provider_ids={
            "axdata.plugin.close_refresh_a",
            "axdata.plugin.close_refresh_b",
        }
    )
    registry.register_manifest(collector_manifest("axdata.plugin.close_refresh_a"))
    registry.register_manifest(collector_manifest("axdata.plugin.close_refresh_b"))

    snapshot = registry.snapshot()

    assert "close.refresh.daily" not in snapshot.collectors
    assert snapshot.providers["axdata.plugin.close_refresh_a"].status == PluginStatus.CONFLICT.value
    assert snapshot.providers["axdata.plugin.close_refresh_b"].status == PluginStatus.CONFLICT.value
    assert "Collector conflict" in snapshot.providers["axdata.plugin.close_refresh_a"].error
    assert "Interface name conflict" not in snapshot.providers["axdata.plugin.close_refresh_a"].error
