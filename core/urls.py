"""Core routes for UI and JSON endpoints."""
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/platforms/", views.platforms, name="platforms"),
    path("api/platforms/<int:platform_id>/delete/", views.delete_platform, name="delete_platform"),
    path("api/settings/", views.settings_api, name="settings_api"),
    path("api/download/start/", views.start_download, name="start_download"),
    path("api/download/<str:job_id>/", views.download_status, name="download_status"),
    path("api/download/<str:job_id>/cancel/", views.cancel_download, name="cancel_download"),
]
