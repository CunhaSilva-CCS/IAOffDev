export type Role = "user" | "assistant" | "system" | "tool";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  toolName?: string;
  pending?: boolean;
}

export interface ModelInfo {
  name: string;
  size?: number | null;
  modified_at?: string | null;
}

export interface StatusResponse {
  online: boolean;
  ollama_url: string;
  models: ModelInfo[];
  default_model: string;
  message: string;
}

export interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number | null;
}

export interface AgentEvent {
  type: "token" | "tool_start" | "tool_result" | "assistant_partial" | "done" | "error";
  content?: string;
  name?: string;
  arguments?: Record<string, unknown>;
  model?: string;
  workspace?: string;
  tool_calls?: unknown[];
}

const API_BASE = "";

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/api/status`);
  if (!res.ok) throw new Error("Falha ao consultar status");
  return res.json();
}

export async function fetchWorkspace(path?: string): Promise<{ path: string; entries: FileEntry[] }> {
  const qs = path ? `?path=${encodeURIComponent(path)}` : "";
  const res = await fetch(`${API_BASE}/api/workspace${qs}`);
  if (!res.ok) throw new Error("Falha ao carregar workspace");
  return res.json();
}

export async function fetchTree(workspace: string, relative = "."): Promise<FileEntry[]> {
  const qs = new URLSearchParams({ path: workspace, relative });
  const res = await fetch(`${API_BASE}/api/workspace/tree?${qs}`);
  if (!res.ok) throw new Error("Falha ao listar diretório");
  return res.json();
}

export async function readFile(workspace: string, path: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/files/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace, path }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Falha ao ler arquivo");
  }
  const data = await res.json();
  return data.content as string;
}

export async function* streamChat(payload: {
  messages: { role: string; content: string }[];
  model?: string;
  workspace?: string;
  use_tools?: boolean;
}): AsyncGenerator<AgentEvent> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, stream: true }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Falha ao iniciar chat");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const json = line.slice(5).trim();
      if (!json) continue;
      try {
        yield JSON.parse(json) as AgentEvent;
      } catch {
        // ignore malformed chunk
      }
    }
  }
}

export function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function formatBytes(size?: number | null): string {
  if (size == null) return "";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
