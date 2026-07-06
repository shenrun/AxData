"""TDX statistics resource row models and parsers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class TdxStatRow:
    market_id: int
    code: str
    stats_date: str | None
    beta_60d: float | None
    pe_ttm: float | None
    free_float_shares_10k: float | None
    year_limit_up_days: int | None
    limit_stat_days: int | None
    limit_up_count_in_stat_days: int | None
    limit_up_streak_days: int | None

    @property
    def key(self) -> tuple[int, str]:
        return self.market_id, self.code


@dataclass(frozen=True, slots=True)
class TdxStat2Row:
    market_id: int
    code: str
    stats_date: str | None
    prev_amount_10k: float | None
    prev_seal_amount_10k: float | None
    prev2_amount_10k: float | None
    prev2_seal_amount_10k: float | None
    prev3_amount_10k: float | None
    prev3_seal_amount_10k: float | None
    prev_open_volume_hand: float | None
    prev2_open_volume_hand: float | None
    prev_open_amount_10k: float | None
    prev2_open_amount_10k: float | None

    @property
    def key(self) -> tuple[int, str]:
        return self.market_id, self.code


@dataclass(frozen=True, slots=True)
class TdxStatsResource:
    stat: dict[tuple[int, str], TdxStatRow]
    stat2: dict[tuple[int, str], TdxStat2Row]
    source_path: str
    metadata: dict[str, object] | None = None

    def row(self, market_id: int, code: str) -> tuple[TdxStatRow | None, TdxStat2Row | None]:
        key = (int(market_id), str(code).zfill(6))
        return self.stat.get(key), self.stat2.get(key)

    @property
    def stats_date(self) -> str | None:
        for row in self.stat2.values():
            if row.stats_date:
                return row.stats_date
        for row in self.stat.values():
            if row.stats_date:
                return row.stats_date
        if self.metadata:
            value = self.metadata.get("stats_date")
            if value:
                return str(value)
        return None


def stats_resource_from_lines(
    stat_lines: Iterable[str],
    stat2_lines: Iterable[str],
    *,
    source_path: str,
    metadata: dict[str, object] | None = None,
) -> TdxStatsResource:
    return TdxStatsResource(
        stat={row.key: row for row in parse_stat_rows(stat_lines)},
        stat2={row.key: row for row in parse_stat2_rows(stat2_lines)},
        source_path=source_path,
        metadata=metadata,
    )


def decode_lines(payload: bytes) -> list[str]:
    return payload.decode("gbk", errors="ignore").splitlines()


def parse_stat_rows(lines: Iterable[str]) -> Iterable[TdxStatRow]:
    for line in lines:
        parts = line.rstrip("\n\r").split("|")
        if len(parts) < 35:
            continue
        market_id = int_value(parts[0])
        code = parts[1].strip()
        if market_id is None or not code:
            continue
        yield TdxStatRow(
            market_id=market_id,
            code=code,
            stats_date=text_value(parts[4]),
            beta_60d=float_value(parts[2]),
            pe_ttm=float_value(parts[3]),
            free_float_shares_10k=float_value(parts[11]),
            year_limit_up_days=int_value(parts[26]),
            limit_stat_days=int_value(parts[31]),
            limit_up_count_in_stat_days=int_value(parts[32]),
            limit_up_streak_days=int_value(parts[33]),
        )


def parse_stat2_rows(lines: Iterable[str]) -> Iterable[TdxStat2Row]:
    for line in lines:
        parts = line.rstrip("\n\r").split("|")
        if len(parts) < 21:
            continue
        market_id = int_value(parts[0])
        code = parts[1].strip()
        if market_id is None or not code:
            continue
        yield TdxStat2Row(
            market_id=market_id,
            code=code,
            stats_date=text_value(parts[2]),
            prev_amount_10k=float_value(parts[3]),
            prev_seal_amount_10k=float_value(parts[4]),
            prev2_amount_10k=float_value(parts[5]),
            prev2_seal_amount_10k=float_value(parts[6]),
            prev3_amount_10k=float_value(parts[7]),
            prev3_seal_amount_10k=float_value(parts[8]),
            prev_open_volume_hand=float_value(parts[9]),
            prev2_open_volume_hand=float_value(parts[10]),
            prev_open_amount_10k=float_value(parts[14]),
            prev2_open_amount_10k=float_value(parts[15]),
        )


def text_value(value: str) -> str | None:
    text = value.strip()
    return text or None


def float_value(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def int_value(value: str) -> int | None:
    number = float_value(value)
    if number is None:
        return None
    return int(number)
