from __future__ import annotations

import json
from pathlib import Path

from scripts.build_pages import build_site, load_interface_entries


def test_pages_catalog_uses_public_plugin_interfaces() -> None:
    entries = load_interface_entries()
    names = {entry["name"] for entry in entries}

    assert len(entries) >= 250
    assert "stock_codes_tdx" in names
    assert "futures_contracts_tdx" in names
    assert "cninfo_announcements" in names
    assert "tencent_realtime_snapshot" in names
    assert all(entry.get("enabled", True) is True for entry in entries)


def test_build_pages_writes_static_interface_site(tmp_path: Path) -> None:
    summary = build_site(tmp_path)
    catalog_path = tmp_path / "interfaces" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert summary["interface_count"] == len(catalog["interfaces"])
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "interfaces" / "index.html").is_file()
    assert (tmp_path / "interfaces" / "stock_codes_tdx.html").is_file()
    assert (tmp_path / "interfaces" / "tencent_realtime_snapshot.html").is_file()
    assert (tmp_path / "docs" / "quickstart.html").is_file()
    assert catalog["interface_count"] == summary["interface_count"]
    assert any(item["name"] == "stock_codes_tdx" for item in catalog["interfaces"])
