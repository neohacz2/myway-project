import asyncio
from contextlib import asynccontextmanager

from .config import Config, load_config
from .freshness import load_state, now_iso, save_state
from .logging_setup import setup_logging
from .notebooklm_adapter import (
    Adapter,
    AuthExpiredError,
    real_adapter,
    sanitize_log,
)


_ARTIFACT_TYPES = ("audio", "video", "mind_map")


@asynccontextmanager
async def _adapter_ctx(injected: Adapter | None):
    if injected is not None:
        yield injected
    else:
        async with real_adapter() as a:
            yield a


async def run_batch(adapter: Adapter | None = None, config: Config | None = None) -> None:
    if config is None:
        config = load_config()
    log = setup_logging(config.log_path)
    state = load_state(config.state_path)

    if state.sources_added_since_last_batch == 0:
        log.info("no new sources; skip artifact batch")
        return

    async with _adapter_ctx(adapter) as a:
        for artifact_type in _ARTIFACT_TYPES:
            method = getattr(a, f"generate_{artifact_type}")
            try:
                task_id = await method(config.notebook_id)
            except AuthExpiredError:
                log.error("auth expired — run `notebooklm login` to re-authenticate")
                return
            except Exception as e:
                log.error(
                    f"{artifact_type}: fail "
                    f"{type(e).__name__}: {sanitize_log(str(e))}"
                )
                continue
            log.info(f"{artifact_type}: ok (task_id={task_id})")

    state.last_batch_at = now_iso()
    state.sources_added_since_last_batch = 0
    save_state(state, config.state_path)


def main() -> None:
    asyncio.run(run_batch())


if __name__ == "__main__":
    main()
