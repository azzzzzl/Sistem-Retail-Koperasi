from datetime import datetime, timezone
from decimal import Decimal

from .payment_repositories import SupplierPaymentRepository
from .invoice_repositories import SupplierInvoiceRepository
from .purchase_repositories import PurchaseRepository


def _normalize_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError("paymentDate memiliki format tanggal tidak valid.") from exc
    raise ValueError("paymentDate harus berupa tanggal.")


class SupplierPaymentService:
    STATUS_UNPAID = "UNPAID"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_PAID = "PAID"

    PAYMENT_METHODS = {
        "CASH",
        "TRANSFER",
        "QRIS",
        "GIRO",
        "OTHER",
    }

    def __init__(self):
        self.repository = SupplierPaymentRepository()
        self.invoice_repository = SupplierInvoiceRepository()
        self.purchase_repository = PurchaseRepository()

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


        if payment_date is None:
            payment_date = datetime.now(timezone.utc)
        payment_date = _normalize_datetime(payment_date)

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

        # Create the payment first. The invoice update is conditional/atomic.
        # If the invoice update fails, remove the payment so neither side is left partial.
        payment = self.repository.create(payment_data)
        try:
            updated_invoice = self.invoice_repository.apply_payment(invoice_id, amount)
            if not updated_invoice:
                self.repository.delete(payment["_id"])
                raise ValueError("Pembayaran gagal: sisa invoice berubah atau jumlah melebihi hutang.")
        except Exception:
            self.repository.delete(payment["_id"])
            raise

        purchase_id = updated_invoice.get("purchaseId")
        if purchase_id:
            remaining = Decimal(str(updated_invoice.get("remainingAmount", 0)))
            paid = Decimal(str(updated_invoice.get("paidAmount", 0)))
            status = "PAID" if remaining <= 0 else ("PARTIAL" if paid > 0 else "UNPAID")
            try:
                purchase_update = self.purchase_repository.update(purchase_id, {"paymentStatus": status})
                if not purchase_update:
                    raise RuntimeError("Status pembayaran pembelian gagal disinkronkan.")
            except Exception:
                self.invoice_repository.reverse_payment(invoice_id, amount)
                self.repository.delete(payment["_id"])
                raise
        return {"payment": payment, "invoice": updated_invoice}

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