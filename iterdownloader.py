#!/usr/bin/env python3
import asyncio
import logging
import os
import urllib.parse
from configparser import ConfigParser
from typing import Generator

import bs4
import aiohttp
import aiofiles

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


async def iter_all_file(session: aiohttp.ClientSession, server_address: str, url: str) -> Generator[str, None, None]:
    async with session.get(f'{server_address}{url}') as response:
        soup = bs4.BeautifulSoup(await response.text(), 'lxml')
        for a_tag in soup.find_all('a'):
            next_url = a_tag['href']
            if next_url.endswith('/'):
                async for u in iter_all_file(session, server_address, f'{url}{next_url}'):
                    yield u
            yield f'{url}{next_url}'


async def download(session: aiohttp.ClientSession, url: str, file_name: str) -> None:
    if file_name.endswith('/') or file_name.endswith('.lnk'):
        return
    if os.path.exists(urllib.parse.unquote(file_name)):
        return
    async with session.get(url) as response:
        for n in range(len((group := file_name.split('/')[:-1]))):
            path = urllib.parse.unquote(os.path.join(*group))
            if not os.path.exists(path):
                os.mkdir(path)
        async with aiofiles.open(urllib.parse.unquote(file_name), 'wb') as file:
            while chunk := await response.content.read(102400):
                await file.write(chunk)
    logger.info('Downloaded %s', urllib.parse.unquote(file_name))


async def main():
    config = ConfigParser()
    config.read('config.ini')
    session = aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(2))
    async for x in iter_all_file(
        session,
        server_address := config.get('server', 'address', fallback='http://localhost:8000/'),
        ''
    ):
        await download(session, f'{server_address}{x}', x)
    await session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(lineno)d - %(message)s')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
