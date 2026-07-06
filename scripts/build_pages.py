"""Build the AxData GitHub Pages documentation site.

The generated site is static: it reads Provider/Interface metadata from the
local plugin catalog at build time and writes HTML/JSON files under ``site/``.
Opening the generated pages never calls AxData API or third-party sources.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "site"
PUBLIC_SOURCE_PROVIDER_IDS = (
    "axdata.source.tdx_external",
    "axdata.source.tdx_ext_external",
)
SOURCE_ORDER = (
    "通达信",
    "通达信扩展行情",
    "交易所",
    "东方财富",
    "巨潮",
    "腾讯财经",
    "新浪财经",
    "财联社",
    "开盘红",
)
DOC_PAGES: tuple[tuple[str, str], ...] = (
    ("quickstart.md", "快速开始"),
    ("architecture.md", "架构设计"),
    ("api-design.md", "API 与 SDK"),
    ("data-layers.md", "数据分层"),
    ("schema.md", "Schema 与字段"),
    ("source-provider-development.md", "数据源插件开发"),
    ("collector-plugin-development.md", "采集器插件开发"),
    ("plugin-development.md", "插件开发总览"),
    ("axdata-development-standards.md", "开发指南"),
    ("plugin-spec.md", "插件协议"),
    ("plugin-install-management.md", "插件安装管理"),
    ("axp-packaging-guide.md", "AXP 打包分享"),
    ("release-packaging.md", "发布打包检查"),
    ("roadmap.md", "路线图"),
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build AxData static documentation site.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for the generated static site. Defaults to ./site.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON build summary.",
    )
    args = parser.parse_args(argv)

    summary = build_site(args.output)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            f"Built AxData docs site: {summary['interface_count']} interfaces, "
            f"{summary['doc_count']} docs -> {summary['output_dir']}"
        )
    return 0


def build_site(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_path = Path(output_dir).resolve()
    entries = load_interface_entries()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    prepared_entries = prepare_interface_entries(entries)

    if output_path.exists():
        shutil.rmtree(output_path)
    (output_path / "interfaces").mkdir(parents=True, exist_ok=True)
    (output_path / "docs").mkdir(parents=True, exist_ok=True)
    copy_assets(output_path)

    write_text(output_path / ".nojekyll", "")
    write_text(output_path / "styles.css", site_css())
    write_text(output_path / "index.html", render_home(prepared_entries, generated_at))
    write_text(output_path / "interfaces" / "index.html", render_interface_index(prepared_entries, generated_at))
    write_json(output_path / "interfaces" / "catalog.json", catalog_json(prepared_entries, generated_at))

    for entry in prepared_entries:
        write_text(
            output_path / "interfaces" / f"{entry['slug']}.html",
            render_interface_detail(entry, generated_at),
        )

    rendered_docs = render_doc_pages(output_path)
    write_text(output_path / "docs" / "index.html", render_docs_index(rendered_docs, generated_at))

    source_counts = Counter(entry["source_name_zh"] for entry in prepared_entries)
    return {
        "output_dir": str(output_path),
        "interface_count": len(prepared_entries),
        "source_counts": dict(sorted(source_counts.items(), key=lambda item: source_sort_key(item[0]))),
        "doc_count": len(rendered_docs),
        "generated_at": generated_at,
    }


def load_interface_entries() -> list[dict[str, Any]]:
    """Load the public interface catalog from the plugin registry."""

    ensure_repo_import_paths()
    from axdata_core.plugin_config import PluginConfig
    from axdata_core.provider_catalog import list_registry_interface_dicts

    config = PluginConfig(enabled_provider_ids=PUBLIC_SOURCE_PROVIDER_IDS)
    rows = list_registry_interface_dicts(plugin_config=config)
    enabled_rows = [
        dict(row)
        for row in rows
        if row.get("enabled", True) is True and str(row.get("plugin_status", "enabled")) == "enabled"
    ]
    return sorted(enabled_rows, key=interface_sort_key)


def ensure_repo_import_paths() -> None:
    """Allow this script to run from a clean checkout without editable installs."""

    candidates = [
        REPO_ROOT / "libs" / "axdata_core",
        *(path for path in (REPO_ROOT / "packages").glob("axdata-source-*/src")),
    ]
    for candidate in reversed(candidates):
        if candidate.is_dir():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)


def prepare_interface_entries(entries: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for raw in entries:
        entry = dict(raw)
        name = str(entry.get("name") or entry.get("interface_name") or "unknown_interface")
        slug = unique_slug(name, seen_slugs)
        entry["name"] = name
        entry["slug"] = slug
        entry["title"] = str(entry.get("display_name_zh") or name)
        entry["source_name_zh"] = str(entry.get("source_name_zh") or "其它")
        entry["source_code"] = str(entry.get("source_code") or "unknown")
        entry["category"] = str(entry.get("category") or "接口")
        entry["menu_path"] = normalize_menu_path(entry)
        entry["parameters"] = list(entry.get("parameters") or [])
        entry["fields"] = list(entry.get("fields") or [])
        entry["reference_sections"] = list(entry.get("reference_sections") or [])
        entry["example"] = normalize_example(entry.get("example"))
        entry["summary"] = first_text(
            entry.get("summary_zh"),
            entry.get("description_zh"),
            entry.get("description"),
            entry["title"],
        )
        entry["description_text"] = first_text(
            entry.get("description_zh"),
            entry.get("description"),
            entry["summary"],
        )
        prepared.append(entry)
    return prepared


def normalize_menu_path(entry: Mapping[str, Any]) -> list[str]:
    raw = entry.get("menu_path")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        values = [str(item) for item in raw if str(item).strip()]
    else:
        values = []
    if not values:
        values = [
            str(entry.get("source_name_zh") or "其它"),
            str(entry.get("category") or "接口"),
        ]
    return values


def normalize_example(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {"request": {}, "response": []}
    request = raw.get("request")
    response = raw.get("response")
    return {
        "request": dict(request) if isinstance(request, Mapping) else {},
        "response": list(response) if isinstance(response, list) else [],
    }


def catalog_json(entries: Sequence[Mapping[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "project": "AxData",
        "generated_at": generated_at,
        "interface_count": len(entries),
        "sources": [
            {"name": source, "count": count}
            for source, count in sorted(
                Counter(entry["source_name_zh"] for entry in entries).items(),
                key=lambda item: source_sort_key(item[0]),
            )
        ],
        "interfaces": [
            {
                "name": entry["name"],
                "title": entry["title"],
                "source_name_zh": entry["source_name_zh"],
                "source_code": entry["source_code"],
                "category": entry["category"],
                "menu_path": entry["menu_path"],
                "asset_class": entry.get("asset_class"),
                "provider_id": entry.get("provider_id"),
                "summary": entry["summary"],
                "url": f"interfaces/{entry['slug']}.html",
            }
            for entry in entries
        ],
    }


def render_home(entries: Sequence[Mapping[str, Any]], generated_at: str) -> str:
    source_counts = sorted(
        Counter(entry["source_name_zh"] for entry in entries).items(),
        key=lambda item: source_sort_key(item[0]),
    )
    stats = "".join(
        f"<div class=\"stat\"><strong>{count}</strong><span>{escape(source)}</span></div>"
        for source, count in source_counts
    )
    screenshot_grid = "".join(
        f"<figure><img src=\"assets/{escape(name)}\" alt=\"{escape(title)}\"><figcaption>{escape(title)}</figcaption></figure>"
        for name, title in (
            ("axdata-start-overview.png", "开始页与架构边界"),
            ("axdata-interface-catalog.png", "接口目录与字段说明"),
            ("axdata-collector-task.png", "采集任务"),
            ("axdata-plugin-management.png", "插件管理"),
        )
        if (REPO_ROOT / "docs" / "assets" / name).is_file()
    )
    body = f"""
