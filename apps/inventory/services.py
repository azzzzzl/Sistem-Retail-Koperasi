from datetime import datetime, timezone

from .repositories import StockMovementRepository


class StockMovementService:
    MOVEMENT_TYPES = {"IN", "OUT", "ADJUSTMENT"}
    REFERENCE_TYPES = {
        "GOODS_RECEIPT", "SALE", "STOCK_OPNAME", "STOCK_ADJUSTMENT",
        "OPENING_BALANCE", "MASTER_DATA", "PURCHASE_RETURN", "SALES_RETURN", "SALE_CANCEL", "OTHER",
    }

    def __init__(self):
        self.repository = StockMovementRepository()

    def create_movement(
        self,
        product_id,
        movement_type,
        quantity,
        reference_type,
        reference_id=None,
        notes="",
        created_by=None,
        adjustment_quantity=None,
    ):
        if not product_id:
            raise ValueError("productId wajib diisi.")
        product = self.repository.get_product(product_id)
        if not product:
            raise ValueError(f"Product dengan ID {product_id} tidak ditemukan.")

        movement_type = str(movement_type or "").upper()
        if movement_type not in self.MOVEMENT_TYPES:
            raise ValueError("movementType harus berupa IN, OUT, atau ADJUSTMENT.")

        try:
            quantity = int(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("Quantity harus berupa angka.") from exc
        if quantity <= 0:
            raise ValueError("Quantity harus lebih besar dari 0.")

        reference_type = str(reference_type or "").upper()
        if reference_type not in self.REFERENCE_TYPES:
            raise ValueError("referenceType tidak valid.")

        if movement_type == "ADJUSTMENT":
            if adjustment_quantity is None:
                raise ValueError("adjustmentQuantity wajib diisi untuk adjustment.")
            try:
                adjustment_quantity = int(adjustment_quantity)
            except (TypeError, ValueError) as exc:
                raise ValueError("adjustmentQuantity harus berupa angka.") from exc
            if adjustment_quantity == 0:
                raise ValueError("adjustmentQuantity tidak boleh 0.")
            delta = adjustment_quantity
        elif movement_type == "IN":
            delta = quantity
        else:
            delta = -quantity

        result = self.repository.apply_stock_change(product_id, delta)
        if not result:
            if delta < 0:
                raise ValueError("Stok tidak mencukupi atau produk tidak ditemukan.")
            raise ValueError("Gagal memperbarui stok produk.")

        before_stock = result["beforeStock"]
        after_stock = result["afterStock"]
        now = datetime.now(timezone.utc)
        movement_data = {
            "productId": str(product_id),
            "movementType": movement_type,
            "quantity": quantity,
            "beforeStock": before_stock,
            "afterStock": after_stock,
            "referenceType": reference_type,
            "referenceId": str(reference_id) if reference_id is not None else None,
            "notes": notes,
            "createdBy": created_by,
            "createdAt": now,
        }
        if movement_type == "ADJUSTMENT":
            movement_data["adjustmentQuantity"] = adjustment_quantity

        try:
            return self.repository.create(movement_data)
        except Exception:
            rollback = self.repository.restore_stock(product_id, after_stock, before_stock)
            if not rollback or getattr(rollback, "modified_count", 0) != 1:
                raise RuntimeError(
                    "Stock movement gagal disimpan dan rollback stok juga gagal; periksa stok produk."
                )
            raise

    def get_all_movements(self):
        return self.repository.find_all()

    def get_movement_by_id(self, movement_id):
        return self.repository.find_by_id(movement_id)

    def get_product_movements(self, product_id):
        if not product_id:
            raise ValueError("productId wajib diisi.")
        return self.repository.find_by_product(product_id)

    def get_current_stock(self, product_id):
        if not product_id:
            raise ValueError("productId wajib diisi.")
        stock = self.repository.get_product_stock(product_id)
        if stock is None:
            raise ValueError(f"Product dengan ID {product_id} tidak ditemukan.")
        return int(stock)
