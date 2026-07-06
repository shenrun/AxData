"""Pure topic ranking helpers for TDX limit-ladder style requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


__all__ = [
    "attach_limit_ladder_themes",
    "limit_ladder_stock_summary_text",
    "limit_ladder_theme_is_noise",
    "limit_ladder_theme_rank_rows",
    "limit_ladder_theme_stats",
    "limit_ladder_theme_strength_score",
    "topic_missing_stock_count",
]


LIMIT_LADDER_THEME_NOISE_KEYWORDS = (
    "不可减持",
    "持股",
    "罗素",
    "MSCI",
    "富时",
    "标普",
    "沪股通",
    "深股通",
    "融资融券",
    "转融券",
    "国企改革",
    "国资改革",
    "央企改革",
    "参股券商",
    "参股新三板",
    "最近闪拉",
    "定向增发",
    "并购基金",
    "财报",
    "证金",
    "汇金",
    "社保基金",
    "养老金",
)


def attach_limit_ladder_themes(
    rows: list[dict[str, Any]],
    topic_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    theme_stats = limit_ladder_theme_stats(rows, topic_rows)
    for row in rows:
        instrument_id = str(row.get("instrument_id") or "")
        topics = []
        for topic in topic_rows.get(instrument_id, ()):
            topic_name = str(topic.get("topic_name") or "").strip()
            if not topic_name or limit_ladder_theme_is_noise(topic_name):
                continue
            stats = theme_stats.get(topic_name, {})
            topics.append(
                {
                    "topic_name": topic_name,
                    "topic_id": topic.get("topic_id"),
                    "relevance": _round_optional_float(topic.get("relevance"))
                    if topic.get("relevance") not in (None, "")
                    else None,
                    "theme_strength_score": stats.get("theme_strength_score"),
                    "same_theme_limit_up_count": stats.get("same_theme_limit_up_count"),
                    "same_theme_highest_board": stats.get("same_theme_highest_board"),
                    "same_theme_lianban_count": stats.get("same_theme_lianban_count"),
                }
            )
        topics.sort(
            key=lambda topic: (
                -float(topic.get("same_theme_limit_up_count") or 0),
                -float(topic.get("same_theme_highest_board") or 0),
                -float(topic.get("same_theme_lianban_count") or 0),
                -float(topic.get("relevance") or 0),
                str(topic.get("topic_name") or ""),
            )
        )
        best = topics[0] if topics else None
        row["primary_theme"] = best.get("topic_name") if best else None
        top_themes = topics[:4]
        secondary_themes = topics[1:4]
        row["secondary_themes"] = "+".join(
            str(topic.get("topic_name") or "") for topic in secondary_themes if topic.get("topic_name")
        ) or None
        row["top_theme_names"] = "、".join(
            str(topic.get("topic_name") or "") for topic in top_themes if topic.get("topic_name")
        ) or None
        row["top_themes"] = top_themes
        row["themes"] = []
        row["theme_count"] = len(topics)
        row["theme_strength_score"] = best.get("theme_strength_score") if best else None
        row["same_theme_limit_up_count"] = best.get("same_theme_limit_up_count") if best else None
        row["same_theme_highest_board"] = best.get("same_theme_highest_board") if best else None
        row["same_theme_lianban_count"] = best.get("same_theme_lianban_count") if best else None


def limit_ladder_theme_stats(
    rows: Sequence[Mapping[str, Any]],
    topic_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    row_by_instrument_id = {str(row.get("instrument_id") or ""): row for row in rows}
    for instrument_id, topics in topic_rows.items():
        row = row_by_instrument_id.get(str(instrument_id))
        if not row:
            continue
        sealed = row.get("limit_status") == "sealed"
        ladder_level = int(row.get("ladder_level") or 0)
        seen_names: set[str] = set()
        for topic in topics:
            topic_name = str(topic.get("topic_name") or "").strip()
            if not topic_name or topic_name in seen_names or limit_ladder_theme_is_noise(topic_name):
                continue
            seen_names.add(topic_name)
            item = stats.setdefault(
                topic_name,
                {
                    "same_theme_limit_up_count": 0,
                    "same_theme_highest_board": 0,
                    "same_theme_lianban_count": 0,
                },
            )
            if sealed:
                item["same_theme_limit_up_count"] += 1
                item["same_theme_highest_board"] = max(item["same_theme_highest_board"], ladder_level)
                if ladder_level >= 2:
                    item["same_theme_lianban_count"] += 1
    for item in stats.values():
        item["theme_strength_score"] = limit_ladder_theme_strength_score(item)
    return stats


def topic_missing_stock_count(
    topic_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    rows: Sequence[Mapping[str, Any]],
) -> int:
    if not rows:
        return 0
    count = 0
    for row in rows:
        instrument_id = str(row.get("instrument_id") or "")
        if instrument_id and not topic_rows.get(instrument_id):
            count += 1
    return count


def limit_ladder_theme_rank_rows(
    rows: Sequence[Mapping[str, Any]],
    topic_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    topic_type: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    row_by_instrument_id = {str(row.get("instrument_id") or ""): row for row in rows}
    for instrument_id, topics in topic_rows.items():
        row = row_by_instrument_id.get(str(instrument_id))
        if not row or row.get("limit_status") != "sealed":
            continue
        seen_names: set[str] = set()
        for topic in topics:
            topic_name = str(topic.get("topic_name") or "").strip()
            if not topic_name or topic_name in seen_names or limit_ladder_theme_is_noise(topic_name):
                continue
            seen_names.add(topic_name)
            item = grouped.setdefault(
                topic_name,
                {
                    "rank": None,
                    "trade_date": row.get("trade_date"),
                    "topic_type": topic_type,
                    "topic_name": topic_name,
                    "topic_id": topic.get("topic_id"),
                    "theme_strength_score": 0.0,
                    "limit_up_count": 0,
                    "highest_ladder_level": 0,
                    "lianban_stock_count": 0,
                    "first_board_count": 0,
                    "leader_instrument_id": None,
                    "leader_name": None,
                    "leader_ladder_level": None,
                    "leader_limit_board_text": None,
                    "leader_seal_amount": None,
                    "seal_amount_sum": 0.0,
                    "amount_sum": 0.0,
                    "top_stock_summary": None,
                    "_stocks": [],
                },
            )
            if not item.get("topic_id") and topic.get("topic_id"):
                item["topic_id"] = topic.get("topic_id")
            ladder_level = int(row.get("ladder_level") or 0)
            item["limit_up_count"] += 1
            item["highest_ladder_level"] = max(int(item["highest_ladder_level"] or 0), ladder_level)
            if ladder_level >= 2:
                item["lianban_stock_count"] += 1
            else:
                item["first_board_count"] += 1
            item["seal_amount_sum"] += float(row.get("seal_amount") or 0)
            item["amount_sum"] += float(row.get("amount") or 0)
            item["_stocks"].append(row)

    result: list[dict[str, Any]] = []
    for item in grouped.values():
        stocks = sorted(
            item.pop("_stocks"),
            key=lambda row: (
                -int(row.get("ladder_level") or 0),
                -float(row.get("seal_amount") or 0),
                int(row.get("rank") or 0),
            ),
        )
        leader = stocks[0] if stocks else {}
        item["leader_instrument_id"] = leader.get("instrument_id")
        item["leader_name"] = leader.get("name")
        item["leader_ladder_level"] = leader.get("ladder_level")
        item["leader_limit_board_text"] = leader.get("limit_board_text")
        item["leader_seal_amount"] = leader.get("seal_amount")
        item["top_stock_summary"] = " ".join(limit_ladder_stock_summary_text(stock) for stock in stocks[:5]) or None
        item["seal_amount_sum"] = round(float(item["seal_amount_sum"] or 0), 6)
        item["amount_sum"] = round(float(item["amount_sum"] or 0), 6)
        item["theme_strength_score"] = limit_ladder_theme_strength_score(
            {
                "same_theme_limit_up_count": item["limit_up_count"],
                "same_theme_highest_board": item["highest_ladder_level"],
                "same_theme_lianban_count": item["lianban_stock_count"],
            }
        )
        result.append(item)

    result.sort(
        key=lambda item: (
            -int(item.get("limit_up_count") or 0),
            -int(item.get("highest_ladder_level") or 0),
            -int(item.get("lianban_stock_count") or 0),
            -float(item.get("theme_strength_score") or 0),
            -float(item.get("seal_amount_sum") or 0),
            str(item.get("topic_name") or ""),
        )
    )
    for index, item in enumerate(result, start=1):
        item["rank"] = index
    return result


def limit_ladder_stock_summary_text(stock: Mapping[str, Any]) -> str:
    name = str(stock.get("name") or stock.get("instrument_id") or "").strip()
    board_text = str(stock.get("limit_board_text") or "").strip()
    if not name:
        return ""
    if board_text:
        return f"{name}（{board_text}）"
    ladder_level = int(stock.get("ladder_level") or 0)
    return f"{name}（{ladder_level}板）" if ladder_level > 0 else name


def limit_ladder_theme_strength_score(item: Mapping[str, Any]) -> float:
    return round(
        float(item.get("same_theme_limit_up_count") or 0) * 100
        + float(item.get("same_theme_highest_board") or 0) * 10
        + float(item.get("same_theme_lianban_count") or 0) * 5,
        6,
    )


def limit_ladder_theme_is_noise(topic_name: Any) -> bool:
    text = str(topic_name or "").strip()
    if not text:
        return True
    upper_text = text.upper()
    return any(keyword.upper() in upper_text for keyword in LIMIT_LADDER_THEME_NOISE_KEYWORDS)


def _round_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)
