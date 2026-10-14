"""Telegram long-polling bot. Each text message is an independent request."""
import logging
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from config import Settings, required
from llm import LLM, public_error
from provider_store import ProviderStore

logger = logging.getLogger(__name__)


def split_reply(text: str, limit: int = 4000):
    # Telegram measures length in UTF-16 units; emoji may occupy two units.
    chunk, size = [], 0
    for char in text:
        units = len(char.encode('utf-16-le')) // 2
        if size + units > limit:
            yield ''.join(chunk)
            chunk, size = [], 0
        chunk.append(char)
        size += units
    if chunk:
        yield ''.join(chunk)


def build_application(settings: Settings, token: str, allowed_ids: set[int],
                      store_path: Path | None = None) -> Application:
    clients = {settings.provider: LLM(settings)}
    store = ProviderStore(store_path or Path(__file__).parent / 'data' / 'providers.sqlite3')

    def client_for(provider: str) -> LLM:
        if provider not in clients:
            clients[provider] = LLM(Settings.load(provider))
        return clients[provider]

    async def shutdown(app: Application):
        for client in clients.values():
            await client.close()
        store.close()

    async def permitted(update: Update) -> bool:
        return bool(update.effective_user and (
            not allowed_ids or update.effective_user.id in allowed_ids))

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_message and await permitted(update):
            await update.effective_message.reply_text(
                'Отправьте текстовый вопрос. Каждый вопрос — отдельный диалог.\n'
                '/provider — выбрать OpenAI или Ollama.')
            await provider_menu(update, context)

    async def provider_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_message or not await permitted(update):
            return
        current = store.get(update.effective_user.id, settings.provider)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('OpenAI', callback_data='provider:openai'),
            InlineKeyboardButton('Ollama', callback_data='provider:ollama'),
        ]])
        await update.effective_message.reply_text(
            f'Сейчас выбран: {current}.\n'
            'OpenAI — запросы в облако, оплата по вашему API-ключу.\n'
            'Ollama — модель на этом компьютере.\n'
            'Выбор сохраняется лично для вас.', reply_markup=keyboard)

    async def select_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        if not await permitted(update):
            await query.answer('Нет доступа.', show_alert=True)
            return
        provider = (query.data or '').removeprefix('provider:')
        if provider not in {'openai', 'ollama'}:
            await query.answer('Неизвестный провайдер.', show_alert=True)
            return
        try:
            selected = client_for(provider).settings
        except ValueError:
            await query.answer('Провайдер не настроен. Проверьте его модель и ключ в .env.', show_alert=True)
            return
        store.set(update.effective_user.id, provider)
        await query.answer(f'Выбран {provider}: {selected.model}', show_alert=True)

    async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg or not msg.text or not await permitted(update):
            return
        if len(msg.text) > 6000:
            await msg.reply_text('Сократите вопрос до 6000 символов.')
            return
        try:
            provider = store.get(update.effective_user.id, settings.provider)
            answer = await client_for(provider).ask(msg.text)
        except Exception as error:
            logger.warning('LLM request failed (%s)', type(error).__name__)
            await msg.reply_text(public_error(error))
            return
        for chunk in split_reply(answer):
            await msg.reply_text(chunk)

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.warning('Telegram update failed (%s)', type(context.error).__name__)

    app = (Application.builder().token(token).concurrent_updates(False)
           .post_shutdown(shutdown).build())
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    app.add_handler(CommandHandler('provider', provider_menu))
    app.add_handler(CallbackQueryHandler(select_provider, pattern=r'^provider:'))
    app.add_error_handler(on_error)
    return app


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    try:
        settings = Settings.load()
        token = required('TELEGRAM_BOT_TOKEN')
        try:
            allowed_ids = {int(value.strip()) for value in
                           os.getenv('TELEGRAM_ALLOWED_USER_IDS', '').split(',') if value.strip()}
        except ValueError:
            raise ValueError('TELEGRAM_ALLOWED_USER_IDS: нужны числовые ID через запятую.') from None
        app = build_application(settings, token, allowed_ids)
    except ValueError as error:
        print(error)
        return 1
    print(f'Бот запускается: {settings.provider} / {settings.model}')
    try:
        app.run_polling(allowed_updates=['message', 'callback_query'])
    except Exception as error:
        logger.error('Bot stopped (%s). Проверьте токен и доступ к Telegram.', type(error).__name__)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
