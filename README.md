# IAOffDev

Agente de IA **offline** para desenvolvimento de software — no Mac, instala e abre como um programa normal.

> **Manual completo:** [docs/MANUAL_DO_USUARIO.md](docs/MANUAL_DO_USUARIO.md)  
> Inclui instalação, interface e **como conectar o agente aos modelos** (Ollama, LM Studio, LocalAI, etc.).

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

## IAs offline suportadas

O agente descobre automaticamente motores locais e, no modo **Consultar todas as IAs offline**, pergunta em paralelo e sintetiza a resposta:

| Provedor | Endpoint padrão |
|----------|-----------------|
| Ollama | `http://127.0.0.1:11434` |
| LM Studio | `http://127.0.0.1:1234/v1` |
| LocalAI | `http://127.0.0.1:8080/v1` |
| llama.cpp | `http://127.0.0.1:8081/v1` |
| Jan | `http://127.0.0.1:1337/v1` |
| GPT4All | `http://127.0.0.1:4891/v1` |
| Oobabooga | `http://127.0.0.1:5000/v1` |
| TabbyAPI | `http://127.0.0.1:5001/v1` |

Provedores extras via env:

```bash
export IAOFFDEV_EXTRA_PROVIDERS='[{"id":"meu","name":"Meu LLM","kind":"openai_compat","base_url":"http://127.0.0.1:9999/v1"}]'
```

## O que faz

- Chat em português focado em desenvolvimento
- **Consulta coletiva** a todas as IAs offline detectadas
- Ferramentas do agente: listar pastas, ler/escrever arquivos, buscar no código
- Painel de arquivos do workspace
- Streaming de respostas
- Janela nativa no macOS (WebView)
- Modo demonstração local quando nenhuma IA estiver online

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
