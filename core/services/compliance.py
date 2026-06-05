"""Compliance and safety validators for download requests."""
from dataclasses import dataclass
from datetime import date
from typing import Iterable


class ComplianceViolation(ValueError):
    """Raised when a request violates project safety or legal rules."""


@dataclass(frozen=True)
class ComplianceResult:
    """Result of compliance validation."""

    allowed: bool
    messages: list[str]


SENSITIVE_KEYWORDS = {"nsfw", "adult", "explicit", "rule34", "r34", "sensitive"}


def calculate_age(birth_date: date, today: date | None = None) -> int:
    """Calculate age in complete years."""
    current = today or date.today()
    age = current.year - birth_date.year
    if (current.month, current.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def validate_nsfw_access(nsfw_enabled: bool, birth_date: date | None, today: date | None = None) -> ComplianceResult:
    """Validate whether the user may enable NSFW connectors."""
    if not nsfw_enabled:
        return ComplianceResult(True, ["NSFW deshabilitado: se omitirán resultados sensibles."])
    if birth_date is None:
        raise ComplianceViolation("Debes indicar tu fecha de nacimiento para habilitar contenido NSFW.")
    age = calculate_age(birth_date, today)
    if age < 18:
        raise ComplianceViolation("No puedes habilitar contenido NSFW porque eres menor de edad. Debes ser mayor de 18 años para continuar.")
    return ComplianceResult(True, ["Validación de edad correcta para contenido NSFW."])


def query_mentions_sensitive_content(query: str, categories: Iterable[str] = ()) -> bool:
    """Detect obvious sensitive terms in user search fields."""
    haystack = " ".join([query, *categories]).lower()
    return any(keyword in haystack for keyword in SENSITIVE_KEYWORDS)


def validate_public_download_policy(
    *,
    terms_accepted: bool,
    is_private: bool = False,
    is_paid: bool = False,
    is_exclusive: bool = False,
    license_known: bool = True,
    allows_download: bool = True,
    strict_license_mode: bool = True,
) -> ComplianceResult:
    """Validate legal metadata before allowing a result to be downloaded."""
    errors: list[str] = []
    if not terms_accepted:
        errors.append("Términos de servicio no aceptados para esta plataforma.")
    if is_private:
        errors.append("Contenido privado: descarga bloqueada.")
    if is_paid:
        errors.append("Contenido de pago o tras paywall: descarga bloqueada.")
    if is_exclusive:
        errors.append("Contenido exclusivo o de membresía: descarga bloqueada.")
    if not allows_download:
        errors.append("La fuente no permite descarga de este recurso.")
    if strict_license_mode and not license_known:
        errors.append("Licencia no clara en modo estricto: descarga bloqueada.")
    if errors:
        raise ComplianceViolation(" ".join(errors))
    return ComplianceResult(True, ["Política pública y licencia validadas."])
