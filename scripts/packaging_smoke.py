from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
TDX_PROVIDER_ID = "axdata.source.tdx_external"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.work_dir:
        work_dir = Path(args.work_dir).expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
        return _run_smoke(args, work_dir)

    with tempfile.TemporaryDirectory(prefix="axdata-packaging-smoke-") as tmp:
        return _run_smoke(args, Path(tmp))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local packaging smoke in a temporary virtual environment."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to create the smoke venv. Defaults to this interpreter.",
    )
    parser.add_argument(
        "--work-dir",
        help="Directory for the temporary venv, wheelhouse, and data root. Omit to auto-clean.",
    )
    parser.add_argument(
        "--mode",
        choices=("editable", "wheel"),
        default="editable",
        help="Install AxData workspace/core/SDK from editable paths or locally built wheels.",
    )
    parser.add_argument(
        "--tdx-mode",
        choices=("editable", "wheel", "axp"),
        default="editable",
        help="Install the TDX plugin as editable, wheel, or AxData-managed AXP.",
    )
    parser.add_argument(
        "--upgrade-pip",
        action="store_true",
        help="Upgrade pip inside the smoke venv before installing packages.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of a short text summary.",
    )
    return parser


def _run_smoke(args: argparse.Namespace, work_dir: Path) -> int:
    venv_dir = work_dir / "venv"
    data_root = work_dir / "runtime" / "data"
    wheelhouse = work_dir / "wheelhouse"
    axp_path = work_dir / "axdata-source-tdx.axp"
    source_paths = _materialize_package_sources(work_dir)

    _run([args.python, "-m", "venv", str(venv_dir)], cwd=REPO_ROOT)
    venv_python = _venv_python(venv_dir)
    pip = [str(venv_python), "-m", "pip"]

    if args.upgrade_pip:
        _run([*pip, "install", "--upgrade", "pip"], cwd=REPO_ROOT)

    built_wheels: list[str] = []
    if args.mode == "wheel":
        built_wheels.extend(_build_local_wheels(pip, wheelhouse, _base_package_paths(source_paths)))
        _pip_install_wheels(pip, wheelhouse, built_wheels)
    else:
        editable_paths = _base_package_paths(source_paths)
        if args.tdx_mode == "editable":
            editable_paths.append(source_paths["tdx"])
        _pip_install_editable(pip, editable_paths)

    if args.tdx_mode in {"wheel", "axp"}:
        tdx_wheels = _build_local_wheels(
            pip,
            wheelhouse,
            [source_paths["tdx"]],
        )
        built_wheels.extend(tdx_wheels)
        if args.tdx_mode == "wheel":
            _pip_install_wheels(pip, wheelhouse, tdx_wheels)
        else:
            tdx_wheel = _find_wheel(wheelhouse, "axdata_source_tdx")
            _build_tdx_axp(tdx_wheel, axp_path)

    axdata = _venv_console(venv_dir, "axdata")
    commands: list[str] = []
    _run_capture([str(axdata), "--help"], commands=commands, cwd=REPO_ROOT)
    _run_capture([str(axdata), "--data-root", str(data_root), "init", "--json"], commands=commands)
    _run_capture(
        [str(axdata), "--data-root", str(data_root), "config", "show", "--json"],
        commands=commands,
    )
    doctor_before = _run_json(
        [str(axdata), "--data-root", str(data_root), "doctor", "--json"],
        commands=commands,
    )
    status_before = _run_json(
        [str(axdata), "--data-root", str(data_root), "status", "--json"],
        commands=commands,
    )

    axp_preview: dict[str, object] | None = None
    axp_install: dict[str, object] | None = None
    plugin_site_packages: str | None = None
    if args.tdx_mode == "axp":
        axp_preview = _run_json(
            [str(axdata), "--data-root", str(data_root), "plugin", "axp-preview", str(axp_path), "--json"],
            commands=commands,
        )
        axp_install = _run_json(
            [
                str(axdata),
                "--data-root",
                str(data_root),
                "plugin",
                "axp-install",
                str(axp_path),
                "--no-pth",
                "--json",
            ],
            commands=commands,
        )
        if isinstance(axp_install, dict):
            value = axp_install.get("site_packages")
            plugin_site_packages = str(value) if value else None

    providers_before_enable = _run_json(
        [str(axdata), "--data-root", str(data_root), "plugin", "list", "--json"],
        commands=commands,
    )
    tdx_before = _find_tdx_provider(providers_before_enable)
    _run_capture(
        [str(axdata), "--data-root", str(data_root), "plugin", "enable", TDX_PROVIDER_ID],
        commands=commands,
    )
    providers_after_enable = _run_json(
        [str(axdata), "--data-root", str(data_root), "plugin", "list", "--json"],
        commands=commands,
    )
    tdx_after = _find_tdx_provider(providers_after_enable)
    if tdx_after.get("status") != "enabled":
        raise RuntimeError(f"TDX provider did not enable cleanly: {tdx_after!r}")

    doctor_after = _run_json(
        [str(axdata), "--data-root", str(data_root), "doctor", "--json"],
        commands=commands,
    )
    _verify_tdx_manifest(venv_python, plugin_site_packages=plugin_site_packages)

    summary = {
        "work_dir": str(work_dir),
        "source_root": str(source_paths["source_root"]),
        "venv": str(venv_dir),
        "data_root": str(data_root),
        "mode": args.mode,
        "tdx_mode": args.tdx_mode,
        "built_wheels": built_wheels,
        "axp": str(axp_path) if args.tdx_mode == "axp" else None,
        "commands": commands,
        "doctor_before_status": doctor_before["summary"]["status"],
        "status_before_status": status_before["summary"]["status"],
        "doctor_after_status": doctor_after["summary"]["status"],
        "tdx_before": {
            "provider_id": tdx_before["provider_id"],
            "status": tdx_before["status"],
            "interfaces": tdx_before["interfaces"],
        },
        "tdx_after": {
            "provider_id": tdx_after["provider_id"],
            "status": tdx_after["status"],
            "interfaces": tdx_after["interfaces"],
        },
        "axp_preview": axp_preview,
        "axp_install": axp_install,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("AxData packaging smoke passed")
        print(f"mode={args.mode} tdx_mode={args.tdx_mode}")
        print(f"data_root={data_root}")
        print(f"tdx_before={tdx_before['status']} tdx_after={tdx_after['status']}")
        print(f"doctor_after={doctor_after['summary']['status']}")
    return 0


def _base_package_paths(source_paths: dict[str, Path]) -> list[Path]:
    return [
        source_paths["workspace"],
        source_paths["core"],
        source_paths["sdk"],
    ]


def _materialize_package_sources(work_dir: Path) -> dict[str, Path]:
    source_root = Path(tempfile.mkdtemp(prefix="sources-", dir=work_dir))
    workspace = source_root / "workspace"
    workspace.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "pyproject.toml", workspace / "pyproject.toml")

    core = _copy_source_tree(REPO_ROOT / "libs" / "axdata_core", source_root / "axdata-core")
    sdk = _copy_source_tree(REPO_ROOT / "packages" / "axdata-sdk", source_root / "axdata-sdk")
    tdx = _copy_source_tree(REPO_ROOT / "packages" / "axdata-source-tdx", source_root / "axdata-source-tdx")
    return {
        "source_root": source_root,
        "workspace": workspace,
        "core": core,
        "sdk": sdk,
        "tdx": tdx,
    }


