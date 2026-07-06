# GitHub Pages 文档站

AxData 的 GitHub Pages 文档站用于承载公开说明书和完整接口文档。README 负责项目首页介绍；Pages 负责放接口目录、接口详情、插件开发规范、AXP 分享说明和发布相关文档。

## 设计原则

- 文档站是静态站点，打开页面时不请求 AxData 后端，也不访问第三方数据源。
- 接口文档由 `scripts/build_pages.py` 从 Provider Registry 读取插件接口目录生成，不手工维护全部接口页面。
- 每个接口页面展示中文名、接口名、数据源、目录、参数、返回字段、SDK 示例、HTTP 示例和固定 example response。
- 生成产物写入 `site/`，该目录是本地构建产物，不提交到仓库。
- GitHub Pages 发布由 `.github/workflows/pages.yml` 在 GitHub Actions 中完成。

## 本地构建

```powershell
npm run build:docs
```

构建完成后会生成：

```text
site/
  index.html
  interfaces/
    index.html
    catalog.json
    <interface>.html
  docs/
    index.html
    <doc>.html
  assets/
```

本地预览：

```powershell
npm run preview:docs
```

打开：

```text
http://127.0.0.1:8670
```

## GitHub 发布

仓库推到 GitHub 后，在仓库设置中把 Pages source 设为 GitHub Actions。之后 `main` 分支 push 或手动运行 `Pages` workflow，会自动构建并部署 `site/`。

当前本地仓库不需要提前提交 `site/`。Pages 页面上的接口数量和字段说明以构建时的插件接口目录为准。
