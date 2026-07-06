"""Chinese display copy migrated from the old Web request catalog.

This module is intentionally metadata-only. It does not perform source
requests, collection, or network access; built-in Provider projection uses it
to expose the same display fields that external provider manifests can carry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class SourceDisplayDoc:
    summary_zh: str = ""
    description_zh: str = ""
    params_note_zh: str = ""
    params_example_zh: str = ""


_DISPLAY_DOCS: Mapping[str, SourceDisplayDoc] = {
    "stock_trade_calendar_exchange": SourceDisplayDoc(
        summary_zh="从深交所官方交易日历返回指定日期范围内的开闭市信息。",
        description_zh="不传日期时默认返回当前自然年；传 year 返回全年；传 start_date/end_date 返回指定范围。",
        params_note_zh="日期优先级：start_date/end_date > year > 当前自然年。",
        params_example_zh=(
            "# 指定日期范围\n"
            "client.call(\n"
            '    "stock_trade_calendar_exchange",\n'
            '    start_date="20260617",\n'
            '    end_date="20260622",\n'
            ")\n"
            "\n"
            "# 指定年份\n"
            'client.call("stock_trade_calendar_exchange", year=2026)\n'
            "\n"
            "# 不传日期，默认当前自然年\n"
            'client.call("stock_trade_calendar_exchange")'
        ),
    ),
    "stock_basic_info_exchange": SourceDisplayDoc(
        summary_zh="返回交易所官方当前股票基础资料；不传参数默认全部支持交易所。",
        description_zh=(
            "用于查看交易所官方当前股票基础资料，例如名称、板块、行业、地区、上市日期和股本信息；"
            "这是当前列表口径，不表示历史某天状态。"
        ),
        params_note_zh=(
            "这是当前官方股票基础资料接口；不传参数默认返回全部支持交易所。"
            "不同交易所公开字段不完全一致，源端未提供的字段返回空值。"
        ),
        params_example_zh=(
            "# 查询单只股票\n"
            'client.call("stock_basic_info_exchange", code="000001.SZ")\n'
            "\n"
            "# 按交易所查询\n"
            'client.call("stock_basic_info_exchange", exchange="SZSE")\n'
            "\n"
            "# 批量查询\n"
            "client.call(\n"
            '    "stock_basic_info_exchange",\n'
            '    code=["000001.SZ", "600000.SH"],\n'
            ")"
        ),
    ),
    "stock_historical_list_exchange": SourceDisplayDoc(
        summary_zh="按交易所官方上市日期和退市日期计算一个或多个日期仍处于上市生命周期内的股票列表。",
        description_zh=(
            "传 trade_date 返回单日或多个指定日期的股票池；传 start_date/end_date 返回连续日期范围；"
            "可用 exchange 限定 SSE、SZSE 或 BSE。"
        ),
        params_note_zh="判断规则：上市日期不晚于目标日期，且未退市或退市日期不早于目标日期；trade_date 和 start_date/end_date 二选一。",
        params_example_zh=(
            "# 指定日期和交易所\n"
            "client.call(\n"
            '    "stock_historical_list_exchange",\n'
            '    trade_date="20240102",\n'
            '    exchange="SZSE",\n'
            ")\n"
            "\n"
            "# 批量指定多个日期\n"
            "client.call(\n"
            '    "stock_historical_list_exchange",\n'
            '    trade_date=["20240102", "20240103"],\n'
            '    exchange="SZSE",\n'
            ")\n"
            "\n"
            "# 指定连续日期范围\n"
            "client.call(\n"
            '    "stock_historical_list_exchange",\n'
            '    start_date="20240102",\n'
            '    end_date="20240105",\n'
            ")"
        ),
    ),
    "cninfo_announcements": SourceDisplayDoc(
        summary_zh="按股票和日期范围临时获取巨潮公告元信息。",
        description_zh="这个接口返回公告元信息和 PDF 下载地址。",
        params_note_zh="不传 fields 时返回上方全部字段；临时调用只查一次。",
        params_example_zh='client.call("cninfo_announcements", code="000001.SZ", start_date="20240101", end_date="20240131", limit=3)',
    ),
    "cninfo_announcement_detail": SourceDisplayDoc(
        summary_zh="确认巨潮公告 PDF 的文件类型、大小和下载地址；不解析正文。",
        description_zh="这个接口只确认 PDF 文件类型、大小和下载地址，不解析 PDF 正文。",
        params_note_zh="url 可以传完整 PDF 地址，也可以传巨潮返回的相对路径。",
        params_example_zh=(
            'client.call("cninfo_announcement_detail", announcement_id="1218968511", '
            'url="https://static.cninfo.com.cn/finalpage/2024-01-23/1218968511.PDF")'
        ),
    ),
    "tencent_realtime_snapshot": SourceDisplayDoc(
        summary_zh="临时获取腾讯财经快照，覆盖 A 股、指数和 ETF 的确认字段。",
        description_zh="这个接口返回源端快照时间；价格单位为元或指数点，比例字段是百分比数值。",
        params_note_zh="不传 fields 时返回上方全部字段；临时调用只查一次。",
        params_example_zh='client.call("tencent_realtime_snapshot", code=["000001.SZ", "600000.SH"])',
    ),
    "eastmoney_dragon_tiger_daily": SourceDisplayDoc(
        summary_zh="低频获取东方财富龙虎榜每日汇总，金额单位为元。",
        description_zh="这个接口只保留已确认字段；金额字段单位为元，遇到源端空结果返回空表。",
        params_note_zh="不传 fields 时返回上方全部字段；临时调用只查一次。",
        params_example_zh='client.call("eastmoney_dragon_tiger_daily", trade_date="20240102", limit=5)',
    ),
    "eastmoney_margin_trading": SourceDisplayDoc(
        summary_zh="低频获取单股融资融券明细，金额单位为元，融券数量单位为股。",
        description_zh="这个接口只保留已确认字段；金额字段单位为元，遇到源端空结果返回空表。",
        params_note_zh="不传 fields 时返回上方全部字段；临时调用只查一次。",
        params_example_zh='client.call("eastmoney_margin_trading", code="000001.SZ", start_date="20240102", end_date="20240105", limit=5)',
    ),
    "eastmoney_research_reports": SourceDisplayDoc(
        summary_zh="低频获取个股研报列表元信息；不抓取 PDF 正文。",
        description_zh="这个接口只保留已确认字段；金额字段单位为元，遇到源端空结果返回空表。",
        params_note_zh="不传 fields 时返回上方全部字段；临时调用只查一次。",
        params_example_zh='client.call("eastmoney_research_reports", code="000001.SZ", start_date="20240101", end_date="20241231", limit=5)',
    ),
}


def display_doc_for_interface(interface_name: str) -> SourceDisplayDoc:
    return _DISPLAY_DOCS.get(interface_name, SourceDisplayDoc())
