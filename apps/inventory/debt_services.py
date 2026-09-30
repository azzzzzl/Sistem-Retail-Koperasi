from decimal import Decimal

from .invoice_repositories import SupplierInvoiceRepository


class SupplierDebtService:

    def __init__(self):
        self.invoice_repository = SupplierInvoiceRepository()

    def _to_number(self, value):
        try:
            return Decimal(str(value or 0))
        except (TypeError, ValueError):
            return Decimal("0")

    def _format_number(self, value):
        if value == value.to_integral_value():
            return int(value)

        return float(value)

    def get_supplier_debt(self, supplier_id):
        if not supplier_id:
            raise ValueError(
                "supplierId wajib diisi."
            )

        invoices = self.invoice_repository.find_by_supplier_id(
            supplier_id
        )

        invoice_data = []
        total_amount = Decimal("0")
        total_paid = Decimal("0")
        total_remaining = Decimal("0")

        for invoice in invoices:
            total = self._to_number(
                invoice.get("total")
            )

            paid_amount = self._to_number(
                invoice.get("paidAmount")
            )

            remaining_amount = self._to_number(
                invoice.get("remainingAmount")
            )

            total_amount += total
            total_paid += paid_amount
            total_remaining += remaining_amount

            invoice_data.append(
                {
                    "invoiceId": str(
                        invoice.get("_id")
                    ),
                    "invoiceNumber": invoice.get(
                        "invoiceNumber"
                    ),
                    "supplierId": invoice.get(
                        "supplierId"
                    ),
                    "invoiceDate": invoice.get(
                        "invoiceDate"
                    ),
                    "dueDate": invoice.get(
                        "dueDate"
                    ),
                    "total": self._format_number(
                        total
                    ),
                    "paidAmount": self._format_number(
                        paid_amount
                    ),
                    "remainingAmount": self._format_number(
                        remaining_amount
                    ),
                    "status": invoice.get(
                        "status"
                    ),
                }
            )

        return {
            "supplierId": supplier_id,
            "invoiceCount": len(invoice_data),
            "totalAmount": self._format_number(
                total_amount
            ),
            "totalPaid": self._format_number(
                total_paid
            ),
            "totalDebt": self._format_number(
                total_remaining
            ),
            "invoices": invoice_data,
        }

    def get_all_outstanding_invoices(
        self,
        supplier_id=None,
    ):
        if supplier_id:
            invoices = (
                self.invoice_repository
                .find_by_supplier_id(supplier_id)
            )
        else:
            invoices = (
                self.invoice_repository
                .find_all()
            )

        outstanding = []

        for invoice in invoices:
            remaining_amount = self._to_number(
                invoice.get("remainingAmount")
            )

            if remaining_amount <= 0:
                continue

            outstanding.append(
                {
                    "invoiceId": str(
                        invoice.get("_id")
                    ),
                    "invoiceNumber": invoice.get(
                        "invoiceNumber"
                    ),
                    "supplierId": invoice.get(
                        "supplierId"
                    ),
                    "invoiceDate": invoice.get(
                        "invoiceDate"
                    ),
                    "dueDate": invoice.get(
                        "dueDate"
                    ),
                    "total": invoice.get(
                        "total",
                        0,
                    ),
                    "paidAmount": invoice.get(
                        "paidAmount",
                        0,
                    ),
                    "remainingAmount": invoice.get(
                        "remainingAmount",
                        0,
                    ),
                    "status": invoice.get(
                        "status"
                    ),
                }
            )

        return outstanding