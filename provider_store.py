"""Persist only provider choices, never API keys or message contents."""
import sqlite3
from pathlib import Path


class ProviderStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS providers (user_id INTEGER PRIMARY KEY, provider TEXT NOT NULL)')
        self.db.commit()

    def get(self, user_id: int, default: str) -> str:
        row = self.db.execute('SELECT provider FROM providers WHERE user_id = ?', (user_id,)).fetchone()
        return row[0] if row else default

    def set(self, user_id: int, provider: str):
        if provider not in {'openai', 'ollama'}:
            raise ValueError('Unknown provider')
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO providers VALUES (?, ?)', (user_id, provider))

    def close(self):
        self.db.close()
