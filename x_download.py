"""Compatibility shim for the package-based X/Twitter downloader."""

from pinchana_twitter import (
    XConfigurationError,
    XDownloadError,
    download_x_post_assets,
    extract_x_post_id,
)

__all__ = [
    "XConfigurationError",
    "XDownloadError",
    "download_x_post_assets",
    "extract_x_post_id",
]
