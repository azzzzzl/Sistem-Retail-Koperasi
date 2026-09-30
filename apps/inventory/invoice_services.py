from datetime import datetime, timezone
from decimal import Decimal

from .invoice_repositories import SupplierInvoiceRepository
from .purchase_repositories import PurchaseRepository


class SupplierInvoiceService:
    """
    Business logic Supplier Invoice.
    """

    STATUS_UNPAID = "UNPAID"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_PAID = "PAID"
    STATUS_OVERDUE = "OVERDUE"

    ALLOWED_STATUSES = {
        STATUS_UNPAID,
        STATUS_PARTIAL,
        STATUS_PAID,
        STATUS_OVERDUE,
    }

    def __init__(self):
        self.repository = SupplierInvoiceRepository()
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

    def _parse_date(self, value, field_name):
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} harus berupa tanggal."
            )

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            raise ValueError(
                f"{field_name} memiliki format tanggal tidak valid."
            )

    def create_invoice(
        self,
        invoice_number,
        purchase_id,
        invoice_date=None,
        due_date=None,
        created_by=None,
    ):
        if not invoice_number:
            raise ValueError(
                "invoiceNumber wajib diisi."
            )

        if not purchase_id:
            raise ValueError(
                "purchaseId wajib diisi."
            )

        existing_invoice = (
            self.repository.find_by_number(
                invoice_number
            )
        )

        if existing_invoice:
            raise ValueError(
                "invoiceNumber sudah digunakan."
            )

        purchase = self.purchase_repository.find_by_id(
            purchase_id
        )

        if not purchase:
            raise ValueError(
                "Pembelian tidak ditemukan."
            )

        existing_purchase_invoices = (
            self.repository.find_by_purchase_id(
                purchase_id
            )
        )

        if existing_purchase_invoices:
            raise ValueError(
                "Purchase tersebut sudah memiliki Supplier Invoice."
            )

        supplier_id = purchase.get(
            "supplierId"
        )

        if not supplier_id:
            raise ValueError(
                "supplierId pada pembelian tidak ditemukan."
            )

        subtotal = self._to_number(
            purchase.get("subtotal", 0),
            "subtotal",
        )

        tax = self._to_number(
            purchase.get("tax", 0),
            "tax",
        )

        total = self._to_number(
            purchase.get("total", 0),
            "total",
        )

        expected_total = (
            subtotal + tax
        )

        if total != expected_total:
            raise ValueError(
                "Total pembelian tidak sesuai "
                "dengan subtotal + tax."
            )

        if total <= 0:
            raise ValueError(
                "Total invoice harus lebih besar dari 0."
            )

        invoice_date = self._parse_date(
            invoice_date,
            "invoiceDate",
        )

        due_date = self._parse_date(
            due_date,
            "dueDate",
        )

        if invoice_date is None:
            invoice_date = datetime.now(
                timezone.utc
            )

        if due_date is not None and due_date < invoice_date:
            raise ValueError(
                "dueDate tidak boleh lebih awal "
                "dari invoiceDate."
            )

        now = datetime.now(timezone.utc)

        invoice_data = {
            "invoiceNumber": invoice_number,
            "supplierId": supplier_id,
            "purchaseId": purchase_id,
            "invoiceDate": invoice_date,
            "dueDate": due_date,
            "subtotal": self._format_number(
                subtotal
            ),
            "tax": self._format_number(
                tax
            ),
            "total": self._format_number(
                total
            ),
            "paidAmount": 0,
            "remainingAmount": self._format_number(
                total
            ),
            "status": self.STATUS_UNPAID,
            "createdBy": created_by,
            "createdAt": now,
            "updatedAt": now,
        }

        return self.repository.create(
            invoice_data
        )

    def get_all_invoices(self):
        return self.repository.find_all()

    def get_invoice_by_id(self, invoice_id):
        return self.repository.find_by_id(
            invoice_id
        )

    def get_invoices_by_supplier(
        self,
        supplier_id,
    ):
        if not supplier_id:
            raise ValueError(
                "supplierId wajib diisi."
            )

        return self.repository.find_by_supplier_id(
            supplier_id
        )

    def get_invoices_by_purchase(
        self,
        purchase_id,
    ):
        if not purchase_id:
            raise ValueError(
                "purchaseId wajib diisi."
            )

        return self.repository.find_by_purchase_id(
            purchase_id
        )

    def update_payment_status(
        self,
        invoice_id,
        paid_amount,
    ):
        invoice = self.repository.find_by_id(
            invoice_id
        )

        if not invoice:
            raise ValueError(
                "Supplier Invoice tidak ditemukan."
            )

        total = self._to_number(
            invoice.get("total", 0),
            "total",
        )

        paid_amount = self._to_number(
            paid_amount,
            "paidAmount",
        )

        if paid_amount > total:
            raise ValueError(
                "paidAmount tidak boleh melebihi total invoice."
            )

        remaining_amount = (
            total - paid_amount
        )

        if paid_amount == 0:
            status = self.STATUS_UNPAID
        elif paid_amount < total:
            status = self.STATUS_PARTIAL
        else:
            status = self.STATUS_PAID

        return self.repository.update(
            invoice_id,
            {
                "paidAmount": self._format_number(
                    paid_amount
                ),
                "remainingAmount": self._format_number(
                    remaining_amount
                ),
                "status": status,
            },
        )

    def get_outstanding_invoices(self):
        invoices = self.repository.find_all()

        result = []

        for invoice in invoices:
            remaining = invoice.get(
                "remainingAmount",
                0,
            )

            if remaining > 0:
                result.append(invoice)

        return result

    def get_supplier_debt(
        self,
        supplier_id,
    ):
        if not supplier_id:
            raise ValueError(
                "supplierId wajib diisi."
            )

        invoices = (
            self.repository.find_by_supplier_id(
                supplier_id
            )
        )

        result = []

        for invoice in invoices:
            remaining = invoice.get(
                "remainingAmount",
                0,
            )

            if remaining > 0:
                result.append(invoice)

        return result