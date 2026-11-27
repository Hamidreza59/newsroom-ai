import asyncio

from newsroom_api.cache import TTLCache


async def test_ttl_cache_loads_once_per_window():
    now = [0.0]
    cache = TTLCache(clock=lambda: now[0])
    calls = []

    async def loader():
        calls.append(1)
        await asyncio.sleep(0)
        return len(calls)

    results = await asyncio.gather(*(cache.get("k", 10, loader) for _ in range(5)))
    assert {r[0] for r in results} == {1} and len(calls) == 1
    now[0] = 11
    assert (await cache.get("k", 10, loader))[0] == 2