<section class="hero">
  <p class="eyebrow">开源量化数据库框架</p>
  <h1>AxData</h1>
  <p class="lead">AxData 将数据源接口、采集任务、开放文件存储、本地查询、插件管理、Python SDK、HTTP API 和 Web 控制台放在同一个可扩展的数据平台里，面向个人量化研究、本地数据管理和数据源插件开发。</p>
  <div class="actions">
    <a class="button primary" href="interfaces/index.html">查看接口文档</a>
    <a class="button" href="docs/quickstart.html">快速开始</a>
  </div>
</section>
<section>
  <h2>接口目录</h2>
  <p>文档站在构建时从 AxData Provider Registry 读取接口声明，并生成静态页面。打开 GitHub Pages 时不会请求 AxData 后端，也不会访问第三方数据源。</p>
  <div class="stats">{stats}</div>
</section>
<section>
  <h2>项目边界</h2>
  <div class="grid two">
    <div class="panel">
      <h3>数据源接口</h3>
      <p>Provider 插件负责一次性源端请求，返回 AxData 字段，默认不写入 data 目录。</p>
    </div>
    <div class="panel">
      <h3>采集器</h3>
      <p>Collector 插件负责显式采集任务、Parquet 写出、质量检查和元数据记录。</p>
    </div>
  </div>
