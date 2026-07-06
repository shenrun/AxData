from __future__ import annotations

from axdata_core.tdx_server_config import (
    built_in_servers,
    effective_host_strings,
    probe_servers,
    read_user_servers,
    reset_user_servers,
    server_status,
    write_user_servers,
)


def test_builtin_quote_servers_are_clean_rows():
    servers = built_in_servers("quote")

    assert servers
    first = servers[0]
    assert first.host
    assert first.port == 7709
    assert first.enabled is True


def test_user_servers_override_builtin_and_reset(tmp_path):
    write_user_servers(
        "quote",
        [{"name": "测试", "host": "127.0.0.1", "port": 7709, "enabled": True}],
        cache_root=tmp_path,
    )

    assert read_user_servers("quote", cache_root=tmp_path)[0].host == "127.0.0.1"
    assert effective_host_strings("quote", cache_root=tmp_path) == ["127.0.0.1:7709"]

    reset_user_servers("quote", cache_root=tmp_path)

    assert server_status("quote", cache_root=tmp_path)["source"] == "built_in"


def test_probe_servers_records_error_and_can_save(tmp_path):
    write_user_servers(
        "quote",
        [{"name": "不可用", "host": "127.0.0.1", "port": 1, "enabled": True}],
        cache_root=tmp_path,
    )

    servers = probe_servers("quote", cache_root=tmp_path, timeout=0.2, save=True)

    assert servers[0].last_checked_at
    assert servers[0].last_error
    assert read_user_servers("quote", cache_root=tmp_path)[0].last_error

