from abc import ABC
from typing import NoReturn

import aiohttp

from errors import GetDataError


class DataGetter(ABC):

    @staticmethod
    async def get_request(url,
                          headers=None,
                          params=None,
                          cookies=None,
                          timeout=15,
                          only_bytes: bool = False) -> dict | NoReturn:
        # asynchrony request get
        for _ in range(3):
            try:
                client_timeout = aiohttp.ClientTimeout(total=timeout * 3, connect=timeout)
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                    async with session.get(url, headers=headers, params=params, cookies=cookies, ssl=False,
                                           timeout=client_timeout) as response:
                        if only_bytes:
                            return await response.read()
                        return await response.text()
            except Exception:
                continue
