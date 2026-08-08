import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from aiogram import Bot
from aiogram.types import (
    FSInputFile,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
)
from tiktokdl.download_post import get_post

from instagram_config import configure_instagram_download
from tiktok_config import configure_tiktok_download
from youtube_config import configure_youtube_download


SUPPORTED_HOSTS = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "x.com": "X",
    "twitter.com": "X",
}
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def extract_supported_url(text: str) -> tuple[str, str] | None:
    """Return the first supported URL and its platform name."""
    for match in URL_PATTERN.finditer(text or ""):
        url = match.group(0).rstrip(".,!?;:)]}")
        hostname = (urlparse(url).hostname or "").lower()
        hostname = hostname.removeprefix("www.")
        for supported_host, platform in SUPPORTED_HOSTS.items():
            if hostname == supported_host or hostname.endswith(f".{supported_host}"):
                return url, platform
    return None


@dataclass(frozen=True)
class StoredMedia:
    kind: str
    file_id: str
    title: str


@dataclass(frozen=True)
class DownloadedMedia:
    kind: str
    path: str
    title: str


class InlineMediaService:
    def __init__(
        self,
        bot: Bot,
        storage_chat_id: int,
        temp_directory: str,
        wait_seconds: float = 8.0,
    ):
        self.bot = bot
        self.storage_chat_id = storage_chat_id
        self.temp_directory = temp_directory
        self.wait_seconds = wait_seconds
        self.cache_file = Path(temp_directory).parent / ".inline_cache.json"
        self._cache = self._load_cache()
        self._tasks: dict[str, asyncio.Task[list[StoredMedia]]] = {}

    async def get_or_start(self, url: str, platform: str, user_id: int):
        cache_key = self._cache_key(url)
        if cache_key in self._cache:
            self._tasks.pop(cache_key, None)
            return "ready", self._cache[cache_key]

        task = self._tasks.get(cache_key)
        if task is None:
            task = asyncio.create_task(self._process(cache_key, url, platform, user_id))
            task.add_done_callback(self._log_background_failure)
            self._tasks[cache_key] = task

        try:
            results = await asyncio.wait_for(asyncio.shield(task), timeout=self.wait_seconds)
            return "ready", results
        except asyncio.TimeoutError:
            return "processing", []
        finally:
            if task.done():
                self._tasks.pop(cache_key, None)

    async def _process(
        self,
        cache_key: str,
        url: str,
        platform: str,
        user_id: int,
    ) -> list[StoredMedia]:
        downloaded = await self._download(url, platform, user_id)
        stored: list[StoredMedia] = []
        try:
            for media in downloaded:
                stored.append(await self._upload(media))
        finally:
            self._cleanup_downloads(downloaded)

        if not stored:
            raise RuntimeError("No downloadable media was found at this URL.")
        self._cache[cache_key] = stored
        self._save_cache()
        return stored

    async def _download(self, url: str, platform: str, user_id: int) -> list[DownloadedMedia]:
        if platform == "TikTok" and "/photo/" in url:
            result = await get_post(url)
            if not result:
                raise RuntimeError("TikTok did not return slideshow media.")
            media = [
                DownloadedMedia("photo", path, "TikTok photo")
                for path in result.get("images", [])
                if path
            ]
            audio_path = result.get("audio")
            if audio_path:
                media.append(DownloadedMedia("audio", audio_path, "TikTok audio"))
            return media

        return await asyncio.to_thread(self._download_sync, url, platform, user_id)

    def _download_sync(self, url: str, platform: str, user_id: int) -> list[DownloadedMedia]:
        request_id = uuid.uuid4().hex[:8]
        request_dir = Path(self.temp_directory) / f"inline_{user_id}_{request_id}"
        request_dir.mkdir(parents=True, exist_ok=True)

        try:
            return self._download_sync_into(request_dir, url, platform, user_id, request_id)
        except Exception:
            shutil.rmtree(request_dir, ignore_errors=True)
            raise

    def _download_sync_into(
        self,
        request_dir: Path,
        url: str,
        platform: str,
        user_id: int,
        request_id: str,
    ) -> list[DownloadedMedia]:

        if platform == "X":
            from pinchana_twitter import download_x_post_assets

            result = download_x_post_assets(url, str(request_dir), user_id, request_id)
            return [
                DownloadedMedia(item["media_type"], item["path"], "X media")
                for item in result.get("files", [])
            ]

        output_template = str(request_dir / "media.%(ext)s")
        options = {
            "outtmpl": output_template,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
        }
        if platform == "YouTube":
            configure_youtube_download(options)
        elif platform == "Instagram":
            configure_instagram_download(options)
        elif platform == "TikTok":
            configure_tiktok_download(options)

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        downloaded = []
        for path in request_dir.iterdir():
            if path.is_file() and path.suffix.lower() not in {".part", ".ytdl", ".json"}:
                downloaded.append(
                    DownloadedMedia(self._media_kind(path), str(path), f"{platform} media")
                )
        return downloaded

    async def _upload(self, media: DownloadedMedia) -> StoredMedia:
        upload = FSInputFile(media.path)
        if media.kind == "photo":
            message = await self.bot.send_photo(self.storage_chat_id, upload)
            return StoredMedia("photo", message.photo[-1].file_id, media.title)
        if media.kind == "audio":
            message = await self.bot.send_audio(self.storage_chat_id, upload, title=media.title)
            return StoredMedia("audio", message.audio.file_id, media.title)
        if media.kind == "video":
            try:
                message = await self.bot.send_video(self.storage_chat_id, upload)
                return StoredMedia("video", message.video.file_id, media.title)
            except Exception:
                logging.exception("Video upload failed; retrying as a document")

        message = await self.bot.send_document(self.storage_chat_id, FSInputFile(media.path))
        return StoredMedia("document", message.document.file_id, media.title)

    def build_results(self, media: list[StoredMedia], url: str):
        results = []
        for index, item in enumerate(media[:50]):
            result_id = hashlib.sha256(f"{item.file_id}:{index}".encode()).hexdigest()[:32]
            caption = url if index == 0 else None
            if item.kind == "video":
                result = InlineQueryResultCachedVideo(
                    id=result_id,
                    video_file_id=item.file_id,
                    title=item.title,
                    caption=caption,
                )
            elif item.kind == "photo":
                result = InlineQueryResultCachedPhoto(
                    id=result_id,
                    photo_file_id=item.file_id,
                    title=item.title,
                    caption=caption,
                )
            elif item.kind == "audio":
                result = InlineQueryResultCachedAudio(
                    id=result_id,
                    audio_file_id=item.file_id,
                    caption=caption,
                )
            else:
                result = InlineQueryResultCachedDocument(
                    id=result_id,
                    document_file_id=item.file_id,
                    title=item.title,
                    caption=caption,
                )
            results.append(result)
        return results

    @staticmethod
    def _media_kind(path: Path) -> str:
        extension = path.suffix.lower()
        if extension in {".jpg", ".jpeg", ".png", ".webp"}:
            return "photo"
        if extension in {".mp3", ".m4a", ".ogg", ".wav", ".aac"}:
            return "audio"
        if extension in {".mp4", ".mov", ".mkv", ".webm"}:
            return "video"
        return "document"

    @staticmethod
    def _cleanup_downloads(downloaded: list[DownloadedMedia]):
        directories = set()
        for media in downloaded:
            path = Path(media.path)
            directories.add(path.parent)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logging.exception("Could not remove inline temporary file %s", path)
        for directory in directories:
            if directory.name.startswith("inline_"):
                shutil.rmtree(directory, ignore_errors=True)

    @staticmethod
    def _cache_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _load_cache(self) -> dict[str, list[StoredMedia]]:
        try:
            raw_cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            return {
                key: [StoredMedia(**item) for item in items]
                for key, items in raw_cache.items()
            }
        except FileNotFoundError:
            return {}
        except Exception:
            logging.exception("Could not load inline media cache")
            return {}

    def _save_cache(self):
        serialized = {
            key: [asdict(item) for item in items]
            for key, items in self._cache.items()
        }
        self.cache_file.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    @staticmethod
    def _log_background_failure(task: asyncio.Task):
        if task.cancelled():
            return
        try:
            error = task.exception()
            if error is not None:
                logging.error(
                    "Inline media processing failed",
                    exc_info=(type(error), error, error.__traceback__),
                )
        except Exception:
            logging.exception("Could not inspect inline media task")