def _copy_source_tree(source: Path, target: Path) -> Path:
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.egg-info",
            "build",
            "dist",
        ),
    )
    return target


def _pip_install_editable(pip: list[str], paths: list[Path]) -> None:
    command = [*pip, "install"]
    for path in paths:
        command.extend(["-e", str(path)])
    _run(command, cwd=REPO_ROOT)


def _build_local_wheels(pip: list[str], wheelhouse: Path, paths: list[Path]) -> list[str]:
    wheelhouse.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in wheelhouse.glob("*.whl")}
    _run([*pip, "wheel", "--no-deps", "-w", str(wheelhouse), *map(str, paths)], cwd=REPO_ROOT)
    after = sorted(path.name for path in wheelhouse.glob("*.whl"))
    return [name for name in after if name not in before]


def _pip_install_wheels(pip: list[str], wheelhouse: Path, wheel_names: list[str]) -> None:
    wheel_paths = [str(wheelhouse / name) for name in wheel_names]
    _run([*pip, "install", "--find-links", str(wheelhouse), *wheel_paths], cwd=REPO_ROOT)


def _build_tdx_axp(tdx_wheel: Path, axp_path: Path) -> None:
    manifest_path = (
        REPO_ROOT
        / "packages"
        / "axdata-source-tdx"
        / "src"
        / "axdata_source_tdx"
        / "axdata-provider.json"
    )
    readme_path = REPO_ROOT / "packages" / "axdata-source-tdx" / "README.md"
    license_path = REPO_ROOT / "LICENSE"
    digest = hashlib.sha256(tdx_wheel.read_bytes()).hexdigest()
    with ZipFile(axp_path, "w") as archive:
        archive.write(manifest_path, "manifest.json")
        archive.write(tdx_wheel, f"wheels/{tdx_wheel.name}")
        archive.writestr("checksums.txt", f"{digest}  wheels/{tdx_wheel.name}\n")
        if readme_path.exists():
            archive.write(readme_path, "README.md")
        if license_path.exists():
            archive.write(license_path, "LICENSE")
        samples_dir = REPO_ROOT / "packages" / "axdata-source-tdx" / "samples"
        if samples_dir.exists():
            for sample in sorted(path for path in samples_dir.rglob("*") if path.is_file()):
                archive.write(sample, sample.relative_to(samples_dir.parent).as_posix())


