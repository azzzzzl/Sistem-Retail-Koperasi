from datetime import datetime, timezone
from unittest.mock import Mock

from django.test import SimpleTestCase

from .services import ReportService


class ReportServiceTests(SimpleTestCase):
    def test_parse_period_is_end_exclusive(self):
        start, end = ReportService.parse_period("2026-09-01", "2026-09-30")
        self.assertEqual(start, datetime(2026, 9, 1, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2026, 10, 1, tzinfo=timezone.utc))

    def test_parse_period_rejects_invalid_date(self):
        with self.assertRaises(ValueError):
            ReportService.parse_period("2026/09/01", "2026-09-30")

    def test_parse_period_rejects_reversed_range(self):
        with self.assertRaises(ValueError):
            ReportService.parse_period("2026-09-30", "2026-09-01")

    def test_number_handles_invalid_value(self):
        self.assertEqual(ReportService.number("not-number"), 0)

    def test_clean_document_serializes_datetime(self):
        result = ReportService.clean_document({"createdAt": datetime(2026, 1, 1, tzinfo=timezone.utc)})
        self.assertEqual(result["createdAt"], "2026-01-01T00:00:00+00:00")
