# IAOffDev

Agente de IA **offline** com interface amigável para desenvolvimento de software.

O IAOffDev roda 100% na sua máquina: a interface fala com um backend local, que por sua vez usa [Ollama](https://ollama.com) para inferência — sem enviar código para a nuvem.

## O que faz

- Chat em português focado em desenvolvimento
- Ferramentas do agente: listar pastas, ler/escrever arquivos, buscar no código
- Painel de arquivos do workspace
- Streaming de respostas
- Modo demonstração local quando o Ollama estiver offline (ainda edita arquivos)

## Requisitos

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.com) (recomendado) + um modelo coder, por exemplo:

```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

## Início rápido

```bash
# Terminal 1 — API
chmod +x scripts/*.sh
./scripts/start-backend.sh

# Terminal 2 — Interface
./scripts/start-frontend.sh
```

Abra [http://127.0.0.1:5173](http://127.0.0.1:5173).

Variáveis úteis (prefixo `IAOFFDEV_`):

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL do Ollama |
| `DEFAULT_MODEL` | `qwen2.5-coder:7b` | Modelo padrão |
| `WORKSPACE_ROOT` | `~/projects` | Pasta que o agente pode acessar |
| `HOST` / `PORT` | `127.0.0.1` / `8765` | Bind da API |

## Docker

```bash
docker compose up --build
```

A UI fica em `:5173`, a API em `:8765`, o Ollama em `:11434`.

Depois baixe um modelo no container:

```bash
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

## Arquitetura

```
frontend (React + Vite)  →  backend (FastAPI)  →  Ollama (LLM local)
                                 ↓
                         ferramentas de filesystem
                         (workspace sandbox)
```

## API principal

- `GET /api/status` — saúde do Ollama e modelos
- `POST /api/chat` — chat com SSE (`token`, `tool_start`, `tool_result`, `done`, `error`)
- `GET /api/workspace` — raiz e listagem
- `POST /api/files/read` / `write` — leitura/escrita
- `POST /api/search` — busca no código

## Licença

MIT
