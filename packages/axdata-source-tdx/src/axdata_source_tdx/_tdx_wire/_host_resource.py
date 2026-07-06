"""Provider-owned packaged quote host resource loader."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from ._host_defaults import DEFAULT_QUOTE_HOSTS
from ._host_utils import unique_hosts

SERVER_RESOURCE_PACKAGE = "axdata_source_tdx.resources"
SERVER_FILE = "tdx_quote_servers.json"


def load_server_config() -> dict[str, Any]:
    """Load packaged 7709 host configuration.

    The file is deliberately optional at runtime. If a downstream package strips
    it out, the client still falls back to the built-in static host list.
    """

    try:
        content = resources.files(SERVER_RESOURCE_PACKAGE).joinpath(SERVER_FILE).read_text(encoding="utf-8")
        data = json.loads(content)
    except (FileNotFoundError, ModuleNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def load_server_hosts() -> list[str]:
    """Return normalized hosts from the packaged server config."""

    data = load_server_config()
    rows = data.get("servers")
    if isinstance(rows, list):
        values: list[Any] = []
        for row in rows:
            if isinstance(row, dict):
                host = row.get("host")
                port = row.get("port")
                if host not in (None, "") and port not in (None, ""):
                    values.append(f"{host}:{port}")
                    continue
                values.append(row.get("address"))
            else:
                values.append(row)
        return unique_hosts(values)

    hosts = data.get("hosts")
    if isinstance(hosts, list):
        return unique_hosts(hosts)

    values: list[Any] = [data.get("current_host")]
    for key in ("manual_hosts", "imported_hosts"):
        item = data.get(key, [])
        if isinstance(item, list):
            values.extend(item)
    return unique_hosts(values)


DEFAULT_HOSTS: tuple[str, ...] = tuple(load_server_hosts() or DEFAULT_QUOTE_HOSTS)

__all__ = [
    "DEFAULT_HOSTS",
    "SERVER_FILE",
    "SERVER_RESOURCE_PACKAGE",
    "load_server_config",
    "load_server_hosts",
]
