"""Connector interfaces and metadata structures."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SearchRequest:
    """User search request after UI validation."""

    category: str
    query: str
    source: str
    download_dir: Path
    nsfw_enabled: bool = False
    birth_date: str = ""


@dataclass(frozen=True)
class RemoteAsset:
    """A remote image candidate plus legal and technical metadata."""

    title: str
    download_url: str
    source_url: str
    author: str = "Desconocido"
    license_name: str = "Desconocida"
    license_known: bool = False
    is_private: bool = False
    is_paid: bool = False
    is_exclusive: bool = False
    allows_download: bool = True
    is_nsfw: bool = False
    expected_hash: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class BaseConnector:
    """Base class for platform connectors."""

    connector_type = "base"
    display_name = "Base"

    def search(self, request: SearchRequest, platform) -> list[RemoteAsset]:
        """Return candidate assets for the request."""
        raise NotImplementedError
