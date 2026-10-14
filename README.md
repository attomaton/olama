# Локальная Ollama

## Python-клиент и Telegram-бот

Для запуска двойным щелчком используйте `start-bot.cmd` и оставьте окно открытым. В Telegram отправьте `/provider` (или `/start`) и нажмите **OpenAI** или **Ollama**. Переключение действует со следующего вопроса и сохраняется для вашего Telegram ID после перезапуска в `data/providers.sqlite3`. База содержит только выбор провайдера. `.env` при переключении не изменяется; `LLM_PROVIDER` задаёт начальный выбор для новых пользователей. Имена моделей и ключ OpenAI берутся из `.env`. После изменения этих настроек перезапустите бота. Для выбора OpenAI должны быть заполнены `OPENAI_API_KEY` и `OPENAI_MODEL`.

Проверенное оборудование: около 16 ГБ ОЗУ, NVIDIA RTX 2050 (4 ГБ VRAM). Установлена Qwen3 4B Instruct; Ollama распределяет модель между GPU и CPU.

Окружение `.venv` и зависимости уже установлены. Для установки на другом компьютере с Python 3.10+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Создайте `.env` копированием `.env.example`, если файла ещё нет. Для локальной модели оставьте `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://localhost:11434/v1` и `OLLAMA_MODEL=qwen3:4b-instruct`. Ключ OpenAI в этом режиме не используется. Все секреты в `.env.example` — заглушки; `.env` исключён из Git.

Запустите Ollama и проверьте Python-клиент:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ollama.ps1 list
.\.venv\Scripts\python.exe ask.py "Сколько будет 2 + 2?"
```

`ask.py` и `bot.py` используют общий `llm.py`: `AsyncOpenAI(base_url=..., api_key=...)` и `chat.completions.create`. Для локального сервера используется техническое значение `api_key="ollama"`, а не секрет.

Для Telegram заполните `TELEGRAM_BOT_TOKEN` в локальном `.env` токеном своего бота от BotFather, затем выполните:

```powershell
.\.venv\Scripts\python.exe bot.py
```

Откройте своего бота в Telegram, отправьте `/start`, затем вопрос. Каждый вопрос обрабатывается независимо, история не сохраняется. Длинные ответы разбиваются на сообщения. Остановка — Ctrl+C. По желанию задайте `TELEGRAM_ALLOWED_USER_IDS` числовыми ID через запятую; пустое значение разрешает всем пользователям обращаться к боту. Для Telegram нужен интернет, хотя генерация в режиме Ollama остаётся локальной.

Чтобы переключиться на OpenAI, укажите в `.env` `LLM_PROVIDER=openai`, собственный `OPENAI_API_KEY` и доступное вам имя модели в `OPENAI_MODEL`, затем перезапустите бота. В этом режиме сообщения отправляются в OpenAI. Обратное переключение: `LLM_PROVIDER=ollama` и перезапуск. Не публикуйте `.env` и не вставляйте настоящие токены в `.env.example`.

Проверки без обращения к Telegram и OpenAI:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Документация: [OpenAI-совместимый API Ollama](https://docs.ollama.com/api/openai-compatibility), [python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/).

Ollama для Windows с моделью **Qwen3 4B Instruct**. Программа и веса модели находятся в этой папке. Облачные функции отключены, API доступен только на `127.0.0.1:11434`.

## Запуск

Дважды нажмите `start-chat.cmd`. Запустится сервер Ollama и откроется консольный чат. Для выхода из чата введите `/bye`. Сервер остаётся в фоне до завершения процесса или перезагрузки Windows.

После загрузки модели интернет для общения не нужен. История текущего диалога занимает контекст размером 4096 токенов. Используется официальный вариант `qwen3:4b-instruct` для обычного чата.

## Команды PowerShell

Выполняйте из этой папки:

```powershell
# Чат
.\ollama.ps1

# Список скачанных моделей
.\ollama.ps1 list

# Проверить использование GPU
.\ollama.ps1 ps

# Выгрузить модель из памяти
.\ollama.ps1 stop qwen3:4b-instruct
```

Если PowerShell блокирует скрипты, используйте `start-chat.cmd` или `powershell -NoProfile -ExecutionPolicy Bypass -File .\ollama.ps1 list`.

## Файлы

- `.runtime/ollama/` — официальная Ollama 0.40.4.
- `models/` — локальные веса Qwen3 4B Instruct (~2,5 ГБ).
- `logs/` — журналы сервера для диагностики.
- `ollama.ps1` — запуск сервера и команд Ollama с настройками проекта.

Не запускайте `.runtime/ollama/ollama.exe` напрямую: обёртка задаёт расположение моделей на диске F и параметры сервера. Если порт 11434 уже занят другой Ollama, обёртка подключится к ней; её настройки и папка моделей могут отличаться.

Источники: [Ollama для Windows](https://docs.ollama.com/windows), [Qwen3 4B Instruct](https://ollama.com/library/qwen3:4b-instruct), [официальный релиз](https://github.com/ollama/ollama/releases/tag/v0.40.4).
