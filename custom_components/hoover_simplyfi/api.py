"""Client del protocollo HTTP locale Candy/Hoover simply-Fi."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp

READ_PATH = "/http-read.json?encrypted=1"
WRITE_PATH = "/http-write.json"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=8)
RETRIES = 3
RETRY_DELAY = 1.5

# Inizi noti del documento di stato: più lunghi della chiave (16 byte), quindi
# bastano a ricavarla da una sola risposta cifrata.
KNOWN_PREFIXES = (
    b'{\r\n\t"statusLavatrice":{',
    b'{"statusLavatrice":{"',
    b'{\n\t"statusLavatrice":{\n',
)
KEY_LENGTH = 16


class SimplyFiError(Exception):
    """Errore generico del client."""


class SimplyFiConnectionError(SimplyFiError):
    """La lavatrice non risponde (spenta o Wi-Fi a riposo)."""


class SimplyFiProtocolError(SimplyFiError):
    """Risposta non interpretabile."""


class SimplyFiCommandError(SimplyFiError):
    """La lavatrice ha rifiutato un comando."""


def xor(data: bytes, key: str) -> bytes:
    """XOR a chiave ripetuta: la stessa funzione cifra e decifra."""
    k = key.encode()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))


def _parse_status(text: str) -> dict[str, Any] | None:
    try:
        doc = json.loads(text)
    except ValueError:
        return None
    if not isinstance(doc, dict):
        return None
    status = doc.get("statusLavatrice")
    return status if isinstance(status, dict) else None


def recover_key(cipher: bytes) -> str:
    """Ricava la chiave XOR da una risposta di stato cifrata."""
    if len(cipher) >= KEY_LENGTH:
        for prefix in KNOWN_PREFIXES:
            key = bytes(
                c ^ p for c, p in zip(cipher[:KEY_LENGTH], prefix[:KEY_LENGTH])
            ).decode("latin-1")
            if key.isascii() and key.isalnum():
                if _parse_status(xor(cipher, key).decode("utf-8", "replace")):
                    return key
    raise SimplyFiProtocolError("Impossibile ricavare la chiave di cifratura")


class SimplyFiClient:
    """Legge lo stato di una lavatrice simply-Fi sulla rete locale."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, key: str | None = None
    ) -> None:
        self._session = session
        self.host = host
        self.key = key
        # Il modulo Wi-Fi serve una connessione alla volta: letture e comandi
        # non devono mai sovrapporsi.
        self._lock = asyncio.Lock()

    async def _get(self, path: str, retries: int = RETRIES) -> str:
        """GET con ritentativi: il modulo accetta una connessione alla volta."""
        last: Exception | None = None
        for attempt in range(retries):
            try:
                async with self._lock, self._session.get(
                    f"http://{self.host}{path}", timeout=REQUEST_TIMEOUT
                ) as resp:
                    return (await resp.text(encoding="latin-1")).strip()
            except (aiohttp.ClientError, TimeoutError, OSError) as err:
                last = err
                if attempt < retries - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        raise SimplyFiConnectionError(
            f"Lavatrice non raggiungibile su {self.host}: {last}"
        )

    async def async_recover_key(self) -> str:
        """Scopre la chiave; stringa vuota se la lavatrice risponde in chiaro."""
        body = await self._get(READ_PATH)
        if body.startswith("{"):
            if _parse_status(body) is None:
                raise SimplyFiProtocolError("Il dispositivo non è una lavatrice simply-Fi")
            self.key = ""
        else:
            try:
                cipher = bytes.fromhex(body)
            except ValueError as err:
                raise SimplyFiProtocolError("Risposta non valida") from err
            self.key = recover_key(cipher)
        return self.key

    async def async_status(self) -> dict[str, Any]:
        """Restituisce il contenuto di statusLavatrice."""
        if self.key is None:
            await self.async_recover_key()
        body = await self._get(READ_PATH)
        if body.startswith("{"):
            text = body
        else:
            try:
                text = xor(bytes.fromhex(body), self.key or "").decode(
                    "utf-8", "replace"
                )
            except ValueError as err:
                raise SimplyFiProtocolError("Risposta non valida") from err
        status = _parse_status(text)
        if status is None:
            raise SimplyFiProtocolError("Stato non interpretabile")
        return status

    async def async_command(self, params: str) -> None:
        """Invia un comando. Un solo tentativo: un comando non si ripete alla cieca."""
        if self.key is None:
            await self.async_recover_key()
        if self.key:
            data = xor(params.encode(), self.key).hex().upper()
            path = f"{WRITE_PATH}?encrypted=1&data={data}"
        else:
            path = f"{WRITE_PATH}?encrypted=0&{params}"
        body = await self._get(path, retries=1)
        if not body.startswith("{"):
            try:
                body = xor(bytes.fromhex(body), self.key or "").decode(
                    "utf-8", "replace"
                )
            except ValueError as err:
                raise SimplyFiProtocolError("Risposta non valida") from err
        try:
            response = json.loads(body).get("response")
        except (ValueError, AttributeError) as err:
            raise SimplyFiProtocolError("Risposta non valida") from err
        if str(response).upper() != "SUCCESS":
            raise SimplyFiCommandError(f"Comando rifiutato: {response}")
