# IAOffDev

Agente de IA **offline** para desenvolvimento de software — no Mac, instala e abre como um programa normal.

## App para Mac (recomendado)

No Mac, na pasta do projeto:

```bash
chmod +x scripts/*.sh
./scripts/install-mac.sh
```

Isso cria **IAOffDev.app** em `/Applications` (use `./scripts/install-mac.sh --user` para `~/Applications`).

Depois é só abrir pelo Launchpad / Spotlight — como qualquer app.

Para gerar um instalador `.dmg` (somente no Mac):

```bash
./scripts/build-mac-dmg.sh
```

Sem instalar no Applications, dá para testar a janela nativa com:

```bash
./scripts/start-app.sh
```

### Ollama (cérebro local)

O app funciona sem Ollama (modo demonstração). Para respostas inteligentes:

```bash
brew install ollama
ollama serve
ollama pull qwen2.5-coder:7b
```

Requisitos do instalador: **Python 3.11+** e **Node.js 20+** (só na hora de instalar/gerar o app).

## O que faz

- Chat em português focado em desenvolvimento
- Ferramentas do agente: listar pastas, ler/escrever arquivos, buscar no código
- Painel de arquivos do workspace
- Streaming de respostas
- Janela nativa no macOS (WebView)
- Modo demonstração local quando o Ollama estiver offline

## Desenvolvimento (web + API separados)

```bash
./scripts/start-backend.sh   # API em :8765
./scripts/start-frontend.sh  # UI em :5173
```

Variáveis úteis (prefixo `IAOFFDEV_`):

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL do Ollama |
| `DEFAULT_MODEL` | `qwen2.5-coder:7b` | Modelo padrão |
| `WORKSPACE_ROOT` | `~/Documents/IAOffDev` (app) ou `~/projects` | Pasta acessível ao agente |
| `HOST` / `PORT` | `127.0.0.1` / `8765` | Bind da API |

## Docker

```bash
docker compose up --build
```

A UI fica em `:5173`, a API em `:8765`, o Ollama em `:11434`.

```bash
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

## Arquitetura

```
IAOffDev.app (janela nativa)
   └─ launcher → FastAPI (API + UI estática) → Ollama
                      └─ ferramentas de arquivos (workspace)
```

## API principal

- `GET /api/status` — saúde do Ollama e modelos
- `POST /api/chat` — chat com SSE
- `GET /api/workspace` — raiz e listagem
- `POST /api/files/read` / `write` — leitura/escrita
- `POST /api/search` — busca no código

## Licença

MIT
