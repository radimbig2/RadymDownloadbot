import base64
import io

import pytest

from instagram_config import (
    configure_instagram_download,
    get_instagram_auth_guidance,
    is_instagram_auth_error,
    load_instagram_cookie_text,
)


COOKIE_TEXT = (
    "# Netscape HTTP Cookie File\n"
    ".instagram.com\tTRUE\t/\tTRUE\t0\tsessionid\ttest-session"
)


def test_configure_instagram_download_uses_base64_cookie_env(monkeypatch) -> None:
    encoded = base64.b64encode(COOKIE_TEXT.encode()).decode()
    monkeypatch.setenv("INSTAGRAM_COOKIES_BASE64", encoded)
    monkeypatch.delenv("INSTAGRAM_COOKIES", raising=False)
    options = {}

    configure_instagram_download(options)

    assert isinstance(options["cookiefile"], io.StringIO)
    assert options["cookiefile"].getvalue() == COOKIE_TEXT


def test_raw_instagram_cookies_are_supported(monkeypatch) -> None:
    monkeypatch.delenv("INSTAGRAM_COOKIES_BASE64", raising=False)
    monkeypatch.setenv("INSTAGRAM_COOKIES", COOKIE_TEXT.replace("\n", "\\n"))

    assert load_instagram_cookie_text() == COOKIE_TEXT


def test_configure_instagram_download_uses_cookie_file(monkeypatch) -> None:
    cookie_file = "test-instagram-cookies.txt"
    monkeypatch.delenv("INSTAGRAM_COOKIES_BASE64", raising=False)
    monkeypatch.delenv("INSTAGRAM_COOKIES", raising=False)
    monkeypatch.setenv("INSTAGRAM_COOKIES_FILE", cookie_file)
    monkeypatch.setattr("instagram_config.os.path.isfile", lambda path: True)
    options = {}

    configure_instagram_download(options)

    assert options["cookiefile"].endswith(cookie_file)


def test_invalid_base64_has_actionable_error(monkeypatch) -> None:
    monkeypatch.setenv("INSTAGRAM_COOKIES_BASE64", "not base64!")

    with pytest.raises(ValueError, match="INSTAGRAM_COOKIES_BASE64"):
        load_instagram_cookie_text()


def test_empty_media_response_is_treated_as_auth_error(monkeypatch) -> None:
    monkeypatch.delenv("INSTAGRAM_COOKIES_BASE64", raising=False)
    monkeypatch.delenv("INSTAGRAM_COOKIES", raising=False)
    error = RuntimeError("Instagram sent an empty media response")

    assert is_instagram_auth_error(error)
    assert "INSTAGRAM_COOKIES_BASE64" in get_instagram_auth_guidance()
