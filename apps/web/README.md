# AxData Web

AxData 本地网站/开发者门户，基于 Vite + React。首页就是控制台，包含本地服务状态、数据目录、API Reference、调度任务和质量检查。

## 启动

```bash
cd /Users/ax/Desktop/AxData/apps/web
npm install
npm run dev
```

默认访问：

```text
http://127.0.0.1:8667
```

门户会尝试从本地 API 拉取健康状态：

```text
http://127.0.0.1:8666/health
```

如果默认端口已被其他服务占用，可以指定本机 Web 端口：

```bash
AXDATA_WEB_PORT=8767 npm run dev
```

如果本地 API 尚未启动，页面会显示 `API Offline`，其余控制台内容仍可查看。
Web 控制台只作为本机管理台，host 固定为 `127.0.0.1`；其他设备请通过 SDK/API 访问 AxData。

## 构建

```bash
npm run build
```