</section>
<section>
  <h2>界面预览</h2>
  <div class="screenshots">{screenshot_grid}</div>
</section>
<section>
  <h2>致谢与声明</h2>
  <p>感谢 pytdx、AKShare、levistock 等开源项目为公开接口研究提供参考。AxData 仅用于个人学习、协议研究和非商业研究；通过本项目获取的数据禁止用于商业行为、付费服务、生产服务、转售或其他营利用途。</p>
</section>
<p class="build-note">生成时间：{escape(generated_at)}</p>
"""
    return page("AxData 文档站", body, active="home")


def render_interface_index(entries: Sequence[Mapping[str, Any]], generated_at: str) -> str:
    source_options = "".join(
        f"<option value=\"{escape(source)}\">{escape(source)} ({count})</option>"
        for source, count in sorted(
            Counter(entry["source_name_zh"] for entry in entries).items(),
            key=lambda item: source_sort_key(item[0]),
        )
    )
    rows = "\n".join(
        render_interface_index_row(entry)
        for entry in entries
    )
    body = f"""
<section class="page-head">
  <p class="eyebrow">Interface Catalog</p>
  <h1>接口文档</h1>
  <p class="lead">共 {len(entries)} 个 source_request 接口。所有详情页来自插件接口目录和固定 example 快照。</p>
</section>
<section class="toolbar">
  <label>
    搜索
    <input id="interface-search" type="search" placeholder="输入接口名、中文名、字段或数据源">
  </label>
  <label>
    数据源
    <select id="source-filter">
      <option value="">全部数据源 ({len(entries)})</option>
      {source_options}
    </select>
  </label>
</section>
<section>
  <div class="table-wrap">
    <table id="interface-table">
      <thead>
        <tr>
          <th>接口</th>
          <th>数据源</th>
          <th>目录</th>
          <th>参数</th>
          <th>字段</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</section>
<p class="build-note">生成时间：{escape(generated_at)}</p>
<script>
const searchInput = document.getElementById("interface-search");
const sourceFilter = document.getElementById("source-filter");
const rows = Array.from(document.querySelectorAll("#interface-table tbody tr"));
function applyFilters() {{
  const query = searchInput.value.trim().toLowerCase();
  const source = sourceFilter.value;
  for (const row of rows) {{
    const matchesSource = !source || row.dataset.source === source;
    const matchesQuery = !query || row.dataset.text.includes(query);
    row.hidden = !(matchesSource && matchesQuery);
  }}
}}
searchInput.addEventListener("input", applyFilters);
sourceFilter.addEventListener("change", applyFilters);
</script>
"""
    return page("接口文档 - AxData", body, active="interfaces")


def render_interface_index_row(entry: Mapping[str, Any]) -> str:
    params = entry.get("parameters") or []
    fields = entry.get("fields") or []
    text = " ".join(
        [
            str(entry.get("name") or ""),
            str(entry.get("title") or ""),
            str(entry.get("source_name_zh") or ""),
            " ".join(str(item) for item in entry.get("menu_path") or []),
            " ".join(str(item.get("name", "")) for item in params if isinstance(item, Mapping)),
            " ".join(str(item.get("name", "")) for item in fields if isinstance(item, Mapping)),
        ]
    ).lower()
    menu_path = " / ".join(str(item) for item in entry.get("menu_path") or [])
    return f"""
