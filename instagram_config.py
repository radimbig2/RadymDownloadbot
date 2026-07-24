import base64
import io
import logging
import os


def get_instagram_settings() -> dict:
    return {
        "cookies": os.getenv("INSTAGRAM_COOKIES"),
        "cookies_base64": os.getenv("INSTAGRAM_COOKIES_BASE64"),
        "cookies_file": os.getenv("INSTAGRAM_COOKIES_FILE"),
    }


def load_instagram_cookie_text() -> str | None:
    settings = get_instagram_settings()

    if settings["cookies_base64"]:
        try:
            cookie_text = base64.b64decode(
                settings["cookies_base64"], validate=True
            ).decode("utf-8")
        except Exception as exc:
            raise ValueError(
                "Invalid INSTAGRAM_COOKIES_BASE64 value. "
                "Expected base64-encoded Netscape cookies."
            ) from exc
    else:
        cookie_text = settings["cookies"]

    if not cookie_text:
        return None

    return (
        cookie_text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .strip()
    )


def configure_instagram_download(ytdlp_options: dict) -> None:
    cookie_text = load_instagram_cookie_text()
    if cookie_text:
        # A file-like object avoids writing authentication cookies to disk.
        ytdlp_options["cookiefile"] = io.StringIO(cookie_text)
    elif get_instagram_settings()["cookies_file"]:
        cookie_path = os.path.abspath(
            os.path.expanduser(get_instagram_settings()["cookies_file"])
        )
        if not os.path.isfile(cookie_path):
            raise ValueError(f"Instagram cookies file was not found: {cookie_path}")
        ytdlp_options["cookiefile"] = cookie_path


def log_instagram_startup_status() -> None:
    settings = get_instagram_settings()
    logging.info(
        "Instagram cookies configured: %s",
        bool(
            settings["cookies_base64"]
            or settings["cookies"]
            or settings["cookies_file"]
        ),
    )


def is_instagram_auth_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return any(
        marker in error_text
        for marker in (
            "instagram sent an empty media response",
            "login required",
            "login_required",
            "rate-limit reached",
            "use --cookies-from-browser or --cookies",
        )
    )


def get_instagram_auth_guidance() -> str:
    settings = get_instagram_settings()
    if (
        settings["cookies_base64"]
        or settings["cookies"]
        or settings["cookies_file"]
    ):
        return (
            "❌ Instagram rejected the configured session. Export fresh Instagram "
            "cookies from a logged-in browser, update INSTAGRAM_COOKIES_BASE64 "
            "(or INSTAGRAM_COOKIES), and restart the bot."
        )
    return (
        "❌ Instagram requires a logged-in session for this reel. Export Instagram "
        "cookies in Netscape format, add them as INSTAGRAM_COOKIES_BASE64 "
        "(recommended) or INSTAGRAM_COOKIES, and restart the bot."
    )
