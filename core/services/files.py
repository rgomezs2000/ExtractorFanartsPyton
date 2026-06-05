"""File integrity and safe-save helpers."""
import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path

IMAGE_SIGNATURES = {
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "gif": [b"GIF87a", b"GIF89a"],
    "webp": [b"RIFF"],
}


@dataclass(frozen=True)
class FileDecision:
    """Decision for a target file before writing."""

    should_download: bool
    reason: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hash of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_supported_image(path: Path, allowed_extensions: list[str]) -> bool:
    """Validate image extension and magic bytes without external dependencies."""
    extension = path.suffix.lower().lstrip(".")
    if extension not in allowed_extensions:
        return False
    signatures = IMAGE_SIGNATURES.get(extension, [])
    with path.open("rb") as handle:
        header = handle.read(16)
    if extension == "webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    return any(header.startswith(signature) for signature in signatures)


def target_file_decision(path: Path, allowed_extensions: list[str], expected_hash: str = "") -> FileDecision:
    """Decide whether an existing target should be skipped or overwritten."""
    if not path.exists():
        return FileDecision(True, "El archivo no existe; se guardará.")
    if not path.is_file():
        return FileDecision(False, "La ruta destino existe pero no es un archivo.")
    if not is_supported_image(path, allowed_extensions):
        return FileDecision(True, "El archivo existente está corrupto o no es una imagen compatible; se sobrescribirá.")
    if expected_hash and sha256_file(path) != expected_hash:
        return FileDecision(True, "El hash local difiere del remoto; se sobrescribirá.")
    return FileDecision(False, "El archivo existente está íntegro; se saltará.")


def guess_extension_from_content_type(content_type: str, fallback: str = "jpg") -> str:
    """Infer an image extension from a Content-Type header."""
    clean_type = content_type.split(";", 1)[0].strip().lower()
    extension = mimetypes.guess_extension(clean_type) or f".{fallback}"
    normalized = extension.lstrip(".")
    if normalized == "jpe":
        return "jpg"
    return normalized


def safe_filename(value: str, default: str = "download") -> str:
    """Return a filesystem-safe filename stem."""
    allowed = [character if character.isalnum() or character in "._-" else "_" for character in value.strip()]
    filename = "".join(allowed).strip("._")
    return filename or default
