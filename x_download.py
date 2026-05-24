import mimetypes
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request


class XDownloadError(Exception):
    pass


class XConfigurationError(XDownloadError):
    pass


def extract_x_post_id(url: str) -> str:
    match = re.search(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/[^/?#]+/status/(\d+)", url)
    if not match:
        raise XDownloadError("Could not extract the X post ID from the provided URL.")
    return match.group(1)


def _normalize_sdk_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _normalize_sdk_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_sdk_value(item) for item in value]
    if hasattr(value, 'model_dump'):
        return _normalize_sdk_value(value.model_dump(exclude_none=True))
    if hasattr(value, 'dict'):
        return _normalize_sdk_value(value.dict(exclude_none=True))
    if hasattr(value, '__dict__'):
        return _normalize_sdk_value(
            {
                key: item
                for key, item in vars(value).items()
                if not key.startswith('_')
            }
        )
    return value


def _create_x_client():
    try:
        from xdk import Client
    except ImportError as error:
        raise XConfigurationError('The X SDK is not installed. Run pip install -r requirements.txt.') from error

    bearer_token = os.getenv('X_BEARER_TOKEN', '').strip()
    if bearer_token:
        return Client(bearer_token=urllib.parse.unquote(bearer_token))

    api_key = os.getenv('X_CONSUMER_KEY', '').strip()
    api_secret = os.getenv('X_SECRET_KEY', '').strip()
    access_token = os.getenv('X_ACCESS_TOKEN', '').strip()
    access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET', '').strip()

    if api_key and api_secret and access_token and access_token_secret:
        try:
            from xdk.oauth1_auth import OAuth1
        except ImportError as error:
            raise XConfigurationError('The X SDK OAuth support is not available. Reinstall the xdk package.') from error

        oauth1 = OAuth1(
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        return Client(auth=oauth1)

    raise XConfigurationError(
        'X credentials are missing. Set X_BEARER_TOKEN or the OAuth 1.0a set X_CONSUMER_KEY, X_SECRET_KEY, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET.'
    )


def _request_x_post(post_id: str) -> dict:
    client = _create_x_client()
    try:
        response = client.posts.get_by_id(
            id=post_id,
            tweet_fields=['attachments', 'author_id', 'text'],
            expansions=['attachments.media_keys', 'author_id'],
            media_fields=['alt_text', 'duration_ms', 'height', 'media_key', 'preview_image_url', 'type', 'url', 'variants', 'width'],
            user_fields=['name', 'username'],
        )
    except Exception as error:
        raise XDownloadError(f'X API request failed: {error}') from error

    payload = _normalize_sdk_value(response)
    if not isinstance(payload, dict):
        raise XDownloadError('X SDK returned an unexpected response payload.')
    return payload


def _resolve_photo_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query['name'] = ['orig']
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))


def _extract_media_entries(payload: dict) -> list[dict]:
    data = payload.get('data') or {}
    includes = payload.get('includes') or {}
    media_by_key = {media.get('media_key'): media for media in includes.get('media', [])}
    media_keys = data.get('attachments', {}).get('media_keys', [])

    entries = []
    for media_key in media_keys:
        media = media_by_key.get(media_key) or {}
        media_type = media.get('type')
        if media_type == 'photo' and media.get('url'):
            entries.append({'media_type': 'photo', 'url': _resolve_photo_url(media['url'])})
            continue

        if media_type in {'video', 'animated_gif'}:
            variants = media.get('variants') or []
            mp4_variants = [
                variant for variant in variants
                if variant.get('content_type') == 'video/mp4' and variant.get('url')
            ]
            if not mp4_variants:
                continue
            best_variant = max(mp4_variants, key=lambda item: item.get('bit_rate', 0))
            entries.append({'media_type': 'video', 'url': best_variant['url']})

    return entries


def _guess_extension(url: str, content_type: str | None) -> str:
    path = urllib.parse.urlparse(url).path
    extension = os.path.splitext(path)[1]
    if extension:
        return extension
    guessed = mimetypes.guess_extension(content_type or '')
    return guessed or '.bin'


def _download_file(url: str, target_path_without_ext: str) -> str:
    request = urllib.request.Request(url, headers={'User-Agent': 'RadymDownloadBot/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content_type = response.headers.get_content_type()
            file_path = target_path_without_ext + _guess_extension(url, content_type)
            with open(file_path, 'wb') as output_file:
                shutil.copyfileobj(response, output_file)
    except urllib.error.HTTPError as error:
        raise XDownloadError(f'Failed to download X media: HTTP {error.code}') from error
    except urllib.error.URLError as error:
        raise XDownloadError(f'Failed to download X media: {error.reason}') from error
    return file_path


def download_x_post_assets(post_url: str, temp_directory: str, user_id: int, request_id: str) -> dict:
    post_id = extract_x_post_id(post_url)
    payload = _request_x_post(post_id)
    data = payload.get('data') or {}
    includes = payload.get('includes') or {}
    users = includes.get('users') or []

    author_username = None
    author_id = data.get('author_id')
    if author_id:
        for user in users:
            if user.get('id') == author_id:
                author_username = user.get('username')
                break

    downloaded_files = []
    for index, media_entry in enumerate(_extract_media_entries(payload), start=1):
        base_path = os.path.join(temp_directory, f'x_{user_id}_{request_id}_{index}')
        file_path = _download_file(media_entry['url'], base_path)
        downloaded_files.append({'path': file_path, 'media_type': media_entry['media_type']})

    return {
        'text': (data.get('text') or '').strip(),
        'author_username': author_username,
        'files': downloaded_files,
    }