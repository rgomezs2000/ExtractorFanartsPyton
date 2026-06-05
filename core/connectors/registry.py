"""Connector registry."""
from .base import BaseConnector
from .manual_url import ManualUrlConnector

CONNECTORS: dict[str, type[BaseConnector]] = {
    ManualUrlConnector.connector_type: ManualUrlConnector,
}

PLACEHOLDER_CONNECTORS = {
    "booru_api": "Conector preparado para API pública booru; requiere implementación específica de términos y endpoints.",
    "mastodon_api": "Conector preparado para API Mastodon; debe respetar privacidad de publicaciones.",
    "tumblr_api": "Conector preparado para API Tumblr oficial.",
    "deviantart_api": "Conector preparado para API DeviantArt oficial.",
    "discord_bot": "Conector preparado únicamente para bots autorizados, nunca self-bots.",
    "civitai_api": "Conector preparado para Civitai API con licencias y filtros sensibles.",
    "wiki_api": "Conector preparado para APIs tipo MediaWiki con revisión de licencias.",
}


def get_connector(connector_type: str) -> BaseConnector:
    """Return a connector instance or raise a clear error for unsupported types."""
    connector_class = CONNECTORS.get(connector_type)
    if connector_class is None:
        message = PLACEHOLDER_CONNECTORS.get(connector_type, "Conector no registrado.")
        raise NotImplementedError(message)
    return connector_class()
