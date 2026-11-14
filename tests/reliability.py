"""Misura quante richieste singole (senza ritentativi) vanno a buon fine.

    python tests/reliability.py <ip> [aiohttp|urllib] [pausa_secondi]
"""

import asyncio
import sys
import time
import urllib.request

HOST = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "urllib"
PAUSE = float(sys.argv[3]) if len(sys.argv) > 3 else 5
URL = f"http://{HOST}/http-read.json?encrypted=1"
N = 8


def once_urllib():
    with urllib.request.urlopen(URL, timeout=8) as r:
        return len(r.read())


async def run_aiohttp():
    import aiohttp

    async with aiohttp.ClientSession() as s:
        for i in range(N):
            t = time.time()
            try:
                async with s.get(URL, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    print(i, "ok", len(await r.read()), f"{time.time() - t:.1f}s", flush=True)
            except Exception as e:  # noqa: BLE001
                print(i, "FAIL", type(e).__name__, e, f"{time.time() - t:.1f}s", flush=True)
            await asyncio.sleep(PAUSE)


if MODE == "aiohttp":
    asyncio.run(run_aiohttp())
else:
    for i in range(N):
        t = time.time()
        try:
            print(i, "ok", once_urllib(), f"{time.time() - t:.1f}s", flush=True)
        except Exception as e:  # noqa: BLE001
            print(i, "FAIL", type(e).__name__, e, f"{time.time() - t:.1f}s", flush=True)
        time.sleep(PAUSE)
