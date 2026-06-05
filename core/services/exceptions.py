"""Application exception classes and user-facing messages."""


class ExtractorError(Exception):
    """Base application error."""


class NetworkError(ExtractorError):
    """Network connectivity, DNS, SSL, timeout, proxy, or VPN error."""


class PermissionError(ExtractorError):
    """Platform, token, bot, or filesystem permission error."""


class RegionalBlockError(ExtractorError):
    """Regional restriction detected; the app must not bypass it automatically."""


class TermsError(ExtractorError):
    """Terms of service or license validation failed."""


class CaptchaRequiredError(ExtractorError):
    """Manual captcha validation is required to continue."""


class FileIntegrityError(ExtractorError):
    """Downloaded file is corrupt or does not match integrity checks."""


HTTP_ERROR_MESSAGES = {
    400: "Solicitud inválida.",
    401: "No autorizado: revisa token, API key o sesión bot permitida.",
    403: "Acceso prohibido: posible falta de permisos, términos o bloqueo regional.",
    404: "Recurso no encontrado.",
    408: "Tiempo de espera agotado.",
    409: "Conflicto de estado en la plataforma.",
    410: "Recurso eliminado.",
    429: "Rate limit alcanzado: se debe pausar antes de continuar.",
    451: "No disponible por razones legales o restricción regional.",
    500: "Error interno de la plataforma.",
    502: "Gateway inválido en la plataforma.",
    503: "Servicio no disponible.",
    504: "Gateway timeout en la plataforma.",
}


def message_for_http_status(status_code: int) -> str:
    """Return a Spanish message for common HTTP/API failures."""
    return HTTP_ERROR_MESSAGES.get(status_code, f"Error HTTP no clasificado: {status_code}.")
