"""Admin registrations for local configuration."""
from django.contrib import admin

from .models import AppSetting, PlatformCredential


@admin.register(PlatformCredential)
class PlatformCredentialAdmin(admin.ModelAdmin):
    """Manage configured platform connectors."""

    list_display = ("name", "connector_type", "enabled", "allows_nsfw", "terms_accepted", "rate_limit_seconds")
    list_filter = ("connector_type", "enabled", "allows_nsfw", "terms_accepted")
    search_fields = ("name", "base_url")


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    """Manage key-value desktop settings."""

    list_display = ("key", "value")
    search_fields = ("key",)
