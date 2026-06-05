"""Manual URL connector for user-provided public image URLs."""
from urllib.parse import urlparse

from .base import BaseConnector, RemoteAsset, SearchRequest


class ManualUrlConnector(BaseConnector):
    """Download a single user-provided public URL after compliance checks."""

    connector_type = "manual_url"
    display_name = "URL manual autorizada"

    def search(self, request: SearchRequest, platform) -> list[RemoteAsset]:
        parsed = urlparse(request.query)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return []
        title = parsed.path.rsplit("/", 1)[-1] or "manual-download"
        return [
            RemoteAsset(
                title=title,
                download_url=request.query,
                source_url=request.query,
                author="URL manual",
                license_name="Confirmada por el usuario" if not platform.strict_license_mode else "Requiere verificación",
                license_known=not platform.strict_license_mode,
                allows_download=True,
                is_nsfw=platform.allows_nsfw,
            )
        ]
