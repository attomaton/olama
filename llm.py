"""Shared asynchronous OpenAI-compatible client for CLI and Telegram."""
from openai import AsyncOpenAI, OpenAIError

from config import Settings


class LLM:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=180.0,
            max_retries=0,
        )

    async def ask(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {'role': 'system', 'content': 'Отвечай на языке пользователя, ясно и по существу.'},
                {'role': 'user', 'content': prompt},
            ],
            max_completion_tokens=1024,
        )
        if not response.choices or not response.choices[0].message.content:
            raise ValueError('Модель вернула пустой ответ.')
        return response.choices[0].message.content.strip()

    async def close(self) -> None:
        await self.client.close()


def public_error(error: Exception) -> str:
    # Never send raw SDK exceptions: they may contain request or credential data.
    if isinstance(error, OpenAIError):
        return 'Ошибка LLM: проверьте запуск Ollama, имя модели или настройки OpenAI в .env.'
    return 'Не удалось получить ответ модели. Попробуйте ещё раз.'
