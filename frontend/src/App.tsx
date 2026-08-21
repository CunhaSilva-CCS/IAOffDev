import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchStatus,
  fetchWorkspace,
  modelLabel,
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
    title: "Consultar todas as IAs",
    detail: "Peça opinião coletiva das IAs offline.",
    prompt:
      "Compare abordagens para organizar um projeto Python + FastAPI com testes. Quero a melhor prática consolidada.",
  },
];

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [workspace, setWorkspace] = useState("");
  const [model, setModel] = useState("");
  const [council, setCouncil] = useState(true);
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
        const preferred = st.models[0]?.id || st.models[0]?.name || st.default_model;
        setModel(preferred);
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
          setModel((current) => current || st.models[0]?.id || st.models[0]?.name || st.default_model);
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
    () => Boolean(input.trim()) && !streaming && (online || council),
    [input, streaming, online, council]
  );

  async function sendPrompt(text: string) {
    const prompt = text.trim();
    if (!prompt || streaming) return;

    setError(null);
    const userMsg: ChatMessage = { id: uid(), role: "user", content: prompt };
    const assistantId = uid();
    setMessages([
      ...messages,
      userMsg,
      { id: assistantId, role: "assistant", content: "", pending: true },
    ]);
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
        use_tools: !council,
        council,
      })) {
        if (event.type === "token") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + (event.content || ""), pending: false }
                : m
            )
          );
        } else if (event.type === "council_start") {
          setMessages((prev) => [
            ...prev.filter((m) => m.id !== assistantId || m.content),
            {
              id: uid(),
              role: "tool",
              toolName: "council",
              content: `${event.content || "Consultando IAs…"}\n${(event.models || []).join("\n")}`,
            },
            { id: assistantId, role: "assistant", content: "", pending: true },
          ]);
        } else if (event.type === "council_result") {
          const preview = (event.content || "").slice(0, 900);
          setMessages((prev) => [
            ...prev,
            {
              id: uid(),
              role: "tool",
              toolName: event.name || "ia",
              content: `${event.ok === false ? "[falhou] " : ""}${event.provider || ""} · ${event.name}\n${preview}`,
            },
          ]);
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
                    content: m.content || `Erro: ${event.content}`,
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

  const onlineProviders = status?.providers?.filter((p) => p.online) || [];
  const offlineProviders = status?.providers?.filter((p) => !p.online) || [];

  return (
    <div className="app-shell">
      <aside className="panel left">
        <div className="brand-block">
          <div className="brand-mark">
            <div className="brand-orb" aria-hidden />
            <div className="brand-name">IAOffDev</div>
          </div>
          <p className="brand-tag">
            Agente offline que consulta todas as IAs locais de desenvolvimento na sua máquina.
          </p>
          <div className="status-chip" title={status?.message}>
            <span className={`status-dot ${online ? "online" : ""}`} />
            {online
              ? `${onlineProviders.length} IA(s) online · ${status?.models?.length || 0} modelo(s)`
              : "Nenhuma IA offline detectada"}
          </div>
        </div>

        <div className="sidebar-section">
          <label className="sidebar-label" htmlFor="council">
            Modo de consulta
          </label>
          <label className="toggle-row" htmlFor="council">
            <input
              id="council"
              type="checkbox"
              checked={council}
              onChange={(e) => setCouncil(e.target.checked)}
            />
            <span>Consultar todas as IAs offline</span>
          </label>
          <p className="hint">
            Liga Ollama, LM Studio, LocalAI, llama.cpp, Jan, GPT4All e sintetiza a melhor resposta.
          </p>
        </div>

        <div className="sidebar-section">
          <label className="sidebar-label" htmlFor="model">
            Modelo principal
          </label>
          <select
            id="model"
            className="select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={council}
          >
            {(status?.models?.length
              ? status.models
              : [{ name: status?.default_model || "qwen2.5-coder:7b", id: status?.default_model }]
            ).map((m) => {
              const value = m.id || m.name;
              return (
                <option key={value} value={value}>
                  {modelLabel(m)}
                </option>
              );
            })}
          </select>
          <p className="hint">
            {council
              ? "No modo coletivo o modelo principal só sintetiza o resultado."
              : status?.message || "Conectando…"}
          </p>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">Provedores locais</span>
          <div className="provider-list">
            {(status?.providers || []).map((p) => (
              <div key={p.id} className={`provider-row ${p.online ? "on" : "off"}`}>
                <span className={`status-dot ${p.online ? "online" : ""}`} />
                <div>
                  <strong>{p.name}</strong>
                  <small>
                    {p.online ? `${p.models.length} modelo(s)` : p.error || "offline"}
                  </small>
                </div>
              </div>
            ))}
            {!status?.providers?.length && (
              <p className="hint">Detectando Ollama, LM Studio, LocalAI…</p>
            )}
          </div>
          {offlineProviders.length > 0 && onlineProviders.length > 0 && (
            <p className="hint">{offlineProviders.length} provedor(es) ainda offline.</p>
          )}
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
      </aside>

      <main className="main">
        <header className="main-header">
          <div>
            <h1>Assistente de desenvolvimento</h1>
            <p>
              {council
                ? "Modo coletivo: pergunta em paralelo a todas as IAs offline e consolida a resposta."
                : "Modo único: usa o modelo selecionado com ferramentas de arquivos."}
            </p>
          </div>
          <button type="button" className="ghost-btn" onClick={clearChat} disabled={streaming}>
            Nova conversa
          </button>
        </header>

        <div className="chat-scroll" ref={scrollRef}>
          {messages.length === 0 && (
            <section className="welcome">
              <h2>Uma pergunta. Todas as IAs locais.</h2>
              <p>
                O IAOffDev descobre motores offline na sua máquina, consulta os modelos de
                desenvolvimento e entrega uma síntese prática — sem nuvem.
              </p>
              <div className="prompt-grid">
                {SUGGESTIONS.map((item) => (
                  <button
                    key={item.title}
                    type="button"
                    className="prompt-btn"
                    onClick={() => {
                      if (item.title.includes("todas")) setCouncil(true);
                      void sendPrompt(item.prompt);
                    }}
                    disabled={streaming || (!online && !item.title.includes("todas"))}
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
                online || council
                  ? council
                    ? "Pergunte e todas as IAs offline vão responder…"
                    : "Peça para criar uma função, explicar um arquivo, corrigir um bug…"
                  : "Inicie Ollama, LM Studio ou outra IA local"
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
              {streaming ? "Consultando…" : council ? "Consultar todas" : "Enviar"}
            </button>
          </div>
          <div className="composer-meta">
            <span>Enter envia · Shift+Enter nova linha</span>
            <span>{council ? "modo coletivo" : model || "sem modelo"}</span>
          </div>
        </form>
      </main>

      <aside className="panel right">
        {workspace ? <FileExplorer workspace={workspace} /> : <div className="empty-files">Sem workspace</div>}
      </aside>
    </div>
  );
}
