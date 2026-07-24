import pytest

from encode_cookies_env import filter_cookie_text


COOKIE_EXPORT = (
    "# Netscape HTTP Cookie File\n"
    ".instagram.com\tTRUE\t/\tTRUE\t0\tsessionid\tinstagram-secret\n"
    ".tiktok.com\tTRUE\t/\tTRUE\t0\tsessionid\ttiktok-secret\n"
    ".example.com\tTRUE\t/\tTRUE\t0\tsessionid\tunrelated-secret"
)


def test_filter_cookie_text_keeps_only_requested_domain() -> None:
    filtered = filter_cookie_text(COOKIE_EXPORT, ("instagram.com",))

    assert "instagram-secret" in filtered
    assert "tiktok-secret" not in filtered
    assert "unrelated-secret" not in filtered


def test_filter_cookie_text_accepts_http_only_cookie() -> None:
    cookie_text = (
        "# Netscape HTTP Cookie File\n"
        "#HttpOnly_.instagram.com\tTRUE\t/\tTRUE\t0\tsessionid\tsecret"
    )

    assert "sessionid" in filter_cookie_text(cookie_text, ("instagram.com",))


def test_filter_cookie_text_rejects_missing_platform() -> None:
    with pytest.raises(ValueError, match="No cookies"):
        filter_cookie_text(COOKIE_EXPORT, ("youtube.com", "google.com"))
