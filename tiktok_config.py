import base64
import io
import logging
import os


def get_tiktok_settings() -> dict:
    return {
        "cookies": os.getenv("TIKTOK_COOKIES"),
        "cookies_base64": os.getenv("TIKTOK_COOKIES_BASE64"),
        "cookies_file": os.getenv("TIKTOK_COOKIES_FILE"),
    }


def load_tiktok_cookie_text() -> str | None:
    settings = get_tiktok_settings()

    if settings["cookies_base64"]:
        try:
            cookie_text = base64.b64decode(
                settings["cookies_base64"], validate=True
            ).decode("utf-8")
        except Exception as exc:
            raise ValueError(
                "Invalid TIKTOK_COOKIES_BASE64 value. "
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


def configure_tiktok_download(ytdlp_options: dict) -> None:
    cookie_text = load_tiktok_cookie_text()
    if cookie_text:
        ytdlp_options["cookiefile"] = io.StringIO(cookie_text)
        return

    cookies_file = get_tiktok_settings()["cookies_file"]
    if cookies_file:
        cookie_path = os.path.abspath(os.path.expanduser(cookies_file))
        if not os.path.isfile(cookie_path):
            raise ValueError(f"TikTok cookies file was not found: {cookie_path}")
        ytdlp_options["cookiefile"] = cookie_path


def log_tiktok_startup_status() -> None:
    settings = get_tiktok_settings()
    logging.info(
        "TikTok cookies configured: %s",
        bool(
            settings["cookies_base64"]
            or settings["cookies"]
            or settings["cookies_file"]
        ),
    )


def is_tiktok_auth_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return any(
        marker in error_text
        for marker in (
            "login required",
            "login_required",
            "age-restricted",
            "age restricted",
            "cookies are needed",
            "fresh cookies",
            "unable to extract webpage video data",
        )
    )


def get_tiktok_auth_guidance() -> str:
    settings = get_tiktok_settings()
    configured = bool(
        settings["cookies_base64"]
        or settings["cookies"]
        or settings["cookies_file"]
    )
    if configured:
        return (
            "❌ TikTok rejected the configured session. Sign in to an age-verified "
            "TikTok account, export fresh cookies, and restart the bot."
        )
    return (
        "❌ This TikTok requires a logged-in, age-verified session. Export TikTok "
        "cookies and configure TIKTOK_COOKIES_FILE or TIKTOK_COOKIES_BASE64."
    )
