"""Tests for compliance, file handling, and UI endpoints."""
import json
import tempfile
from datetime import date
from pathlib import Path

from django.test import Client, TestCase

from core.models import PlatformCredential
from core.services.compliance import ComplianceViolation, calculate_age, validate_nsfw_access
from core.services.exceptions import message_for_http_status
from core.services.files import is_supported_image, target_file_decision


class ComplianceTests(TestCase):
    """Validate NSFW and legal compliance helpers."""

    def test_calculate_age_handles_birthdays(self) -> None:
        self.assertEqual(calculate_age(date(2008, 6, 5), date(2026, 6, 5)), 18)
        self.assertEqual(calculate_age(date(2008, 6, 6), date(2026, 6, 5)), 17)

    def test_nsfw_requires_adult_birth_date(self) -> None:
        with self.assertRaises(ComplianceViolation):
            validate_nsfw_access(True, date(2010, 1, 1), date(2026, 6, 5))
        result = validate_nsfw_access(True, date(2000, 1, 1), date(2026, 6, 5))
        self.assertTrue(result.allowed)

    def test_http_status_messages_include_regional_block(self) -> None:
        self.assertIn("restricción regional", message_for_http_status(451))


class FilePolicyTests(TestCase):
    """Validate corruption detection and skip/overwrite decisions."""

    def test_corrupt_existing_file_is_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.png"
            path.write_bytes(b"not an image")
            decision = target_file_decision(path, ["png"])
            self.assertTrue(decision.should_download)
            self.assertIn("corrupto", decision.reason)

    def test_valid_png_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
            self.assertTrue(is_supported_image(path, ["png"]))
            decision = target_file_decision(path, ["png"])
            self.assertFalse(decision.should_download)


class UiEndpointTests(TestCase):
    """Validate desktop JSON endpoints."""

    def test_index_loads(self) -> None:
        response = Client().get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Extractor Fanarts Python")

    def test_platform_api_creates_platform_with_rate_limit_cap(self) -> None:
        response = Client().post(
            "/api/platforms/",
            data=json.dumps({
                "name": "URL manual segura",
                "connector_type": "manual_url",
                "terms_accepted": True,
                "strict_license_mode": False,
                "rate_limit_seconds": 99,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        platform = PlatformCredential.objects.get(name="URL manual segura")
        self.assertEqual(platform.rate_limit_seconds, 30)
