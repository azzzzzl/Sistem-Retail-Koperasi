from datetime import datetime, timezone
from decimal import Decimal

from .po_repositories import PurchaseOrderRepository


class PurchaseOrderService:
    """
    Service untuk business logic Purchase Order.
    """

    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    ALLOWED_STATUSES = {
        STATUS_DRAFT,
        STATUS_PENDING,
        STATUS_APPROVED,
        STATUS_PARTIAL,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
    }

    def __init__(self):
        self.repository = PurchaseOrderRepository()

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

    def _validate_items(self, items):
        if not isinstance(items, list) or not items:
            raise ValueError(
                "Items PO wajib diisi."
            )

        processed_items = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    "Setiap item PO harus berupa object."
                )

            product_id = item.get("productId")

            if not product_id:
                raise ValueError(
                    "productId wajib diisi."
                )

            name = item.get(
                "name",
                ""
            )

            if not name:
                raise ValueError(
                    "name produk wajib diisi."
                )

            quantity = self._to_number(
                item.get("quantity"),
                "quantity",
            )

            if quantity <= 0:
                raise ValueError(
                    "quantity harus lebih besar dari 0."
                )

            purchase_price = self._to_number(
                item.get("purchasePrice"),
                "purchasePrice",
            )

            subtotal = (
                quantity * purchase_price
            )

            processed_items.append({
                "productId": product_id,
                "name": name,
                "quantity": self._format_number(
                    quantity
                ),
                "purchasePrice": self._format_number(
                    purchase_price
                ),
                "subtotal": self._format_number(
                    subtotal
                ),
            })

        return processed_items

    def create_purchase_order(
        self,
        po_number,
        supplier_id,
        order_date=None,
        items=None,
        discount=0,
        notes="",
        created_by=None,
    ):
        if not po_number:
            raise ValueError(
                "poNumber wajib diisi."
            )

        if not supplier_id:
            raise ValueError(
                "supplierId wajib diisi."
            )

        existing_po = (
            self.repository.find_by_number(
                po_number
            )
        )

        if existing_po:
            raise ValueError(
                "poNumber sudah digunakan."
            )

        processed_items = self._validate_items(
            items
        )

        subtotal = sum(
            Decimal(str(item["subtotal"]))
            for item in processed_items
        )

        discount = self._to_number(
            discount,
            "discount",
        )

        if discount > subtotal:
            raise ValueError(
                "Discount tidak boleh lebih besar "
                "dari subtotal."
            )

        total = subtotal - discount

        if order_date is None:
            order_date = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)

        po_data = {
            "poNumber": po_number,
            "supplierId": supplier_id,
            "orderDate": order_date,
            "status": self.STATUS_DRAFT,
            "items": processed_items,
            "subtotal": self._format_number(
                subtotal
            ),
            "discount": self._format_number(
                discount
            ),
            "total": self._format_number(
                total
            ),
            "notes": notes,
            "createdBy": created_by,
            "approvedBy": None,
            "createdAt": now,
            "updatedAt": now,
        }

        return self.repository.create(
            po_data
        )

    def get_all_purchase_orders(self):
        return self.repository.find_all()

    def get_purchase_order_by_id(self, po_id):
        return self.repository.find_by_id(
            po_id
        )

    def submit_purchase_order(self, po_id):
        po = self.repository.find_by_id(
            po_id
        )

        if not po:
            raise ValueError(
                "Purchase Order tidak ditemukan."
            )

        if po.get("status") != self.STATUS_DRAFT:
            raise ValueError(
                "Hanya PO dengan status DRAFT "
                "yang dapat disubmit."
            )

        return self.repository.update(
            po_id,
            {
                "status": self.STATUS_PENDING,
            },
        )

    def approve_purchase_order(
        self,
        po_id,
        approved_by=None,
    ):
        po = self.repository.find_by_id(
            po_id
        )

        if not po:
            raise ValueError(
                "Purchase Order tidak ditemukan."
            )

        if po.get("status") != self.STATUS_PENDING:
            raise ValueError(
                "Hanya PO dengan status PENDING "
                "yang dapat disetujui."
            )

        return self.repository.update(
            po_id,
            {
                "status": self.STATUS_APPROVED,
                "approvedBy": approved_by,
            },
        )

    def cancel_purchase_order(self, po_id):
        po = self.repository.find_by_id(
            po_id
        )

        if not po:
            raise ValueError(
                "Purchase Order tidak ditemukan."
            )

        status = po.get("status")

        if status in {
            self.STATUS_COMPLETED,
            self.STATUS_CANCELLED,
        }:
            raise ValueError(
                "PO yang sudah COMPLETED atau CANCELLED "
                "tidak dapat dibatalkan."
            )

        return self.repository.update(
            po_id,
            {
                "status": self.STATUS_CANCELLED,
            },
        )
