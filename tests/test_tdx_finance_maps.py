from __future__ import annotations

from axdata_core.adapters.tdx.finance_maps import (
    load_finance_local_maps,
    load_finance_local_maps_from_root,
    lookup_finance_profile_maps,
)


def test_tdx_finance_builtin_maps_provide_default_profile_mappings():
    maps = load_finance_local_maps()
    profile = lookup_finance_profile_maps("000001", market_id=0, province_raw=18, local_maps=maps)

    assert maps.loaded is True
    assert maps.root == "builtin"
    assert profile["province_name"] == "深圳"
    assert profile["tdx_industry_name"] == "银行"
    assert profile["tdx_research_industry_name"] == "股份制银行"


def test_tdx_finance_local_maps_parse_region_and_industry(tmp_path):
    (tmp_path / "incon.dat").write_text(
        "\n".join(
            [
                "#HY",
                "T10|金融",
                "T1001|银行",
                "X50|银行",
                "X5001|全国性银行",
                "X500102|股份制银行",
            ]
        ),
        encoding="gbk",
    )
    cache = tmp_path / "T0002" / "hq_cache"
    cache.mkdir(parents=True)
    (cache / "tdxzs.cfg").write_text(
        "\n".join(
            [
                "轮动趋势|880081|5|2|0|轮动趋势",
                "深圳板块|880218|3|1|0|18",
            ]
        ),
        encoding="gbk",
    )
    (cache / "tdxhy.cfg").write_text(
        "0|000001|T1001|||X500102\n",
        encoding="gbk",
    )

    maps = load_finance_local_maps_from_root(tmp_path)
    profile = lookup_finance_profile_maps("000001", market_id=0, province_raw=18, local_maps=maps)

    assert maps.loaded is True
    assert profile == {
        "province_name": "深圳",
        "province_board_name": "深圳板块",
        "province_board_code": "880218",
        "tdx_industry_code": "T1001",
        "tdx_industry_name": "银行",
        "tdx_industry_path": "金融 / 银行",
        "tdx_research_industry_code": "X500102",
        "tdx_research_industry_name": "股份制银行",
        "tdx_research_industry_path": "银行 / 全国性银行 / 股份制银行",
    }


def test_tdx_finance_local_maps_missing_files_are_non_blocking(tmp_path):
    maps = load_finance_local_maps_from_root(tmp_path)

    assert maps.loaded is False
    assert maps.region_by_raw == {}
    assert maps.industry_by_security == {}
    assert maps.errors
