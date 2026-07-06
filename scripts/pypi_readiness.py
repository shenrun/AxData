from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PackageSpec:
    dist_name: str
    source_path: Path
    import_name: str | None = None
    provider_entry_point: str | None = None
    provider_id: str | None = None

    @property
    def source_name(self) -> str:
        return self.source_path.name

    @property
    def wheel_prefix(self) -> str:
        return self.dist_name.replace("-", "_")


PACKAGES: tuple[PackageSpec, ...] = (
    PackageSpec(
        "axdata-core",
        REPO_ROOT / "libs" / "axdata_core",
        import_name="axdata_core",
    ),
    PackageSpec(
        "axdata",
        REPO_ROOT / "packages" / "axdata-sdk",
        import_name="axdata",
    ),
    PackageSpec(
        "axdata-source-tdx",
        REPO_ROOT / "packages" / "axdata-source-tdx",
        import_name="axdata_source_tdx",
        provider_entry_point="tdx",
        provider_id="axdata.source.tdx_external",
    ),
    PackageSpec(
        "axdata-source-tdx-ext",
        REPO_ROOT / "packages" / "axdata-source-tdx-ext",
        import_name="axdata_source_tdx_ext",
        provider_entry_point="tdx_ext",
        provider_id="axdata.source.tdx_ext_external",
    ),
    PackageSpec(
        "axdata-source-tencent",
        REPO_ROOT / "packages" / "axdata-source-tencent",
        import_name="axdata_source_tencent",
        provider_entry_point="tencent",
        provider_id="axdata.source.tencent_external",
    ),
    PackageSpec(
        "axdata-source-cninfo",
        REPO_ROOT / "packages" / "axdata-source-cninfo",
        import_name="axdata_source_cninfo",
        provider_entry_point="cninfo",
        provider_id="axdata.source.cninfo_external",
    ),
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.work_dir:
        work_dir = Path(args.work_dir).expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
        return _run_check(args, work_dir)

    with tempfile.TemporaryDirectory(prefix="axdata-pypi-readiness-") as tmp:
        return _run_check(args, Path(tmp))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build AxData PyPI candidate distributions and install them in a fresh "
            "temporary venv. This script never uploads to PyPI."
        )
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to create temporary venvs. Defaults to this interpreter.",
    )
    parser.add_argument(
        "--work-dir",
        help="Keep temporary sources, dists, and venvs under this directory for debugging.",
    )
    parser.add_argument(
        "--skip-twine-check",
        action="store_true",
        help="Skip `twine check` for generated wheel/sdist files.",
    )
    parser.add_argument(
        "--upgrade-pip",
        action="store_true",
        help="Upgrade pip in temporary venvs before installing tools/packages.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of text.",
    )
    return parser


