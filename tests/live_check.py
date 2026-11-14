"""Verifica dal vivo: usa lo stesso client dell'integrazione sulla lavatrice vera.

    python tests/live_check.py <ip>
"""

import asyncio
import sys

import aiohttp

from custom_components.hoover_simplyfi.api import SimplyFiClient
from custom_components.hoover_simplyfi.coordinator import WasherData


async def main(host: str) -> None:
    async with aiohttp.ClientSession() as session:
        client = SimplyFiClient(session, host)
        key = await client.async_recover_key()
        print("chiave ricavata:", "sì" if key else "non necessaria (risposta in chiaro)")
        data = WasherData(online=True, raw=await client.async_status())
        for name in ("state", "running", "phase", "remaining_minutes", "program",
                     "temperature", "spin_speed", "remote_control", "error"):
            print(f"{name:<18}{getattr(data, name)}")


asyncio.run(main(sys.argv[1]))
