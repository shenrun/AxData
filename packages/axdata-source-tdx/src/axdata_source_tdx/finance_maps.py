"""Local TDX finance code-table mappings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TdxFinanceLocalMaps:
    loaded: bool
    root: str | None
    source_files: tuple[str, ...]
    region_by_raw: dict[int, dict[str, str]]
    industry_by_security: dict[str, dict[str, Any]]
    name_by_code: dict[str, str]
    errors: tuple[str, ...] = ()


_DEFAULT_MAP_PACKAGE = "axdata_source_tdx.resources.finance_maps"


def empty_finance_local_maps(
    root: Path | None = None,
    *,
    errors: tuple[str, ...] = (),
) -> TdxFinanceLocalMaps:
    return TdxFinanceLocalMaps(
        loaded=False,
        root=str(root) if root is not None else None,
        source_files=(),
        region_by_raw={},
        industry_by_security={},
        name_by_code={},
        errors=errors,
    )


@lru_cache(maxsize=1)
def load_finance_local_maps() -> TdxFinanceLocalMaps:
    """Load AxData's bundled TDX finance mappings."""

    return _load_default_finance_local_maps()


@lru_cache(maxsize=16)
def load_finance_local_maps_from_root(root: str | Path | None) -> TdxFinanceLocalMaps:
    if root is None:
        return load_finance_local_maps()
    return _load_finance_local_maps_from_root(Path(root))