def _run_check(args: argparse.Namespace, work_dir: Path) -> int:
    sources_dir = work_dir / "sources"
    dist_dir = work_dir / "dist"
    data_root = work_dir / "runtime" / "data"
    build_venv = work_dir / "build-venv"
    install_venv = work_dir / "install-venv"
    commands: list[str] = []

    copied_sources = _copy_package_sources(sources_dir)

    _create_venv(args.python, build_venv)
    build_python = _venv_python(build_venv)
    build_pip = [str(build_python), "-m", "pip"]
    if args.upgrade_pip:
        _run([*build_pip, "install", "--upgrade", "pip"], commands=commands)
    _run([*build_pip, "install", "build>=1.2"], commands=commands)
    if not args.skip_twine_check:
        _run([*build_pip, "install", "twine>=5"], commands=commands)

    artifacts: list[Path] = []
    package_artifacts: dict[str, list[str]] = {}
    for package in PACKAGES:
        source = copied_sources[package.dist_name]
        built = _build_distribution(build_python, source, dist_dir, commands=commands)
        artifacts.extend(built)
        package_artifacts[package.dist_name] = [path.name for path in built]

    if not args.skip_twine_check:
        _run(
            [str(build_python), "-m", "twine", "check", *map(str, artifacts)],
            commands=commands,
        )

    _create_venv(args.python, install_venv)
    install_python = _venv_python(install_venv)
    install_pip = [str(install_python), "-m", "pip"]
    if args.upgrade_pip:
        _run([*install_pip, "install", "--upgrade", "pip"], commands=commands)

    wheel_paths = [_find_wheel(dist_dir, package) for package in PACKAGES]
    _run(
        [
            *install_pip,
            "install",
            "--find-links",
            str(dist_dir),
            *map(str, wheel_paths),
        ],
        commands=commands,
    )

    import_summary = _verify_python_imports(install_python, commands=commands)
    axdata = _venv_console(install_venv, "axdata")
    _run_capture([str(axdata), "--help"], commands=commands)
    _run_json([str(axdata), "--data-root", str(data_root), "init", "--json"], commands=commands)
    doctor = _run_json(
        [str(axdata), "--data-root", str(data_root), "doctor", "--json"],
        commands=commands,
    )
    status = _run_json(
        [str(axdata), "--data-root", str(data_root), "status", "--json"],
        commands=commands,
    )
    providers = _run_json(
        [str(axdata), "--data-root", str(data_root), "plugin", "list", "--json"],
        commands=commands,
    )
    provider_summary = _summarize_providers(providers)
    _verify_provider_ids(provider_summary)
    _verify_default_enabled_providers(provider_summary)

    summary = {
        "work_dir": str(work_dir),
        "dist_dir": str(dist_dir),
        "data_root": str(data_root),
        "packages": package_artifacts,
        "wheels_installed": [path.name for path in wheel_paths],
        "twine_check": "skipped" if args.skip_twine_check else "passed",
        "doctor_status": doctor.get("summary", {}).get("status") if isinstance(doctor, dict) else None,
        "runtime_status": status.get("summary", {}).get("status") if isinstance(status, dict) else None,
        "imports": import_summary,
        "providers": provider_summary,
        "commands": commands,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("AxData PyPI readiness check passed")
        print(f"built packages: {', '.join(package.dist_name for package in PACKAGES)}")
        print(f"twine_check={summary['twine_check']}")
        print(f"doctor_status={summary['doctor_status']}")
        print(f"runtime_status={summary['runtime_status']}")
        print(f"work_dir={work_dir}")
    return 0


def _copy_package_sources(sources_dir: Path) -> dict[str, Path]:
    sources_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for package in PACKAGES:
        target = sources_dir / package.source_name
        shutil.copytree(
            package.source_path,
            target,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "*.egg-info",
                "build",
                "dist",
            ),
        )
        copied[package.dist_name] = target
    return copied


def _create_venv(python: str, venv_dir: Path) -> None:
    _run([python, "-m", "venv", str(venv_dir)], commands=[])


def _build_distribution(
    python: Path,
    source: Path,
    dist_dir: Path,
    *,
    commands: list[str],
) -> list[Path]:
    dist_dir.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in dist_dir.iterdir() if path.is_file()}
    _run(
        [
            str(python),
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--outdir",
            str(dist_dir),
            str(source),
        ],
        commands=commands,
    )
    return sorted(path for path in dist_dir.iterdir() if path.is_file() and path.name not in before)


def _find_wheel(dist_dir: Path, package: PackageSpec) -> Path:
    matches = sorted(dist_dir.glob(f"{package.wheel_prefix}-*.whl"))
    if not matches:
        raise RuntimeError(f"No wheel found for {package.dist_name!r} in {dist_dir}")
    return matches[-1]


