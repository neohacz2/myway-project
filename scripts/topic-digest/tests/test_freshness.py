from pathlib import Path

from topic_digest.freshness import (
    AppState,
    is_new,
    load_state,
    now_iso,
    save_state,
)


def test_load_state_returns_default_when_file_missing(tmp_path: Path):
    assert load_state(tmp_path / "missing.json") == AppState()


def test_save_then_load_roundtrip(tmp_path: Path):
    p = tmp_path / "state.json"
    s = AppState(
        ingested_video_ids=["a", "b"],
        last_polled_at="2026-05-28T00:00:00+00:00",
        last_batch_at=None,
        sources_added_since_last_batch=2,
    )
    save_state(s, p)
    assert load_state(p) == s


def test_save_creates_parent_dirs(tmp_path: Path):
    p = tmp_path / "nested" / "dir" / "state.json"
    save_state(AppState(), p)
    assert p.exists()


def test_is_new_true_for_unseen():
    assert is_new(AppState(ingested_video_ids=["a"]), "b") is True


def test_is_new_false_for_already_ingested():
    assert is_new(AppState(ingested_video_ids=["a"]), "a") is False


def test_now_iso_has_tz_suffix():
    assert now_iso().endswith("+00:00")
