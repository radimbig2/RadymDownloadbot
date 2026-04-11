import base64
import io
import logging
import os


def _get_float_env(var_name: str, default: float | None = None) -> float | None:
    raw_value = os.getenv(var_name)
    if raw_value in (None, ''):
        return default
    try:
        return float(raw_value)
    except ValueError:
        logging.warning("Invalid float value for %s: %s", var_name, raw_value)
        return default


def _get_int_env(var_name: str, default: int) -> int:
    raw_value = os.getenv(var_name)
    if raw_value in (None, ''):
        return default
    try:
        return int(raw_value)
    except ValueError:
        logging.warning("Invalid integer value for %s: %s", var_name, raw_value)
        return default


def _mask_secret(value: str | None, visible_chars: int = 6) -> str:
    if not value:
        return 'missing'
    if len(value) <= visible_chars * 2:
        return value
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def get_youtube_settings() -> dict:
    return {
        'cookies': os.getenv('YTDLP_COOKIES'),
        'cookies_base64': os.getenv('YTDLP_COOKIES_BASE64'),
        'impersonate': os.getenv('YTDLP_IMPERSONATE'),
        'sleep_requests': _get_float_env('YTDLP_SLEEP_REQUESTS', 1.0),
        'sleep_interval': _get_float_env('YTDLP_SLEEP_INTERVAL', 2.0),
        'max_sleep_interval': _get_float_env('YTDLP_MAX_SLEEP_INTERVAL', 5.0),
        'max_duration_seconds': _get_int_env('YOUTUBE_MAX_DURATION_SECONDS', 300),
    }


def load_ytdlp_cookie_text() -> str | None:
    settings = get_youtube_settings()
    cookie_text = None

    if settings['cookies_base64']:
        try:
            cookie_text = base64.b64decode(settings['cookies_base64']).decode('utf-8')
        except Exception as exc:
            raise ValueError('Invalid YTDLP_COOKIES_BASE64 value. Expected base64-encoded Netscape cookies.') from exc
    elif settings['cookies']:
        cookie_text = settings['cookies']

    if not cookie_text:
        return None

    return (
        cookie_text
        .replace('\r\n', '\n')
        .replace('\r', '\n')
        .replace('\\r\\n', '\n')
        .replace('\\n', '\n')
        .strip()
    )


def extract_cookie_names(cookie_text: str | None) -> list[str]:
    if not cookie_text:
        return []

    cookie_names: list[str] = []
    for line in cookie_text.split('\n'):
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith('#') and not stripped_line.startswith('#HttpOnly_'):
            continue

        parts = stripped_line.split('\t')
        if len(parts) >= 7:
            cookie_names.append(parts[5])

    return cookie_names


def log_youtube_startup_status():
    settings = get_youtube_settings()

    logging.info(
        'YTDLP_COOKIES_BASE64 status: present=%s length=%s preview=%s',
        bool(settings['cookies_base64']),
        len(settings['cookies_base64']) if settings['cookies_base64'] else 0,
        _mask_secret(settings['cookies_base64']),
    )

    cookie_text = load_ytdlp_cookie_text()
    cookie_names = extract_cookie_names(cookie_text)
    unique_names = sorted(set(cookie_names))
    expected_auth_names = {
        'SID', 'HSID', 'SSID', 'APISID', 'SAPISID',
        '__Secure-1PAPISID', '__Secure-3PAPISID', 'LOGIN_INFO',
    }
    present_auth_names = sorted(expected_auth_names.intersection(unique_names))

    logging.info(
        'YouTube cookie diagnostics: total=%s names=%s auth_related=%s',
        len(cookie_names),
        ','.join(unique_names[:12]) if unique_names else 'none',
        ','.join(present_auth_names) if present_auth_names else 'none',
    )

    if cookie_names and not present_auth_names:
        logging.warning(
            'YouTube cookies were loaded from env, but no auth cookies were found. '
            'The export is likely incomplete or taken from a non-authenticated session.'
        )


def configure_youtube_download(ytdlp_options: dict):
    settings = get_youtube_settings()
    ytdlp_options['format'] = (
        'bv*[height<=1080][ext=mp4]+ba[ext=m4a]'
        '/bv*[height<=1080]+ba'
        '/b[height<=1080]'
        '/bv*+ba/b'
    )
    ytdlp_options['match_filter'] = youtube_duration_filter
    ytdlp_options['merge_output_format'] = 'mp4'

    cookie_text = load_ytdlp_cookie_text()
    if cookie_text:
        ytdlp_options['cookiefile'] = io.StringIO(cookie_text)

    if settings['impersonate']:
        ytdlp_options['impersonate'] = settings['impersonate'].strip()
    if settings['sleep_requests'] is not None:
        ytdlp_options['sleep_interval_requests'] = settings['sleep_requests']
    if settings['sleep_interval'] is not None:
        ytdlp_options['sleep_interval'] = settings['sleep_interval']
    if settings['max_sleep_interval'] is not None:
        ytdlp_options['max_sleep_interval'] = settings['max_sleep_interval']


def is_youtube_bot_check_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        'sign in to confirm you\'re not a bot' in error_text
        or 'use --cookies-from-browser or --cookies' in error_text
    )


def get_youtube_auth_guidance() -> str:
    settings = get_youtube_settings()
    if settings['cookies_base64'] or settings['cookies']:
        return (
            '❌ YouTube cookies were loaded, but they look invalid, incomplete, or expired. '
            'Re-export fresh cookies from a signed-in YouTube session and update the env.'
        )
    return (
        '❌ YouTube now requires authenticated cookies for this link. '
        'Add YTDLP_COOKIES_BASE64 or YTDLP_COOKIES to .env, then restart the bot.'
    )


def is_youtube_duration_limit_error(error: Exception) -> bool:
    return 'maximum duration' in str(error).lower()


def get_youtube_duration_limit_message() -> str:
    max_duration_seconds = get_youtube_settings()['max_duration_seconds']
    if max_duration_seconds % 60 == 0:
        max_minutes = max_duration_seconds // 60
        return f'❌ YouTube videos longer than {max_minutes} minutes are not supported.'
    return f'❌ YouTube videos longer than {max_duration_seconds} seconds are not supported.'


def youtube_duration_filter(info_dict, *, incomplete=False):
    duration = info_dict.get('duration')
    if incomplete or duration is None:
        return None

    max_duration_seconds = get_youtube_settings()['max_duration_seconds']
    if duration > max_duration_seconds:
        return f'Maximum duration: {max_duration_seconds}'
    return None