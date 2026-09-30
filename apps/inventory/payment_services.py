from datetime import datetime, timezone
from decimal import Decimal

from .payment_repositories import SupplierPaymentRepository
from .invoice_repositories import SupplierInvoiceRepository


class SupplierPaymentService:
    STATUS_UNPAID = "UNPAID"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_PAID = "PAID"

    PAYMENT_METHODS = {
        "CASH",
        "TRANSFER",
        "GIRO",
        "OTHER",
    }

    def __init__(self):
        self.repository = SupplierPaymentRepository()
        self.invoice_repository = SupplierInvoiceRepository()

    def _to_number(self, value, field_name):
        try:
            number = Decimal(str(value))
        except (TypeError, ValueError):
            raise ValueError(
                f"{field_name} harus berupa angka."
            )

        if number < 0:
            raise ValueError(
                f"{field_name} tidak boleh negatif."
            )

        return number

    def _format_number(self, value):
        if value == value.to_integral_value():
            return int(value)

        return float(value)

    def create_payment(
        self,
        payment_number,
        invoice_id,
        amount,
        payment_date=None,
        payment_method="TRANSFER",
        reference_number="",
        notes="",
        created_by=None,
    ):
        if not payment_number:
            raise ValueError(
                "paymentNumber wajib diisi."
            )

        if not invoice_id:
            raise ValueError(
                "invoiceId wajib diisi."
            )

        existing_payment = self.repository.find_by_number(
            payment_number
        )

        if existing_payment:
            raise ValueError(
                "paymentNumber sudah digunakan."
            )

        invoice = self.invoice_repository.find_by_id(
            invoice_id
        )

        if not invoice:
            raise ValueError(
                "Supplier Invoice tidak ditemukan."
            )

        payment_method = payment_method.upper()

        if payment_method not in self.PAYMENT_METHODS:
            raise ValueError(
                "paymentMethod tidak valid."
            )

        amount = self._to_number(
            amount,
            "amount",
        )

        if amount <= 0:
            raise ValueError(
                "amount harus lebih besar dari 0."
            )

        total = Decimal(
            str(invoice.get("total", 0))
        )

        paid_amount = Decimal(
            str(invoice.get("paidAmount", 0))
        )

        remaining_amount = total - paid_amount

        if remaining_amount < 0:
            remaining_amount = Decimal("0")

        if amount > remaining_amount:
            raise ValueError(
                "Pembayaran tidak boleh melebihi sisa hutang invoice."
            )

        new_paid_amount = paid_amount + amount
        new_remaining_amount = total - new_paid_amount

        if new_remaining_amount < 0:
            raise ValueError(
                "remainingAmount tidak boleh negatif."
            )

        if new_remaining_amount == 0:
            new_status = self.STATUS_PAID
        elif new_paid_amount > 0:
            new_status = self.STATUS_PARTIAL
        else:
            new_status = self.STATUS_UNPAID

        if payment_date is None:
            payment_date = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)

        payment_data = {
            "paymentNumber": payment_number,
            "supplierId": invoice.get("supplierId"),
            "invoiceId": invoice_id,
            "paymentDate": payment_date,
            "amount": self._format_number(amount),
            "paymentMethod": payment_method,
            "referenceNumber": reference_number,
            "notes": notes,
            "createdBy": created_by,
            "createdAt": now,
        }

        payment = self.repository.create(
            payment_data
        )

        try:
            updated_invoice = self.invoice_repository.update(
                invoice_id,
                {
                    "paidAmount": self._format_number(
                        new_paid_amount
                    ),
                    "remainingAmount": self._format_number(
                        new_remaining_amount
                    ),
                    "status": new_status,
                },
            )
        except Exception:
            # Rollback payment jika invoice gagal diperbarui.
            payment_id = payment.get("_id")

            if payment_id:
                from bson import ObjectId

                self.repository.collection.delete_one(
                    {
                        "_id": ObjectId(payment_id)
                    }
                )

            raise

        return {
            "payment": payment,
            "invoice": updated_invoice,
        }

    def get_all_payments(self):
        return self.repository.find_all()

    def get_payment_by_id(self, payment_id):
        return self.repository.find_by_id(payment_id)

    def get_payments_by_invoice(self, invoice_id):
        if not invoice_id:
            raise ValueError(
                "invoiceId wajib diisi."
            )

        return self.repository.find_by_invoice_id(
            invoice_id
        )

    def get_payments_by_supplier(self, supplier_id):
        if not supplier_id:
            raise ValueError(
                "supplierId wajib diisi."
            )

        return self.repository.find_by_supplier_id(
            supplier_id
        )