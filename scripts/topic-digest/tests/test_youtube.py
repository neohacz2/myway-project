import pytest
from pytest_httpx import HTTPXMock

from topic_digest.youtube import ChannelFetchError, fetch_channel_videos


CHANNEL_URL = "https://www.youtube.com/channel/UCdummy12345678901234567"
RSS_URL_EXPECTED = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCdummy12345678901234567"
)


def rss_xml(entries: list[dict]) -> str:
    items = "\n".join(
        f"""<entry>
            <id>yt:video:{e['id']}</id>
            <yt:videoId>{e['id']}</yt:videoId>
            <title>{e['title']}</title>
            <link rel="alternate" href="https://www.youtube.com/watch?v={e['id']}"/>
            <published>{e['published']}</published>
        </entry>"""
        for e in entries
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
    <title>Channel</title>
    {items}
</feed>"""


def test_fetch_three_new_videos(httpx_mock: HTTPXMock):
    entries = [
        {"id": "vid1", "title": "Video 1", "published": "2026-05-28T00:00:00+00:00"},
        {"id": "vid2", "title": "Video 2", "published": "2026-05-27T00:00:00+00:00"},
        {"id": "vid3", "title": "Video 3", "published": "2026-05-26T00:00:00+00:00"},
    ]
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml(entries))

    videos = fetch_channel_videos(CHANNEL_URL)
    assert [v.id for v in videos] == ["vid1", "vid2", "vid3"]
    assert videos[0].url == "https://www.youtube.com/watch?v=vid1"
    assert videos[0].title == "Video 1"


def test_fetch_empty_feed(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=RSS_URL_EXPECTED, text=rss_xml([]))
    assert fetch_channel_videos(CHANNEL_URL) == []


def test_fetch_http_error_raises(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=RSS_URL_EXPECTED, status_code=500)
    with pytest.raises(ChannelFetchError):
        fetch_channel_videos(CHANNEL_URL)


def test_invalid_channel_url_raises():
    with pytest.raises(ChannelFetchError):
        fetch_channel_videos("https://example.com/notayoutube")
