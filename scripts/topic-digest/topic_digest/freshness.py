from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass
class AppState:
    ingested_video_ids: list[str] = field(default_factory=list)
    last_polled_at: str | None = None
    last_batch_at: str | None = None
    sources_added_since_last_batch: int = 0


def load_state(path: Path) -> AppState:
    if not path.exists():
        return AppState()
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return AppState(
        ingested_video_ids=raw.get("ingested_video_ids", []),
        last_polled_at=raw.get("last_polled_at"),
        last_batch_at=raw.get("last_batch_at"),
        sources_added_since_last_batch=raw.get("sources_added_since_last_batch", 0),
    )


def save_state(state: AppState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2, ensure_ascii=False)


def is_new(state: AppState, video_id: str) -> bool:
    return video_id not in state.ingested_video_ids


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
