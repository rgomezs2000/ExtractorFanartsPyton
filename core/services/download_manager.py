"""In-memory background download orchestration for the desktop app."""
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests
from django.conf import settings

from core.connectors.base import SearchRequest
from core.connectors.registry import get_connector
from core.models import PlatformCredential
from core.services.compliance import (
    ComplianceViolation,
    query_mentions_sensitive_content,
    validate_nsfw_access,
    validate_public_download_policy,
)
from core.services.exceptions import (
    CaptchaRequiredError,
    ExtractorError,
    FileIntegrityError,
    NetworkError,
    RegionalBlockError,
    TermsError,
    message_for_http_status,
)
from core.services.files import guess_extension_from_content_type, is_supported_image, safe_filename, target_file_decision


@dataclass
class DownloadJob:
    """Mutable state for a background download job."""

    id: str
    status: str = "queued"
    logs: list[str] = field(default_factory=list)
    downloaded: int = 0
    skipped: int = 0
    errors: int = 0
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def log(self, level: str, message: str) -> None:
        self.logs.append(f"[{level}] {message}")


class DownloadManager:
    """Small process-local job manager for the desktop application."""

    def __init__(self) -> None:
        self.jobs: dict[str, DownloadJob] = {}
        self._lock = threading.Lock()

    def start(self, payload: dict) -> DownloadJob:
        """Create and run a job in the background."""
        job = DownloadJob(id=str(uuid.uuid4()))
        with self._lock:
            self.jobs[job.id] = job
        thread = threading.Thread(target=self._run, args=(job, payload), daemon=True)
        thread.start()
        return job

    def cancel(self, job_id: str) -> bool:
        """Request cancellation of a running job."""
        job = self.jobs.get(job_id)
        if job is None:
            return False
        job.cancel_event.set()
        job.log("WARN", "Cancelación solicitada por el usuario.")
        return True

    def snapshot(self, job_id: str) -> dict | None:
        """Return serializable job state."""
        job = self.jobs.get(job_id)
        if job is None:
            return None
        return {
            "id": job.id,
            "status": job.status,
            "logs": job.logs[-300:],
            "downloaded": job.downloaded,
            "skipped": job.skipped,
            "errors": job.errors,
        }

    def _run(self, job: DownloadJob, payload: dict) -> None:
        job.status = "running"
        job.log("INFO", "Iniciando búsqueda segura.")
        try:
            self._validate_and_download(job, payload)
            if job.cancel_event.is_set():
                job.status = "cancelled"
                job.log("INFO", "Descarga cancelada por el usuario.")
            else:
                job.status = "finished"
                job.log("INFO", "Proceso completado.")
        except (ComplianceViolation, TermsError, RegionalBlockError, CaptchaRequiredError, NetworkError, FileIntegrityError, ExtractorError, NotImplementedError) as exc:
            job.status = "failed"
            job.errors += 1
            job.log("ERROR", str(exc))
        except OSError as exc:
            job.status = "failed"
            job.errors += 1
            job.log("ERROR", f"Error de archivo o sistema: {exc}")

    def _validate_and_download(self, job: DownloadJob, payload: dict) -> None:
        birth_date = self._parse_birth_date(payload.get("birth_date", ""))
        nsfw_enabled = payload.get("nsfw_enabled") is True
        validate_nsfw_access(nsfw_enabled, birth_date)
        query = str(payload.get("query", "")).strip()
        category = str(payload.get("category", "")).strip()
        if not nsfw_enabled and query_mentions_sensitive_content(query, [category]):
            job.log("WARN", "La búsqueda parece sensible y NSFW está deshabilitado; se bloqueará el proceso.")
            raise ComplianceViolation("NSFW deshabilitado: no se permite buscar contenido adulto, Rule34 o sensible.")
        platform = PlatformCredential.objects.get(id=payload.get("source"))
        if not platform.enabled:
            raise TermsError("La plataforma seleccionada está deshabilitada.")
        if not platform.terms_accepted:
            raise TermsError("Debes aceptar y documentar los términos de servicio de la plataforma antes de descargar.")
        download_dir = Path(str(payload.get("download_dir", ""))).expanduser()
        download_dir.mkdir(parents=True, exist_ok=True)
        request = SearchRequest(category=category, query=query, source=platform.name, download_dir=download_dir, nsfw_enabled=nsfw_enabled)
        connector = get_connector(platform.connector_type)
        assets = connector.search(request, platform)
        if not assets:
            job.log("WARN", "No se encontraron recursos descargables para la búsqueda.")
            return
        rate_limit = self._rate_limit(platform.rate_limit_seconds)
        job.log("INFO", f"Pausa configurada: {rate_limit} segundos entre solicitudes.")
        for asset in assets:
            if job.cancel_event.is_set():
                return
            if asset.is_nsfw and not nsfw_enabled:
                job.skipped += 1
                job.log("WARN", f"Resultado omitido por contenido NSFW deshabilitado: {asset.title}")
                continue
            validate_public_download_policy(
                terms_accepted=platform.terms_accepted,
                is_private=asset.is_private,
                is_paid=asset.is_paid,
                is_exclusive=asset.is_exclusive,
                license_known=asset.license_known,
                allows_download=asset.allows_download,
                strict_license_mode=platform.strict_license_mode,
            )
            self._download_asset(job, asset, download_dir)
            if rate_limit and not job.cancel_event.is_set():
                job.log("INFO", f"Esperando {rate_limit} segundos para respetar límites.")
                job.cancel_event.wait(rate_limit)

    def _download_asset(self, job: DownloadJob, asset, download_dir: Path) -> None:
        job.log("INFO", f"Validando descarga: {asset.title}")
        response = self._http_get(asset.download_url)
        content_type = response.headers.get("Content-Type", "image/jpeg")
        if not content_type.lower().startswith("image/"):
            raise FileIntegrityError(f"Tipo MIME no permitido: {content_type}")
        extension = guess_extension_from_content_type(content_type)
        allowed_extensions = list(settings.EXTRACTOR_ALLOWED_EXTENSIONS)
        if extension not in allowed_extensions:
            raise FileIntegrityError(f"Extensión no permitida: {extension}")
        target = download_dir / f"{safe_filename(asset.title)}.{extension}"
        decision = target_file_decision(target, allowed_extensions, asset.expected_hash)
        job.log("INFO", decision.reason)
        if not decision.should_download:
            job.skipped += 1
            return
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.write_bytes(response.content)
        if not is_supported_image(temporary, allowed_extensions):
            temporary.unlink(missing_ok=True)
            raise FileIntegrityError("El archivo descargado está corrupto o no parece una imagen compatible.")
        temporary.replace(target)
        job.downloaded += 1
        job.log("INFO", f"Archivo guardado: {target}")

    def _http_get(self, url: str) -> requests.Response:
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "ExtractorFanartsPython/0.1 compliant-downloader"})
        except requests.RequestException as exc:
            raise NetworkError(f"Error de red: {exc}") from exc
        if response.status_code == 451:
            raise RegionalBlockError(message_for_http_status(response.status_code))
        if response.status_code in {401, 403}:
            raise TermsError(message_for_http_status(response.status_code))
        if response.status_code == 429:
            raise NetworkError(message_for_http_status(response.status_code))
        if response.status_code >= 400:
            raise NetworkError(message_for_http_status(response.status_code))
        if b"captcha" in response.content[:1000].lower():
            raise CaptchaRequiredError("La plataforma requiere captcha manual; la app no lo resolverá automáticamente.")
        return response

    @staticmethod
    def _parse_birth_date(value: str) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)

    @staticmethod
    def _rate_limit(value: int) -> int:
        maximum = int(settings.EXTRACTOR_MAX_RATE_LIMIT_SECONDS)
        return max(0, min(int(value), maximum))


manager = DownloadManager()
