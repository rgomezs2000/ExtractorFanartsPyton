"""Persistent configuration models."""
from django.db import models


class PlatformCredential(models.Model):
    """A configured platform connector and its allowed credential metadata."""

    CONNECTOR_CHOICES = [
        ("manual_url", "URL manual autorizada"),
        ("booru_api", "Booru con API pública"),
        ("mastodon_api", "Mastodon API"),
        ("tumblr_api", "Tumblr API"),
        ("deviantart_api", "DeviantArt API"),
        ("discord_bot", "Discord bot autorizado"),
        ("civitai_api", "Civitai API"),
        ("wiki_api", "Wiki / MediaWiki API"),
    ]

    name = models.CharField(max_length=120, unique=True)
    connector_type = models.CharField(max_length=40, choices=CONNECTOR_CHOICES)
    base_url = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    oauth_token = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True)
    allows_nsfw = models.BooleanField(default=False)
    supports_public_search = models.BooleanField(default=True)
    supports_download = models.BooleanField(default=True)
    terms_accepted = models.BooleanField(default=False)
    strict_license_mode = models.BooleanField(default=True)
    rate_limit_seconds = models.PositiveSmallIntegerField(default=30)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AppSetting(models.Model):
    """Simple key-value settings storage for desktop preferences."""

    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key
