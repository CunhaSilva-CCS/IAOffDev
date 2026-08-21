# Guia rápido — Mac

1. Instale dependências de build (uma vez):
   - Python 3.11+ (`brew install python`)
   - Node.js 20+ (`brew install node`)
2. Na pasta do projeto:
   ```bash
   chmod +x scripts/*.sh
   ./scripts/install-mac.sh
   ```
3. Abra **IAOffDev** pelo Launchpad.
4. (Opcional) IA local:
   ```bash
   brew install ollama
   ollama serve
   ollama pull qwen2.5-coder:7b
   ```

Se o macOS bloquear o app (não assinado): clique com o botão direito → **Abrir**.

Workspace padrão: `~/Documents/IAOffDev`
Logs: `~/Library/Logs/IAOffDev.log`
