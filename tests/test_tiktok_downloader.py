from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import tiktok_downloader


def _bot():
    return SimpleNamespace(
        send_video=AsyncMock(),
        send_photo=AsyncMock(),
        send_media_group=AsyncMock(),
        send_audio=AsyncMock(),
        send_message=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_sends_twenty_photos_in_two_batches_then_soundtrack(tmp_path):
    files = []
    for index in range(20):
        path = tmp_path / f"{index}.jpg"
        path.write_bytes(b"photo")
        files.append({"path": str(path), "media_type": "photo", "index": index})
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"audio")
    files.append({"path": str(audio), "media_type": "audio", "index": 20})
    bot = _bot()

    await tiktok_downloader.send_tiktok_assets(bot, 7, files, "@creator\n\nPost")

    assert bot.send_media_group.await_count == 2
    assert len(bot.send_media_group.await_args_list[0].kwargs["media"]) == 10
    assert len(bot.send_media_group.await_args_list[1].kwargs["media"]) == 10
    assert bot.send_media_group.await_args_list[0].kwargs["media"][0].caption == "@creator\n\nPost"
    assert bot.send_media_group.await_args_list[1].kwargs["media"][0].caption is None
    bot.send_audio.assert_awaited_once()
    assert bot.send_audio.await_args.kwargs["caption"] is None
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_single_photo_is_not_sent_as_invalid_media_group(tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"photo")
    bot = _bot()

    await tiktok_downloader.send_tiktok_assets(
        bot,
        7,
        [{"path": str(photo), "media_type": "photo", "index": 0}],
        "Caption",
    )

    bot.send_photo.assert_awaited_once()
    bot.send_media_group.assert_not_awaited()


@pytest.mark.asyncio
async def test_long_caption_is_sent_as_separate_message(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    bot = _bot()
    caption = "x" * 1025

    await tiktok_downloader.send_tiktok_assets(
        bot,
        7,
        [{"path": str(video), "media_type": "video", "index": 0}],
        caption,
    )

    assert bot.send_video.await_args.kwargs["caption"] is None
    bot.send_message.assert_awaited_once_with(chat_id=7, text=caption)


@pytest.mark.asyncio
async def test_handler_removes_all_downloaded_files(monkeypatch, tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")

    monkeypatch.setattr(
        tiktok_downloader,
        "download_tiktok_post_assets",
        lambda *_args: {
            "caption": "Post",
            "author_username": "creator",
            "files": [{"path": str(video), "media_type": "video", "index": 0}],
        },
    )
    progress = SimpleNamespace(edit_text=AsyncMock(), delete=AsyncMock())
    message = SimpleNamespace(
        text="https://www.tiktok.com/@creator/video/123",
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=7),
        reply=AsyncMock(return_value=progress),
    )
    bot = _bot()

    await tiktok_downloader.handle_tiktok(message, bot, str(tmp_path))

    assert not video.exists()
    progress.delete.assert_awaited_once()
