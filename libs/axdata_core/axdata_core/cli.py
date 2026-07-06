"""AxData command line utilities."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any

from .plugin_config import disable_provider, enable_provider, load_plugin_config, plugin_config_path
from .plugins import (
    MANIFEST_FILE_NAME,
    MANIFEST_VERSION,
    PLUGIN_API_VERSION,
    ProviderManifest,
    manifest_from_provider,
    validate_manifest,
)


MAX_CLI_RUN_LIST_LIMIT = 500
DEFAULT_CLI_STATUS_RUN_LIMIT = 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="axdata")
    parser.add_argument(
        "--data-root",
        help="AxData data root. Defaults to AXDATA_DATA_DIR or ./data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize local AxData directories")
    init_parser.add_argument("--json", action="store_true", help="print JSON")

    config_parser = subparsers.add_parser("config", help="show local AxData configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_show_parser = config_subparsers.add_parser("show", help="show resolved local paths and ports")
    config_show_parser.add_argument("--json", action="store_true", help="print JSON")

    doctor_parser = subparsers.add_parser("doctor", help="diagnose the local AxData environment")
    doctor_parser.add_argument("--json", action="store_true", help="print JSON")

    status_parser = subparsers.add_parser("status", help="alias for doctor")
    status_parser.add_argument("--json", action="store_true", help="print JSON")

    data_parser = subparsers.add_parser("data", help="browse locally collected datasets")
    data_subparsers = data_parser.add_subparsers(dest="data_command", required=True)

    data_list_parser = data_subparsers.add_parser("list", help="list discovered local datasets")
    data_list_parser.add_argument("--json", action="store_true", help="print JSON")

    data_inspect_parser = data_subparsers.add_parser("inspect", help="show one dataset")
    data_inspect_parser.add_argument("dataset", help="dataset or interface name")
    data_inspect_parser.add_argument("--json", action="store_true", help="print JSON")

    data_preview_parser = data_subparsers.add_parser("preview", help="preview rows from one dataset")
    data_preview_parser.add_argument("dataset", help="dataset or interface name")
    data_preview_parser.add_argument("--fields", help="comma-separated fields")
    data_preview_parser.add_argument("--symbol", help="filter by ts_code/instrument_id/symbol when present")
    data_preview_parser.add_argument("--start", help="start date, YYYYMMDD or YYYY-MM-DD")
    data_preview_parser.add_argument("--end", help="end date, YYYYMMDD or YYYY-MM-DD")
    data_preview_parser.add_argument("--filter", action="append", default=[], help="exact filter key=value; repeatable")
    data_preview_parser.add_argument("--limit", type=int, default=20, help="maximum rows, capped at 100")
    data_preview_parser.add_argument("--json", action="store_true", help="print JSON")

    query_parser = subparsers.add_parser("query", help="small filtered query over a local dataset")
    query_parser.add_argument("dataset", help="dataset or interface name")
    query_parser.add_argument("--fields", help="comma-separated fields")
    query_parser.add_argument("--symbol", help="filter by ts_code/instrument_id/symbol when present")
    query_parser.add_argument("--start", help="start date, YYYYMMDD or YYYY-MM-DD")
    query_parser.add_argument("--end", help="end date, YYYYMMDD or YYYY-MM-DD")
    query_parser.add_argument("--filter", action="append", default=[], help="exact filter key=value; repeatable")
    query_parser.add_argument("--limit", type=int, default=100, help="maximum rows, capped at 100")
    query_parser.add_argument("--json", action="store_true", help="print JSON")

    request_parser = subparsers.add_parser("request", help="call a source request interface without persisting data")
    request_parser.add_argument("interface", help="source request interface name")
    request_parser.add_argument("--params", help="JSON object passed as source-interface params")
    request_parser.add_argument("--param", action="append", default=[], help="single source param key=value; repeatable")
    request_parser.add_argument("--fields", help="comma-separated fields")
    request_parser.add_argument("--option", action="append", default=[], help="execution option key=value; repeatable")
    request_parser.add_argument("--limit", type=int, default=20, help="maximum rows to print in text mode")
    request_parser.add_argument("--json", action="store_true", help="print JSON")

    collector_parser = subparsers.add_parser("collector", help="manage local Collector tasks and runs")
    collector_subparsers = collector_parser.add_subparsers(dest="collector_command", required=True)

    collector_task_parser = collector_subparsers.add_parser("task", help="manage Collector tasks")
    collector_task_subparsers = collector_task_parser.add_subparsers(dest="collector_task_command", required=True)

    task_templates_parser = collector_task_subparsers.add_parser("templates", help="list built-in Collector task templates")
    task_templates_parser.add_argument("--json", action="store_true", help="print JSON")

    task_list_parser = collector_task_subparsers.add_parser("list", help="list Collector tasks")
    task_list_parser.add_argument("--json", action="store_true", help="print JSON")

    task_create_template_parser = collector_task_subparsers.add_parser(
        "create-from-template",
        help="create a Collector task from a built-in template",
    )
    task_create_template_parser.add_argument("template_id", help="task template id")
    task_create_template_parser.add_argument("--task-id", help="stable task id")
    task_create_template_parser.add_argument("--name", help="display name")
    task_create_template_parser.add_argument("--disabled", action="store_true", help="create disabled")
    task_create_template_parser.add_argument("--trigger-type", help="manual, interval, daily, or startup")
    task_create_template_parser.add_argument("--interval-seconds", type=int, help="interval trigger seconds")
    task_create_template_parser.add_argument("--daily-time", help="daily local time, HH:MM")
    task_create_template_parser.add_argument("--params", help="JSON object merged over template default_params")
    task_create_template_parser.add_argument("--fields", help="comma-separated fields")
    task_create_template_parser.add_argument("--formats", help="comma-separated output formats")
    task_create_template_parser.add_argument("--json", action="store_true", help="print JSON")

    task_add_parser = collector_task_subparsers.add_parser("add", help="add a Collector task")
    task_add_parser.add_argument("collector_name", help="CollectorSpec name")
    task_add_parser.add_argument("--task-id", help="stable task id")
    task_add_parser.add_argument("--name", help="display name")
    task_add_parser.add_argument("--disabled", action="store_true", help="create disabled")
    task_add_parser.add_argument("--trigger-type", default="manual", help="manual, interval, daily, or startup")
    task_add_parser.add_argument("--interval-seconds", type=int, help="interval trigger seconds")
    task_add_parser.add_argument("--daily-time", help="daily local time, HH:MM")
    task_add_parser.add_argument("--params", help="JSON object merged over collector default_params")
    task_add_parser.add_argument("--fields", help="comma-separated fields")
    task_add_parser.add_argument("--output-root", help="output root")
    task_add_parser.add_argument("--output-dir", help="final output directory")
    task_add_parser.add_argument("--formats", help="comma-separated output formats")
    _add_collector_runtime_args(task_add_parser)
    task_add_parser.add_argument("--json", action="store_true", help="print JSON")

    task_info_parser = collector_task_subparsers.add_parser("info", help="show one Collector task")
    task_info_parser.add_argument("task_id", help="task id")
    task_info_parser.add_argument("--json", action="store_true", help="print JSON")

    task_enable_parser = collector_task_subparsers.add_parser("enable", help="enable one Collector task")
    task_enable_parser.add_argument("task_id", help="task id")
    task_enable_parser.add_argument("--json", action="store_true", help="print JSON")

    task_disable_parser = collector_task_subparsers.add_parser("disable", help="disable one Collector task")
    task_disable_parser.add_argument("task_id", help="task id")
    task_disable_parser.add_argument("--json", action="store_true", help="print JSON")

    task_run_parser = collector_task_subparsers.add_parser("run", help="run one Collector task")
    task_run_parser.add_argument("task_id", help="task id")
    task_run_parser.add_argument("--trigger-type", default="manual", help="manual, interval, daily, or startup")
    task_run_parser.add_argument("--params", help="JSON params merged only into this run")
    task_run_parser.add_argument("--start", help="date override, YYYYMMDD or YYYY-MM-DD")
    task_run_parser.add_argument("--end", help="date override, YYYYMMDD or YYYY-MM-DD")
    task_run_parser.add_argument("--symbol", help="code/symbol override for this run")
    task_run_parser.add_argument("--limit", type=int, help="limit/count override for this run")
    task_run_parser.add_argument("--wait", action="store_true", help="wait for completion")
    task_run_parser.add_argument("--json", action="store_true", help="print JSON")

    task_backfill_parser = collector_task_subparsers.add_parser("backfill", help="run one Collector task for a date range")
    task_backfill_parser.add_argument("task_id", help="task id")
    task_backfill_parser.add_argument("--start", required=True, help="start date, YYYYMMDD or YYYY-MM-DD")
    task_backfill_parser.add_argument("--end", required=True, help="end date, YYYYMMDD or YYYY-MM-DD")
    task_backfill_parser.add_argument("--params", help="JSON params merged only into this backfill run")
    task_backfill_parser.add_argument("--symbol", help="code/symbol override for this run")
    task_backfill_parser.add_argument("--limit", type=int, help="limit/count override for this run")
    task_backfill_parser.add_argument("--wait", action="store_true", help="wait for completion")
    task_backfill_parser.add_argument("--json", action="store_true", help="print JSON")

    collector_run_parser = collector_subparsers.add_parser("run", help="inspect Collector runs")
    collector_run_subparsers = collector_run_parser.add_subparsers(dest="collector_run_command", required=True)

    run_list_parser = collector_run_subparsers.add_parser("list", help="list Collector runs")
    run_list_parser.add_argument("--task-id", help="filter by task id")
    run_list_parser.add_argument("--status", help="filter by run status")
    run_list_parser.add_argument("--limit", type=int, default=20, help="maximum rows")
    run_list_parser.add_argument("--json", action="store_true", help="print JSON")

    run_info_parser = collector_run_subparsers.add_parser("info", help="show one Collector run")
    run_info_parser.add_argument("run_id", help="run id")
    run_info_parser.add_argument("--json", action="store_true", help="print JSON")

    collector_status_parser = collector_subparsers.add_parser("status", help="show Collector scheduler status")
    collector_status_parser.add_argument("--json", action="store_true", help="print JSON")

    plugin_parser = subparsers.add_parser("plugin", help="manage AxData source providers")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command", required=True)

    list_parser = plugin_subparsers.add_parser("list", help="list discovered providers")
    list_parser.add_argument("--json", action="store_true", help="print JSON")

    installed_parser = plugin_subparsers.add_parser("installed", help="list AxData-managed installed plugins")
    installed_parser.add_argument("--json", action="store_true", help="print JSON")

    list_installed_parser = plugin_subparsers.add_parser(
        "list-installed",
        help="alias for installed",
    )
    list_installed_parser.add_argument("--json", action="store_true", help="print JSON")

    info_parser = plugin_subparsers.add_parser("info", help="show one provider manifest")
    info_parser.add_argument("provider_id", help="provider id")
    info_parser.add_argument("--json", action="store_true", help="print JSON")

    collectors_parser = plugin_subparsers.add_parser("collectors", help="list enabled collector capabilities")
    collectors_parser.add_argument("--json", action="store_true", help="print JSON")

    collector_info_parser = plugin_subparsers.add_parser("collector-info", help="show one collector capability")
    collector_info_parser.add_argument("collector_name", help="collector name")
    collector_info_parser.add_argument("--json", action="store_true", help="print JSON")

    collector_run_parser = plugin_subparsers.add_parser("collector-run", help="run one collector capability")
    collector_run_parser.add_argument("collector_name", help="collector name")
    collector_run_parser.add_argument("--params", help="JSON object merged over collector default_params")
    collector_run_parser.add_argument("--fields", help="comma-separated fields to persist")
    collector_run_parser.add_argument("--output-root", help="directory used as the downloader output root")
    collector_run_parser.add_argument("--output-dir", help="final directory where output files are written")
    collector_run_parser.add_argument("--formats", help="comma-separated output file formats")
    collector_run_parser.add_argument("--collect-mode", help="collection mode")
    collector_run_parser.add_argument("--connection-mode", help="downloader connection mode")
    collector_run_parser.add_argument("--concurrency-mode", help="downloader concurrency preset mode")
    collector_run_parser.add_argument("--connection-count", type=int, help="number of source connections/workers")
    collector_run_parser.add_argument("--source-server-count", type=int, help="number of source servers to use")
    collector_run_parser.add_argument("--connections-per-server", type=int, help="long connections per source server")
    collector_run_parser.add_argument("--max-concurrent-tasks", type=int, help="maximum concurrent downloader tasks")
    collector_run_parser.add_argument("--batch-size", type=int, help="downloader task batch size")
    collector_run_parser.add_argument("--request-interval-ms", type=int, help="interval between source requests")
    collector_run_parser.add_argument("--retry-count", type=int, help="retry count for source requests")
    collector_run_parser.add_argument("--timeout-ms", type=int, help="per-request timeout in milliseconds")
    collector_run_parser.add_argument("--json", action="store_true", help="print JSON")

    check_parser = plugin_subparsers.add_parser("check", help="validate one plugin/provider manifest")
    _add_provider_source_args(check_parser, required=False)
    check_parser.add_argument(
        "--manifest",
        help="manifest path to validate, or compare with the Provider-generated manifest",
    )

    build_manifest_parser = plugin_subparsers.add_parser("build", help="generate provider manifest JSON")
    _add_provider_source_args(build_manifest_parser)
    build_manifest_parser.add_argument(
        "--output",
        "-o",
        help=f"output manifest path. Defaults to ./{MANIFEST_FILE_NAME}.",
    )

    enable_parser = plugin_subparsers.add_parser("enable", help="enable a provider in AxData config")
    enable_parser.add_argument("provider_id", help="provider id")

    disable_parser = plugin_subparsers.add_parser("disable", help="disable a provider in AxData config")
    disable_parser.add_argument("provider_id", help="provider id")

    uninstall_parser = plugin_subparsers.add_parser("uninstall", help="uninstall an AxData-managed external plugin")
    uninstall_parser.add_argument("provider_id", help="provider id")
    uninstall_parser.add_argument("--json", action="store_true", help="print JSON")
    uninstall_parser.add_argument(
        "--disable-first",
        action="store_true",
        help="disable the Provider before uninstalling. Default refuses enabled Providers.",
    )

    axp_preview_parser = plugin_subparsers.add_parser("axp-preview", help="preview an AXP plugin archive")
    axp_preview_parser.add_argument("path", help="AXP archive path")
    axp_preview_parser.add_argument("--json", action="store_true", help="print JSON")

    axp_install_parser = plugin_subparsers.add_parser("axp-install", help="install an AXP plugin archive")
    axp_install_parser.add_argument("path", help="AXP archive path")
    axp_install_parser.add_argument(
        "--install-root",
        help="plugin install root. Defaults to metadata-adjacent AxData plugins directory.",
    )
    axp_install_parser.add_argument(
        "--enable",
        action="store_true",
        help="enable the Provider after install. Default is installed but disabled.",
    )
    axp_install_parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing AxData-managed install for the same provider_id.",
    )
    axp_install_parser.add_argument(
        "--no-pth",
        action="store_true",
        help="do not write a user-site .pth file for future process discovery.",
    )
    axp_install_parser.add_argument(
        "--allow-online-deps",
        action="store_true",
        help="allow pip to install missing required dependencies from configured indexes. Default is offline.",
    )
    axp_install_parser.add_argument("--json", action="store_true", help="print JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return _init_local(args)
        if args.command == "config":
            return _run_config_cli(args)
        if args.command in {"doctor", "status"}:
            return _doctor(args)
        if args.command == "data":
            return _run_data_cli(args)
        if args.command == "query":
            return _query_local(args)
        if args.command == "request":
            return _source_request(args)
        if args.command == "collector":
            return _run_collector_cli(args)
        if args.command == "plugin":
            return _run_plugin(args)
    except (ImportError, AttributeError, KeyError, ValueError, OSError) as exc:
        parser.error(str(exc))

    parser.error(f"Unknown command: {args.command}")
    return 2


def _init_local(args: argparse.Namespace) -> int:
    from .diagnostics import initialize_local_environment

    payload = initialize_local_environment(args.data_root)
    if args.json:
        _print_json(payload)
        return 0
    print(f"data_root\t{payload['data_root']}")
    print(f"metadata_root\t{payload['metadata_root']}")
    print(f"plugin_site_packages\t{payload['plugin_site_packages']}")
    print(f"plugin_config\t{payload['plugin_config_path']}")
    print(f"created\t{len(payload['created'])}")
    print(f"existing\t{len(payload['existing'])}")
    return 0


def _run_config_cli(args: argparse.Namespace) -> int:
    command = args.config_command
    if command == "show":
        return _config_show(args)
    raise ValueError(f"Unknown config command: {command}")


def _run_data_cli(args: argparse.Namespace) -> int:
    command = args.data_command
    if command == "list":
        return _data_list(args)
    if command == "inspect":
        return _data_inspect(args)
    if command == "preview":
        return _data_preview(args)
    raise ValueError(f"Unknown data command: {command}")


def _data_list(args: argparse.Namespace) -> int:
    from .data_browser import list_datasets

    rows = [item.to_dict() for item in list_datasets(data_root=args.data_root)]
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No local datasets found.")
        print("Run a Collector/Downloader first, for example: axdata collector task run <task_id> --wait --json")
        return 0
    print("dataset\tlayer\tprovider\trows\tdate_range\tquality\tupdated_at")
    for row in rows:
        date_range = _format_date_range(row)
        print(
            "\t".join(
                [
                    row["dataset"],
                    row.get("layer") or "",
                    row.get("provider") or row.get("source") or "",
                    str(row.get("row_count") if row.get("row_count") is not None else ""),
                    date_range,
                    row.get("quality_status") or "",
                    row.get("updated_at") or "",
                ]
            )
        )
    return 0


def _data_inspect(args: argparse.Namespace) -> int:
    from .data_browser import get_dataset

    dataset = get_dataset(args.dataset, data_root=args.data_root)
    payload = dataset.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"dataset\t{payload['dataset']}")
    print(f"interface\t{payload['interface_name']}")
    print(f"layer\t{payload.get('layer') or ''}")
    print(f"provider\t{payload.get('provider') or payload.get('source') or ''}")
    print(f"rows\t{payload.get('row_count') if payload.get('row_count') is not None else ''}")
    print(f"date_range\t{_format_date_range(payload)}")
    if payload.get("write_mode"):
        print(f"write_mode\t{payload.get('write_mode')}")
    if payload.get("primary_key"):
        print("primary_key\t" + ",".join(payload["primary_key"]))
    if payload.get("partition_by"):
        print("partition_by\t" + ",".join(payload["partition_by"]))
    if payload.get("date_field"):
        print(f"date_field\t{payload.get('date_field')}")
    for key in (
        "rows_before",
        "rows_written",
        "rows_after",
        "duplicate_rows_dropped",
        "replace_range_start",
        "replace_range_end",
    ):
        if payload.get(key) is not None:
            print(f"{key}\t{payload.get(key)}")
    print(f"quality\t{payload.get('quality_status') or ''}")
    quality = payload.get("quality") or {}
    if isinstance(quality, dict):
        for key in (
            "calendar_coverage_status",
            "date_gap_count",
            "extra_non_trading_dates",
            "price_ohlc_anomaly_count",
            "negative_volume_count",
            "negative_amount_count",
            "invalid_adj_factor_count",
        ):
            if key in quality:
                print(f"{key}\t{_cell_text(quality.get(key))}")
    for warning in payload.get("quality_warnings") or []:
        print(f"warning\t{warning}")
    for error in payload.get("quality_errors") or []:
        print(f"error\t{error}")
    if payload.get("columns"):
        print("columns\t" + ",".join(payload["columns"]))
    for format_name, path in sorted((payload.get("output_paths") or {}).items()):
        print(f"path\t{format_name}\t{path}")
    if payload.get("missing_paths"):
        for path in payload["missing_paths"]:
            print(f"missing_path\t{path}")
        print("message\tRun metadata points to missing files; rerun collection or inspect the run.")
    return 0


def _data_preview(args: argparse.Namespace) -> int:
    from .data_browser import preview_dataset

    preview = preview_dataset(
        args.dataset,
        data_root=args.data_root,
        fields=args.fields,
        filters=_parse_filter_args(getattr(args, "filter", None) or []),
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        limit=args.limit,
    )
    payload = preview.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    rows = payload["rows"]
    if not rows:
        print(f"No rows matched dataset {payload['dataset']['dataset']}.")
        return 0
    _print_rows(rows, payload["columns"])
    return 0


def _query_local(args: argparse.Namespace) -> int:
    from .data_browser import preview_dataset
    from .query import query_table
    from .schema import get_schema

    fields = _comma_list_arg(args.fields)
    filters = _parse_filter_args(getattr(args, "filter", None) or [])
    try:
        schema = get_schema(args.dataset)
        if args.symbol:
            symbol_field = _schema_symbol_field(schema)
            if symbol_field:
                filters.setdefault(symbol_field, args.symbol)
        query_fields = fields or list(schema.field_names)
        frame = query_table(
            args.dataset,
            root=args.data_root or os.getenv("AXDATA_DATA_DIR", "data"),
            filters=filters,
            fields=query_fields,
            start_date=_normalize_date_text(args.start),
            end_date=_normalize_date_text(args.end),
            limit=args.limit,
        )
        payload = {
            "dataset": {"dataset": schema.name, "interface_name": schema.name, "layer": "core"},
            "rows": frame.to_dict(orient="records"),
            "limit": args.limit,
            "filters": {**filters, **_date_filter_payload(args.start, args.end)},
            "columns": list(frame.columns),
            "count": len(frame),
        }
    except (KeyError, FileNotFoundError):
        preview = preview_dataset(
            args.dataset,
            data_root=args.data_root,
            fields=args.fields,
            filters=_parse_filter_args(getattr(args, "filter", None) or []),
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            limit=args.limit,
        )
        payload = preview.to_dict()

    if args.json:
        _print_json(payload)
        return 0
    rows = payload["rows"]
    if not rows:
        dataset = payload.get("dataset") or {}
        dataset_name = dataset.get("dataset") if isinstance(dataset, dict) else args.dataset
        print(f"No rows matched dataset {dataset_name}.")
        return 0
    _print_rows(rows, payload["columns"])
    return 0


def _schema_symbol_field(schema: Any) -> str | None:
    fields = set(getattr(schema, "field_names", ()) or ())
    for candidate in ("ts_code", "instrument_id", "symbol", "code"):
        if candidate in fields:
            return candidate
    return None


def _source_request(args: argparse.Namespace) -> int:
    from .source_errors import (
        SourceAdapterError,
        SourceAdapterNotFound,
        SourceInterfaceNotFound,
        SourceRequestValidationError,
        SourceUnavailableError,
    )
    from .source_request import request_interface

    params = _json_object_arg(args.params, "--params") or {}
    params.update(_parse_key_value_args(getattr(args, "param", None) or [], "--param"))
    options = _parse_key_value_args(getattr(args, "option", None) or [], "--option")
    fields = _comma_list_arg(args.fields)

    try:
        result = request_interface(
            args.interface,
            params=params,
            fields=fields,
            persist=False,
            options=options or None,
            data_root=args.data_root,
        )
    except SourceInterfaceNotFound as exc:
        return _print_source_request_error(
            code="SOURCE_INTERFACE_NOT_FOUND",
            message=str(exc),
            interface_name=args.interface,
            params=params,
            fields=fields,
            options=options,
            args=args,
        )
    except SourceRequestValidationError as exc:
        return _print_source_request_error(
            code="SOURCE_REQUEST_VALIDATION_ERROR",
            message=str(exc),
            interface_name=args.interface,
            params=params,
            fields=fields,
            options=options,
            args=args,
        )
    except SourceAdapterNotFound as exc:
        return _print_source_request_error(
            code="SOURCE_ADAPTER_NOT_FOUND",
            message=str(exc),
            interface_name=args.interface,
            params=params,
            fields=fields,
            options=options,
            args=args,
        )
    except SourceUnavailableError as exc:
        return _print_source_request_error(
            code="SOURCE_UNAVAILABLE",
            message=str(exc),
            interface_name=args.interface,
            params=params,
            fields=fields,
            options=options,
            args=args,
        )
    except SourceAdapterError as exc:
        return _print_source_request_error(
            code="SOURCE_ADAPTER_ERROR",
            message=str(exc),
            interface_name=args.interface,
            params=params,
            fields=fields,
            options=options,
            args=args,
        )

    meta = dict(result.meta)
    meta.update(
        {
            "interface_name": args.interface,
            "request_mode": "source_request",
            "persisted": False,
            "params": params,
            "options": options,
            "count": len(result.records),
        }
    )
    payload = {
        "success": True,
        "data": result.records,
        "meta": meta,
    }
    if args.json:
        _print_json(payload)
        return 0
    rows = result.records[: max(0, int(args.limit))]
    if not rows:
        print(f"No rows returned from source request {args.interface}.")
        print("persisted\tfalse")
        return 0
    columns = fields or list(rows[0])
    _print_rows(rows, columns)
    if len(result.records) > len(rows):
        print(f"# showing {len(rows)} of {len(result.records)} rows")
    return 0


def _config_show(args: argparse.Namespace) -> int:
    from .diagnostics import local_config

    payload = local_config(args.data_root)
    if args.json:
        _print_json(payload)
        return 0
    for key in (
        "data_root",
        "metadata_root",
        "plugin_config_path",
        "plugin_site_packages",
        "collector_store_path",
        "api_base",
        "web_base",
    ):
        print(f"{key}\t{payload[key]}")
    print(f"auth_enabled\t{str(payload['auth_enabled']).lower()}")
    return 0


def _doctor(args: argparse.Namespace) -> int:
    from .diagnostics import build_local_diagnostics

    payload = build_local_diagnostics(args.data_root)
    if args.json:
        _print_json(payload)
        return 0
    summary = payload["summary"]
    print(
        "status\t"
        f"{summary['status']}\t"
        f"ok={summary['ok']}\twarning={summary['warning']}\terror={summary['error']}"
    )
    print(f"python\t{payload['python']['version']}\t{payload['python']['executable']}")
    print(f"axdata\t{payload['axdata']['version']}")
    print(f"data_root\t{payload['config']['data_root']}")
    print(f"metadata_root\t{payload['config']['metadata_root']}")
    print(f"plugin_site_packages\t{payload['config']['plugin_site_packages']}")
    print(
        "registry\t"
        f"providers={payload['registry'].get('provider_count', 0)}\t"
        f"interfaces={payload['registry'].get('interface_count', 0)}\t"
        f"collectors={payload['registry'].get('collector_count', 0)}"
    )
    print(f"tdx\t{payload['tdx']['status']}\t{payload['tdx']['message']}")
    print(
        "collector\t"
        f"tasks={payload['collector'].get('task_count', 0)}\t"
        f"active={payload['collector'].get('active_run_count', 0)}"
    )
    print("checks")
    for check in payload["checks"]:
        print(
            "\t".join(
                [
                    str(check["status"]),
                    str(check["category"]),
                    str(check["name"]),
                    str(check["message"]),
                ]
            )
        )
    if payload["next_actions"]:
        print("next_actions")
        for action in payload["next_actions"]:
            print(f"- {action}")
    return 0


def _run_plugin(args: argparse.Namespace) -> int:
    command = args.plugin_command
    if command == "list":
        return _plugin_list(args)
    if command in {"installed", "list-installed"}:
        return _plugin_installed(args)
    if command == "info":
        return _plugin_info(args)
    if command == "collectors":
        return _plugin_collectors(args)
    if command == "collector-info":
        return _plugin_collector_info(args)
    if command == "collector-run":
        return _plugin_collector_run(args)
    if command == "check":
        return _plugin_check(args)
    if command == "build":
        return _plugin_build(args)
    if command == "enable":
        return _plugin_enable(args)
    if command == "disable":
        return _plugin_disable(args)
    if command == "uninstall":
        return _plugin_uninstall(args)
    if command == "axp-preview":
        return _plugin_axp_preview(args)
    if command == "axp-install":
        return _plugin_axp_install(args)
    raise ValueError(f"Unknown plugin command: {command}")


def _run_collector_cli(args: argparse.Namespace) -> int:
    command = args.collector_command
    if command == "task":
        return _run_collector_task(args)
    if command == "run":
        return _run_collector_run(args)
    if command == "status":
        return _collector_status(args)
    raise ValueError(f"Unknown collector command: {command}")


def _run_collector_task(args: argparse.Namespace) -> int:
    command = args.collector_task_command
    if command == "templates":
        return _collector_task_templates(args)
    if command == "list":
        return _collector_task_list(args)
    if command == "create-from-template":
        return _collector_task_create_from_template(args)
    if command == "add":
        return _collector_task_add(args)
    if command == "info":
        return _collector_task_info(args)
    if command == "enable":
        return _collector_task_enable(args)
    if command == "disable":
        return _collector_task_disable(args)
    if command == "run":
        return _collector_task_run(args)
    if command == "backfill":
        return _collector_task_backfill(args)
    raise ValueError(f"Unknown collector task command: {command}")


def _run_collector_run(args: argparse.Namespace) -> int:
    command = args.collector_run_command
    if command == "list":
        return _collector_run_list(args)
    if command == "info":
        return _collector_run_info(args)
    raise ValueError(f"Unknown collector run command: {command}")


def _collector_service(args: argparse.Namespace):
    from .collector_scheduler import CollectorSchedulerService

    return CollectorSchedulerService(data_root=args.data_root)


def _collector_task_list(args: argparse.Namespace) -> int:
    rows = [task.to_dict() for task in _collector_service(args).list_tasks()]
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No collector tasks.")
        return 0
    print("task_id\tenabled\ttrigger\tcollector\tdependency\twrite_mode\tresource_group\tlast_status\tnext_run_at\tmessage")
    for row in rows:
        print(
            "\t".join(
                [
                    row["task_id"],
                    str(row["enabled"]).lower(),
                    row["trigger_type"],
                    row["collector_name"],
                    row.get("dependency_status") or "",
                    row.get("write_mode") or "",
                    row.get("resource_group") or "",
                    row.get("last_status") or "",
                    row.get("next_run_at") or "",
                    row.get("status_message") or "",
                ]
            )
        )
    return 0


def _collector_task_templates(args: argparse.Namespace) -> int:
    from .collector_templates import list_task_templates

    rows = [template.to_dict() for template in list_task_templates(data_root=args.data_root)]
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No collector task templates.")
        return 0
    print("template_id\tavailable\tcollector\tresource_group\tschedule\tnext_action")
    for row in rows:
        print(
            "\t".join(
                [
                    row["template_id"],
                    str(row["available"]).lower(),
                    row["collector_name"],
                    row.get("resource_group") or "",
                    row.get("schedule_hint") or "",
                    row.get("action_command") or row.get("next_action") or "",
                ]
            )
        )
    return 0


def _collector_task_create_from_template(args: argparse.Namespace) -> int:
    from .collector_templates import task_template_to_create_kwargs

    kwargs = task_template_to_create_kwargs(
        args.template_id,
        data_root=args.data_root,
        task_id=args.task_id,
        name=args.name,
        enabled=not args.disabled,
        params=_json_object_arg(args.params, "--params") or None,
        fields=_comma_list_arg(args.fields),
        formats=_comma_list_arg(args.formats),
        trigger_type=args.trigger_type,
        interval_seconds=args.interval_seconds,
        daily_time=args.daily_time,
    )
    collector_name = kwargs.pop("collector_name")
    task = _collector_service(args).create_task(collector_name, **kwargs)
    payload = task.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"created {payload['task_id']}")
    print(f"template {args.template_id}")
    print(f"collector {payload['collector_name']}")
    print(f"trigger {payload['trigger_type']}")
    return 0


def _collector_task_add(args: argparse.Namespace) -> int:
    service = _collector_service(args)
    task = service.create_task(
        args.collector_name,
        task_id=args.task_id,
        name=args.name,
        enabled=not args.disabled,
        trigger_type=args.trigger_type,
        interval_seconds=args.interval_seconds,
        daily_time=args.daily_time,
        params=_json_object_arg(args.params, "--params") or {},
        fields=_comma_list_arg(args.fields),
        output_root=args.output_root,
        output_dir=args.output_dir,
        formats=_comma_list_arg(args.formats),
        collect_mode=args.collect_mode,
        connection_mode=args.connection_mode,
        concurrency_mode=args.concurrency_mode,
        connection_count=args.connection_count,
        source_server_count=args.source_server_count,
        connections_per_server=args.connections_per_server,
        max_concurrent_tasks=args.max_concurrent_tasks,
        batch_size=args.batch_size,
        request_interval_ms=args.request_interval_ms,
        retry_count=args.retry_count,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
        timeout_ms=args.timeout_ms,
    )
    payload = task.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"created {payload['task_id']}")
    print(f"collector {payload['collector_name']}")
    print(f"trigger {payload['trigger_type']}")
    return 0


def _collector_task_info(args: argparse.Namespace) -> int:
    service = _collector_service(args)
    task = service.store.get_task(args.task_id)
    if task is None:
        raise KeyError(f"Unknown collector task {args.task_id!r}.")
    task = service.refresh_task(task)
    payload = task.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _collector_task_enable(args: argparse.Namespace) -> int:
    task = _collector_service(args).store.set_task_enabled(args.task_id, True)
    if args.json:
        _print_json(task.to_dict())
        return 0
    print(f"enabled {task.task_id}")
    return 0


def _collector_task_disable(args: argparse.Namespace) -> int:
    task = _collector_service(args).store.set_task_enabled(args.task_id, False)
    if args.json:
        _print_json(task.to_dict())
        return 0
    print(f"disabled {task.task_id}")
    return 0


def _collector_task_run(args: argparse.Namespace) -> int:
    service = _collector_service(args)
    overrides = _collector_param_overrides_from_args(args, include_dates=True)
    run = service.submit_task(
        args.task_id,
        trigger_type=args.trigger_type,
        allow_disabled_manual_run=args.trigger_type == "manual",
        params_override=overrides or None,
        metadata={"run_mode": "manual", "params_override": overrides} if overrides else None,
    )
    if args.wait and run.status not in {"skipped", "failed", "success", "cancelled"}:
        run = service.wait_for_run(run.run_id) or run
    return _print_collector_run_payload(run.to_dict(), args=args, service=service)


def _collector_task_backfill(args: argparse.Namespace) -> int:
    service = _collector_service(args)
    overrides = _collector_param_overrides_from_args(args, include_dates=False)
    run = service.backfill_task(
        args.task_id,
        start=args.start,
        end=args.end,
        params_override=overrides or None,
    )
    if args.wait and run.status not in {"skipped", "failed", "success", "cancelled"}:
        run = service.wait_for_run(run.run_id) or run
    return _print_collector_run_payload(run.to_dict(), args=args, service=service)


def _collector_run_list(args: argparse.Namespace) -> int:
    limit = min(max(int(args.limit), 0), MAX_CLI_RUN_LIST_LIMIT)
    rows = [
        run.to_dict()
        for run in _collector_service(args).store.list_runs(
            task_id=args.task_id,
            status=args.status,
            limit=limit,
        )
    ]
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No collector runs.")
        return 0
    print("run_id\tstatus\ttrigger\ttask_id\tcollector\tresource_group\trows_written\twrite_mode\tduration_ms\tmessage\tnext_action\tfinished_at")
    for row in rows:
        message = row.get("status_message") or row.get("error") or row.get("skip_reason") or ""
        print(
            "\t".join(
                [
                    row["run_id"],
                    row["status"],
                    row["trigger_type"],
                    row["task_id"],
                    row["collector_name"],
                    row.get("resource_group") or "",
                    str(row.get("rows_written") if row.get("rows_written") is not None else ""),
                    row.get("write_mode") or "",
                    str(row.get("duration_ms") or ""),
                    message,
                    row.get("next_action") or "",
                    row.get("finished_at") or "",
                ]
            )
        )
    return 0


def _collector_run_info(args: argparse.Namespace) -> int:
    run = _collector_service(args).store.get_run(args.run_id)
    if run is None:
        raise KeyError(f"Unknown collector run {args.run_id!r}.")
    payload = run.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    _print_collector_run_detail(payload)
    return 0


def _print_collector_run_payload(payload: dict[str, Any], *, args: argparse.Namespace, service: Any) -> int:
    service.shutdown(wait=False)
    if args.json:
        _print_json(payload)
        return 0
    print(f"run_id\t{payload['run_id']}")
    print(f"task_id\t{payload['task_id']}")
    print(f"status\t{payload['status']}")
    if payload.get("status_message"):
        print(f"message\t{payload['status_message']}")
    if payload.get("next_action"):
        print(f"next_action\t{payload['next_action']}")
    if payload.get("action_command"):
        print(f"action_command\t{payload['action_command']}")
    if payload.get("duration_ms") is not None:
        print(f"duration_ms\t{payload['duration_ms']}")
    if payload.get("retry_count") is not None:
        print(f"retry_count\t{payload['retry_count']}")
    if payload.get("skip_reason"):
        print(f"skip_reason\t{payload['skip_reason']}")
    if payload.get("error"):
        print(f"error\t{payload['error']}")
    if payload.get("error_category"):
        print(f"error_category\t{payload['error_category']}")
    if payload.get("error_summary"):
        print(f"error_summary\t{payload['error_summary']}")
    if payload.get("backoff_until"):
        print(f"backoff_until\t{payload['backoff_until']}")
    if payload.get("stage_timings"):
        print("stage_timings\t" + json.dumps(payload["stage_timings"], ensure_ascii=False, sort_keys=True))
    if payload.get("params_override"):
        print("params_override\t" + json.dumps(payload["params_override"], ensure_ascii=False, sort_keys=True))
    if payload.get("quality"):
        print("quality\t" + json.dumps(payload["quality"], ensure_ascii=False, sort_keys=True))
    for event in payload.get("events") or []:
        print(
            "event\t"
            + "\t".join(
                [
                    str(event.get("sequence") or ""),
                    str(event.get("timestamp") or ""),
                    str(event.get("level") or ""),
                    str(event.get("stage") or ""),
                    str(event.get("category") or ""),
                    str(event.get("message") or ""),
                ]
            )
        )
    for format_name, output_path in sorted((payload.get("output_paths") or {}).items()):
        print(f"output_path.{format_name}\t{output_path}")
    return 0


def _print_collector_run_detail(payload: dict[str, Any]) -> None:
    print(f"run_id\t{payload['run_id']}")
    print(f"task_id\t{payload['task_id']}")
    print(f"collector\t{payload['collector_name']}")
    print(f"status\t{payload['status']}")
    print(f"trigger\t{payload['trigger_type']}")
    print(f"resource_group\t{payload.get('resource_group') or 'default'}")
    print(f"started_at\t{payload.get('started_at') or ''}")
    print(f"finished_at\t{payload.get('finished_at') or ''}")
    print(f"duration_ms\t{payload.get('duration_ms') if payload.get('duration_ms') is not None else ''}")
    print(f"retry_count\t{payload.get('retry_count') if payload.get('retry_count') is not None else ''}")
    for key in [
        "records_read",
        "rows_written",
        "write_mode",
        "rows_before",
        "rows_after",
        "duplicate_rows_dropped",
    ]:
        if payload.get(key) is not None:
            print(f"{key}\t{_cell_text(payload.get(key))}")
    for key in ["partition_by", "primary_key", "partitions_touched"]:
        if payload.get(key):
            print(f"{key}\t{_cell_text(payload.get(key))}")
    if payload.get("error_category"):
        print(f"error_category\t{payload['error_category']}")
    if payload.get("error_summary"):
        print(f"error_summary\t{payload['error_summary']}")
    if payload.get("error"):
        print(f"error\t{payload['error']}")
    if payload.get("skip_reason"):
        print(f"skip_reason\t{payload['skip_reason']}")
    if payload.get("status_message"):
        print(f"message\t{payload['status_message']}")
    if payload.get("next_action"):
        print(f"next_action\t{payload['next_action']}")
    if payload.get("action_command"):
        print(f"action_command\t{payload['action_command']}")
    if payload.get("stage_timings"):
        print("stage_timings")
        for key, value in payload["stage_timings"].items():
            print(f"  {key}\t{value if value is not None else ''}")
    if payload.get("params_override"):
        print("params_override\t" + json.dumps(payload["params_override"], ensure_ascii=False, sort_keys=True))
    if payload.get("quality"):
        print("quality\t" + json.dumps(payload["quality"], ensure_ascii=False, sort_keys=True))
    output_paths = payload.get("output_paths") or {}
    if output_paths:
        print("output_paths")
        for format_name, output_path in sorted(output_paths.items()):
            print(f"  {format_name}\t{output_path}")
    events = payload.get("events") or []
    if events:
        print("events")
        for event in events:
            category = event.get("category") or ""
            print(
                "  "
                + "\t".join(
                    [
                        str(event.get("sequence") or ""),
                        str(event.get("timestamp") or ""),
                        str(event.get("level") or ""),
                        str(event.get("stage") or ""),
                        str(category),
                        str(event.get("message") or ""),
                    ]
                )
            )


def _collector_status(args: argparse.Namespace) -> int:
    service = _collector_service(args)
    tasks = service.store.list_tasks()
    run_summary = service.store.run_summary(recent_limit=DEFAULT_CLI_STATUS_RUN_LIMIT)
    recent_runs = run_summary["recent_runs"]
    active_runs = run_summary["active_runs"]
    latest_by_task = {
        task.task_id: latest.to_dict()
        for task in tasks
        if (latest := run_summary["latest_by_task"].get(task.task_id)) is not None
    }
    payload = {
        "task_count": len(tasks),
        "enabled_task_count": sum(1 for task in tasks if task.enabled),
        "run_count": len(recent_runs),
        "total_run_count": run_summary["total_run_count"],
        "recent_run_count": len(recent_runs),
        "recent_run_limit": DEFAULT_CLI_STATUS_RUN_LIMIT,
        "status_counts": run_summary["status_counts"],
        "active_run_count": len(active_runs),
        "active_runs": [run.to_dict() for run in active_runs],
        "latest_runs": latest_by_task,
    }
    if args.json:
        _print_json(payload)
        return 0
    print(f"tasks\t{payload['task_count']}")
    print(f"enabled\t{payload['enabled_task_count']}")
    print(f"runs\t{payload['run_count']}")
    print(f"total_runs\t{payload['total_run_count']}")
    print(f"recent_run_limit\t{payload['recent_run_limit']}")
    print(f"active_runs\t{payload['active_run_count']}")
    failed_runs = [
        run
        for run in service.store.list_runs(status="failed", limit=5)
    ]
    if failed_runs:
        print("recent_failed_runs")
        for run in failed_runs:
            print(f"{run.run_id}\t{run.task_id}\t{run.error or ''}")
    return 0


def _plugin_list(args: argparse.Namespace) -> int:
    from .provider_catalog import build_builtin_provider_registry
    from .plugin_status import expected_provider_statuses, managed_provider_ids, provider_status_row

    registry = build_builtin_provider_registry(data_root=args.data_root)
    snapshot = registry.snapshot()
    config = load_plugin_config(data_root=args.data_root)
    managed_ids = managed_provider_ids(data_root=args.data_root)
    rows = [
        provider_status_row(
            provider,
            snapshot=snapshot,
            provider_overrides=registry.provider_overrides,
            managed_provider_ids=managed_ids,
            removed_provider_ids=getattr(config, "removed_provider_ids", ()),
        )
        for provider in registry.list_providers()
    ]
    rows.extend(expected_provider_statuses(row["provider_id"] for row in rows))
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No providers discovered.")
        return 0
    print("provider_id\tstatus\teffective_trust\tsource_code\tversion\tinterfaces\tdownloaders\tcollectors\tnext_action")
    for row in rows:
        print(
            "\t".join(
                [
                    row["provider_id"],
                    row["status"],
                    row["effective_trust_level"],
                    row["source_code"],
                    row["version"],
                    str(row["interface_count"]),
                    str(row["downloader_count"]),
                    str(row["collector_count"]),
                    row.get("next_action") or "",
                ]
            )
        )
    return 0


def _plugin_installed(args: argparse.Namespace) -> int:
    from .axp import list_installed_axp_plugins

    rows = [plugin.to_dict() for plugin in list_installed_axp_plugins(data_root=args.data_root)]
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No AxData-managed plugins installed.")
        return 0
    print("provider_id\tstatus\tenabled\teffective_trust\tsource_code\tversion\tinterfaces\tdownloaders\tcollectors\tnext_action")
    for row in rows:
        print(
            "\t".join(
                [
                    row["provider_id"],
                    row["status"],
                    str(row["enabled"]).lower(),
                    row["effective_trust_level"],
                    row["source_code"],
                    row["version"],
                    str(row["interface_count"]),
                    str(row["downloader_count"]),
                    str(row.get("collector_count", 0)),
                    row.get("next_action") or "",
                ]
            )
        )
    return 0


def _plugin_info(args: argparse.Namespace) -> int:
    from .provider_catalog import build_builtin_provider_registry
    from .plugin_status import managed_provider_ids, provider_status_row

    registry = build_builtin_provider_registry(data_root=args.data_root)
    snapshot = registry.snapshot()
    config = load_plugin_config(data_root=args.data_root)
    provider = snapshot.providers.get(args.provider_id)
    if provider is None:
        raise KeyError(f"Unknown provider {args.provider_id!r}.")
    payload = {
        **provider_status_row(
            provider,
            snapshot=snapshot,
            provider_overrides=registry.provider_overrides,
            managed_provider_ids=managed_provider_ids(data_root=args.data_root),
            removed_provider_ids=getattr(config, "removed_provider_ids", ()),
        ),
        "error": provider.error,
        "enabled": provider.enabled,
        "built_in": provider.built_in,
        "manifest": provider.manifest.to_dict(),
    }
    if args.json:
        _print_json(payload)
        return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _plugin_collectors(args: argparse.Namespace) -> int:
    from .provider_catalog import list_registry_collector_dicts

    rows = list(list_registry_collector_dicts(data_root=args.data_root))
    if args.json:
        _print_json(rows)
        return 0
    if not rows:
        print("No collectors available.")
        return 0
    print(
        "collector_id\tcollector_plugin_id\tprovider_id\tplugin_status\t"
        "effective_trust\tresource_group\tdataset_id\tlegacy\tinterfaces"
    )
    for row in rows:
        print(
            "\t".join(
                [
                    row["collector_id"],
                    str(row.get("collector_plugin_id") or ""),
                    row["provider_id"],
                    row["plugin_status"],
                    row["effective_trust_level"],
                    row["resource_group"],
                    str(row.get("dataset_id") or ""),
                    "yes" if row.get("is_legacy") else "no",
                    ",".join(row["interfaces"]),
                ]
            )
        )
    return 0


def _plugin_collector_info(args: argparse.Namespace) -> int:
    from .provider_catalog import list_registry_collector_dicts

    rows = {
        row["name"]: row
        for row in list_registry_collector_dicts(data_root=args.data_root)
    }
    collector = rows.get(args.collector_name)
    if collector is None:
        raise KeyError(f"Unknown collector {args.collector_name!r}.")
    if args.json:
        _print_json(collector)
        return 0
    print(json.dumps(collector, ensure_ascii=False, indent=2))
    return 0


def _plugin_collector_run(args: argparse.Namespace) -> int:
    from .collector_runner import run_collector

    result = run_collector(
        args.collector_name,
        params=_json_object_arg(args.params, "--params"),
        fields=_comma_list_arg(args.fields),
        data_root=args.data_root,
        output_root=args.output_root,
        output_dir=args.output_dir,
        formats=_comma_list_arg(args.formats),
        collect_mode=args.collect_mode,
        connection_mode=args.connection_mode,
        concurrency_mode=args.concurrency_mode,
        connection_count=args.connection_count,
        source_server_count=args.source_server_count,
        connections_per_server=args.connections_per_server,
        max_concurrent_tasks=args.max_concurrent_tasks,
        batch_size=args.batch_size,
        request_interval_ms=args.request_interval_ms,
        retry_count=args.retry_count,
        timeout_ms=args.timeout_ms,
    )
    if args.json:
        _print_json(result)
        return 0
    print(f"collector\t{result['collector_name']}")
    print(f"interface\t{result['target_interface']}")
    print(f"status\t{result['status']}")
    print(f"rows\t{result['download_result'].get('row_count', 0)}")
    output_path = result["download_result"].get("output_path")
    if output_path:
        print(f"output_path\t{output_path}")
    return 0


def _plugin_check(args: argparse.Namespace) -> int:
    has_provider_source = bool(getattr(args, "builtin", None) or getattr(args, "provider", None))
    if not has_provider_source and not getattr(args, "manifest", None):
        raise ValueError("plugin check requires --manifest, --builtin, or --provider.")
    if not has_provider_source:
        manifest = _load_manifest_file(args.manifest)
        _validate_manifest_for_cli(manifest)
        _print_manifest_check_ok(manifest)
        return 0

    provider = _load_provider_from_args(args)
    manifest = manifest_from_provider(provider)
    _validate_manifest_for_cli(manifest)
    if getattr(args, "manifest", None):
        embedded_manifest = _load_manifest_file(args.manifest)
        _validate_manifest_for_cli(embedded_manifest)
        if _manifest_check_payload(embedded_manifest) != _manifest_check_payload(manifest):
            raise ValueError(
                f"Manifest {args.manifest!r} does not match Provider "
                f"{manifest.identity!r}."
            )
    _print_manifest_check_ok(manifest)
    return 0


def _print_manifest_check_ok(manifest: ProviderManifest) -> None:
    print(
        f"OK {manifest.identity} "
        f"interfaces={len(manifest.interfaces)} "
        f"downloaders={len(manifest.downloaders)} "
        f"collectors={len(manifest.collectors)}"
    )


def _validate_manifest_for_cli(manifest: ProviderManifest) -> None:
    validate_manifest(manifest)
    if manifest.manifest_version != MANIFEST_VERSION:
        raise ValueError(
            f"Unsupported manifest_version {manifest.manifest_version!r}; "
            f"expected {MANIFEST_VERSION!r}."
        )
    if manifest.plugin_api_version != PLUGIN_API_VERSION:
        raise ValueError(
            f"Unsupported plugin_api_version {manifest.plugin_api_version!r}; "
            f"expected {PLUGIN_API_VERSION!r}."
        )


def _manifest_check_payload(manifest: ProviderManifest) -> dict[str, Any]:
    payload = manifest.to_dict()
    payload.pop("build", None)
    _drop_empty_v2_manifest_fields(payload)
    return payload


def _drop_empty_v2_manifest_fields(payload: dict[str, Any]) -> None:
    """Normalize old provider-only manifests during drift checks."""

    if payload.get("plugin") is None:
        payload.pop("plugin", None)
    if payload.get("collectors") == []:
        payload.pop("collectors", None)
    if payload.get("dependencies") == []:
        payload.pop("dependencies", None)
    config_schema = payload.get("config_schema")
    if isinstance(config_schema, dict) and config_schema.get("required_config", []) == []:
        payload.pop("config_schema", None)


def _plugin_build(args: argparse.Namespace) -> int:
    provider = _load_provider_from_args(args)
    manifest = manifest_from_provider(provider)
    _validate_manifest_for_cli(manifest)
    output = Path(args.output or MANIFEST_FILE_NAME).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(str(output))
    return 0


def _plugin_enable(args: argparse.Namespace) -> int:
    config = enable_provider(args.provider_id, data_root=args.data_root)
    print(f"enabled {args.provider_id}")
    print(f"config {plugin_config_path(data_root=args.data_root)}")
    return 0 if args.provider_id in config.enabled_provider_ids else 1


def _plugin_disable(args: argparse.Namespace) -> int:
    config = disable_provider(args.provider_id, data_root=args.data_root)
    print(f"disabled {args.provider_id}")
    print(f"config {plugin_config_path(data_root=args.data_root)}")
    return 0 if args.provider_id in config.disabled_provider_ids else 1


def _plugin_uninstall(args: argparse.Namespace) -> int:
    from .axp import uninstall_axp_plugin

    result = uninstall_axp_plugin(
        args.provider_id,
        data_root=args.data_root,
        disable_first=args.disable_first,
    )
    payload = result.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"uninstalled {payload['provider_id']}")
    print(f"uninstall_mode {payload.get('uninstall_mode', 'physical_remove')}")
    print(f"removed_paths {len(payload['removed_paths'])}")
    if payload.get("message"):
        print(f"message {payload['message']}")
    return 0


def _plugin_axp_preview(args: argparse.Namespace) -> int:
    from .axp import preview_axp

    preview = preview_axp(args.path, data_root=args.data_root)
    payload = preview.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"provider_id\t{payload['provider_id']}")
    print(f"source_code\t{payload['source_code']}")
    print(f"version\t{payload['version']}")
    print(f"effective_trust\t{payload['effective_trust_level']}")
    print(f"status_after_install\t{payload['status_after_install']}")
    print("wheels\t" + ",".join(wheel["file_name"] for wheel in payload["wheels"]))
    for warning in payload["warnings"]:
        print(f"warning\t{warning}")
    return 0


def _plugin_axp_install(args: argparse.Namespace) -> int:
    from .axp import install_axp

    result = install_axp(
        args.path,
        data_root=args.data_root,
        install_root=args.install_root,
        enable=args.enable,
        replace=args.replace,
        write_pth=not args.no_pth,
        allow_online_deps=args.allow_online_deps,
    )
    payload = result.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"installed {payload['provider_id']}")
    print(f"status_after_install {payload['status_after_install']}")
    print(f"site_packages {payload['site_packages']}")
    if not args.enable:
        print(f"enable with: axdata --data-root {args.data_root or 'data'} plugin enable {payload['provider_id']}")
    return 0


def _add_provider_source_args(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument(
        "--builtin",
        metavar="SOURCE_CODE",
        help="built-in provider source_code, for example tdx or tencent",
    )
    group.add_argument(
        "--provider",
        metavar="MODULE:OBJECT",
        help="provider import path, for example axdata_source_demo.provider:provider",
    )


def _add_collector_runtime_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--collect-mode", help="collection mode")
    parser.add_argument("--connection-mode", help="downloader connection mode")
    parser.add_argument("--concurrency-mode", help="downloader concurrency preset mode")
    parser.add_argument("--connection-count", type=int, help="number of source connections/workers")
    parser.add_argument("--source-server-count", type=int, help="number of source servers to use")
    parser.add_argument("--connections-per-server", type=int, help="long connections per source server")
    parser.add_argument("--max-concurrent-tasks", type=int, help="maximum concurrent downloader tasks")
    parser.add_argument("--batch-size", type=int, help="downloader task batch size")
    parser.add_argument("--request-interval-ms", type=int, help="interval between source requests")
    parser.add_argument("--retry-count", type=int, help="retry count for source requests")
    parser.add_argument("--max-retries", type=int, help="Collector run-level retry attempts after the first failure")
    parser.add_argument("--backoff-seconds", type=int, help="seconds to wait between Collector run-level retries")
    parser.add_argument("--timeout-ms", type=int, help="per-request timeout in milliseconds")


def _collector_param_overrides_from_args(
    args: argparse.Namespace,
    *,
    include_dates: bool,
) -> dict[str, Any]:
    overrides = _json_object_arg(getattr(args, "params", None), "--params") or {}
    if include_dates:
        start = getattr(args, "start", None)
        end = getattr(args, "end", None)
        if start or end:
            if not start or not end:
                raise ValueError("--start and --end must be provided together.")
            from .collector_scheduler import normalize_date_range

            start_date, end_date = normalize_date_range(start, end)
            overrides.setdefault("start_date", start_date)
            overrides.setdefault("end_date", end_date)
    symbol = getattr(args, "symbol", None)
    if symbol:
        overrides.setdefault("code", symbol)
    limit = getattr(args, "limit", None)
    if limit is not None:
        if int(limit) < 0:
            raise ValueError("--limit must be non-negative.")
        overrides.setdefault("limit", int(limit))
        overrides.setdefault("count", int(limit))
    return overrides


def _parse_filter_args(values: list[str]) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for item in values:
        if "=" not in item:
            raise ValueError("--filter must use key=value.")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("--filter key cannot be empty.")
        filters[key] = value.strip()
    return filters


def _normalize_date_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text.replace("-", "")
    return text


def _date_filter_payload(start: str | None, end: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    normalized_start = _normalize_date_text(start)
    normalized_end = _normalize_date_text(end)
    if normalized_start:
        payload["start"] = normalized_start
    if normalized_end:
        payload["end"] = normalized_end
    return payload


def _parse_key_value_args(values: list[str], flag_name: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"{flag_name} must use key=value.")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{flag_name} key cannot be empty.")
        params[key] = _parse_scalar_value(raw_value.strip())
    return params


def _parse_scalar_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _print_source_request_error(
    *,
    code: str,
    message: str,
    interface_name: str,
    params: dict[str, Any],
    fields: list[str] | None,
    options: dict[str, Any],
    args: argparse.Namespace,
) -> int:
    guidance = _source_request_guidance(code, interface_name)
    payload: dict[str, Any] = {
        "success": False,
        "error": {"code": code, "message": message},
        "data": None,
        "meta": {
            "interface_name": interface_name,
            "request_mode": "source_request",
            "persisted": False,
            "params": params,
            "fields": fields,
            "options": options,
            **guidance,
        },
    }
    if args.json:
        _print_json(payload)
    else:
        print(f"error\t{code}")
        print(f"message\t{message}")
        if guidance.get("next_action"):
            print(f"next_action\t{guidance['next_action']}")
        if guidance.get("action_command"):
            print(f"action_command\t{guidance['action_command']}")
    return 2


def _source_request_guidance(code: str, interface_name: str) -> dict[str, str | None]:
    if code == "SOURCE_UNAVAILABLE" and interface_name.endswith("_tdx"):
        return {
            "next_action": "安装并启用 TDX Provider 后重试该源端直取接口。",
            "action_command": "axdata plugin enable axdata.source.tdx_external",
        }
    if code == "SOURCE_REQUEST_VALIDATION_ERROR":
        return {
            "next_action": "检查接口参数名、必填参数和字段选择；可先查看接口目录示例。",
            "action_command": "axdata request <interface> --params '{\\\"key\\\":\\\"value\\\"}' --json",
        }
    if code == "SOURCE_ADAPTER_NOT_FOUND":
        return {
            "next_action": "检查对应 Provider 是否已安装、启用，或是否存在接口冲突。",
            "action_command": "axdata plugin list --json",
        }
    return {"next_action": None, "action_command": None}


def _format_date_range(payload: dict[str, Any]) -> str:
    start = payload.get("date_min") or payload.get("datetime_min")
    end = payload.get("date_max") or payload.get("datetime_max")
    if start and end:
        return f"{start}..{end}"
    return str(start or end or "")


def _print_rows(rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not columns and rows:
        columns = list(rows[0])
    print("\t".join(columns))
    for row in rows:
        print("\t".join(_cell_text(row.get(column)) for column in columns))


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _load_provider_from_args(args: argparse.Namespace) -> Any:
    if getattr(args, "builtin", None):
        from .builtin_providers import get_builtin_provider

        return get_builtin_provider(args.builtin)
    return _load_object(args.provider)


def _load_object(spec: str) -> Any:
    module_name, separator, object_name = str(spec or "").partition(":")
    if not module_name or not separator or not object_name:
        raise ValueError("Provider path must use MODULE:OBJECT.")
    module = importlib.import_module(module_name)
    value: Any = module
    for part in object_name.split("."):
        value = getattr(value, part)
    return value


def _load_manifest_file(path: str) -> ProviderManifest:
    payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest {path!r} must contain a JSON object.")
    return ProviderManifest.from_dict(payload)


def _json_object_arg(value: str | None, flag_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{flag_name} must be a JSON object.")
    return parsed


def _comma_list_arg(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _manifest_display_name(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.source_name_zh
    if manifest.plugin is not None:
        return manifest.plugin.name_zh
    return "未知插件"


def _manifest_version(manifest: ProviderManifest) -> str:
    if manifest.provider is not None:
        return manifest.provider.version
    if manifest.plugin is not None:
        return manifest.plugin.version
    return "0.0.0"


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