<tr data-source="{escape(str(entry['source_name_zh']))}" data-text="{escape(text)}">
  <td><a href="{escape(str(entry['slug']))}.html">{escape(str(entry['title']))}</a><code>{escape(str(entry['name']))}</code></td>
  <td>{escape(str(entry['source_name_zh']))}</td>
  <td>{escape(menu_path)}</td>
  <td>{len(params)}</td>
  <td>{len(fields)}</td>
</tr>"""


def render_interface_detail(entry: Mapping[str, Any], generated_at: str) -> str:
    request = entry["example"]["request"]
    response = entry["example"]["response"]
    meta = [
        ("接口名", entry["name"]),
        ("Provider", entry.get("provider_id") or entry.get("source_code") or ""),
        ("数据源", f"{entry['source_name_zh']} / {entry['source_code']}"),
        ("目录", " / ".join(str(item) for item in entry.get("menu_path") or [])),
        ("资产类型", entry.get("asset_class") or "unknown"),
        ("请求模式", entry.get("request_mode") or "source_request"),
        ("采集支持", collection_label(entry.get("collection"))),
    ]
    body = f"""
<section class="page-head">
  <p class="breadcrumb"><a href="index.html">接口文档</a> / {escape(str(entry['source_name_zh']))}</p>
  <h1>{escape(str(entry['title']))}</h1>
  <p class="code-title">{escape(str(entry['name']))}</p>
  <p class="lead">{escape(str(entry['summary']))}</p>
</section>
<section>
  <h2>接口信息</h2>
  {definition_grid(meta)}
  <p>{escape(str(entry['description_text']))}</p>
</section>
<section>
  <h2>参数</h2>
  {parameter_table(entry.get("parameters") or [])}
  {optional_note("参数说明", entry.get("params_note_zh"))}
  {optional_note("参数示例", entry.get("params_example_zh"))}
</section>
<section>
  <h2>返回字段</h2>
  {field_table(entry.get("fields") or [])}
</section>
<section>
  <h2>调用示例</h2>
  <h3>Python SDK</h3>
  {code_block(sdk_example(str(entry['name']), request), "python")}
  <h3>HTTP API</h3>
  {code_block(http_example(str(entry['name']), request), "http")}
</section>
<section>
  <h2>真实样例快照</h2>
  <h3>请求参数</h3>
  {code_block(json.dumps(request, ensure_ascii=False, indent=2), "json")}
  <h3>响应样例</h3>
  {code_block(json.dumps(response, ensure_ascii=False, indent=2), "json")}
</section>
{reference_sections(entry.get("reference_sections") or [])}
<p class="build-note">生成时间：{escape(generated_at)}</p>
"""
    return page(f"{entry['title']} - AxData 接口文档", body, active="interfaces")


def render_doc_pages(output_path: Path) -> list[dict[str, str]]:
    rendered: list[dict[str, str]] = []
    for filename, title in DOC_PAGES:
        source = REPO_ROOT / "docs" / filename
        if not source.is_file():
            continue
        slug = source.stem
        html = markdown_to_html(source.read_text(encoding="utf-8"), base_depth=1)
        body = f"""
<section class="page-head">
  <p class="breadcrumb"><a href="index.html">开发文档</a></p>
  <h1>{escape(title)}</h1>
</section>
<article class="markdown-body">{html}</article>
"""
        write_text(output_path / "docs" / f"{slug}.html", page(f"{title} - AxData 文档", body, active="docs"))
        rendered.append({"title": title, "slug": slug, "filename": filename})
    return rendered


def render_docs_index(docs: Sequence[Mapping[str, str]], generated_at: str) -> str:
    items = "".join(
        f"<a class=\"doc-card\" href=\"{escape(doc['slug'])}.html\"><strong>{escape(doc['title'])}</strong><span>{escape(doc['filename'])}</span></a>"
        for doc in docs
    )
    body = f"""
