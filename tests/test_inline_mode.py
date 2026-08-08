from access_control import AccessControl
from inline_mode import InlineMediaService, StoredMedia, extract_supported_url


def test_extract_supported_url_from_inline_query() -> None:
    assert extract_supported_url("download https://www.instagram.com/reel/example/?x=1") == (
        "https://www.instagram.com/reel/example/?x=1",
        "Instagram",
    )


def test_extract_supported_url_ignores_unsupported_sites() -> None:
    assert extract_supported_url("https://example.com/video") is None


def test_extract_supported_url_strips_message_punctuation() -> None:
    assert extract_supported_url("(https://youtu.be/example).") == (
        "https://youtu.be/example",
        "YouTube",
    )


def test_build_cached_video_result() -> None:
    service = object.__new__(InlineMediaService)
    results = service.build_results(
        [StoredMedia(kind="video", file_id="telegram-file-id", title="TikTok media")],
        "https://www.tiktok.com/@user/video/123",
    )

    assert len(results) == 1
    assert results[0].video_file_id == "telegram-file-id"
    assert results[0].title == "TikTok media"


def test_inline_access_accepts_whitelisted_users_and_bot_admins(tmp_path) -> None:
    access = AccessControl(str(tmp_path))
    access.whitelisted_chat_ids = [100]
    access.admin_ids = [200]

    assert access.is_allowed_user(100)
    assert access.is_allowed_user(200)
    assert not access.is_allowed_user(300)
