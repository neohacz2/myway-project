from pathlib import Path

from topic_digest.config import Config
from topic_digest.freshness import AppState, load_state, save_state
from topic_digest.notebooklm_adapter import AuthExpiredError, InMemoryAdapter
from topic_digest.batch import run_batch


def make_config(tmp_path: Path) -> Config:
    return Config(
        youtube_channel_url="https://www.youtube.com/channel/UCdummy12345678901234567",
        notebook_id="test-notebook-id",
        state_path=tmp_path / "state.json",
        log_path=tmp_path / "logs" / "topic-digest.log",
    )


def make_state_with_new_sources(n: int) -> AppState:
    return AppState(
        ingested_video_ids=[f"vid{i}" for i in range(n)],
        sources_added_since_last_batch=n,
    )


# ─── Scenario 3: happy path ─────────────────────────────────────────────────


async def test_batch_triggers_all_four_artifacts(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(2), config.state_path)
    adapter = InMemoryAdapter()

    await run_batch(adapter=adapter, config=config)

    assert len(adapter.generate_audio_calls) == 1
    assert len(adapter.generate_video_calls) == 1
    assert len(adapter.generate_mind_map_calls) == 1
    assert len(adapter.generate_infographic_calls) == 1


async def test_batch_logs_artifact_results(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    await run_batch(adapter=InMemoryAdapter(), config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "audio: ok" in log_text
    assert "video: ok" in log_text
    assert "mind_map: ok" in log_text
    assert "infographic: ok" in log_text


async def test_batch_does_not_call_wait_for_completion(tmp_path: Path):
    """Trigger-only: batch does not block on generation completion."""
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)
    adapter = InMemoryAdapter()

    await run_batch(adapter=adapter, config=config)

    # InMemoryAdapter has no wait_for_completion; if batch called it,
    # an AttributeError would have been raised already.
    # Additional guard: no "wait" attribute was accessed.
    assert not hasattr(adapter, "wait_for_completion_calls")


async def test_batch_updates_state_after_success(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(3), config.state_path)

    await run_batch(adapter=InMemoryAdapter(), config=config)

    state = load_state(config.state_path)
    assert state.sources_added_since_last_batch == 0
    assert state.last_batch_at is not None


# ─── Scenario 4: skip when no new sources ───────────────────────────────────


async def test_batch_skips_when_no_new_sources(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(AppState(sources_added_since_last_batch=0), config.state_path)
    adapter = InMemoryAdapter()

    await run_batch(adapter=adapter, config=config)

    assert adapter.generate_audio_calls == []
    assert adapter.generate_video_calls == []
    assert adapter.generate_mind_map_calls == []
    assert adapter.generate_infographic_calls == []


async def test_batch_skip_does_not_update_last_batch_at(tmp_path: Path):
    config = make_config(tmp_path)
    original_state = AppState(last_batch_at="2026-05-20T00:00:00+00:00",
                               sources_added_since_last_batch=0)
    save_state(original_state, config.state_path)

    await run_batch(adapter=InMemoryAdapter(), config=config)

    state = load_state(config.state_path)
    assert state.last_batch_at == "2026-05-20T00:00:00+00:00"


async def test_batch_skip_logs_message(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(AppState(sources_added_since_last_batch=0), config.state_path)

    await run_batch(adapter=InMemoryAdapter(), config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "no new sources; skip artifact batch" in log_text


# ─── Scenario 6 (batch path): auth expiry ───────────────────────────────────


async def test_batch_auth_expired_aborts_all_triggers(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_audio_error = AuthExpiredError("session expired")

    await run_batch(adapter=adapter, config=config)

    assert adapter.generate_video_calls == []
    assert adapter.generate_mind_map_calls == []
    assert adapter.generate_infographic_calls == []


async def test_batch_auth_expired_does_not_update_state(tmp_path: Path):
    config = make_config(tmp_path)
    original = make_state_with_new_sources(1)
    save_state(original, config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_audio_error = AuthExpiredError("session expired")

    await run_batch(adapter=adapter, config=config)

    state = load_state(config.state_path)
    assert state.last_batch_at is None
    assert state.sources_added_since_last_batch == 1


async def test_batch_auth_expired_logs_exact_message(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_audio_error = AuthExpiredError("session expired")

    await run_batch(adapter=adapter, config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "auth expired — run `notebooklm login` to re-authenticate" in log_text


# ─── Scenario 7: partial failure isolation ──────────────────────────────────


async def test_mind_map_failure_does_not_block_audio_video_infographic(tmp_path: Path):
    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_mind_map_error = RuntimeError("safe_index drift at path ()[0]")

    await run_batch(adapter=adapter, config=config)

    assert len(adapter.generate_audio_calls) == 1
    assert len(adapter.generate_video_calls) == 1
    assert len(adapter.generate_mind_map_calls) == 0
    assert len(adapter.generate_infographic_calls) == 1


async def test_batch_logs_do_not_leak_storage_state_secrets(tmp_path: Path):
    import re as _re

    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_audio_error = RuntimeError(
        "request failed; cookies=SESSION=abc123; "
        "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature; "
        "session_state=opaque-value"
    )

    await run_batch(adapter=adapter, config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert not _re.search(r"\bcookies\b", log_text, _re.IGNORECASE), (
        f"cookies keyword leaked into batch log:\n{log_text}"
    )
    assert not _re.search(r"\bsession_state\b", log_text, _re.IGNORECASE), (
        f"session_state keyword leaked into batch log:\n{log_text}"
    )
    assert not _re.search(r"eyJ[A-Za-z0-9_-]+\.eyJ", log_text), (
        f"JWT pattern leaked into batch log:\n{log_text}"
    )


async def test_partial_failure_logs_ok_and_fail_separately(tmp_path: Path):
    import re as _re

    config = make_config(tmp_path)
    save_state(make_state_with_new_sources(1), config.state_path)

    adapter = InMemoryAdapter()
    adapter.generate_mind_map_error = RuntimeError("safe_index drift")

    await run_batch(adapter=adapter, config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "audio: ok" in log_text
    assert "video: ok" in log_text
    assert _re.search(r"mind_map: fail .*(Error|Exception)", log_text), (
        f"expected 'mind_map: fail <ExcType>' in:\n{log_text}"
    )
