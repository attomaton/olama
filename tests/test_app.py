import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from openai import AsyncOpenAI

from bot import build_application, split_reply
from config import Settings
from llm import LLM


class ConfigTests(unittest.TestCase):
    def load(self, values):
        with patch.dict(os.environ, values, clear=True), patch('config.load_dotenv'):
            return Settings.load()

    def test_ollama_never_uses_openai_key(self):
        settings = self.load({'LLM_PROVIDER': 'ollama', 'OPENAI_API_KEY': 'dummy-test-secret'})
        self.assertEqual(settings.api_key, 'ollama')
        self.assertEqual(settings.base_url, 'http://localhost:11434/v1')

    def test_openai_requires_real_configuration(self):
        with self.assertRaisesRegex(ValueError, 'OPENAI_API_KEY'):
            self.load({'LLM_PROVIDER': 'openai', 'OPENAI_MODEL': 'test-model',
                       'OPENAI_API_KEY': 'your_openai_api_key_here'})
        settings = self.load({'LLM_PROVIDER': 'openai', 'OPENAI_MODEL': 'test-model',
                              'OPENAI_API_KEY': 'dummy-test-key'})
        self.assertEqual(settings.base_url, 'https://api.openai.com/v1')
        self.assertEqual(settings.model, 'test-model')

    def test_unknown_provider_fails(self):
        with self.assertRaises(ValueError):
            self.load({'LLM_PROVIDER': 'typo'})

    def test_telegram_chunks_preserve_unicode(self):
        answer = 'Привет 😀' * 1500
        chunks = list(split_reply(answer))
        self.assertEqual(''.join(chunks), answer)
        self.assertTrue(all(len(part.encode('utf-16-le')) // 2 <= 4000 for part in chunks))


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_request_routing_and_response(self):
        for provider, url, key in [('ollama', 'http://localhost:11434/v1', 'ollama'),
                                   ('openai', 'https://api.openai.com/v1', 'dummy-test-key')]:
            settings = Settings(provider, 'test-model', key, url)
            llm = LLM(settings)
            await llm.close()
            requests = []

            def reply(request):
                requests.append(request)
                return httpx.Response(200, json={
                    'id': 'test', 'created': 0, 'object': 'chat.completion',
                    'model': 'test-model', 'choices': [{'index': 0, 'finish_reason': 'stop',
                        'message': {'role': 'assistant', 'content': 'Привет'}}]})

            llm.client = AsyncOpenAI(api_key=key, base_url=url,
                http_client=httpx.AsyncClient(transport=httpx.MockTransport(reply)))
            try:
                self.assertEqual(await llm.ask('Тест'), 'Привет')
                self.assertEqual(str(requests[0].url), url + '/chat/completions')
                self.assertEqual(requests[0].headers['authorization'], 'Bearer ' + key)
            finally:
                await llm.close()

    async def test_telegram_handler_and_access_filter(self):
        settings = Settings('ollama', 'test-model', 'ollama', 'http://localhost:11434/v1')
        with patch('bot.LLM') as factory:
            service = factory.return_value
            service.ask = AsyncMock(return_value='Ответ')
            service.close = AsyncMock()
            temp = tempfile.TemporaryDirectory()
            self.addCleanup(temp.cleanup)
            app = build_application(settings, '123:test-token', {42}, Path(temp.name) / 'providers.db')
            from types import SimpleNamespace
            msg = SimpleNamespace(text='Вопрос', reply_text=AsyncMock())
            update = SimpleNamespace(effective_message=msg, effective_user=SimpleNamespace(id=7))
            handler = app.handlers[0][1]
            await handler.callback(update, None)
            service.ask.assert_not_awaited()
            update.effective_user.id = 42
            await handler.callback(update, None)
            service.ask.assert_awaited_once_with('Вопрос')
            msg.reply_text.assert_awaited_once_with('Ответ')
            await app.post_shutdown(app)

    async def test_switch_routes_per_user_and_survives_restart(self):
        from types import SimpleNamespace
        from provider_store import ProviderStore
        settings = Settings('ollama', 'local', 'ollama', 'http://localhost:11434/v1')
        remote = Settings('openai', 'remote', 'dummy', 'https://api.openai.com/v1')
        local_client = SimpleNamespace(settings=settings, ask=AsyncMock(return_value='local'), close=AsyncMock())
        remote_client = SimpleNamespace(settings=remote, ask=AsyncMock(return_value='remote'), close=AsyncMock())
        with tempfile.TemporaryDirectory() as tmp, patch('bot.LLM', side_effect=[local_client, remote_client]), patch('bot.Settings.load', return_value=remote):
            path = Path(tmp) / 'providers.db'
            app = build_application(settings, '123:test', {42, 43}, path)
            callback = app.handlers[0][3].callback
            query = SimpleNamespace(data='provider:openai', answer=AsyncMock())
            update = SimpleNamespace(callback_query=query, effective_user=SimpleNamespace(id=7))
            await callback(update, None)
            self.assertIn('Нет доступа', query.answer.call_args.args[0])
            update.effective_user.id = 42
            await callback(update, None)
            msg = SimpleNamespace(text='test', reply_text=AsyncMock())
            update.effective_message = msg
            await app.handlers[0][1].callback(update, None)
            remote_client.ask.assert_awaited_once_with('test')
            update.effective_user.id = 43
            await app.handlers[0][1].callback(update, None)
            local_client.ask.assert_awaited_once_with('test')
            query.data = 'provider:ollama'
            update.effective_user.id = 42
            await callback(update, None)
            await app.post_shutdown(app)
            saved = ProviderStore(path)
            self.assertEqual(saved.get(42, 'openai'), 'ollama')
            saved.close()


if __name__ == '__main__':
    unittest.main()
