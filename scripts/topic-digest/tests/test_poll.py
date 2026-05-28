import re
from pathlib import Path

from pytest_httpx import HTTPXMock

from topic_digest.config import Config
from topic_digest.freshness import load_state
from topic_digest.notebooklm_adapter import InMemoryAdapter
from topic_digest.poll import run_poll
from tests.test_youtube import CHANNEL_URL, RSS_URL_EXPECTED, rss_xml


def make_config(tmp_path: Path) -> Config:
    return Config(
        youtube_channel_url=CHANNEL_URL,
        notebook_id="test-notebook-id",
        state_path=tmp_path / "state.json",
        log_path=tmp_path / "logs" / "topic-digest.log",
    )


async def test_three_new_videos_pushed(tmp_path: Path, httpx_mock: HTTPXMock):
    entries = [
        {"id": f"vid{i}", "title": f"Video {i}", "published": "2026-05-28T00:00:00+00:00"}
        for i in (1, 2, 3)
    ]
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    config = make_config(tmp_path)
    adapter = InMemoryAdapter()

    await run_poll(adapter=adapter, config=config)

    assert len(adapter.add_url_calls) == 3
    pushed_urls = {url for _, url in adapter.add_url_calls}
    assert pushed_urls == {f"https://www.youtube.com/watch?v=vid{i}" for i in (1, 2, 3)}

    state = load_state(config.state_path)
    assert sorted(state.ingested_video_ids) == ["vid1", "vid2", "vid3"]
    assert state.sources_added_since_last_batch == 3


async def test_no_new_videos_is_noop(tmp_path: Path, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml([]))
    config = make_config(tmp_path)
    adapter = InMemoryAdapter()

    await run_poll(adapter=adapter, config=config)

    assert adapter.add_url_calls == []
    state = load_state(config.state_path)
    assert state.ingested_video_ids == []
    assert state.sources_added_since_last_batch == 0


async def test_summary_log_line_matches_pattern(tmp_path: Path, httpx_mock: HTTPXMock):
    entries = [{"id": "vid1", "title": "V", "published": "2026-05-28T00:00:00+00:00"}]
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    config = make_config(tmp_path)

    await run_poll(adapter=InMemoryAdapter(), config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    pattern = r"polled .+; found \d+ new; added \d+; skipped \d+; failed \d+"
    assert re.search(pattern, log_text), f"summary line missing in:\n{log_text}"


async def test_second_poll_does_not_re_push(tmp_path: Path, httpx_mock: HTTPXMock):
    entries = [{"id": "vid1", "title": "V", "published": "2026-05-28T00:00:00+00:00"}]
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    config = make_config(tmp_path)
    adapter = InMemoryAdapter()

    await run_poll(adapter=adapter, config=config)
    first_calls = list(adapter.add_url_calls)
    first_state_ids = list(load_state(config.state_path).ingested_video_ids)

    await run_poll(adapter=adapter, config=config)

    assert adapter.add_url_calls == first_calls
    assert load_state(config.state_path).ingested_video_ids == first_state_ids


async def test_dedupe_logs_skip_message(tmp_path: Path, httpx_mock: HTTPXMock):
    entries = [{"id": "vid1", "title": "V", "published": "2026-05-28T00:00:00+00:00"}]
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))
    config = make_config(tmp_path)
    adapter = InMemoryAdapter()

    await run_poll(adapter=adapter, config=config)
    await run_poll(adapter=adapter, config=config)

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "skipped: already ingested" in log_text
