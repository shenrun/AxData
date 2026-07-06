# AxData 文档目录

文档站地址：[https://electkismet.github.io/AxData/](https://electkismet.github.io/AxData/)

本目录保留面向用户、插件开发者和项目维护者的文档。普通用户建议先阅读快速开始；需要扩展数据源或采集能力时，再阅读插件开发文档；维护者参考用于发布、接口盘点和调度设计。

## 用户入口

- [quickstart.md](quickstart.md)：本地安装、启动 API/Web、查看插件、运行采集任务。
- [api-design.md](api-design.md)：HTTP API、SDK 调用边界、鉴权和错误格式。
- [schema.md](schema.md)：核心表、字段契约和兼容规则。
- [data-layers.md](data-layers.md)：Parquet、DuckDB、raw/staging/core/factor 分层。

## 插件开发

- [plugin-development.md](plugin-development.md)：插件总体开发指南。
- [source-provider-development.md](source-provider-development.md)：数据源 Provider、接口目录、参数字段和 Adapter。
- [collector-plugin-development.md](collector-plugin-development.md)：采集器 CollectorSpec、runner、任务、写入和质量规则。
- [plugin-spec.md](plugin-spec.md)：插件 manifest 和能力协议字段。
- [plugin-install-management.md](plugin-install-management.md)：安装、启用、禁用、卸载和诊断。
- [axp-packaging-guide.md](axp-packaging-guide.md)：AXP 打包、预览、安装和导出。
- [github-pages.md](github-pages.md)：GitHub Pages 文档站的本地构建、预览和发布方式。

## 架构与开发规范

- [architecture.md](architecture.md)：整体架构和模块边界。
- [axdata-development-standards.md](axdata-development-standards.md)：数据源、采集器、数据集与 Web UI 开发规范。
- [dataset-and-duckdb.md](dataset-and-duckdb.md)：数据集声明与 DuckDB 查询缓存说明。
- [ui-standards.md](ui-standards.md)：Web UI 页面口径。
- [collector-scheduling.md](collector-scheduling.md)：采集调度、资源组、运行状态和诊断。

## 维护者参考

以下文档主要服务项目维护、发布准备和接口资产管理。普通用户不需要先阅读这些内容。

- [data-interface-inventory.md](data-interface-inventory.md)：当前接口资产矩阵。
- [release-packaging.md](release-packaging.md)：PyPI 发布前本地打包、安装和元数据验证。
- [roadmap.md](roadmap.md)：项目阶段路线图。
