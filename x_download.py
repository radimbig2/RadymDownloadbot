import importlib.machinery
import importlib.util
import mimetypes
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request


class XDownloadError(Exception):
    pass


class XConfigurationError(XDownloadError):
    pass


class _CompatModuleLoader:
    def __init__(self, spec):
        self._spec = spec

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        module = importlib.util.module_from_spec(self._spec)
        sys.modules[fullname] = module
        self._spec.loader.exec_module(module)
        return module


def _ensure_snscrape_python313_compatibility():
    if hasattr(importlib.machinery.FileFinder, 'find_module'):
        return

    def _find_module(self, fullname, path=None):
        spec = self.find_spec(fullname)
        if spec is None or spec.loader is None:
            return None
        if hasattr(spec.loader, 'load_module'):
            return spec.loader
        return _CompatModuleLoader(spec)

    importlib.machinery.FileFinder.find_module = _find_module


def extract_x_post_id(url: str) -> str:
    match = re.search(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/[^/?#]+/status/(\d+)", url)
    if not match:
        raise XDownloadError("Could not extract the X post ID from the provided URL.")
    return match.group(1)


def _import_snscrape_twitter_module():
    _ensure_snscrape_python313_compatibility()
    try:
        import snscrape.modules.twitter as sntwitter
    except ImportError as error:
        raise XConfigurationError('snscrape is not installed. Run pip install -r requirements.txt.') from error
    return sntwitter


def _request_x_post(post_url: str):
    sntwitter = _import_snscrape_twitter_module()
    try:
        return next(sntwitter.TwitterTweetScraper(post_url).get_items())
    except StopIteration as error:
        raise XDownloadError('Could not fetch the X post.') from error
    except Exception as error:
        raise XDownloadError(f'Failed to fetch the X post: {error}') from error


def _get_attr(media, *names):
    for name in names:
        if hasattr(media, name):
            value = getattr(media, name)
            if value:
                return value
    return None


def _resolve_variant_url(variants) -> str | None:
    if not variants:
        return None

    normalized_variants = []
    for variant in variants:
        if isinstance(variant, dict):
            normalized_variants.append(variant)
        elif hasattr(variant, '__dict__'):
            normalized_variants.append(vars(variant))

    direct_mp4 = [
        variant for variant in normalized_variants
        if variant.get('url') and str(variant.get('contentType') or variant.get('content_type') or '').lower() == 'video/mp4'
    ]
    if direct_mp4:
        return max(direct_mp4, key=lambda item: item.get('bitrate') or item.get('bit_rate') or 0).get('url')

    for variant in normalized_variants:
        if variant.get('url'):
            return variant['url']
    return None


def _resolve_photo_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query['name'] = ['orig']
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))


def _extract_media_entries(tweet) -> list[dict]:
    entries = []
    for media in getattr(tweet, 'media', []) or []:
        media_class_name = media.__class__.__name__.lower()

        photo_url = _get_attr(media, 'fullUrl', 'url')
        if 'photo' in media_class_name and photo_url:
            entries.append({'media_type': 'photo', 'url': _resolve_photo_url(photo_url)})
            continue

        if 'video' in media_class_name or 'gif' in media_class_name:
            video_url = _resolve_variant_url(_get_attr(media, 'variants'))
            if not video_url:
                video_url = _get_attr(media, 'thumbnailUrl', 'url')
            if video_url:
                entries.append({'media_type': 'video', 'url': video_url})

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
    extract_x_post_id(post_url)
    tweet = _request_x_post(post_url)
    author = getattr(tweet, 'user', None)
    author_username = getattr(author, 'username', None)

    downloaded_files = []
    for index, media_entry in enumerate(_extract_media_entries(tweet), start=1):
        base_path = os.path.join(temp_directory, f'x_{user_id}_{request_id}_{index}')
        file_path = _download_file(media_entry['url'], base_path)
        downloaded_files.append({'path': file_path, 'media_type': media_entry['media_type']})

    return {
        'text': (getattr(tweet, 'content', None) or getattr(tweet, 'rawContent', None) or '').strip(),
        'author_username': author_username,
        'files': downloaded_files,
    }