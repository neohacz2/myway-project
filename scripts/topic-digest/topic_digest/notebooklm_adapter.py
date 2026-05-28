import re
from contextlib import asynccontextmanager
from typing import Protocol, runtime_checkable


_SECRET_PATTERNS = (
    re.compile(r"cookies?\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"session_state\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)?"),
)


def sanitize_log(text: str) -> str:
    """Redact cookie/JWT patterns before writing to log."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text


class AuthExpiredError(Exception):
    """NotebookLM authentication is no longer valid."""


@runtime_checkable
class Adapter(Protocol):
    async def add_url(self, notebook_id: str, url: str) -> None: ...
    async def generate_audio(self, notebook_id: str) -> str: ...
    async def generate_video(self, notebook_id: str) -> str: ...
    async def generate_mind_map(self, notebook_id: str) -> str: ...


def _looks_like_auth_failure(e: Exception) -> bool:
    msg = str(e).lower()
    return any(token in msg for token in ("unauthor", "401", "session", "expired"))


def _extract_task_id(result) -> str:
    """notebooklm-py 0.5.0 returns either an object with .task_id or a dict (spike-log)."""
    if hasattr(result, "task_id"):
        return getattr(result, "task_id") or "?"
    if isinstance(result, dict):
        return result.get("task_id", "?")
    return "?"


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

    async def generate_audio(self, notebook_id: str) -> str:
        return await self._gen("generate_audio", notebook_id)

    async def generate_video(self, notebook_id: str) -> str:
        return await self._gen("generate_video", notebook_id)

    async def generate_mind_map(self, notebook_id: str) -> str:
        return await self._gen("generate_mind_map", notebook_id)

    async def _gen(self, method_name: str, notebook_id: str) -> str:
        try:
            method = getattr(self._client.artifacts, method_name)
            result = await method(notebook_id)
            return _extract_task_id(result)
        except Exception as e:
            if _looks_like_auth_failure(e):
                raise AuthExpiredError("storage_state expired or rejected") from None
            raise


class InMemoryAdapter:
    """Adapter stub for tests. Captures calls and replays scripted errors."""

    def __init__(self) -> None:
        self.add_url_calls: list[tuple[str, str]] = []
        self.add_url_error: Exception | None = None
        self.generate_audio_calls: list[str] = []
        self.generate_audio_error: Exception | None = None
        self.generate_video_calls: list[str] = []
        self.generate_video_error: Exception | None = None
        self.generate_mind_map_calls: list[str] = []
        self.generate_mind_map_error: Exception | None = None

    async def add_url(self, notebook_id: str, url: str) -> None:
        if self.add_url_error is not None:
            raise self.add_url_error
        self.add_url_calls.append((notebook_id, url))

    async def generate_audio(self, notebook_id: str) -> str:
        if self.generate_audio_error is not None:
            raise self.generate_audio_error
        self.generate_audio_calls.append(notebook_id)
        return f"audio-task-{len(self.generate_audio_calls)}"

    async def generate_video(self, notebook_id: str) -> str:
        if self.generate_video_error is not None:
            raise self.generate_video_error
        self.generate_video_calls.append(notebook_id)
        return f"video-task-{len(self.generate_video_calls)}"

    async def generate_mind_map(self, notebook_id: str) -> str:
        if self.generate_mind_map_error is not None:
            raise self.generate_mind_map_error
        self.generate_mind_map_calls.append(notebook_id)
        return f"mind_map-task-{len(self.generate_mind_map_calls)}"


@asynccontextmanager
async def real_adapter():
    from notebooklm import NotebookLMClient

    async with NotebookLMClient.from_storage() as client:
        yield NotebookLMAdapter(client)
