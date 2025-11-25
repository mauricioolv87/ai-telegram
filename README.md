AI Telegram Bot
================

Bot que transcreve áudios, extrai informações de gastos e registra transações no Organizze.

Resumo
------
- Transcrição de áudio via OpenAI Whisper/OpenAI API.
- Extração de dados (valor, descrição, data, categoria, forma de pagamento) via modelo.
- Registro automático no Organizze.
- Dois modos de operação:
	- polling — para desenvolvimento local (bot busca atualizações via getUpdates)
	- webhook — para produção (Telegram envia updates para um endpoint HTTPS)

Principais arquivos
-------------------
- `main.py` — aplicação FastAPI + gerencia ciclo de vida do bot (lifespan). Suporta polling e webhook.
- `src/config/settings.py` — carregamento de variáveis de ambiente e detecção automática de modo.
- `src/bot/handlers.py` — handlers do Telegram (áudio, start, etc.).
- `src/graph/*` — workflow (transcrição, extração, envio) e composição de mensagens.
- `setup_webhook.py` — utilitário para configurar o webhook via API do Telegram (pode ser usado localmente).

Requisitos
----------
- Python 3.11+

Gerenciamento de dependências
-----------------------------
Este projeto usa `pyproject.toml` + `uv.lock` para gerenciar dependências e reproduzir builds. A ferramenta usada aqui é o `uv` (ver `https://docs.astral.sh/uv/`), que é o padrão para instalar a partir do lockfile e executar comandos reprodutíveis.

Recomendado (usar `uv`)
```powershell

# instalar o utilitário 'uv' (se ainda não tiver)
python -m pip install uv

# criar novo projeto
uv init <nome-projeto>

# sincronizar dependências definidas em pyproject.toml/uv.lock
uv sync

# executar a aplicação via runner 'uv'
uv run main.py
```

Observações:
- `uv sync` instala dependências com base em `pyproject.toml` e `uv.lock`, garantindo versões reproduzíveis.
- `uv run` é o runner usado no repositório (equivalente a `uvicorn` para este projeto).

Fallback (pip)
```
# Se preferir usar pip diretamente ou não tiver `uv` disponível:
python -m pip install -U pip
# se existir requirements.txt
python -m pip install -r requirements.txt
# ou instale manualmente o mínimo necessário
python -m pip install fastapi python-telegram-bot python-dotenv httpx
```

Configuração (.env)
--------------------
Crie um arquivo `.env` na raiz com as variáveis:

```
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
ORGANIZZE_EMAIL=...
ORGANIZZE_TOKEN=...
# Opcional para deploy em produção (URL pública que o Telegram chamará)
WEBHOOK_URL=https://your-domain/path-or-base

# Controle de modo (opcional)
# BOT_MODE: 'auto' (default), 'polling' ou 'webhook'
BOT_MODE=auto
# RUN_ENV (influencia detecção automática). Use 'production' em deploy.
RUN_ENV=development

# Controla se o app tenta registrar webhook automaticamente no startup
AUTO_SET_WEBHOOK=1
```

Observações sobre `WEBHOOK_URL`:
- Se sua URL pública já inclui o caminho `/webhook`, você pode colocá-la completa em `WEBHOOK_URL`.
- A aplicação não acrescenta `/webhook` automaticamente ao registrar o webhook — use a URL exata desejada.

Modo de detecção (behavior)
---------------------------
- `BOT_MODE=auto` (padrão):
	- Se `RUN_ENV` != `development` e `WEBHOOK_URL` estiver configurado → usa `webhook`.
	- Caso contrário → usa `polling` (prático para desenvolvimento local).
- Você pode forçar `BOT_MODE=polling` ou `BOT_MODE=webhook` para comportamento explícito.

Execução
--------
- Desenvolvimento (polling) — inicia o bot em background e o servidor FastAPI:

```powershell
# ativa virtualenv
.\.venv\Scripts\Activate.ps1
python main.py
# ou com uvicorn
uvicorn main:app --reload
```

- Produção (webhook) — rode o app com `WEBHOOK_URL` configurado e `RUN_ENV=production`:

```powershell
set RUN_ENV=production
set WEBHOOK_URL=https://mydomain/path
set BOT_MODE=webhook
python main.py
```

Webhook automático
------------------
- Ao iniciar em `webhook` mode a aplicação tentará registrar o webhook automaticamente usando a variável `AUTO_SET_WEBHOOK` (padrão `1`).
- Se falhar (por exemplo URL não acessível no momento do startup), o erro será logado e você pode configurar manualmente:

```powershell
curl -X GET http://<app-host>/set-webhook
```

Endpoints úteis
---------------
- `POST /webhook` — endpoint que recebe updates do Telegram (só ativo em modo `webhook`).
- `GET /set-webhook` — registra o webhook via API do Telegram (só em modo `webhook`).
- `GET /webhook-info` — informações sobre o webhook atual (só em modo `webhook`).
- `DELETE /webhook` — remove o webhook remoto (só em modo `webhook`).
- `GET /health` — health check.

Desenvolvimento e testes
------------------------
- Para testar localmente prefira `polling` (modo padrão em dev). Basta iniciar o app e enviar mensagens/áudios para o bot via Telegram.
- Logs detalhados mostram chamadas ao OpenAI e ao Organizze para depuração.

Segurança
--------
- Nunca comite seu `.env` com tokens no repositório. Adicione `.env` ao `.gitignore`.
- Tokens e chaves aparecem em variáveis de ambiente e não devem ser expostas.

Ajuda e troubleshooting
----------------------
- Se `main.py` reclamar de dependências faltando, instale os pacotes listados acima.
- Se o webhook não for registrado automaticamente, verifique se `WEBHOOK_URL` é acessível publicamente por HTTPS.
- Para debug rápido, force `BOT_MODE=polling` localmente e verifique o fluxo de mensagens no terminal.

Contribuições
-------------
Pull requests bem-vindos. Para mudanças grandes abra uma issue primeiro descrevendo a proposta.

---
README atualizado para refletir a versão atual da aplicação.