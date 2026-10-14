"""Read project-local .env without overriding process environment variables."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def required(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value or value.startswith('your_'):
        raise ValueError(f'Задайте {name} в .env (сейчас нет значения или стоит заглушка).')
    return value


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    api_key: str
    base_url: str

    @classmethod
    def load(cls, provider: str | None = None) -> 'Settings':
        load_dotenv(Path(__file__).with_name('.env'))
        provider = (provider or os.getenv('LLM_PROVIDER', 'ollama')).strip().lower()
        if provider == 'ollama':
            return cls(provider, os.getenv('OLLAMA_MODEL', 'qwen3:4b-instruct').strip(),
                       'ollama', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1').strip())
        if provider == 'openai':
            return cls(provider, required('OPENAI_MODEL'), required('OPENAI_API_KEY'),
                       'https://api.openai.com/v1')
        raise ValueError('LLM_PROVIDER должен быть openai или ollama.')
