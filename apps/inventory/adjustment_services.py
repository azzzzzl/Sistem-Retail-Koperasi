from datetime import datetime, timezone

from .adjustment_repositories import StockAdjustmentRepository
from .services import StockMovementService


class StockAdjustmentService:
    """
    Service untuk business logic Stock Adjustment.
    """

    ADJUSTMENT_TYPES = {
        "INCREASE",
        "DECREASE",
    }

    def __init__(self):
        self.repository = StockAdjustmentRepository()
        self.stock_movement_service = StockMovementService()

    def create_adjustment(
        self,
        adjustment_number,
        product_id,
        adjustment_type,
        quantity,
        reason="",
        notes="",
        created_by=None,
    ):
        if not adjustment_number:
            raise ValueError(
                "adjustmentNumber wajib diisi."
            )

        if not product_id:
            raise ValueError(
                "productId wajib diisi."
            )

        if not adjustment_type:
            raise ValueError(
                "adjustmentType wajib diisi."
            )

        adjustment_type = adjustment_type.upper()

        if adjustment_type not in self.ADJUSTMENT_TYPES:
            raise ValueError(
                "adjustmentType harus berupa "
                "INCREASE atau DECREASE."
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError(
                "Quantity harus berupa angka."
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity harus lebih besar dari 0."
            )

        existing_adjustment = (
            self.repository.find_by_number(
                adjustment_number
            )
        )

        if existing_adjustment:
            raise ValueError(
                "adjustmentNumber sudah digunakan."
            )

        current_stock = (
            self.stock_movement_service
            .get_current_stock(product_id)
        )

        if (
            adjustment_type == "DECREASE"
            and quantity > current_stock
        ):
            raise ValueError(
                f"Stok tidak mencukupi. "
                f"Stok tersedia: {current_stock}."
            )

        if adjustment_type == "INCREASE":
            adjustment_quantity = quantity
        else:
            adjustment_quantity = -quantity

        new_stock = (
            current_stock + adjustment_quantity
        )

        if new_stock < 0:
            raise ValueError(
                "Adjustment tidak boleh membuat "
                "stok menjadi negatif."
            )

        now = datetime.now(timezone.utc)

        adjustment_data = {
            "adjustmentNumber": adjustment_number,
            "productId": product_id,
            "adjustmentType": adjustment_type,
            "quantity": quantity,
            "reason": reason,
            "notes": notes,
            "beforeStock": current_stock,
            "afterStock": new_stock,
            "adjustmentQuantity": adjustment_quantity,
            "createdBy": created_by,
            "createdAt": now,
        }

        adjustment = self.repository.create(
            adjustment_data
        )

        try:
            self.stock_movement_service.create_movement(
                product_id=product_id,
                movement_type="ADJUSTMENT",
                quantity=quantity,
                reference_type="STOCK_ADJUSTMENT",
                reference_id=str(
                    adjustment["_id"]
                ),
                notes=(
                    f"Stock adjustment "
                    f"{adjustment_number}: "
                    f"{current_stock} -> {new_stock}. "
                    f"{reason}"
                ),
                created_by=created_by,
                adjustment_quantity=adjustment_quantity,
            )
        except Exception:
            # Jika stock movement gagal, hapus dokumen
            # adjustment yang baru dibuat agar tidak
            # meninggalkan data adjustment tanpa movement.
            from bson import ObjectId

            try:
                adjustment_id = ObjectId(
                    adjustment["_id"]
                )

                self.repository.collection.delete_one({
                    "_id": adjustment_id
                })
            except Exception:
                pass

            raise

        return adjustment

    def get_all_adjustments(self):
        return self.repository.find_all()

    def get_adjustment_by_id(self, adjustment_id):
        return self.repository.find_by_id(
            adjustment_id
        )