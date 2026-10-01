from datetime import datetime, timezone
from decimal import Decimal

from .purchase_repositories import PurchaseRepository
from .po_repositories import PurchaseOrderRepository
from .gr_repositories import GoodsReceiptRepository


class PurchaseService:
    """
    Service untuk business logic Pembelian.
    """

    PAYMENT_UNPAID = "UNPAID"
    PAYMENT_PARTIAL = "PARTIAL"
    PAYMENT_PAID = "PAID"

    PAYMENT_STATUSES = {
        PAYMENT_UNPAID,
        PAYMENT_PARTIAL,
        PAYMENT_PAID,
    }

    def __init__(self):
        self.repository = PurchaseRepository()
        self.po_repository = PurchaseOrderRepository()
        self.receipt_repository = GoodsReceiptRepository()

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
        if value is None or isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError(f"{field_name} harus berupa tanggal.")
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} memiliki format tanggal tidak valid.") from exc
        return result if result.tzinfo else result.replace(tzinfo=timezone.utc)

    def _build_items_from_receipt(
        self,
        receipt,
    ):
        items = []

        for item in receipt.get(
            "items",
            [],
        ):
            accepted_quantity = self._to_number(
                item.get("acceptedQuantity", 0),
                "acceptedQuantity",
            )

            if accepted_quantity <= 0:
                continue

            purchase_price = self._to_number(
                item.get("purchasePrice", 0),
                "purchasePrice",
            )

            subtotal = (
                accepted_quantity * purchase_price
            )

            items.append({
                "productId": item.get(
                    "productId"
                ),
                "quantity": self._format_number(
                    accepted_quantity
                ),
                "purchasePrice": self._format_number(
                    purchase_price
                ),
                "subtotal": self._format_number(
                    subtotal
                ),
            })

        if not items:
            raise ValueError(
                "Goods Receipt tidak memiliki "
                "barang yang diterima."
            )

        return items

    def create_purchase(
        self,
        purchase_number,
        po_id,
        goods_receipt_id,
        purchase_date=None,
        discount=0,
        tax=0,
        created_by=None,
    ):
        if not purchase_number:
            raise ValueError(
                "purchaseNumber wajib diisi."
            )

        if not po_id:
            raise ValueError(
                "poId wajib diisi."
            )

        if not goods_receipt_id:
            raise ValueError(
                "goodsReceiptId wajib diisi."
            )

        existing_purchase = (
            self.repository.find_by_number(
                purchase_number
            )
        )

        if existing_purchase:
            raise ValueError(
                "purchaseNumber sudah digunakan."
            )

        po = self.po_repository.find_by_id(
            po_id
        )

        if not po:
            raise ValueError(
                "Purchase Order tidak ditemukan."
            )

        receipt = (
            self.receipt_repository.find_by_id(
                goods_receipt_id
            )
        )

        if not receipt:
            raise ValueError(
                "Goods Receipt tidak ditemukan."
            )

        if str(receipt.get("poId")) != str(po_id):
            raise ValueError(
                "Goods Receipt tidak sesuai "
                "dengan Purchase Order."
            )

        existing_for_receipt = (
            self.repository.find_by_goods_receipt_id(
                goods_receipt_id
            )
        )

        if existing_for_receipt:
            raise ValueError(
                "Goods Receipt tersebut sudah "
                "digunakan dalam pembelian."
            )

        items = self._build_items_from_receipt(
            receipt
        )

        subtotal = sum(
            Decimal(str(item["subtotal"]))
            for item in items
        )

        discount = self._to_number(
            discount,
            "discount",
        )

        tax = self._to_number(
            tax,
            "tax",
        )

        if discount > subtotal:
            raise ValueError(
                "Discount tidak boleh lebih besar "
                "dari subtotal."
            )

        total = (
            subtotal
            - discount
            + tax
        )

        purchase_date = self._parse_date(purchase_date, "purchaseDate")
        if purchase_date is None:
            purchase_date = datetime.now(timezone.utc)

        now = datetime.now(
            timezone.utc
        )

        purchase_data = {
            "purchaseNumber": purchase_number,
            "poId": po_id,
            "supplierId": po.get(
                "supplierId"
            ),
            "goodsReceiptId": goods_receipt_id,
            "purchaseDate": purchase_date,
            "items": items,
            "subtotal": self._format_number(
                subtotal
            ),
            "discount": self._format_number(
                discount
            ),
            "tax": self._format_number(
                tax
            ),
            "total": self._format_number(
                total
            ),
            "paymentStatus": (
                self.PAYMENT_UNPAID
            ),
            "createdBy": created_by,
            "createdAt": now,
            "updatedAt": now,
        }

        return self.repository.create(
            purchase_data
        )

    def get_all_purchases(self):
        return self.repository.find_all()

    def get_purchase_by_id(
        self,
        purchase_id,
    ):
        return self.repository.find_by_id(
            purchase_id
        )

    def get_purchases_by_po(
        self,
        po_id,
    ):
        if not po_id:
            raise ValueError(
                "poId wajib diisi."
            )

        return self.repository.find_by_po_id(
            po_id
        )

    def get_purchases_by_goods_receipt(
        self,
        goods_receipt_id,
    ):
        if not goods_receipt_id:
            raise ValueError(
                "goodsReceiptId wajib diisi."
            )

        return (
            self.repository
            .find_by_goods_receipt_id(
                goods_receipt_id
            )
        )