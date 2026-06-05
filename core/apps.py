"""Core Django app configuration."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application configuration for UI, settings, and safe download orchestration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
