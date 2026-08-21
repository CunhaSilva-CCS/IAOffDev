# Manual do Usuário — IAOffDev

**Versão do produto:** 1.1  
**Idioma:** Português (Brasil)  
**Público:** desenvolvedores que querem um agente de IA **100% local** (offline) para criar, ler e evoluir código.

---

## Sumário

1. [O que é o IAOffDev](#1-o-que-é-o-iaoffdev)
2. [Requisitos](#2-requisitos)
3. [Instalação no Mac (como programa)](#3-instalação-no-mac-como-programa)
4. [Primeira abertura](#4-primeira-abertura)
5. [Visão geral da interface](#5-visão-geral-da-interface)
6. [Como conectar o agente aos modelos](#6-como-conectar-o-agente-aos-modelos)
7. [Modos de consulta](#7-modos-de-consulta)
8. [Workspace e arquivos](#8-workspace-e-arquivos)
9. [Fluxos de uso no dia a dia](#9-fluxos-de-uso-no-dia-a-dia)
10. [Configurações avançadas](#10-configurações-avançadas)
11. [Execução em modo desenvolvimento](#11-execução-em-modo-desenvolvimento)
12. [Solução de problemas](#12-solução-de-problemas)
13. [Perguntas frequentes](#13-perguntas-frequentes)
14. [Glossário](#14-glossário)

---

## 1. O que é o IAOffDev

O **IAOffDev** é um agente de IA para desenvolvimento de software que roda **na sua máquina**. Ele:

- conversa em português sobre código;
- lê, busca e edita arquivos de um **workspace** (pasta do projeto);
- descobre automaticamente IAs offline instaladas (Ollama, LM Studio, LocalAI, etc.);
- pode **consultar várias IAs ao mesmo tempo** e sintetizar uma resposta final;
- **não envia** seu código para a nuvem.

Sem nenhum modelo online, o app ainda abre em **modo demonstração** (ferramentas de arquivo locais), mas as respostas inteligentes só aparecem depois que você conectar pelo menos um motor/modelo local.

---

## 2. Requisitos

### Para instalar o app no Mac

| Item | Versão sugerida | Observação |
|------|-----------------|------------|
| macOS | 12+ | Testado com Ventura/Sonoma/Sequoia |
| Python | 3.11+ | `brew install python` |
| Node.js | 20+ | `brew install node` (só na instalação) |

### Para respostas inteligentes (cérebro local)

Instale **pelo menos um** destes motores:

- [Ollama](https://ollama.com) (mais simples para começar)
- [LM Studio](https://lmstudio.ai)
- LocalAI, llama.cpp server, Jan, GPT4All, Oobabooga, TabbyAPI

### Hardware sugerido

| Uso | RAM | Disco |
|-----|-----|-------|
| Modelo 3B–7B | 8–16 GB | 5–10 GB por modelo |
| Modelo 14B+ | 24 GB+ | 10–20 GB+ |

---

## 3. Instalação no Mac (como programa)

### 3.1 Baixar o projeto

```bash
git clone https://github.com/CunhaSilva-CCS/IAOffDev.git
cd IAOffDev
```

Se você já tem o repositório:

```bash
cd IAOffDev
git pull
```

### 3.2 Instalar no Applications

```bash
chmod +x scripts/*.sh
./scripts/install-mac.sh
```

- Instala em `/Applications/IAOffDev.app`
- Só para o seu usuário: `./scripts/install-mac.sh --user` → `~/Applications`

### 3.3 Abrir o app

- Spotlight (`Cmd + Espaço`) → digite **IAOffDev**
- ou Launchpad
- ou Terminal: `open -a IAOffDev`

### 3.4 Se o macOS bloquear

O app ainda não é assinado pela Apple. Na primeira vez:

1. Clique com o **botão direito** no ícone → **Abrir**
2. Confirme **Abrir** no aviso de segurança

### 3.5 Gerar DMG (opcional)

No Mac:

```bash
./scripts/build-mac-dmg.sh
```

O arquivo fica em `dist/mac/IAOffDev-1.0.0.dmg`.

### 3.6 Sem instalar (teste rápido)

```bash
./scripts/start-app.sh
```

Abre a janela nativa usando o código da pasta do projeto.

---

## 4. Primeira abertura

1. O app sobe um servidor local (API + interface).
2. Na **primeira execução**, pode demorar alguns minutos enquanto cria o ambiente Python.
3. Workspace padrão: `~/Documents/IAOffDev`
4. Logs: `~/Library/Logs/IAOffDev.log`

Na barra lateral esquerda você verá:

- status das IAs (**online / offline**);
- lista de provedores (Ollama, LM Studio, …);
- toggle **Consultar todas as IAs offline**;
- seletor de **modelo principal**;
- campo **Workspace**.

Se nenhum provedor estiver online, o status dirá algo como:

> Nenhuma IA offline detectada…

Siga a [seção 6](#6-como-conectar-o-agente-aos-modelos) para conectar os modelos.

---

## 5. Visão geral da interface

```
┌──────────────┬────────────────────────────┬─────────────────┐
│  Marca       │  Chat / boas             │  Arquivos       │
│  Status IAs  │                            │  do workspace   │
│  Modo        │  Mensagens do agente       │                 │
│  Modelo      │  Resultados das IAs        │  Pré-visualização│
│  Provedores  │                            │                 │
│  Workspace   │  Caixa de pergunta         │                 │
└──────────────┴────────────────────────────┴─────────────────┘
```

| Área | Função |
|------|--------|
| **Esquerda** | Configuração: modo, modelo, provedores, pasta do projeto |
| **Centro** | Conversa com o agente |
| **Direita** | Navegador de arquivos do workspace |

### Atalhos

| Ação | Como |
|------|------|
| Enviar mensagem | `Enter` |
| Nova linha | `Shift + Enter` |
| Nova conversa | botão **Nova conversa** |

---

## 6. Como conectar o agente aos modelos

O IAOffDev **não baixa modelos sozinho**. Ele se conecta a motores que já estão rodando na sua máquina e lista os modelos que cada um expõe.

### 6.1 Ideia geral (checklist)

1. Instale um motor (ex.: Ollama).
2. Baixe/carregue um **modelo coder**.
3. Deixe o servidor do motor **ligado**.
4. Abra (ou recarregue) o IAOffDev.
5. Confira na sidebar se o provedor ficou **verde/online**.
6. Escolha o modelo **ou** use o modo **Consultar todas**.

O app consulta estas portas locais:

| Provedor | URL padrão | Tipo de API |
|----------|------------|-------------|
| Ollama | `http://127.0.0.1:11434` | API Ollama |
| LM Studio | `http://127.0.0.1:1234/v1` | OpenAI-compatível |
| LocalAI | `http://127.0.0.1:8080/v1` | OpenAI-compatível |
| llama.cpp | `http://127.0.0.1:8081/v1` | OpenAI-compatível |
| Jan | `http://127.0.0.1:1337/v1` | OpenAI-compatível |
| GPT4All | `http://127.0.0.1:4891/v1` | OpenAI-compatível |
| Oobabooga | `http://127.0.0.1:5000/v1` | OpenAI-compatível |
| TabbyAPI | `http://127.0.0.1:5001/v1` | OpenAI-compatível |

---

### 6.2 Conectar com **Ollama** (recomendado para começar)

#### Passo 1 — Instalar

```bash
brew install ollama
```

Ou baixe em [https://ollama.com](https://ollama.com).

#### Passo 2 — Iniciar o serviço

```bash
ollama serve
```

(No Mac, o app Ollama costuma manter o serviço ativo sozinho após a instalação.)

#### Passo 3 — Baixar um modelo para desenvolvimento

Sugestões:

```bash
# Bom equilíbrio qualidade/velocidade
ollama pull qwen2.5-coder:7b

# Alternativas
ollama pull deepseek-coder-v2:16b
ollama pull codellama:7b
ollama pull qwen2.5-coder:3b   # mais leve
```

Verifique:

```bash
ollama list
```

#### Passo 4 — Confirmar no IAOffDev

1. Abra o IAOffDev.
2. Na lista **Provedores locais**, **Ollama** deve aparecer online.
3. Em **Modelo principal**, selecione por exemplo `ollama · qwen2.5-coder:7b`.
4. Envie: `Liste a estrutura do workspace`.

Se Ollama estiver online mas a lista de modelos vazia, o modelo ainda não foi baixado (`ollama pull …`).

---

### 6.3 Conectar com **LM Studio**

1. Instale o [LM Studio](https://lmstudio.ai).
2. Baixe um modelo (ex.: Qwen2.5-Coder, DeepSeek Coder).
3. Vá em **Local Server** / **Developer**.
4. Clique em **Start Server**.
5. Confirme a porta **1234** (padrão do IAOffDev: `http://127.0.0.1:1234/v1`).
6. Carregue o modelo na UI do LM Studio.
7. Abra o IAOffDev — o provedor **LM Studio** deve ficar online.

Dica: no LM Studio, ative a API no estilo OpenAI (“OpenAI-compatible”).

---

### 6.4 Conectar com **LocalAI**

```bash
# Exemplo com Docker
docker run -d -p 8080:8080 localai/localai:latest
```

O IAOffDev espera: `http://127.0.0.1:8080/v1`.

Baixe/configure um modelo coder conforme a documentação do LocalAI e recarregue o app.

---

### 6.5 Conectar com **llama.cpp** (server)

Suba o servidor com API OpenAI, por exemplo na porta **8081**:

```bash
./llama-server -m ./meu-modelo.gguf --port 8081 --host 127.0.0.1
```

O endpoint esperado é `http://127.0.0.1:8081/v1`.

Se você usar outra porta, veja [provedores extras](#106-provedor-extra-qualquer-api-openai-local).

---

### 6.6 Conectar com **Jan**

1. Instale o [Jan](https://jan.ai).
2. Baixe/carregue um modelo.
3. Ative o **Local API Server** (porta padrão **1337**).
4. No IAOffDev, o provedor **Jan** deve aparecer online.

---

### 6.7 Conectar com **GPT4All**

1. Instale o GPT4All.
2. Ative o servidor de API local (porta padrão **4891**).
3. Carregue um modelo.
4. Recarregue o IAOffDev.

---

### 6.8 Conectar com **Oobabooga** (text-generation-webui)

1. Inicie a WebUI com API OpenAI habilitada.
2. Porta padrão usada pelo IAOffDev: **5000** → `http://127.0.0.1:5000/v1`.
3. Carregue um modelo e confirme no app.

---

### 6.9 Conectar com **TabbyAPI**

1. Suba o TabbyAPI na porta **5001**.
2. Endpoint: `http://127.0.0.1:5001/v1`.
3. O provedor **TabbyAPI** deve listar os modelos carregados.

---

### 6.10 Provedor extra (qualquer API OpenAI local)

Se seu motor usa outra porta/URL, defina antes de abrir o app:

```bash
export IAOFFDEV_EXTRA_PROVIDERS='[
  {
    "id": "meu-llm",
    "name": "Meu LLM",
    "kind": "openai_compat",
    "base_url": "http://127.0.0.1:9999/v1"
  }
]'
```

No app Mac, você pode colocar isso no ambiente de lançamento ou iniciar via Terminal:

```bash
export IAOFFDEV_EXTRA_PROVIDERS='[{"id":"meu-llm","name":"Meu LLM","kind":"openai_compat","base_url":"http://127.0.0.1:9999/v1"}]'
open -a IAOffDev
```

O campo `kind` deve ser:

- `openai_compat` — para APIs estilo OpenAI (`/v1/models`, `/v1/chat/completions`)
- `ollama` — apenas se for outra instância Ollama

---

### 6.11 Como saber se a conexão funcionou

Checklist rápido:

| Sinal | Significado |
|-------|-------------|
| Bolinha verde no provedor | Motor respondendo |
| Modelos no seletor | Modelos descobertos |
| Status “X provedor(es) online” | Pronto para chat |
| Resposta em modo demo pedindo `ollama pull` | Ainda sem IA online |

Teste manual da API (opcional):

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
curl -s http://127.0.0.1:8765/api/providers | python3 -m json.tool
```

---

### 6.12 Modelos recomendados para desenvolvimento

| Objetivo | Modelo sugerido | Via |
|----------|-----------------|-----|
| Uso geral em notebook | `qwen2.5-coder:7b` | Ollama |
| Máquina fraca | `qwen2.5-coder:3b` | Ollama |
| Mais qualidade | `deepseek-coder-v2` / 14B+ | Ollama ou LM Studio |
| Refatoração / explicação | qualquer *coder* 7B+ | qualquer provedor |

Nomes com `coder`, `code`, `deepseek`, `starcoder`, `codellama`, `codestral` etc. são priorizados no modo coletivo.

---

## 7. Modos de consulta

### 7.1 Consultar todas as IAs offline (modo coletivo)

**Ligado por padrão.**

1. Ative **Consultar todas as IAs offline** na sidebar.
2. Digite a pergunta.
3. O agente:
   - escolhe até N modelos online (priorizando coder e diversidade de provedores);
   - pergunta a todos em paralelo;
   - mostra cada resposta parcial;
   - gera uma **síntese final**.

Use quando quiser comparar abordagens ou obter uma resposta mais robusta.

### 7.2 Modelo único

1. Desligue o toggle coletivo.
2. Escolha o **Modelo principal**.
3. Envie a pergunta.

Neste modo o agente (especialmente via Ollama) pode usar **ferramentas** de arquivo: listar pastas, ler, escrever e buscar código.

---

## 8. Workspace e arquivos

### O que é o workspace

É a **única pasta** que o agente pode ler/escrever. Por padrão:

- App Mac: `~/Documents/IAOffDev`
- Scripts de desenvolvimento: `~/projects` (ou o que você configurar)

### Como mudar

1. No campo **Workspace**, digite o caminho absoluto do seu projeto, por exemplo:

   ```text
   /Users/seu-nome/Developer/meu-app
   ```

2. Saia do campo (Tab/`Enter` fora) para o app validar a pasta.
3. O painel da direita atualiza a árvore de arquivos.

### Segurança

- O agente **não** acessa arquivos fora do workspace.
- Evite apontar para a raiz do disco (`/` ou `/Users`).
- Prefira a pasta do repositório Git do projeto.

### Painel de arquivos

- Clique em pastas para navegar.
- Clique em arquivos de texto para pré-visualizar.
- Use **Subir** / **Raiz** para voltar.

---

## 9. Fluxos de uso no dia a dia

### 9.1 Entender um projeto novo

1. Aponte o workspace para o repositório.
2. Ative o modo coletivo (opcional).
3. Pergunte:

> Liste a estrutura do workspace e resuma o propósito de cada arquivo principal.

### 9.2 Criar código

> Crie `src/api/hello.py` com um endpoint FastAPI GET /hello e um teste correspondente.

No modo único + Ollama, o agente pode gravar o arquivo com a ferramenta `write_file`.

### 9.3 Explicar um arquivo

> Leia `demo-app/main.py` e explique o que ele faz.

### 9.4 Comparar soluções com várias IAs

1. Ligue **Consultar todas as IAs offline**.
2. Garanta que Ollama e/ou LM Studio estejam online.
3. Pergunte:

> Qual a melhor forma de organizar autenticação JWT em FastAPI? Quero uma recomendação consolidada.

---

## 10. Configurações avançadas

Todas usam o prefixo `IAOFFDEV_`.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL do Ollama |
| `DEFAULT_MODEL` | `qwen2.5-coder:7b` | Modelo padrão |
| `WORKSPACE_ROOT` | `~/Documents/IAOffDev` (app) | Pasta inicial |
| `HOST` / `PORT` | `127.0.0.1` / `8765` | Endereço da API |
| `COUNCIL_MAX_MODELS` | `6` | Máximo de modelos no modo coletivo |
| `COUNCIL_TIMEOUT_SECONDS` | `90` | Timeout por modelo no coletivo |
| `EXTRA_PROVIDERS` | `[]` | JSON de provedores extras |
| `STATIC_DIR` | auto | Pasta da UI estática |
| `DEBUG` | vazio | Debug do webview (`1` para ligar) |

Exemplo:

```bash
export IAOFFDEV_WORKSPACE_ROOT="$HOME/Developer"
export IAOFFDEV_COUNCIL_MAX_MODELS=4
export IAOFFDEV_OLLAMA_BASE_URL="http://127.0.0.1:11434"
./scripts/start-app.sh
```

---

## 11. Execução em modo desenvolvimento

Para contribuir ou depurar sem o `.app`:

```bash
# Terminal 1 — API
./scripts/start-backend.sh

# Terminal 2 — Interface Vite
./scripts/start-frontend.sh
```

Abra [http://127.0.0.1:5173](http://127.0.0.1:5173).

### Docker

```bash
docker compose up --build
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

- UI: `:5173`
- API: `:8765`
- Ollama: `:11434`

---

## 12. Solução de problemas

### O provedor aparece offline

1. Confirme que o motor está rodando (`ollama serve`, LM Studio Server, etc.).
2. Teste no navegador/curl a URL da tabela da seção 6.
3. Desative VPN/firewall local temporariamente.
4. Recarregue o IAOffDev (feche e abra).

### Ollama online, mas sem modelos

```bash
ollama pull qwen2.5-coder:7b
ollama list
```

### App Mac não abre / trava na primeira vez

- Veja `~/Library/Logs/IAOffDev.log`
- Confirme Python 3: `python3 --version`
- Reinstale: `./scripts/install-mac.sh`

### macOS diz que o app é de desenvolvedor não identificado

Botão direito → **Abrir** (seção 3.4).

### Respostas vazias ou muito lentas

- Use modelo menor (3B/7B).
- Reduza `IAOFFDEV_COUNCIL_MAX_MODELS`.
- No modo coletivo, feche outros apps pesados de GPU/RAM.

### O agente não edita arquivos

- No modo coletivo as tools de arquivo ficam limitadas (consulta + síntese).
- Desligue o toggle coletivo e use um modelo Ollama para edição com ferramentas.

### Porta 8765 ocupada

O launcher tenta outra porta livre automaticamente. Se iniciar só a API:

```bash
export IAOFFDEV_PORT=8766
./scripts/start-backend.sh
```

---

## 13. Perguntas frequentes

**O IAOffDev usa ChatGPT/Claude na nuvem?**  
Não. Só motores locais. Sem provedor online, entra em modo demonstração.

**Preciso de internet?**  
Só para baixar o app/modelos na instalação. O uso diário pode ser offline.

**Posso usar vários motores juntos?**  
Sim. Deixe-os rodando e ative **Consultar todas as IAs offline**.

**Meus arquivos saem do computador?**  
Não. Ficam no workspace local. As IAs consultadas também são locais.

**Qual modelo escolher?**  
Comece com `qwen2.5-coder:7b` no Ollama.

**Funciona no Windows/Linux?**  
A API e a interface web sim (`scripts/start-*.sh`). O instalador `.app` é específico de Mac.

---

## 14. Glossário

| Termo | Significado |
|-------|-------------|
| **Provedor** | Programa que serve modelos (Ollama, LM Studio…) |
| **Modelo** | Rede neural baixada (ex.: qwen2.5-coder:7b) |
| **Workspace** | Pasta permitida para o agente |
| **Modo coletivo / council** | Consulta várias IAs e sintetiza |
| **OpenAI-compatível** | API no formato `/v1/chat/completions` |
| **Tool** | Ferramenta do agente (ler/escrever/buscar arquivo) |

---

## Apoio rápido

| Recurso | Onde |
|---------|------|
| README do projeto | `README.md` |
| Guia curto Mac | `desktop/MAC.md` |
| Este manual | `docs/MANUAL_DO_USUARIO.md` |
| Logs (Mac) | `~/Library/Logs/IAOffDev.log` |
| Status da API | `GET http://127.0.0.1:8765/api/status` |
| Lista de provedores | `GET http://127.0.0.1:8765/api/providers` |

---

*IAOffDev — agente offline para desenvolvimento de software.*
