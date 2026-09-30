from datetime import datetime, timezone
from decimal import Decimal

from .gr_repositories import GoodsReceiptRepository
from .po_repositories import PurchaseOrderRepository
from .po_services import PurchaseOrderService
from .services import StockMovementService


class GoodsReceiptService:
    """
    Service untuk business logic Goods Receipt.
    """

    STATUS_RECEIVED = "RECEIVED"

    def __init__(self):
        self.repository = GoodsReceiptRepository()
        self.po_repository = PurchaseOrderRepository()
        self.po_service = PurchaseOrderService()
        self.stock_movement_service = StockMovementService()

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

    def _get_previous_received(self, po_id):
        receipts = self.repository.find_by_po_id(
            po_id
        )

        received_by_product = {}

        for receipt in receipts:
            for item in receipt.get("items", []):
                product_id = item.get("productId")

                quantity = self._to_number(
                    item.get("receivedQuantity", 0),
                    "receivedQuantity",
                )

                received_by_product[product_id] = (
                    received_by_product.get(
                        product_id,
                        Decimal("0"),
                    )
                    + quantity
                )

        return received_by_product

    def _get_po_item_map(self, po):
        item_map = {}

        for item in po.get("items", []):
            product_id = item.get("productId")

            item_map[product_id] = item

        return item_map

    def _validate_items(
        self,
        po,
        items,
    ):
        if not isinstance(items, list) or not items:
            raise ValueError(
                "Items penerimaan wajib diisi."
            )

        po_item_map = self._get_po_item_map(po)

        previous_received = (
            self._get_previous_received(
                str(po["_id"])
            )
        )

        processed_items = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    "Setiap item penerimaan harus berupa object."
                )

            product_id = item.get("productId")

            if not product_id:
                raise ValueError(
                    "productId wajib diisi."
                )

            if product_id not in po_item_map:
                raise ValueError(
                    f"Produk {product_id} tidak terdapat "
                    "di dalam PO."
                )

            received_quantity = self._to_number(
                item.get("receivedQuantity"),
                "receivedQuantity",
            )

            accepted_quantity = self._to_number(
                item.get("acceptedQuantity"),
                "acceptedQuantity",
            )

            rejected_quantity = self._to_number(
                item.get("rejectedQuantity"),
                "rejectedQuantity",
            )

            if received_quantity <= 0:
                raise ValueError(
                    "receivedQuantity harus lebih besar dari 0."
                )

            if accepted_quantity + rejected_quantity != received_quantity:
                raise ValueError(
                    "acceptedQuantity + rejectedQuantity "
                    "harus sama dengan receivedQuantity."
                )

            po_item = po_item_map[product_id]

            ordered_quantity = self._to_number(
                po_item.get("quantity"),
                "quantity PO",
            )

            already_received = previous_received.get(
                product_id,
                Decimal("0"),
            )

            remaining_quantity = (
                ordered_quantity - already_received
            )

            if received_quantity > remaining_quantity:
                raise ValueError(
                    f"Jumlah penerimaan untuk produk "
                    f"{product_id} melebihi sisa PO. "
                    f"Sisa yang dapat diterima: "
                    f"{self._format_number(remaining_quantity)}."
                )

            processed_items.append({
                "productId": product_id,
                "orderedQuantity": self._format_number(
                    ordered_quantity
                ),
                "receivedQuantity": self._format_number(
                    received_quantity
                ),
                "acceptedQuantity": self._format_number(
                    accepted_quantity
                ),
                "rejectedQuantity": self._format_number(
                    rejected_quantity
                ),
                "purchasePrice": po_item.get(
                    "purchasePrice",
                    0,
                ),
            })

        return processed_items

    def _update_po_status(self, po_id):
        po = self.po_repository.find_by_id(
            po_id
        )

        if not po:
            return

        receipts = self.repository.find_by_po_id(
            po_id
        )

        received_by_product = {}

        for receipt in receipts:
            for item in receipt.get("items", []):
                product_id = item.get("productId")

                quantity = self._to_number(
                    item.get("receivedQuantity", 0),
                    "receivedQuantity",
                )

                received_by_product[product_id] = (
                    received_by_product.get(
                        product_id,
                        Decimal("0"),
                    )
                    + quantity
                )

        all_completed = True
        any_received = False

        for po_item in po.get("items", []):
            product_id = po_item.get("productId")

            ordered_quantity = self._to_number(
                po_item.get("quantity"),
                "quantity PO",
            )

            received_quantity = received_by_product.get(
                product_id,
                Decimal("0"),
            )

            if received_quantity > 0:
                any_received = True

            if received_quantity < ordered_quantity:
                all_completed = False

        if all_completed:
            new_status = (
                PurchaseOrderService.STATUS_COMPLETED
            )
        elif any_received:
            new_status = (
                PurchaseOrderService.STATUS_PARTIAL
            )
        else:
            new_status = (
                PurchaseOrderService.STATUS_APPROVED
            )

        self.po_repository.update(
            po_id,
            {
                "status": new_status,
            },
        )

    def create_goods_receipt(
        self,
        receipt_number,
        po_id,
        receipt_date=None,
        items=None,
        received_by=None,
        notes="",
    ):
        if not receipt_number:
            raise ValueError(
                "receiptNumber wajib diisi."
            )

        if not po_id:
            raise ValueError(
                "poId wajib diisi."
            )

        existing_receipt = (
            self.repository.find_by_number(
                receipt_number
            )
        )

        if existing_receipt:
            raise ValueError(
                "receiptNumber sudah digunakan."
            )

        po = self.po_repository.find_by_id(
            po_id
        )

        if not po:
            raise ValueError(
                "Purchase Order tidak ditemukan."
            )

        if po.get("status") != (
            PurchaseOrderService.STATUS_APPROVED
        ) and po.get("status") != (
            PurchaseOrderService.STATUS_PARTIAL
        ):
            raise ValueError(
                "Goods Receipt hanya dapat dibuat "
                "untuk PO dengan status APPROVED atau PARTIAL."
            )

        processed_items = self._validate_items(
            po,
            items,
        )

        if receipt_date is None:
            receipt_date = datetime.now(
                timezone.utc
            )

        now = datetime.now(timezone.utc)

        receipt_data = {
            "receiptNumber": receipt_number,
            "poId": po_id,
            "supplierId": po.get("supplierId"),
            "receiptDate": receipt_date,
            "status": self.STATUS_RECEIVED,
            "items": processed_items,
            "receivedBy": received_by,
            "notes": notes,
            "createdAt": now,
            "updatedAt": now,
        }

        receipt = self.repository.create(
            receipt_data
        )

        try:
            receipt_id = str(
                receipt["_id"]
            )

            for item in processed_items:
                accepted_quantity = item[
                    "acceptedQuantity"
                ]

                if accepted_quantity <= 0:
                    continue

                self.stock_movement_service.create_movement(
                    product_id=item["productId"],
                    movement_type="IN",
                    quantity=accepted_quantity,
                    reference_type="GOODS_RECEIPT",
                    reference_id=receipt_id,
                    notes=(
                        f"Penerimaan barang "
                        f"{receipt_number}"
                    ),
                    created_by=received_by,
                )

        except Exception:
            self.repository.delete(
                receipt["_id"]
            )
            raise

        self._update_po_status(
            po_id
        )

        return receipt

    def get_all_goods_receipts(self):
        return self.repository.find_all()

    def get_goods_receipt_by_id(
        self,
        receipt_id,
    ):
        return self.repository.find_by_id(
            receipt_id
        )

    def get_goods_receipts_by_po(
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

