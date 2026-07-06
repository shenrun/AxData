const API_PORT_STORAGE_KEY = "axdata.localApiPort";
const RUNTIME_DRAFT_STORAGE_KEY = "axdata.runtimeDraft";

export type LocalRuntimeDraft = {
  api_host?: string;
  api_port?: number;
  web_port?: number;
};

function readLocalApiPort() {
  if (typeof window === "undefined") {
    return "8666";
  }
  const value = window.localStorage.getItem(API_PORT_STORAGE_KEY);
  return value && /^\d{1,5}$/.test(value) ? value : "8666";
}

export function saveLocalApiPort(port: number) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(API_PORT_STORAGE_KEY, String(port));
}

export function readLocalRuntimeDraft(): LocalRuntimeDraft {
  if (typeof window === "undefined") {
    return {};
  }
  try {
    const value = window.localStorage.getItem(RUNTIME_DRAFT_STORAGE_KEY);
    if (!value) {
      return {};
    }
    const draft = JSON.parse(value) as LocalRuntimeDraft;
    return {
      api_host: draft.api_host === "0.0.0.0" ? "0.0.0.0" : draft.api_host === "127.0.0.1" ? "127.0.0.1" : undefined,
      api_port: normalizePort(draft.api_port),
      web_port: normalizePort(draft.web_port)
    };
  } catch {
    return {};
  }
}

export function saveLocalRuntimeDraft(draft: LocalRuntimeDraft) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(RUNTIME_DRAFT_STORAGE_KEY, JSON.stringify(draft));
}

function normalizePort(value: unknown) {
  const port = Number(value);
  return Number.isInteger(port) && port >= 1 && port <= 65535 ? port : undefined;
}

export const DEFAULT_API_BASE = `http://127.0.0.1:${readLocalApiPort()}`;
