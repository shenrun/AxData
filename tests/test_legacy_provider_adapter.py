from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from axdata_core.legacy_provider_adapter import LegacyProviderAdapter, timeout_seconds
from axdata_core.source_adapter_options import timeout_seconds as lightweight_timeout_seconds


REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeLegacyAdapter:
    def __init__(self, options: Mapping[str, object]) -> None:
        self.options = dict(options)
        self.request_count = 0
        self.last_meta = {"upstream": "ok"}

    def request(self, interface_name: str, params: Mapping[str, object]) -> list[dict[str, object]]:
        self.request_count += 1
        return [
            {
                "interface_name": interface_name,
                "value": params.get("value"),
                "timeout_ms": self.options.get("timeout_ms"),
                "request_count": self.request_count,
                "drop_me": True,
            }
        ]


def test_legacy_provider_adapter_uses_temporary_options_without_caching_default() -> None:
    created_options: list[dict[str, object]] = []

    def create_adapter(options: Mapping[str, object]) -> FakeLegacyAdapter:
        created_options.append(dict(options))
        return FakeLegacyAdapter(options)

    adapter = LegacyProviderAdapter(
        source="demo",
        provider_id="axdata.source.demo",
        create_adapter=create_adapter,
        options={"timeout_ms": 1000},
    )

    first = adapter.call(
        "demo_snapshot",
        params={"value": 1},
        fields=["value", "timeout_ms"],
        options={"timeout_ms": 2000},
    )
    second = adapter.call(
        "demo_snapshot",
        params={"value": 2},
        fields=["value", "timeout_ms", "request_count"],
    )
    third = adapter.call(
        "demo_snapshot",
        params={"value": 3},
        fields=["value", "timeout_ms", "request_count"],
    )

    assert created_options == [{"timeout_ms": 2000}, {"timeout_ms": 1000}]
    assert first.data == ({"value": 1, "timeout_ms": 2000},)
    assert second.data == ({"value": 2, "timeout_ms": 1000, "request_count": 1},)
    assert third.data == ({"value": 3, "timeout_ms": 1000, "request_count": 2},)
    assert third.meta == {
        "source": "demo",
        "provider_id": "axdata.source.demo",
        "interface_name": "demo_snapshot",
        "upstream": "ok",
    }


def test_legacy_provider_adapter_import_does_not_load_source_request() -> None:
    code = (
        "import sys\n"
        "import axdata_core.legacy_provider_adapter\n"
        "print('legacy=' + str('axdata_core.legacy_provider_adapter' in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
        "print('source_projection=' + str('axdata_core.source_projection' in sys.modules))\n"
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

    assert "legacy=True" in result.stdout
    assert "source_request=False" in result.stdout
    assert "source_projection=False" in result.stdout
    assert "plugins=False" in result.stdout


def test_timeout_seconds_accepts_common_execution_option_names() -> None:
    assert timeout_seconds({"timeout_ms": 1500}, default=20.0) == 1.5
    assert timeout_seconds({"timeout_seconds": 2}, default=20.0) == 2.0
    assert timeout_seconds({"timeout": "3"}, default=20.0) == 3.0
    assert timeout_seconds({}, default=20.0) == 20.0
    assert lightweight_timeout_seconds({"timeout_ms": 1500}, default=20.0) == 1.5


def test_source_adapter_options_import_is_lightweight() -> None:
    code = (
        "import sys\n"
        "from axdata_core.source_adapter_options import timeout_seconds\n"
        "print('timeout=' + str(timeout_seconds({'timeout_ms': 1500}, default=20.0)))\n"
        "print('options=' + str('axdata_core.source_adapter_options' in sys.modules))\n"
        "print('plugins=' + str('axdata_core.plugins' in sys.modules))\n"
        "print('legacy_provider_adapter=' + str('axdata_core.legacy_provider_adapter' in sys.modules))\n"
        "print('source_request=' + str('axdata_core.source_request' in sys.modules))\n"
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

    assert "timeout=1.5" in result.stdout
    assert "options=True" in result.stdout
    assert "plugins=False" in result.stdout
    assert "legacy_provider_adapter=False" in result.stdout
    assert "source_request=False" in result.stdout
