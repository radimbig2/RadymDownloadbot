from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yt_dlp

from pinchana_twitter import download_x_post_assets


TIKTOK_URL = "https://www.tiktok.com/@mynameisntsico/video/7627575936950619406"
INSTAGRAM_URL = "https://www.instagram.com/p/DWnQ17fDuwc/"
X_URL = "https://x.com/Mericamemed/status/2062957626108084449?s=20"


def _download_with_ytdlp(url: str, temp_dir: Path, prefix: str) -> Path:
    output_path = temp_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.%(ext)s"
    options = {
        "outtmpl": str(output_path),
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noprogress": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    base_path = Path(str(output_path).replace(".%(ext)s", ""))
    candidates = [base_path.with_suffix(ext) for ext in (".mp4", ".webm", ".mkv")]
    existing = [path for path in candidates if path.exists()]
    assert existing, f"No downloaded video file found for {url}"
    return existing[0]


def _assert_downloaded_video(path: Path) -> None:
    assert path.exists(), f"Downloaded file is missing: {path}"
    assert path.is_file(), f"Downloaded path is not a file: {path}"
    assert path.stat().st_size > 0, f"Downloaded file is empty: {path}"


@pytest.mark.media_download
def test_tiktok_video_downloads(tmp_path: Path) -> None:
    video_path = _download_with_ytdlp(TIKTOK_URL, tmp_path, "tiktok")
    _assert_downloaded_video(video_path)


@pytest.mark.media_download
def test_instagram_video_downloads(tmp_path: Path) -> None:
    video_path = _download_with_ytdlp(INSTAGRAM_URL, tmp_path, "instagram")
    _assert_downloaded_video(video_path)


@pytest.mark.media_download
def test_x_video_downloads(tmp_path: Path) -> None:
    result = download_x_post_assets(
        post_url=X_URL,
        temp_directory=str(tmp_path),
        user_id=1,
        request_id=uuid.uuid4().hex[:8],
    )

    files = result.get("files") or []
    video_files = [item for item in files if item.get("media_type") == "video"]
    assert video_files, f"No X video media was downloaded. Result: {result}"

    for item in video_files:
        _assert_downloaded_video(Path(item["path"]))
