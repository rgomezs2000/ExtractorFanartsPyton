"""Django views for the desktop WebView UI."""
import json
from pathlib import Path

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import AppSetting, PlatformCredential
from .services.download_manager import manager

CATEGORIES = [
    "Personajes",
    "Artista / estilo",
    "Concepto",
    "Ropa o accesorio",
    "Herramientas",
    "Fondos o entornos",
    "Poses",
    "Activos o propiedades",
    "Vehículos",
    "Objetos",
    "Acciones",
    "Animales",
]


def index(request: HttpRequest):
    """Render the two-tab desktop UI."""
    return render(
        request,
        "core/index.html",
        {
            "categories": CATEGORIES,
            "connector_choices": PlatformCredential.CONNECTOR_CHOICES,
            "platforms": PlatformCredential.objects.all(),
            "settings": {setting.key: setting.value for setting in AppSetting.objects.all()},
        },
    )


@require_http_methods(["GET", "POST"])
def platforms(request: HttpRequest) -> JsonResponse:
    """List or create/update configured platform connectors."""
    if request.method == "GET":
        return JsonResponse({"platforms": [_platform_to_dict(platform) for platform in PlatformCredential.objects.all()]})
    data = _json_body(request)
    platform_id = data.get("id")
    values = {
        "name": data.get("name", "").strip(),
        "connector_type": data.get("connector_type", "manual_url"),
        "base_url": data.get("base_url", "").strip(),
        "api_key": data.get("api_key", "").strip(),
        "oauth_token": data.get("oauth_token", "").strip(),
        "enabled": bool(data.get("enabled", True)),
        "allows_nsfw": bool(data.get("allows_nsfw", False)),
        "supports_public_search": bool(data.get("supports_public_search", True)),
        "supports_download": bool(data.get("supports_download", True)),
        "terms_accepted": bool(data.get("terms_accepted", False)),
        "strict_license_mode": bool(data.get("strict_license_mode", True)),
        "rate_limit_seconds": min(max(int(data.get("rate_limit_seconds", 30)), 0), 30),
        "notes": data.get("notes", "").strip(),
    }
    if not values["name"]:
        return JsonResponse({"error": "El nombre de plataforma es obligatorio."}, status=400)
    if platform_id:
        platform = get_object_or_404(PlatformCredential, id=platform_id)
        for key, value in values.items():
            setattr(platform, key, value)
        platform.save()
    else:
        platform = PlatformCredential.objects.create(**values)
    return JsonResponse({"platform": _platform_to_dict(platform)})


@require_http_methods(["POST"])
def delete_platform(request: HttpRequest, platform_id: int) -> JsonResponse:
    """Delete a configured platform."""
    platform = get_object_or_404(PlatformCredential, id=platform_id)
    platform.delete()
    return JsonResponse({"deleted": True})


@require_http_methods(["GET", "POST"])
def settings_api(request: HttpRequest) -> JsonResponse:
    """Read or update simple desktop settings."""
    if request.method == "GET":
        return JsonResponse({"settings": {setting.key: setting.value for setting in AppSetting.objects.all()}})
    data = _json_body(request)
    allowed_keys = {
        "default_download_dir",
        "theme",
        "language",
        "max_results",
        "allowed_extensions",
        "clear_console_on_new_download",
        "safe_api_only_mode",
        "strict_license_mode",
    }
    for key, value in data.items():
        if key in allowed_keys:
            AppSetting.objects.update_or_create(key=key, defaults={"value": str(value)})
    return JsonResponse({"settings": {setting.key: setting.value for setting in AppSetting.objects.all()}})


@require_http_methods(["POST"])
def start_download(request: HttpRequest) -> JsonResponse:
    """Start a compliant background download job."""
    data = _json_body(request)
    required = ["category", "query", "source", "download_dir"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Campos obligatorios faltantes: {', '.join(missing)}."}, status=400)
    path = Path(str(data["download_dir"])).expanduser()
    if path.exists() and not path.is_dir():
        return JsonResponse({"error": "La ruta de descarga existe pero no es una carpeta."}, status=400)
    job = manager.start(data)
    return JsonResponse({"job": manager.snapshot(job.id)})


@require_http_methods(["GET"])
def download_status(request: HttpRequest, job_id: str) -> JsonResponse:
    """Return job status and console logs."""
    snapshot = manager.snapshot(job_id)
    if snapshot is None:
        return JsonResponse({"error": "Trabajo no encontrado."}, status=404)
    return JsonResponse({"job": snapshot})


@require_http_methods(["POST"])
def cancel_download(request: HttpRequest, job_id: str) -> JsonResponse:
    """Cancel a running job."""
    if not manager.cancel(job_id):
        return JsonResponse({"error": "Trabajo no encontrado."}, status=404)
    return JsonResponse({"cancelled": True, "job": manager.snapshot(job_id)})


def _json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _platform_to_dict(platform: PlatformCredential) -> dict:
    return {
        "id": platform.id,
        "name": platform.name,
        "connector_type": platform.connector_type,
        "base_url": platform.base_url,
        "enabled": platform.enabled,
        "allows_nsfw": platform.allows_nsfw,
        "supports_public_search": platform.supports_public_search,
        "supports_download": platform.supports_download,
        "terms_accepted": platform.terms_accepted,
        "strict_license_mode": platform.strict_license_mode,
        "rate_limit_seconds": platform.rate_limit_seconds,
        "notes": platform.notes,
        "has_api_key": bool(platform.api_key),
        "has_oauth_token": bool(platform.oauth_token),
    }
