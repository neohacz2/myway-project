from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    youtube_channel_url: str
    notebook_id: str
    state_path: Path
    log_path: Path


def load_config(env_file: str | None = None) -> Config:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    return Config(
        youtube_channel_url=os.environ["YOUTUBE_CHANNEL_URL"],
        notebook_id=os.environ["NOTEBOOK_ID"],
        state_path=Path(os.environ.get("STATE_PATH", "./state.json")),
        log_path=Path(os.environ.get("LOG_PATH", "./logs/topic-digest.log")),
    )
