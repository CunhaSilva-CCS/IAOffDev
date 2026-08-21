import type { ChatMessage } from "../api";
import { Markdown } from "./Markdown";

function Avatar({ role }: { role: ChatMessage["role"] }) {
  if (role === "user") return <div className="avatar user">Você</div>;
  if (role === "tool") return <div className="avatar tool">Fx</div>;
  return <div className="avatar assistant">IA</div>;
}

export function MessageList({
  messages,
  streaming,
}: {
  messages: ChatMessage[];
  streaming: boolean;
}) {
  if (messages.length === 0) {
    return null;
  }

  return (
    <>
      {messages.map((message) => (
        <article key={message.id} className="message">
          <Avatar role={message.role} />
          <div className={`bubble ${message.role === "tool" ? "tool" : ""}`}>
            {message.role === "assistant" || message.role === "user" ? (
              message.content ? (
                <Markdown content={message.content} />
              ) : message.pending ? (
                <div className="typing" aria-label="Gerando resposta">
                  <span />
                  <span />
                  <span />
                </div>
              ) : null
            ) : (
              <>
                <strong>{message.toolName || "ferramenta"}</strong>
                {"\n"}
                {message.content}
              </>
            )}
          </div>
        </article>
      ))}
      {streaming && messages[messages.length - 1]?.role !== "assistant" && (
        <article className="message">
          <Avatar role="assistant" />
          <div className="bubble">
            <div className="typing" aria-label="Gerando resposta">
              <span />
              <span />
              <span />
            </div>
          </div>
        </article>
      )}
    </>
  );
}