<section class="page-head">
  <p class="eyebrow">Developer Docs</p>
  <h1>开发与使用文档</h1>
  <p class="lead">这里收录 AxData 的运行、架构、插件、采集器、AXP 和发布打包文档。接口详情请查看接口文档页。</p>
</section>
<section class="doc-grid">{items}</section>
<p class="build-note">生成时间：{escape(generated_at)}</p>
"""
    return page("开发文档 - AxData", body, active="docs")


def markdown_to_html(markdown: str, *, base_depth: int = 0) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_mode: str | None = None
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_mode
        if list_mode:
            output.append(f"</{list_mode}>")
            list_mode = None

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            output.append(render_markdown_table(table_lines))
            table_lines = []

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            if in_code:
                output.append(code_block("\n".join(code_lines), code_lang))
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                in_code = True
                code_lang = line.strip("`").strip()
            continue
        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            flush_table()
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_list()
            table_lines.append(stripped)
            continue
        flush_table()

        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            flush_list()
            alt, href = image_match.groups()
            output.append(f"<p><img src=\"{escape(normalize_doc_href(href))}\" alt=\"{escape(alt)}\"></p>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = min(6, len(heading_match.group(1)) + base_depth)
            text = heading_match.group(2).strip()
            output.append(f"<h{level}>{render_inline(text)}</h{level}>")
            continue

        unordered = re.match(r"^[-*]\s+(.*)$", stripped)
        ordered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            wanted = "ul" if unordered else "ol"
            if list_mode != wanted:
                flush_list()
                output.append(f"<{wanted}>")
                list_mode = wanted
            text = (unordered or ordered).group(1)
            output.append(f"<li>{render_inline(text)}</li>")
            continue

        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_table()
    if in_code:
        output.append(code_block("\n".join(code_lines), code_lang))
    return "\n".join(output)


def render_markdown_table(lines: Sequence[str]) -> str:
    parsed = [split_table_row(line) for line in lines]
    if not parsed:
        return ""
    header = parsed[0]
    body_rows = parsed[1:]
    if body_rows and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in body_rows[0]):
        body_rows = body_rows[1:]
    head_html = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    rows_html = "".join(
        "<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>"
        for row in body_rows
    )
    return f"<div class=\"table-wrap\"><table><thead><tr>{head_html}</tr></thead><tbody>{rows_html}</tbody></table></div>"


def split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def render_inline(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = normalize_doc_href(match.group(2))
        return f"<a href=\"{escape(href)}\">{label}</a>"

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, escaped)
    return escaped


def normalize_doc_href(href: str) -> str:
    clean = href.strip()
    if clean.startswith(("http://", "https://", "#")):
        return clean
    if clean.startswith("docs/assets/"):
        return "../assets/" + clean.removeprefix("docs/assets/")
    if clean.startswith("assets/"):
        return "../" + clean
    if clean.endswith(".md"):
        return clean[:-3] + ".html"
    return clean


def page(title: str, body: str, *, active: str) -> str:
    nav_items = (
        ("home", "首页", root_link(active, "index.html")),
        ("interfaces", "接口文档", root_link(active, "interfaces/index.html")),
        ("docs", "开发文档", root_link(active, "docs/index.html")),
    )
    nav = "".join(
        f"<a class=\"{'active' if key == active else ''}\" href=\"{escape(href)}\">{escape(label)}</a>"
        for key, label, href in nav_items
    )
    css_href = root_link(active, "styles.css")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{escape(css_href)}">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{escape(root_link(active, 'index.html'))}">AxData</a>
    <nav>{nav}</nav>
  </header>
  <main>{body}</main>
  <footer>AxData is an open-source quantitative database framework for personal learning, protocol research and non-commercial research.</footer>
</body>
</html>
"""


def root_link(active: str, href: str) -> str:
    if active in {"interfaces", "docs"}:
        return "../" + href
    return href


def definition_grid(items: Sequence[tuple[str, Any]]) -> str:
    cells = "".join(
        f"<div><dt>{escape(str(label))}</dt><dd>{escape(str(value))}</dd></div>"
        for label, value in items
    )
    return f"<dl class=\"definition-grid\">{cells}</dl>"


