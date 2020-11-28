import aiohttp


async def async_request(url, method, data=None, params=None, headers=None):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.request(method=method, url=url, params=params, data=data, headers=headers) as response:
            result = await response.json()
    return result