def parse_incon_dict(path: str | Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in _read_gbk(Path(path)).splitlines():
        if not line or line.startswith("#") or line.startswith("######") or "|" not in line:
            continue
        code, name = line.split("|", 1)
        code = code.strip()
        name = name.strip()
        if code and name:
            result[code] = name
    return result


def parse_region_map(path: str | Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for line in _read_gbk(Path(path)).splitlines():
        parts = line.split("|")
        if len(parts) < 6:
            continue
        board_name, board_code, category, _sort_group, _leaf_flag, raw_code = parts[:6]
        if category != "3" or not board_code.startswith("8802") or not raw_code.isdigit():
            continue
        result[int(raw_code)] = {
            "name": _normalize_board_name(board_name),
            "board_name": board_name,
            "board_code": board_code,
        }
    return result


def parse_security_industry_map(
    path: str | Path,
    name_by_code: dict[str, str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line in _read_gbk(Path(path)).splitlines():
        parts = line.split("|")
        if len(parts) < 6:
            continue
        market_raw, code, tdx_industry_code, _unused1, _unused2, research_industry_code = parts[:6]
        if not market_raw.isdigit() or len(code) != 6 or not code.isdigit():
            continue
        tdx_industry_code = tdx_industry_code.strip() or None
        research_industry_code = research_industry_code.strip() or None
        result[f"{int(market_raw)}:{code}"] = {
            "tdx_industry_code": tdx_industry_code,
            "tdx_industry_name": name_by_code.get(tdx_industry_code or ""),
            "tdx_industry_path": _code_name_path(tdx_industry_code, name_by_code),
            "tdx_research_industry_code": research_industry_code,
            "tdx_research_industry_name": name_by_code.get(research_industry_code or ""),
            "tdx_research_industry_path": _code_name_path(research_industry_code, name_by_code),
        }
    return result


def lookup_finance_profile_maps(
    code: str,
    *,
    market_id: int | None,
    province_raw: int | None,
    local_maps: TdxFinanceLocalMaps | None = None,
) -> dict[str, Any]:
    maps = local_maps or load_finance_local_maps()
    region_info = maps.region_by_raw.get(province_raw or -1) or {}
    industry_info = maps.industry_by_security.get(f"{market_id}:{code}") if market_id is not None else None
    industry_info = industry_info or {}
    return {
        "province_name": region_info.get("name"),
        "province_board_name": region_info.get("board_name"),
        "province_board_code": region_info.get("board_code"),
        "tdx_industry_code": industry_info.get("tdx_industry_code"),
        "tdx_industry_name": industry_info.get("tdx_industry_name"),
        "tdx_industry_path": _format_name_path(industry_info.get("tdx_industry_path")),
        "tdx_research_industry_code": industry_info.get("tdx_research_industry_code"),
        "tdx_research_industry_name": industry_info.get("tdx_research_industry_name"),
        "tdx_research_industry_path": _format_name_path(
            industry_info.get("tdx_research_industry_path")
        ),
    }


def _load_default_finance_local_maps() -> TdxFinanceLocalMaps:
    try:
        package_files = resources.files(_DEFAULT_MAP_PACKAGE)
        with (
            resources.as_file(package_files / "incon.dat") as incon_path,
            resources.as_file(package_files / "tdxzs.cfg") as tdxzs_path,
            resources.as_file(package_files / "tdxhy.cfg") as tdxhy_path,
        ):
            name_by_code = parse_incon_dict(incon_path)
            region_by_raw = parse_region_map(tdxzs_path)
            industry_by_security = parse_security_industry_map(tdxhy_path, name_by_code)
            return TdxFinanceLocalMaps(
                loaded=bool(name_by_code or region_by_raw or industry_by_security),
                root="builtin",
                source_files=(
                    f"{_DEFAULT_MAP_PACKAGE}:incon.dat",
                    f"{_DEFAULT_MAP_PACKAGE}:tdxzs.cfg",
                    f"{_DEFAULT_MAP_PACKAGE}:tdxhy.cfg",
                ),
                region_by_raw=region_by_raw,
                industry_by_security=industry_by_security,
                name_by_code=name_by_code,
            )
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        return empty_finance_local_maps(errors=(str(exc),))


def _load_finance_local_maps_from_root(root: Path) -> TdxFinanceLocalMaps:
    errors: list[str] = []
    try:
        resolved = root.expanduser()
    except RuntimeError:
        resolved = root

    incon_path = _first_existing(
        (
            resolved / "incon.dat",
            resolved / "T0002" / "hq_cache" / "incon.dat",
            resolved / "vipdoc" / "incon.dat",
        )
    )
    tdxzs_path = _first_existing(
        (
            resolved / "tdxzs.cfg",
            resolved / "T0002" / "hq_cache" / "tdxzs.cfg",
            resolved / "securities" / "resources" / "tdxzs.cfg",
        )
    )
    tdxhy_path = _first_existing(
        (
            resolved / "tdxhy.cfg",
            resolved / "T0002" / "hq_cache" / "tdxhy.cfg",
            resolved / "securities" / "resources" / "tdxhy.cfg",
        )
    )

    required = {
        "incon.dat": incon_path,
        "tdxzs.cfg": tdxzs_path,
        "tdxhy.cfg": tdxhy_path,
    }
    missing = [name for name, path in required.items() if path is None]
    if missing:
        return empty_finance_local_maps(
            resolved,
            errors=(f"missing {', '.join(missing)} under {resolved}",),
        )

    try:
        name_by_code = parse_incon_dict(incon_path)  # type: ignore[arg-type]
        region_by_raw = parse_region_map(tdxzs_path)  # type: ignore[arg-type]
        industry_by_security = parse_security_industry_map(
            tdxhy_path,  # type: ignore[arg-type]
            name_by_code,
        )
    except OSError as exc:
        errors.append(str(exc))
        return empty_finance_local_maps(resolved, errors=tuple(errors))

    source_files = tuple(str(path) for path in (incon_path, tdxzs_path, tdxhy_path) if path is not None)
    return TdxFinanceLocalMaps(
        loaded=bool(name_by_code or region_by_raw or industry_by_security),
        root=str(resolved),
        source_files=source_files,
        region_by_raw=region_by_raw,
        industry_by_security=industry_by_security,
        name_by_code=name_by_code,
        errors=tuple(errors),
    )


def _load_finance_local_maps_from_candidates(roots: tuple[Path, ...]) -> TdxFinanceLocalMaps:
    candidates = [_finance_map_file_candidates(root) for root in roots]
    incon_path = _first_existing(tuple(path for item in candidates for path in item["incon"]))
    tdxzs_path = _first_existing(tuple(path for item in candidates for path in item["tdxzs"]))
    tdxhy_path = _first_existing(tuple(path for item in candidates for path in item["tdxhy"]))
    missing = [
        name
        for name, path in (
            ("incon.dat", incon_path),
            ("tdxzs.cfg", tdxzs_path),
            ("tdxhy.cfg", tdxhy_path),
        )
        if path is None
    ]
    if missing:
        return empty_finance_local_maps(
            errors=(f"missing {', '.join(missing)} in local TDX map candidates",),
        )

    try:
        name_by_code = parse_incon_dict(incon_path)  # type: ignore[arg-type]
        region_by_raw = parse_region_map(tdxzs_path)  # type: ignore[arg-type]
        industry_by_security = parse_security_industry_map(
            tdxhy_path,  # type: ignore[arg-type]
            name_by_code,
        )
    except OSError as exc:
        return empty_finance_local_maps(errors=(str(exc),))

    source_files = tuple(str(path) for path in (incon_path, tdxzs_path, tdxhy_path) if path is not None)
    roots_text = ";".join(str(root) for root in roots)
    return TdxFinanceLocalMaps(
        loaded=bool(name_by_code or region_by_raw or industry_by_security),
        root=roots_text or None,
        source_files=source_files,
        region_by_raw=region_by_raw,
        industry_by_security=industry_by_security,
        name_by_code=name_by_code,
    )


def _candidate_roots() -> tuple[Path, ...]:
    values: list[str] = []
    for name in (
        "AXDATA_TDX_FINANCE_MAP_ROOT",
        "AXDATA_TDX_LOCAL_ROOT",
        "AXDATA_TDX_ROOT",
    ):
        values.extend(_split_env_paths(os.getenv(name)))

    values.extend(
        [
            r"C:\APP\tdx",
            r"C:\new_tdx",
            r"C:\tdx",
        ]
    )

    paths: list[Path] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        path = Path(text)
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return tuple(paths)


def _split_env_paths(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(os.pathsep) if item.strip()]


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _finance_map_file_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    try:
        resolved = root.expanduser()
    except RuntimeError:
        resolved = root
    return {
        "incon": (
            resolved / "incon.dat",
            resolved / "T0002" / "hq_cache" / "incon.dat",
            resolved / "vipdoc" / "incon.dat",
        ),
        "tdxzs": (
            resolved / "tdxzs.cfg",
            resolved / "T0002" / "hq_cache" / "tdxzs.cfg",
            resolved / "securities" / "resources" / "tdxzs.cfg",
        ),
        "tdxhy": (
            resolved / "tdxhy.cfg",
            resolved / "T0002" / "hq_cache" / "tdxhy.cfg",
            resolved / "securities" / "resources" / "tdxhy.cfg",
        ),
    }


def _read_gbk(path: Path) -> str:
    return path.read_text(encoding="gbk", errors="replace")


def _normalize_board_name(name: str) -> str:
    return name[:-2] if name.endswith("板块") else name


def _code_name_path(code: str | None, name_by_code: dict[str, str]) -> list[str]:
    if not code:
        return []

    if code.startswith("T"):
        prefix_lengths = (3, 5, 7)
    elif code.startswith("X"):
        prefix_lengths = (3, 5, 7, 10, 13)
    else:
        prefix_lengths = tuple(range(1, len(code) + 1))

    path: list[str] = []
    for length in prefix_lengths:
        if length > len(code):
            continue
        name = name_by_code.get(code[:length])
        if name and (not path or path[-1] != name):
            path.append(name)
    return path


def _format_name_path(value: Any) -> str | None:
    if isinstance(value, str):
        return value or None
    if not value:
        return None
    try:
        items = [str(item) for item in value if str(item)]
    except TypeError:
        return str(value)
    return " / ".join(items) if items else None
