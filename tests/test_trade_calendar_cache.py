from __future__ import annotations

from datetime import date, timedelta

from axdata_core import trade_calendar_cache as cache_module


def test_trade_calendar_cache_refreshes_and_checks_range(tmp_path, monkeypatch):
    calls = []

    def fake_request_interface(interface_name, *, params, fields, persist):
        calls.append({"interface_name": interface_name, "params": params, "fields": fields, "persist": persist})
        start = params["start_date"]
        end = params["end_date"]
        records = []
        current = cache_module._parse_date(start, "start_date")
        final = cache_module._parse_date(end, "end_date")
        while current <= final:
            text = cache_module._format_date(current)
            records.append(
                {
                    "cal_date": text,
                    "is_open": current.weekday() < 5,
                    "pretrade_date": None,
                    "next_trade_date": None,
                }
            )
            current += timedelta(days=1)

        class Result:
            def __init__(self, records):
                self.records = records

        return Result(records)

    monkeypatch.setattr(cache_module, "request_interface", fake_request_interface)

    status = cache_module.refresh_trade_calendar_cache(
        tmp_path,
        start_date="20260617",
        end_date="20260622",
        today=date(2026, 6, 20),
        recheck_past_days=0,
    )

    assert status["exists"] is True
    assert status["start_date"] == "20260617"
    assert status["end_date"] == "20260622"
    assert status["row_count"] == 6
    assert status["fetched_ranges"] == [{"start_date": "20260617", "end_date": "20260622"}]

    check = cache_module.check_trade_calendar_cache(tmp_path, start_date="20260619", end_date="20260620")
    assert check["is_available"] is True
    assert check["missing_count"] == 0

    status = cache_module.refresh_trade_calendar_cache(
        tmp_path,
        start_date="20260620",
        end_date="20260625",
        today=date(2026, 6, 20),
        recheck_past_days=0,
    )

    assert status["start_date"] == "20260617"
    assert status["end_date"] == "20260625"
    assert calls[-1]["params"] == {"start_date": "20260620", "end_date": "20260625"}


def test_trade_calendar_cache_status_without_file(tmp_path):
    status = cache_module.get_trade_calendar_cache_status(tmp_path, today=date(2026, 6, 20))

    assert status["exists"] is False
    assert status["row_count"] == 0
    assert status["covers_today"] is False
    assert status["today"] == "20260620"


def test_trade_calendar_cache_merges_collector_records(tmp_path):
    status = cache_module.update_trade_calendar_cache_from_records(
        tmp_path,
        [
            {"cal_date": "20260617", "is_open": True, "pretrade_date": "20260616"},
            {"cal_date": "20260618", "is_open": True, "pretrade_date": "20260617"},
        ],
        today=date(2026, 6, 18),
    )

    assert status["exists"] is True
    assert status["row_count"] == 2
    assert status["start_date"] == "20260617"
    assert status["end_date"] == "20260618"
    assert status["covers_today"] is True

    check = cache_module.check_trade_calendar_cache(tmp_path, start_date="20260617", end_date="20260618")
    assert check["is_available"] is True


def test_trade_calendar_ensure_checks_gaps_and_monthly_rechecks(tmp_path, monkeypatch):
    calls = []

    def fake_refresh(data_root, **kwargs):
        calls.append(kwargs)
        return {"fetched_ranges": [], "requested_start_date": "20260101", "requested_end_date": "20261231"}

    monkeypatch.setattr(cache_module, "refresh_trade_calendar_cache", fake_refresh)

    status = cache_module.ensure_trade_calendar_cache(tmp_path, today=date(2026, 6, 20))
    monthly_status = cache_module.ensure_trade_calendar_cache(tmp_path, today=date(2026, 7, 1))

    assert status["maintenance_mode"] == "startup_gap_check"
    assert monthly_status["maintenance_mode"] == "monthly_recheck"
    assert calls[0]["recheck_past_days"] == 0
    assert calls[1]["recheck_past_days"] == cache_module.DEFAULT_RECHECK_PAST_DAYS