def _verify_python_imports(python: Path, *, commands: list[str]) -> dict[str, object]:
    code = """
import importlib
import importlib.metadata as metadata
import importlib.resources as resources
import json

modules = [
    "axdata",
    "axdata_core",
    "axdata_source_tdx",
    "axdata_source_tdx_ext",
    "axdata_source_tencent",
    "axdata_source_cninfo",
]
for module in modules:
    importlib.import_module(module)

resources_to_check = {
    "axdata_source_tdx": [
        "axdata-provider.json",
        "resources/tdx_quote_servers.json",
        "resources/finance_maps/incon.dat",
    ],
    "axdata_source_tdx_ext": ["axdata-provider.json"],
    "axdata_source_tencent": ["axdata-provider.json"],
    "axdata_source_cninfo": ["axdata-provider.json"],
}
for package, paths in resources_to_check.items():
    root = resources.files(package)
    for item in paths:
        assert root.joinpath(item).is_file(), f"missing {package}:{item}"

entry_points = {
    item.name: item.value
    for item in metadata.entry_points(group="axdata.providers")
}
required_entry_points = {"tdx", "tdx_ext", "tencent", "cninfo"}
missing = sorted(required_entry_points - set(entry_points))
if missing:
    raise AssertionError(f"missing provider entry points: {missing}")

requires = metadata.requires("axdata") or []
required_default_deps = [
    "axdata-source-tdx",
    "axdata-source-tdx-ext",
    "axdata-source-tencent",
    "axdata-source-cninfo",
]
default_dep_requires = [
    requirement
    for requirement in requires
    if "extra ==" not in requirement
]
missing_default_deps = [
    name
    for name in required_default_deps
    if not any(name in requirement for requirement in default_dep_requires)
]
if missing_default_deps:
    raise AssertionError(f"missing axdata default requirements: {missing_default_deps}")

print(json.dumps({
    "modules": modules,
    "provider_entry_points": entry_points,
    "axdata_default_dependencies": default_dep_requires,
}, ensure_ascii=False))
""".strip()
    result = _run_capture([str(python), "-c", code], commands=commands)
    return json.loads(result.stdout)


def _summarize_providers(payload: object) -> dict[str, dict[str, object]]:
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected provider list JSON, got: {payload!r}")
    summary: dict[str, dict[str, object]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        provider_id = item.get("provider_id")
        if not isinstance(provider_id, str):
            continue
        summary[provider_id] = {
            "status": item.get("status"),
            "enabled": item.get("enabled"),
            "interfaces": item.get("interfaces"),
        }
    return summary


def _verify_provider_ids(providers: dict[str, dict[str, object]]) -> None:
    required = sorted(package.provider_id for package in PACKAGES if package.provider_id)
    missing = [provider_id for provider_id in required if provider_id not in providers]
    if missing:
        raise RuntimeError(f"Installed package provider(s) not discovered: {missing}")


def _verify_default_enabled_providers(providers: dict[str, dict[str, object]]) -> None:
    required_enabled = ("axdata.source.tdx_external", "axdata.source.tdx_ext_external")
    disabled = [
        provider_id
        for provider_id in required_enabled
        if providers.get(provider_id, {}).get("status") != "enabled"
        or providers.get(provider_id, {}).get("enabled") is not True
    ]
    if disabled:
        raise RuntimeError(f"Provider(s) should be enabled by default after install: {disabled}")


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_console(venv_dir: Path, name: str) -> Path:
    candidates = (
        [venv_dir / "Scripts" / f"{name}.exe", venv_dir / "Scripts" / name]
        if os.name == "nt"
        else [venv_dir / "bin" / name]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(f"Console script {name!r} was not installed in {venv_dir}")


def _run_json(command: list[str], *, commands: list[str]) -> object:
    result = _run_capture(command, commands=commands)
    return json.loads(result.stdout)


def _run_capture(command: list[str], *, commands: list[str]) -> subprocess.CompletedProcess[str]:
    return _run(command, commands=commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _run(
    command: list[str],
    *,
    commands: list[str],
    stdout: int | None = None,
    stderr: int | None = None,
) -> subprocess.CompletedProcess[str]:
    commands.append(_display_command(command))
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE if stdout is None else stdout,
        stderr=subprocess.PIPE if stderr is None else stderr,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
    return result


def _display_command(command: list[str]) -> str:
    return " ".join(str(part) for part in command)


if __name__ == "__main__":
    raise SystemExit(main())
