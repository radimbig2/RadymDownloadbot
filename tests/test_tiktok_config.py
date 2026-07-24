import base64
import io

import pytest

from tiktok_config import (
    configure_tiktok_download,
    get_tiktok_auth_guidance,
    is_tiktok_auth_error,
    load_tiktok_cookie_text,
)


COOKIE_TEXT = (
    "# Netscape HTTP Cookie File\n"
    ".tiktok.com\tTRUE\t/\tTRUE\t0\tsessionid\ttest-session"
)


def test_configure_tiktok_download_uses_base64_cookie_env(monkeypatch) -> None:
    encoded = base64.b64encode(COOKIE_TEXT.encode()).decode()
    monkeypatch.setenv("TIKTOK_COOKIES_BASE64", encoded)
    monkeypatch.delenv("TIKTOK_COOKIES", raising=False)
    options = {}

    configure_tiktok_download(options)

    assert isinstance(options["cookiefile"], io.StringIO)
    assert options["cookiefile"].getvalue() == COOKIE_TEXT


def test_configure_tiktok_download_uses_cookie_file(monkeypatch) -> None:
    cookie_file = "test-tiktok-cookies.txt"
    monkeypatch.delenv("TIKTOK_COOKIES_BASE64", raising=False)
    monkeypatch.delenv("TIKTOK_COOKIES", raising=False)
    monkeypatch.setenv("TIKTOK_COOKIES_FILE", cookie_file)
    monkeypatch.setattr("tiktok_config.os.path.isfile", lambda path: True)
    options = {}

    configure_tiktok_download(options)

    assert options["cookiefile"].endswith(cookie_file)


def test_raw_tiktok_cookies_are_supported(monkeypatch) -> None:
    monkeypatch.delenv("TIKTOK_COOKIES_BASE64", raising=False)
    monkeypatch.setenv("TIKTOK_COOKIES", COOKIE_TEXT.replace("\n", "\\n"))

    assert load_tiktok_cookie_text() == COOKIE_TEXT


def test_invalid_tiktok_base64_has_actionable_error(monkeypatch) -> None:
    monkeypatch.setenv("TIKTOK_COOKIES_BASE64", "not base64!")

    with pytest.raises(ValueError, match="TIKTOK_COOKIES_BASE64"):
        load_tiktok_cookie_text()


def test_age_restriction_is_treated_as_auth_error(monkeypatch) -> None:
    monkeypatch.delenv("TIKTOK_COOKIES_BASE64", raising=False)
    monkeypatch.delenv("TIKTOK_COOKIES", raising=False)
    monkeypatch.delenv("TIKTOK_COOKIES_FILE", raising=False)
    error = RuntimeError("This video is age-restricted; cookies are needed")

    assert is_tiktok_auth_error(error)
    assert "TIKTOK_COOKIES_FILE" in get_tiktok_auth_guidance()
