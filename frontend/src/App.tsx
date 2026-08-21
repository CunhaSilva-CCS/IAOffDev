import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchStatus,
  fetchWorkspace,
  streamChat,
  uid,
  type ChatMessage,
  type StatusResponse,
} from "./api";
import { FileExplorer } from "./components/FileExplorer";
import { MessageList } from "./components/MessageList";

const SUGGESTIONS = [
  {
    title: "Explorar o projeto",
    detail: "Liste a estrutura e resuma o que cada pasta faz.",
    prompt: "Liste a estrutura do workspace e resuma o propósito de cada arquivo principal.",
  },
  {
    title: "Criar um endpoint",
    detail: "Gere uma API FastAPI com teste básico.",
    prompt:
      "Crie um módulo FastAPI simples em demo-app/api.py com um endpoint GET /hello e um teste em demo-app/test_api.py.",
  },
  {
    title: "Explicar código",
    detail: "Leia main.py e explique em português.",
    prompt: "Leia o arquivo demo-app/main.py e explique o que ele faz, linha a linha de forma breve.",
  },
  {
    title: "Refatorar com testes",
    detail: "Melhore o código e adicione cobertura.",
    prompt:
      "Refatore demo-app/main.py para ficar mais idiomático e adicione testes unitários em demo-app/test_main.py.",
  },
];

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [workspace, setWorkspace] = useState("");
  const [model, setModel] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        const [st, ws] = await Promise.all([fetchStatus(), fetchWorkspace()]);
        if (cancelled) return;
        setStatus(st);
        setWorkspace(ws.path);
        setModel(st.models[0]?.name || st.default_model);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Backend indisponível. Inicie o servidor em :8765."
          );
        }
      }
    }
    void boot();
    const timer = window.setInterval(() => {
      void fetchStatus()
        .then((st) => {
          setStatus(st);
          setModel((current) => current || st.models[0]?.name || st.default_model);
        })
        .catch(() => undefined);
    }, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, streaming]);

  const online = Boolean(status?.online);
  const canSend = useMemo(
    () => Boolean(input.trim()) && !streaming && online && Boolean(model),
    [input, streaming, online, model]
  );

  async function sendPrompt(text: string) {
    const prompt = text.trim();
    if (!prompt || streaming) return;

    setError(null);
    const userMsg: ChatMessage = { id: uid(), role: "user", content: prompt };
    const assistantId = uid();
    const nextMessages = [
      ...messages,
      userMsg,
      { id: assistantId, role: "assistant" as const, content: "", pending: true },
    ];
    setMessages(nextMessages);
    setInput("");
    setStreaming(true);

    const history = [...messages, userMsg]
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      for await (const event of streamChat({
        messages: history,
        model,
        workspace,
        use_tools: true,
      })) {
        if (event.type === "token") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + (event.content || ""), pending: false }
                : m
            )
          );
        } else if (event.type === "tool_start") {
          setMessages((prev) => [
            ...prev.filter((m) => m.id !== assistantId || m.content),
            {
              id: uid(),
              role: "tool",
              toolName: event.name,
              content: `Executando ${event.name}(${JSON.stringify(event.arguments || {})})`,
            },
            { id: assistantId, role: "assistant", content: "", pending: true },
          ]);
        } else if (event.type === "tool_result") {
          setMessages((prev) => [
            ...prev,
            {
              id: uid(),
              role: "tool",
              toolName: event.name,
              content: event.content || "",
            },
          ]);
        } else if (event.type === "error") {
          setError(event.content || "Erro desconhecido");
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    pending: false,
                    content: m.content || `⚠️ ${event.content}`,
                  }
                : m
            )
          );
        } else if (event.type === "done") {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, pending: false } : m))
          );
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no chat");
    } finally {
      setStreaming(false);
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, pending: false } : m))
      );
      // refresh file tree indirectly by bumping workspace string reference? keep same
      setWorkspace((w) => w);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void sendPrompt(input);
  }

  function clearChat() {
    if (streaming) return;
    setMessages([]);
    setError(null);
  }

  return (
    <div className="app-shell">
      <aside className="panel left">
        <div className="brand-block">
          <div className="brand-mark">
            <div className="brand-orb" aria-hidden />
            <div className="brand-name">IAOffDev</div>
          </div>
          <p className="brand-tag">
            Agente de IA 100% local para criar, ler e evoluir código — sem nuvem.
          </p>
          <div className="status-chip" title={status?.message}>
            <span className={`status-dot ${online ? "online" : ""}`} />
            {online ? "Ollama online" : "Ollama offline"}
          </div>
        </div>

        <div className="sidebar-section">
          <label className="sidebar-label" htmlFor="model">
            Modelo local
          </label>
          <select
            id="model"
            className="select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            {(status?.models?.length ? status.models : [{ name: status?.default_model || "qwen2.5-coder:7b" }]).map(
              (m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              )
            )}
          </select>
          <p className="hint">{status?.message || "Conectando…"}</p>
        </div>

        <div className="sidebar-section">
          <label className="sidebar-label" htmlFor="workspace">
            Workspace
          </label>
          <input
            id="workspace"
            className="field"
            value={workspace}
            onChange={(e) => setWorkspace(e.target.value)}
            onBlur={() => {
              void fetchWorkspace(workspace)
                .then((ws) => setWorkspace(ws.path))
                .catch((err) => setError(err instanceof Error ? err.message : "Workspace inválido"));
            }}
            placeholder="/caminho/do/projeto"
          />
          <p className="hint">O agente só acessa arquivos dentro desta pasta.</p>
        </div>

        <div className="sidebar-section" style={{ borderBottom: "none", marginTop: "auto" }}>
          <p className="hint">
            Dica: instale um modelo coder com{" "}
            <code style={{ fontFamily: "var(--mono)" }}>ollama pull qwen2.5-coder:7b</code>
          </p>
        </div>
      </aside>

      <main className="main">
        <header className="main-header">
          <div>
            <h1>Assistente de desenvolvimento</h1>
            <p>Converse, explore o projeto e peça alterações de código — tudo offline.</p>
          </div>
          <button type="button" className="ghost-btn" onClick={clearChat} disabled={streaming}>
            Nova conversa
          </button>
        </header>

        <div className="chat-scroll" ref={scrollRef}>
          {messages.length === 0 && (
            <section className="welcome">
              <h2>Desenvolva com um copiloto local.</h2>
              <p>
                O IAOffDev usa Ollama na sua máquina para ler, buscar e editar arquivos do
                workspace com uma interface simples e focada.
              </p>
              <div className="prompt-grid">
                {SUGGESTIONS.map((item) => (
                  <button
                    key={item.title}
                    type="button"
                    className="prompt-btn"
                    onClick={() => void sendPrompt(item.prompt)}
                    disabled={!online || streaming}
                  >
                    <strong>{item.title}</strong>
                    <span>{item.detail}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          <MessageList messages={messages} streaming={streaming} />
          {error && (
            <div className="message">
              <div className="avatar tool">!</div>
              <div className="bubble tool">{error}</div>
            </div>
          )}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <div className="composer-row">
            <textarea
              className="textarea"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                online
                  ? "Peça para criar uma função, explicar um arquivo, corrigir um bug…"
                  : "Inicie o Ollama para conversar com o agente"
              }
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (canSend) void sendPrompt(input);
                }
              }}
              disabled={streaming}
            />
            <button type="submit" className="primary-btn" disabled={!canSend}>
              {streaming ? "Pensando…" : "Enviar"}
            </button>
          </div>
          <div className="composer-meta">
            <span>Enter envia · Shift+Enter nova linha</span>
            <span>{model || "sem modelo"}</span>
          </div>
        </form>
      </main>

      <aside className="panel right">
        {workspace ? <FileExplorer workspace={workspace} /> : <div className="empty-files">Sem workspace</div>}
      </aside>
    </div>
  );
}
