# Telegram bot with Ollama and OpenAI

A Python Telegram bot that lets each user switch between a local Ollama model and the OpenAI API. Provider choices are saved in a local SQLite file; conversations are not stored.

## Install on Windows

1. Install [Ollama for Windows](https://ollama.com/download/windows) with the official installer. Open a new PowerShell window afterward so that `ollama` is on your PATH. The local API normally listens on `http://localhost:11434`.
2. Download the model:

   ```powershell
   ollama pull qwen3:4b-instruct
   ```

   The model is about 2.5 GB and is stored in your Ollama model directory. Check it with `ollama list`.
3. Install Python 3.10 or newer, clone the repository, and install Python dependencies:

   ```powershell
   git clone https://github.com/attomaton/ollama-telegram-bot.git
   cd ollama-telegram-bot
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN` to your BotFather token:

   ```powershell
   Copy-Item .env.example .env
   ```

   To start with Ollama, keep `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:4b-instruct`, and `OLLAMA_BASE_URL=http://localhost:11434/v1`. To enable OpenAI in the Telegram menu, replace `OPENAI_API_KEY` and `OPENAI_MODEL` with your own key and a model available to your account. The example file contains placeholders only.

5. Start the bot:

   ```powershell
   .\.venv\Scripts\python.exe bot.py
   ```

   Alternatively, double-click `start-bot.cmd` and keep its window open. In Telegram, send `/start` or `/provider` and select **Ollama** or **OpenAI**. The choice applies to your next message and persists across restarts in `data/providers.sqlite3`. Each user has a separate choice. `LLM_PROVIDER` sets the default for users who have not selected one. Restart the bot after editing `.env`.

The machine running the bot must remain on. GitHub hosts the source code, not the bot process. Telegram requires an internet connection; Ollama generates replies locally. Selecting OpenAI sends prompts to the OpenAI API and may incur charges.

## Command-line use

Test the OpenAI-compatible Ollama API with the Python client:

```powershell
.\.venv\Scripts\python.exe ask.py "What is 2 + 2?"
```

The bot and `ask.py` share `llm.py`, which uses the OpenAI Python SDK with `base_url=http://localhost:11434/v1` for Ollama. The SDK requires an API key field; the local server ignores the value `ollama`.

`ollama.ps1` and `start-chat.cmd` provide a console chat. The script uses an optional `.runtime\ollama\ollama.exe` when present; otherwise it uses Ollama installed on PATH or in the standard Windows installation location. In the portable case, models live in this project's `models` directory. With a system installation, Ollama uses its normal model directory. If PowerShell blocks scripts, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\ollama.ps1 list`.

To limit who can use the Telegram bot, set `TELEGRAM_ALLOWED_USER_IDS` to comma-separated numeric IDs. An empty value allows anyone who can message the bot. `.env`, local models, logs, and the SQLite database are excluded from Git.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

References: [Ollama for Windows](https://docs.ollama.com/windows), [Qwen3 4B Instruct](https://ollama.com/library/qwen3:4b-instruct), [Ollama OpenAI-compatible API](https://docs.ollama.com/api/openai-compatibility).
