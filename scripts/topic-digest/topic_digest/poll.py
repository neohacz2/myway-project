import asyncio
import re
from contextlib import asynccontextmanager

from .config import Config, load_config
from .freshness import is_new, load_state, now_iso, save_state
from .logging_setup import setup_logging
from .notebooklm_adapter import (
    Adapter,
    AuthExpiredError,
    real_adapter,
)
from .youtube import ChannelFetchError, fetch_channel_videos


_SECRET_PATTERNS = (
    re.compile(r"cookies?\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"session_state\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)?"),
)


def _sanitize(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text


@asynccontextmanager
async def _adapter_ctx(injected: Adapter | None):
    if injected is not None:
        yield injected
    else:
        async with real_adapter() as a:
            yield a


async def run_poll(adapter: Adapter | None = None, config: Config | None = None) -> None:
    if config is None:
        config = load_config()
    log = setup_logging(config.log_path)
    state = load_state(config.state_path)

    try:
        videos = fetch_channel_videos(config.youtube_channel_url)
    except ChannelFetchError as e:
        log.error(f"channel fetch failed: {_sanitize(str(e))}")
        return

    new_videos = [v for v in videos if is_new(state, v.id)]
    skipped = len(videos) - len(new_videos)
    if skipped > 0:
        log.info(f"skipped: already ingested ({skipped})")

    added = 0
    failed = 0

    async with _adapter_ctx(adapter) as a:
        for video in new_videos:
            try:
                await a.add_url(config.notebook_id, video.url)
            except AuthExpiredError:
                log.error("auth expired — run `notebooklm login` to re-authenticate")
                save_state(state, config.state_path)
                return
            except Exception as e:
                log.error(
                    f"add_url failed for {video.id}: "
                    f"{type(e).__name__}: {_sanitize(str(e))}"
                )
                failed += 1
                continue
            state.ingested_video_ids.append(video.id)
            state.sources_added_since_last_batch += 1
            added += 1

    state.last_polled_at = now_iso()
    save_state(state, config.state_path)
    log.info(
        f"polled {config.youtube_channel_url}; "
        f"found {len(new_videos)} new; added {added}; skipped {skipped}; failed {failed}"
    )


def main() -> None:
    asyncio.run(run_poll())


if __name__ == "__main__":
    main()
