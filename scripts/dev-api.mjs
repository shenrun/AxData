import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptsDir, "..");
const python = process.platform === "win32"
  ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
  : path.join(repoRoot, ".venv", "bin", "python");
const pythonCommand = existsSync(python) ? python : "python";
const metadataDir = path.join(repoRoot, "metadata");
const runtimeConfigPath = process.env.AXDATA_RUNTIME_CONFIG_FILE ?? path.join(metadataDir, "runtime_config.json");
const restartRequestPath = process.env.AXDATA_RESTART_REQUEST_FILE ?? path.join(metadataDir, "runtime_restart.json");
const launcherPath = process.env.AXDATA_LAUNCHER_FILE ?? path.join(metadataDir, "runtime_launcher.json");
const forwardedArgs = process.argv.slice(2);
const reloadEnabled = process.env.AXDATA_API_RELOAD === "1" || forwardedArgs.includes("--reload");
const passthroughArgs = forwardedArgs.filter((arg) => arg !== "--reload");
const reloadDirs = ["apps", "libs", "packages", "services", "scripts"]
  .map((name) => path.join(repoRoot, name))
  .filter((dir) => existsSync(dir));
const launcherId = randomUUID();
let child = null;
let restarting = false;
let stopping = false;
let lastRestartRequestId = null;
let lastRestartRequestMtime = 0;

process.stdout.on("error", () => {});
process.stderr.on("error", () => {});

function readRuntimeConfig() {
  if (!existsSync(runtimeConfigPath)) {
    return {};
  }
  try {
    const payload = JSON.parse(readFileSync(runtimeConfigPath, "utf8"));
    return payload && typeof payload === "object" ? payload : {};
  } catch (error) {
    console.warn(`[axdata] Ignoring invalid runtime config ${runtimeConfigPath}: ${error.message}`);
    return {};
  }
}

function currentLaunchConfig() {
  const config = readRuntimeConfig();
  return {
    host: String(config.api_host ?? process.env.AXDATA_API_HOST ?? "127.0.0.1"),
    port: String(config.api_port ?? process.env.AXDATA_API_PORT ?? "8666"),
    webPort: String(config.web_port ?? process.env.AXDATA_WEB_PORT ?? "8667")
  };
}

function safeWrite(stream, chunk) {
  if (!stream?.writable) {
    return;
  }
  try {
    stream.write(chunk, () => {});
  } catch {
    // Logging must never take down the launcher.
  }
}

function writeLauncherFile(config) {
  writeFileSync(
    launcherPath,
    JSON.stringify({
      pid: process.pid,
      launcher_id: launcherId,
      child_pid: child?.pid ?? null,
      started_at: new Date().toISOString(),
      heartbeat_at: new Date().toISOString(),
      repo_root: repoRoot,
      runtime_config_path: runtimeConfigPath,
      restart_request_path: restartRequestPath
    }, null, 2) + "\n",
    "utf8"
  );
}

function startApi() {
  const config = currentLaunchConfig();
  const env = {
    ...process.env,
    AXDATA_API_HOST: config.host,
    AXDATA_API_PORT: config.port,
    AXDATA_WEB_PORT: config.webPort,
    AXDATA_DEV_LAUNCHER: "1",
    AXDATA_DEV_LAUNCHER_ID: launcherId,
    AXDATA_RUNTIME_CONFIG_FILE: runtimeConfigPath,
    AXDATA_RESTART_REQUEST_FILE: restartRequestPath,
    AXDATA_LAUNCHER_FILE: launcherPath
  };
  console.log(`[axdata] Starting API on ${config.host}:${config.port}`);
  child = spawn(
    pythonCommand,
    [
      "-m",
      "uvicorn",
      "apps.api.main:app",
      "--host",
      config.host,
      "--port",
      config.port,
      ...(reloadEnabled ? ["--reload", ...reloadDirs.flatMap((dir) => ["--reload-dir", dir])] : []),
      ...passthroughArgs
    ],
    {
      cwd: repoRoot,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true
    }
  );
  writeLauncherFile(config);

  child.stdout?.on("data", (chunk) => safeWrite(process.stdout, chunk));
  child.stderr?.on("data", (chunk) => safeWrite(process.stderr, chunk));
  child.on("error", (error) => {
    console.error(`[axdata] API process failed to start: ${error.message}`);
    child = null;
    if (!stopping) {
      restarting = false;
      setTimeout(startApi, 1000);
    }
  });
  child.on("exit", (code, signal) => {
    child = null;
    if (!stopping) {
      if (!restarting) {
        console.warn(`[axdata] API process exited (${signal ?? code ?? "unknown"}). Restarting...`);
      }
      restarting = false;
      setTimeout(startApi, 500);
      return;
    }
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 0);
  });
}

function readRestartRequest() {
  if (!existsSync(restartRequestPath)) {
    return null;
  }
  try {
    const stat = statSync(restartRequestPath);
    if (stat.mtimeMs <= lastRestartRequestMtime) {
      return null;
    }
    const payload = JSON.parse(readFileSync(restartRequestPath, "utf8"));
    if (!payload || typeof payload !== "object") {
      return null;
    }
    const id = String(payload.id ?? "");
    if (!id || id === lastRestartRequestId) {
      lastRestartRequestMtime = stat.mtimeMs;
      return null;
    }
    lastRestartRequestId = id;
    lastRestartRequestMtime = stat.mtimeMs;
    return payload;
  } catch (error) {
    console.warn(`[axdata] Ignoring invalid restart request ${restartRequestPath}: ${error.message}`);
    return null;
  }
}

function requestRestart() {
  if (restarting || stopping) {
    return;
  }
  restarting = true;
  console.log("[axdata] Restart requested from Web. Restarting API...");
  try {
    unlinkSync(restartRequestPath);
  } catch {
    // best effort cleanup
  }
  if (!child) {
    restarting = false;
    startApi();
    return;
  }
  stopChildForRestart();
}

function stopChildForRestart() {
  if (!child) {
    restarting = false;
    startApi();
    return;
  }
  if (process.platform === "win32") {
    const childPid = child.pid;
    const killer = spawn("taskkill", ["/pid", String(childPid), "/t", "/f"], {
      stdio: "ignore",
      windowsHide: true
    });
    killer.on("exit", () => {
      if (child && restarting && !stopping) {
        console.warn("[axdata] Waiting for API process to exit after taskkill...");
      }
    });
    return;
  }
  child.kill("SIGTERM");
}

function pollRestartRequest() {
  const request = readRestartRequest();
  if (request) {
    requestRestart();
  }
}

mkdirSync(metadataDir, { recursive: true });
startApi();
setInterval(() => writeLauncherFile(currentLaunchConfig()), 5000);
setInterval(pollRestartRequest, 1000);

process.on("SIGINT", () => {
  stopping = true;
  if (child) {
    child.kill("SIGINT");
  } else {
    process.exit(0);
  }
});

process.on("SIGTERM", () => {
  stopping = true;
  if (child) {
    child.kill("SIGTERM");
  } else {
    process.exit(0);
  }
});
