from __future__ import annotations

import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_axdata_user_package_depends_on_core_and_exposes_cli() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "packages" / "axdata-sdk" / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = set(pyproject["project"]["dependencies"])

    assert "axdata-core[parquet]>=0.1.0" in dependencies
    assert "fastapi>=0.115.0" in dependencies
    assert "pandas>=1.5.0" in dependencies
    assert "pydantic>=2.7.0" in dependencies
    assert "python-multipart>=0.0.9" in dependencies
    assert pyproject["project"]["scripts"]["axdata"] == "axdata_core.cli:main"
    assert "uvicorn[standard]>=0.30.0" in dependencies


def test_axdata_core_package_exposes_cli_entrypoint() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "libs" / "axdata_core" / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = set(pyproject["project"]["dependencies"])
    package_data = pyproject["tool"]["setuptools"]["package-data"]["axdata_core"]

    assert "packaging>=23" in dependencies
    assert pyproject["project"]["readme"] == "README.md"
    assert pyproject["project"]["scripts"]["axdata"] == "axdata_core.cli:main"
    assert pyproject["project"]["optional-dependencies"]["parquet"] == ["pyarrow>=16.0.0"]
    assert "_tdx_wire/py.typed" in package_data
    assert "resources/*.json" in package_data


def test_workspace_package_is_metadata_only() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["build-system"]["requires"] == ["setuptools>=77"]
    assert pyproject["build-system"]["build-backend"] == "setuptools.build_meta"
    assert pyproject["project"]["license"] == "Apache-2.0"
    assert pyproject["tool"]["setuptools"]["packages"] == []


def test_publishable_packages_use_spdx_license_metadata() -> None:
    package_paths = [
        REPO_ROOT / "libs" / "axdata_core" / "pyproject.toml",
        REPO_ROOT / "packages" / "axdata-sdk" / "pyproject.toml",
        REPO_ROOT / "packages" / "axdata-source-cninfo" / "pyproject.toml",
        REPO_ROOT / "packages" / "axdata-source-tdx" / "pyproject.toml",
        REPO_ROOT / "packages" / "axdata-source-tdx-ext" / "pyproject.toml",
        REPO_ROOT / "packages" / "axdata-source-tencent" / "pyproject.toml",
    ]

    for path in package_paths:
        pyproject = tomllib.loads(path.read_text(encoding="utf-8"))

        assert any(item.startswith("setuptools>=77") for item in pyproject["build-system"]["requires"])
        assert pyproject["project"]["license"] == "Apache-2.0"


def test_workspace_dev_api_script_is_cross_platform_launcher() -> None:
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["scripts"]["dev:api"] == "node scripts/dev-api.mjs"
    assert (REPO_ROOT / "scripts" / "dev-api.mjs").is_file()


def test_packaging_smoke_script_uses_temporary_environment_by_default() -> None:
    script = REPO_ROOT / "scripts" / "packaging_smoke.py"
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "tempfile.TemporaryDirectory" in source
    assert "tempfile.mkdtemp(prefix=\"sources-\"" in source
    assert "shutil.copytree" in source
    assert "default=sys.executable" in source
    assert "axdata --help" not in source
    assert "axdata-source-tdx.axp" in source


def test_pypi_readiness_script_is_local_only() -> None:
    script = REPO_ROOT / "scripts" / "pypi_readiness.py"
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "tempfile.TemporaryDirectory" in source
    assert "shutil.copytree" in source
    assert "twine\", \"check\"" in source
    assert "twine\", \"upload\"" not in source
    assert "testpypi" not in source.lower()
    assert "pypi.org/legacy" not in source
