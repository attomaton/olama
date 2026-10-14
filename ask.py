"""Usage: python ask.py "Ваш вопрос" [--provider ollama|openai]."""
import argparse
import asyncio
import os
import sys

from config import Settings
from llm import LLM, public_error


async def run(prompt: str) -> int:
    try:
        settings = Settings.load()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    llm = LLM(settings)
    try:
        print(await llm.ask(prompt))
        return 0
    except Exception as error:
        print(public_error(error), file=sys.stderr)
        return 1
    finally:
        await llm.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Вопрос локальной Ollama или OpenAI')
    parser.add_argument('prompt')
    parser.add_argument('--provider', choices=['ollama', 'openai'])
    args = parser.parse_args()
    if args.provider:
        os.environ['LLM_PROVIDER'] = args.provider
    raise SystemExit(asyncio.run(run(args.prompt)))