def _find_wheel(wheelhouse: Path, distribution_prefix: str) -> Path:
    matches = sorted(wheelhouse.glob(f"{distribution_prefix}-*.whl"))
    if not matches:
        raise RuntimeError(f"No wheel found for {distribution_prefix} in {wheelhouse}")
    return matches[-1]


def _find_tdx_provider(payload: object) -> dict[str, object]:
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected provider list JSON, got: {payload!r}")
    for item in payload:
        if isinstance(item, dict) and item.get("provider_id") == TDX_PROVIDER_ID:
            interfaces = item.get("interfaces") or []
            if "stock_codes_tdx" not in interfaces:
                raise RuntimeError("TDX provider is missing stock_codes_tdx in manifest.")
            return item
    raise RuntimeError(f"TDX provider {TDX_PROVIDER_ID} was not discovered.")


def _verify_tdx_manifest(python: Path, *, plugin_site_packages: str | None = None) -> None:
    path_setup = ""
    if plugin_site_packages:
        path_setup = f"import sys\nsys.path.insert(0, {plugin_site_packages!r})\n"
    code = path_setup + """
import importlib.resources as resources
import json

manifest = resources.files("axdata_source_tdx").joinpath("axdata-provider.json")
quote_servers = resources.files("axdata_source_tdx").joinpath("resources/tdx_quote_servers.json")
finance_map = resources.files("axdata_source_tdx").joinpath("resources/finance_maps/incon.dat")
payload = json.loads(manifest.read_text(encoding="utf-8"))
assert payload["provider"]["provider_id"] == "axdata.source.tdx_external"
assert quote_servers.is_file()
assert finance_map.is_file()
print("tdx manifest ok")
""".strip()
    _run([str(python), "-c", code], cwd=REPO_ROOT)


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


def _run_capture(
    command: list[str],
    *,
    commands: list[str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    commands.append(_display_command(command))
    return _run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    stdout: int | None = None,
    stderr: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        stdout=stdout,
        stderr=stderr,
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
