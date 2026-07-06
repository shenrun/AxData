from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from axdata_core.adapters.tdx_ext.client import _configured_extended_servers
from axdata_core.adapters.tdx_ext.exceptions import ConnectionClosedError
from axdata_core.adapters.tdx_ext.servers import TdxExtServer

REPO_ROOT = Path(__file__).resolve().parents[1]
TDX_PACKAGE_ROOT = REPO_ROOT / "packages" / "axdata-source-tdx"
sys.path.insert(0, str(TDX_PACKAGE_ROOT / "src"))


def _core_without_site_subprocess(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_tdx_ext_server_model_roundtrips_dict():
    server = TdxExtServer(index=1, name="扩展市场", host="10.0.0.1", port=7727, is_primary=True)

    assert TdxExtServer.from_dict(server.to_dict()) == server


def test_configured_extended_servers_uses_unified_server_config(monkeypatch):
    from axdata_source_tdx.tdx_server_config import TdxServerEntry

    seen_cache_roots = []

    def fake_effective_servers(kind, *, cache_root=None):
        seen_cache_roots.append(cache_root)
        if kind != "extended":
            return ()
        return (
            TdxServerEntry(name="扩展一", host="10.0.0.1", port=7727, priority=1),
            TdxServerEntry(name="扩展二", host="10.0.0.2", port=7727, priority=2),
        )

    monkeypatch.setattr(
        "axdata_core.adapters.tdx_ext.client.effective_servers",
        fake_effective_servers,
    )

    assert _configured_extended_servers() == (
        TdxExtServer(index=1, name="扩展一", host="10.0.0.1", port=7727, is_primary=True),
        TdxExtServer(index=2, name="扩展二", host="10.0.0.2", port=7727, is_primary=False),
    )
    assert _configured_extended_servers(cache_root="/tmp/axdata-tdx-ext") == (
        TdxExtServer(index=1, name="扩展一", host="10.0.0.1", port=7727, is_primary=True),
        TdxExtServer(index=2, name="扩展二", host="10.0.0.2", port=7727, is_primary=False),
    )
    assert seen_cache_roots == [None, "/tmp/axdata-tdx-ext"]


def test_configured_extended_servers_requires_configured_servers(monkeypatch):
    monkeypatch.setattr("axdata_core.adapters.tdx_ext.client.effective_servers", lambda kind, *, cache_root=None: ())

    with pytest.raises(ConnectionClosedError):
        _configured_extended_servers()


def test_tdx_ext_host_config_effective_servers_reads_current_server_config(monkeypatch):
    from axdata_source_tdx import tdx_server_config
    from axdata_source_tdx.tdx_server_config import TdxServerEntry
    from axdata_core.adapters.tdx_ext import host_config

    def fake_effective_servers(kind, *, cache_root=None):
        return (TdxServerEntry(name=f"{kind}:{cache_root}", host="10.0.0.8", port=7727, priority=1),)

    monkeypatch.setattr(tdx_server_config, "effective_servers", fake_effective_servers)
    monkeypatch.setattr(host_config, "effective_servers", fake_effective_servers)

    servers = host_config.effective_servers("extended", cache_root="demo-cache")

    assert len(servers) == 1
    assert servers[0].name == "extended:demo-cache"
    assert servers[0].host == "10.0.0.8"


def test_tdx_ext_pool_config_uses_cache_root_and_caps_connections(monkeypatch):
    from axdata_core.adapters.tdx_ext import pool

    seen_cache_roots = []

    def fake_configured_extended_servers(*, cache_root=None):
        seen_cache_roots.append(cache_root)
        return tuple(
            TdxExtServer(
                index=index,
                name=f"扩展{index}",
                host=f"10.0.0.{index}",
                port=7727,
                is_primary=index == 1,
            )
            for index in range(1, 21)
        )

    monkeypatch.setattr(pool, "_configured_extended_servers", fake_configured_extended_servers)

    config = pool.resolve_tdx_ext_pool_config(
        {
            "server_cache_root": "demo-cache",
            "source_server_count": 20,
            "connections_per_server": 10,
        },
        minimum_tasks=200,
    )

    assert seen_cache_roots == ["demo-cache"]
    assert config is not None
    assert config.source_server_count == 20
    assert config.requested_connections_per_server == 10
    assert config.connection_count == 128
    assert config.connections_per_server == 7
    assert len(config.servers) == 20


def test_tdx_ext_request_quotes_single_client_uses_server_cache_root():
    from axdata_core.adapters.tdx_ext import request_execution

    calls = []

    class FakeClient:
        @classmethod
        def from_config(cls, **kwargs):
            calls.append(kwargs)
            return cls()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def get_quote_multi(self, code_list):
            return tuple(code_list)

    def resolve_pool_config(options, *, minimum_tasks):
        return None

    quotes, pool_config, task_count = request_execution.request_quotes(
        [(1, "IF2606")],
        options={},
        root="tdx-root",
        server_cache_root="server-cache",
        timeout=3.5,
        client_factory=FakeClient,
        pool_tools=(object, list, resolve_pool_config),
    )

    assert quotes == ((1, "IF2606"),)
    assert pool_config is None
    assert task_count is None
    assert calls == [{"tdx_root": "tdx-root", "server_cache_root": "server-cache", "timeout": 3.5}]


def test_tdx_ext_request_quotes_pool_uses_resolved_servers():
    from axdata_core.adapters.tdx_ext import request_execution

    selected_servers = (
        TdxExtServer(index=1, name="扩展一", host="10.0.0.1", port=7727, is_primary=True),
        TdxExtServer(index=2, name="扩展二", host="10.0.0.2", port=7727, is_primary=False),
    )
    pool_calls = []

    class PoolConfig:
        servers = selected_servers
        connections_per_server = 1
        connection_count = 2

    class FakePool:
        def __init__(self, **kwargs):
            pool_calls.append(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def map(self, items, func):
            class PooledClient:
                def get_quote_multi(self, batch):
                    return tuple(batch)

            client = PooledClient()
            return [func(client, item) for item in items]

    class FakeClient:
        @classmethod
        def from_config(cls, **kwargs):
            raise AssertionError("parallel pool path must not create a default configured client")

    def resolve_pool_config(options, *, minimum_tasks):
        assert options == {"source_server_count": 2}
        assert minimum_tasks == 3
        return PoolConfig()

    quotes, pool_config, task_count = request_execution.request_quotes(
        [(1, "IF2606"), (1, "IC2606"), (1, "IH2606")],
        options={"source_server_count": 2},
        root="tdx-root",
        server_cache_root="server-cache",
        timeout=3.5,
        client_factory=FakeClient,
        pool_tools=(FakePool, lambda results: [item for result in results for item in result], resolve_pool_config),
    )

    assert quotes == ((1, "IF2606"), (1, "IC2606"), (1, "IH2606"))
    assert pool_config is not None
    assert task_count == 2
    assert pool_calls == [
        {
            "servers": selected_servers,
            "connections_per_server": 1,
            "connection_count": 2,
            "timeout": 3.5,
            "client_factory": FakeClient,
        }
    ]


def test_tdx_ext_request_items_single_client_uses_server_cache_root():
    from axdata_core.adapters.tdx_ext import request_execution

    calls = []

    class FakeClient:
        @classmethod
        def from_config(cls, **kwargs):
            calls.append(kwargs)
            return cls()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    def resolve_pool_config(options, *, minimum_tasks):
        return None

    rows, pool_config, task_count = request_execution.request_items(
        ["IF2606"],
        options={},
        root="tdx-root",
        server_cache_root="server-cache",
        timeout=3.5,
        client_factory=FakeClient,
        pool_tools=(object, lambda results: [item for result in results for item in result], resolve_pool_config),
        request_item=lambda client, item: [f"{item}:row"],
    )

    assert rows == ["IF2606:row"]
    assert pool_config is None
    assert task_count is None
    assert calls == [{"tdx_root": "tdx-root", "server_cache_root": "server-cache", "timeout": 3.5}]


def test_tdx_ext_request_items_pool_uses_resolved_servers():
    from axdata_core.adapters.tdx_ext import request_execution

    selected_servers = (
        TdxExtServer(index=1, name="扩展一", host="10.0.0.1", port=7727, is_primary=True),
        TdxExtServer(index=2, name="扩展二", host="10.0.0.2", port=7727, is_primary=False),
    )
    pool_calls = []

    class PoolConfig:
        servers = selected_servers
        connections_per_server = 1
        connection_count = 2

    class FakePool:
        def __init__(self, **kwargs):
            pool_calls.append(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def map(self, items, func):
            return [func("pooled-client", item) for item in items]

    class FakeClient:
        @classmethod
        def from_config(cls, **kwargs):
            raise AssertionError("parallel pool path must not create a default configured client")

    def resolve_pool_config(options, *, minimum_tasks):
        assert options == {"source_server_count": 2}
        assert minimum_tasks == 3
        return PoolConfig()

    rows, pool_config, task_count = request_execution.request_items(
        ["IF2606", "IC2606", "IH2606"],
        options={"source_server_count": 2},
        root="tdx-root",
        server_cache_root="server-cache",
        timeout=3.5,
        client_factory=FakeClient,
        pool_tools=(FakePool, lambda results: [item for result in results for item in result], resolve_pool_config),
        request_item=lambda client, item: [f"{client}:{item}"],
    )

    assert rows == ["pooled-client:IF2606", "pooled-client:IC2606", "pooled-client:IH2606"]
    assert pool_config is not None
    assert task_count == 3
    assert pool_calls == [
        {
            "servers": selected_servers,
            "connections_per_server": 1,
            "connection_count": 2,
            "timeout": 3.5,
            "client_factory": FakeClient,
        }
    ]


def test_tdx_ext_host_config_import_does_not_load_server_config():
    code = (
        "import sys\n"
        "from axdata_core.source_errors import SourceUnavailableError\n"
        "from axdata_core.tdx_plugin_required import TDX_PLUGIN_REQUIRED_MESSAGE\n"
        "import axdata_core.adapters.tdx_ext.host_config\n"
        "print('server_config_before=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
        "try:\n"
        "    axdata_core.adapters.tdx_ext.host_config.effective_servers('extended')\n"
        "except SourceUnavailableError as exc:\n"
        "    print('error=' + str(exc))\n"
        "    print('matches=' + str(str(exc) == TDX_PLUGIN_REQUIRED_MESSAGE))\n"
        "print('server_config_after=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
    )
    result = _core_without_site_subprocess(code)

    assert "server_config_before=False" in result.stdout
    assert f"error=TDX 插件未安装或不可用，请安装并启用 TDX 插件。" in result.stdout
    assert "matches=True" in result.stdout
    assert "server_config_after=True" in result.stdout


def test_tdx_ext_client_import_does_not_load_host_config():
    code = (
        "import sys\n"
        "import axdata_core.adapters.tdx_ext.client\n"
        "print('client=' + str('axdata_core.adapters.tdx_ext.client' in sys.modules))\n"
        "print('host_config=' + str('axdata_core.adapters.tdx_ext.host_config' in sys.modules))\n"
        "print('server_config=' + str('axdata_core.tdx_server_config' in sys.modules))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "libs" / "axdata_core"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert "client=True" in result.stdout
    assert "host_config=False" in result.stdout
    assert "server_config=False" in result.stdout
