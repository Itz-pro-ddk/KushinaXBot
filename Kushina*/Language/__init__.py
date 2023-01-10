from typing import AsyncIterator

from aiopath import AsyncPath


async def get_lang_file() -> AsyncIterator[AsyncPath]:
    async for language_file in AsyncPath("kushina/language").iterdir():
        if language_file.suffix == ".yml":
            yield language_file
