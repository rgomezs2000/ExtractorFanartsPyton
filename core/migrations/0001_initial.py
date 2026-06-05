# Generated manually for the initial desktop application models.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=120, unique=True)),
                ("value", models.TextField(blank=True)),
            ],
            options={"ordering": ["key"]},
        ),
        migrations.CreateModel(
            name="PlatformCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("connector_type", models.CharField(choices=[("manual_url", "URL manual autorizada"), ("booru_api", "Booru con API pública"), ("mastodon_api", "Mastodon API"), ("tumblr_api", "Tumblr API"), ("deviantart_api", "DeviantArt API"), ("discord_bot", "Discord bot autorizado"), ("civitai_api", "Civitai API"), ("wiki_api", "Wiki / MediaWiki API")], max_length=40)),
                ("base_url", models.URLField(blank=True)),
                ("api_key", models.CharField(blank=True, max_length=255)),
                ("oauth_token", models.CharField(blank=True, max_length=255)),
                ("enabled", models.BooleanField(default=True)),
                ("allows_nsfw", models.BooleanField(default=False)),
                ("supports_public_search", models.BooleanField(default=True)),
                ("supports_download", models.BooleanField(default=True)),
                ("terms_accepted", models.BooleanField(default=False)),
                ("strict_license_mode", models.BooleanField(default=True)),
                ("rate_limit_seconds", models.PositiveSmallIntegerField(default=30)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
    ]
