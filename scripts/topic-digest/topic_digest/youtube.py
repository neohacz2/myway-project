from dataclasses import dataclass
import re

import feedparser
import httpx


@dataclass(frozen=True)
class Video:
    id: str
    url: str
    title: str
    published: str


class ChannelFetchError(Exception):
    """Raised when the YouTube channel feed cannot be fetched or parsed."""


_CHANNEL_ID_RE = re.compile(r"channel/(UC[\w-]+)")


def _channel_rss_url(channel_url: str) -> str:
    match = _CHANNEL_ID_RE.search(channel_url)
    if not match:
        raise ChannelFetchError(f"cannot extract channel ID from {channel_url}")
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={match.group(1)}"


def fetch_channel_videos(channel_url: str, timeout: float = 15.0) -> list[Video]:
    rss_url = _channel_rss_url(channel_url)
    try:
        response = httpx.get(rss_url, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise ChannelFetchError(f"http error fetching channel feed: {e}") from e

    parsed = feedparser.parse(response.text)
    if parsed.bozo and not parsed.entries:
        raise ChannelFetchError(f"feed parse error: {parsed.bozo_exception}")

    return [
        Video(
            id=getattr(entry, "yt_videoid", entry.id.split(":")[-1]),
            url=entry.link,
            title=entry.title,
            published=entry.get("published", ""),
        )
        for entry in parsed.entries
    ]