def parameter_table(parameters: Sequence[Mapping[str, Any]]) -> str:
    if not parameters:
        return "<p>无参数。</p>"
    rows = "".join(
        "<tr>"
        f"<td><code>{escape(str(item.get('name', '')))}</code></td>"
        f"<td>{escape(str(item.get('dtype') or item.get('type') or ''))}</td>"
        f"<td>{'是' if item.get('required') else '否'}</td>"
        f"<td>{escape(description_for(item))}</td>"
        f"<td>{escape(default_for(item))}</td>"
        "</tr>"
        for item in parameters
    )
    return f"""
<div class="table-wrap"><table>
  <thead><tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>"""


def field_table(fields: Sequence[Mapping[str, Any]]) -> str:
    if not fields:
        return "<p>暂无字段声明。</p>"
    rows = "".join(
        "<tr>"
        f"<td><code>{escape(str(item.get('name', '')))}</code></td>"
        f"<td>{escape(str(item.get('dtype') or item.get('type') or ''))}</td>"
        f"<td>{escape(description_for(item))}</td>"
        "</tr>"
        for item in fields
    )
    return f"""
<div class="table-wrap"><table>
  <thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>"""


def reference_sections(sections: Sequence[Mapping[str, Any]]) -> str:
    if not sections:
        return ""
    html_parts = ["<section><h2>参考表</h2>"]
    for section in sections:
        title = str(section.get("title") or section.get("id") or "参考表")
        note = str(section.get("note") or "")
        columns = [str(column) for column in (section.get("columns") or [])]
        rows = list(section.get("rows") or [])
        html_parts.append(f"<h3>{escape(title)}</h3>")
        if note:
            html_parts.append(f"<p>{escape(note)}</p>")
        if columns and rows:
            head = "".join(f"<th>{escape(column)}</th>" for column in columns)
            body = ""
            for row in rows:
                values = row if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)) else [row]
                body += "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in values) + "</tr>"
            html_parts.append(f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")
    html_parts.append("</section>")
    return "\n".join(html_parts)


def optional_note(title: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return f"<div class=\"note\"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>"


def sdk_example(interface_name: str, request: Mapping[str, Any]) -> str:
    if not request:
        return f'import axdata as ax\n\nclient = ax.AxDataClient()\nrows = client.call("{interface_name}")'
    params = ",\n".join(
        f"    {key}={python_literal(value)}"
        for key, value in sorted(request.items())
    )
    return (
        "import axdata as ax\n\n"
        "client = ax.AxDataClient()\n"
        "rows = client.call(\n"
        f'    "{interface_name}",\n'
        f"{params},\n"
        ")"
    )


def http_example(interface_name: str, request: Mapping[str, Any]) -> str:
    payload = json.dumps({"params": dict(request)}, ensure_ascii=False, indent=2)
    return f"POST /v1/request/{interface_name}\nContent-Type: application/json\n\n{payload}"


def code_block(value: str, lang: str = "") -> str:
    class_name = f" class=\"language-{escape(lang)}\"" if lang else ""
    return f"<pre><code{class_name}>{escape(value)}</code></pre>"


def python_literal(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    return repr(value)


def collection_label(collection: Any) -> str:
    if not isinstance(collection, Mapping):
        return "否"
    if not collection.get("supported"):
        return "否"
    profile = collection.get("default_profile")
    return f"是，默认 {profile}" if profile else "是"


def description_for(item: Mapping[str, Any]) -> str:
    return first_text(item.get("description_zh"), item.get("description"), item.get("display_name_zh"))


def default_for(item: Mapping[str, Any]) -> str:
    if "default" not in item:
        return ""
    return json.dumps(item.get("default"), ensure_ascii=False)


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def unique_slug(value: str, seen: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower() or "item"
    slug = base
    index = 2
    while slug in seen:
        slug = f"{base}-{index}"
        index += 1
    seen.add(slug)
    return slug


def interface_sort_key(entry: Mapping[str, Any]) -> tuple[int, list[str], str]:
    source = str(entry.get("source_name_zh") or "其它")
    menu = entry.get("menu_path")
    menu_parts = [str(item) for item in menu] if isinstance(menu, Sequence) and not isinstance(menu, str) else []
    return (source_sort_key(source), menu_parts, str(entry.get("name") or ""))


def source_sort_key(source: str) -> int:
    try:
        return SOURCE_ORDER.index(source)
    except ValueError:
        return len(SOURCE_ORDER)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def copy_assets(output_path: Path) -> None:
    source_dir = REPO_ROOT / "docs" / "assets"
    if not source_dir.is_dir():
        return
    target_dir = output_path / "assets"
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)


def site_css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-strong: #eef4f8;
  --text: #18212f;
  --muted: #607086;
  --line: #d9e2ea;
  --accent: #146c94;
  --accent-strong: #0f4f6d;
  --accent-soft: #dff1f7;
  --ok: #2f7d5c;
  --warn: #a56218;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.65;
}
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-strong); text-decoration: underline; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 14px clamp(18px, 4vw, 48px);
  background: rgba(255,255,255,.94);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(12px);
}
.brand {
  color: var(--text);
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 0;
}
nav { display: flex; gap: 10px; flex-wrap: wrap; }
nav a {
  color: var(--muted);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 14px;
}
nav a.active, nav a:hover {
  background: var(--accent-soft);
  color: var(--accent-strong);
  text-decoration: none;
}
main {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 34px 0 56px;
}
section {
  margin: 0 0 28px;
  padding: 0;
}
.hero, .page-head {
  padding: 28px 0 10px;
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0;
}
h1, h2, h3 {
  letter-spacing: 0;
  line-height: 1.25;
}
h1 {
  margin: 0 0 14px;
  font-size: clamp(34px, 5vw, 58px);
}
h2 {
  margin: 0 0 14px;
  font-size: 24px;
}
h3 {
  margin: 18px 0 10px;
  font-size: 18px;
}
.lead {
  max-width: 900px;
  color: #314154;
  font-size: 18px;
}
.actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 20px; }
.button {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  padding: 8px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--text);
  background: var(--surface);
}
.button.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}
.stat, .panel, .doc-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
}
.stat strong {
  display: block;
  font-size: 30px;
  line-height: 1;
  color: var(--accent-strong);
}
.stat span { color: var(--muted); }
.grid.two {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}
.screenshots {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}
figure {
  margin: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
figure img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
}
figcaption {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 14px;
}
.toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(200px, 300px);
  gap: 12px;
  align-items: end;
}
label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 14px;
}
input, select {
  width: 100%;
  min-height: 40px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 10px;
  background: var(--surface);
  color: var(--text);
  font: inherit;
}
.table-wrap {
  overflow-x: auto;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
}
table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}
th, td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
th {
  background: var(--surface-strong);
  color: #2b3b4f;
  font-weight: 700;
}
td code {
  display: block;
  margin-top: 4px;
}
code {
  padding: 2px 5px;
  border-radius: 5px;
  background: #eef2f6;
  color: #1e3a4f;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: .92em;
}
pre {
  overflow-x: auto;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #111827;
  color: #eef5ff;
}
pre code {
  padding: 0;
  background: transparent;
  color: inherit;
}
.definition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.definition-grid div {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 12px;
}
dt { color: var(--muted); font-size: 13px; }
dd { margin: 4px 0 0; font-weight: 650; }
.breadcrumb, .code-title, .build-note, footer {
  color: var(--muted);
}
.note {
  margin-top: 12px;
  padding: 12px;
  border-left: 4px solid var(--accent);
  background: var(--accent-soft);
  border-radius: 6px;
}
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.doc-card {
  color: var(--text);
}
.doc-card strong, .doc-card span {
  display: block;
}
.doc-card span {
  color: var(--muted);
  font-size: 14px;
}
.markdown-body img {
  max-width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
}
footer {
  border-top: 1px solid var(--line);
  padding: 22px clamp(18px, 4vw, 48px);
  font-size: 14px;
}
@media (max-width: 720px) {
  .site-header { align-items: flex-start; flex-direction: column; }
  .toolbar { grid-template-columns: 1fr; }
  main { width: min(100vw - 24px, 1180px); }
}
"""


if __name__ == "__main__":
    raise SystemExit(main())
