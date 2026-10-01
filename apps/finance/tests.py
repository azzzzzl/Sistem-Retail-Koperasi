from decimal import Decimal

from django.test import SimpleTestCase

from .services import ExpenseService


class ExpenseValidationTests(SimpleTestCase):
    def test_invalid_category(self):
        service = ExpenseService(repository=FakeRepository())
        try:
            service.create("EXP-TEST", amount=1000, category="INVALID")
        except ValueError as exc:
            self.assertIn("Kategori", str(exc))
        else:
            self.fail("Expected ValueError")

    def test_negative_amount(self):
        service = ExpenseService(repository=FakeRepository())
        try:
            service.create("EXP-TEST", amount=-1)
        except ValueError as exc:
            self.assertIn("lebih besar", str(exc))
        else:
            self.fail("Expected ValueError")


class FakeRepository:
    def exists_number(self, number):
        return False


class DecimalSanityTests(SimpleTestCase):
    def test_decimal(self):
        self.assertEqual(Decimal("10.50"), Decimal("10.50"))
