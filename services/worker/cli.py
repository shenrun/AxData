"""Command line entry point for collection worker jobs."""

from __future__ import annotations

import argparse
import json
from typing import Any

from services.collector import normalize_dataset
from services.worker.jobs import run_update_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m services.worker.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser("update", help="run an update job")
    update_parser.add_argument(
        "dataset",
        choices=[
            "stock_basic",
            "stock-basic",
            "stock_basic_exchange",
            "stock-basic-exchange",
            "trade_cal",
            "trade-cal",
            "daily",
            "adj_factor",
            "adj-factor",
        ],
        help="dataset to update",
    )
    update_parser.add_argument(
        "--source",
        "--adapter",
        dest="source",
        default="csv",
        choices=["csv", "official_exchange", "official", "exchange"],
        help="collector source adapter",
    )
    update_parser.add_argument(
        "--path",
        help="CSV file for the selected dataset, or a directory containing dataset CSVs",
    )
    update_parser.add_argument(
        "--batch-id",
        help="optional batch id; generated when omitted",
    )
    update_parser.add_argument(
        "--data-root",
        help="AxData data root for persisted core parquet tables. Defaults to AXDATA_DATA_DIR or ./data.",
    )
    update_parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra fetch parameter; repeatable",
    )
    update_parser.add_argument(
        "--limit",
        type=int,
        help="limit rows returned by the adapter",
    )
    update_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="fetch rows and report status without writing to storage",
    )
    update_parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="run the placeholder persistence step after fetching",
    )
    update_parser.add_argument(
        "--pretty",
        action="store_true",
        help="pretty-print status JSON",
    )
    return parser


def parse_params(items: list[str], limit: int | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --param '{item}'. Expected KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --param '{item}'. Parameter key cannot be empty")
        params[key] = value

    if limit is not None:
        params["limit"] = limit
    return params


def run_update(args: argparse.Namespace) -> int:
    params = parse_params(args.param, args.limit)
    result = run_update_job(
        normalize_dataset(args.dataset),
        source=args.source,
        path=args.path,
        dry_run=args.dry_run,
        batch_id=args.batch_id,
        data_root=args.data_root,
        params=params,
    )
    indent = 2 if args.pretty else None
    print(json.dumps(result.state.to_dict(), ensure_ascii=False, indent=indent))
    return 1 if result.state.status == "failed" else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "update":
            return run_update(args)
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
