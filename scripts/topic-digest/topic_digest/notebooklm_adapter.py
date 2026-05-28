from contextlib import asynccontextmanager
from typing import Protocol, runtime_checkable


class AuthExpiredError(Exception):
    """NotebookLM authentication is no longer valid."""


@runtime_checkable
class Adapter(Protocol):
    async def add_url(self, notebook_id: str, url: str) -> None: ...


class NotebookLMAdapter:
    def __init__(self, client) -> None:
        self._client = client

    async def add_url(self, notebook_id: str, url: str) -> None:
        try:
            await self._client.sources.add_url(notebook_id, url, wait=True)
        except Exception as e:
            if _looks_like_auth_failure(e):
                raise AuthExpiredError("storage_state expired or rejected") from None
            raise


class InMemoryAdapter:
    """Adapter stub for tests. Captures calls and replays scripted errors."""

    def __init__(self) -> None:
        self.add_url_calls: list[tuple[str, str]] = []
        self.add_url_error: Exception | None = None

    async def add_url(self, notebook_id: str, url: str) -> None:
        if self.add_url_error is not None:
            raise self.add_url_error
        self.add_url_calls.append((notebook_id, url))


def _looks_like_auth_failure(e: Exception) -> bool:
    msg = str(e).lower()
    return any(token in msg for token in ("unauthor", "401", "session", "expired"))


@asynccontextmanager
async def real_adapter():
    from notebooklm import NotebookLMClient

    async with NotebookLMClient.from_storage() as client:
        yield NotebookLMAdapter(client)
