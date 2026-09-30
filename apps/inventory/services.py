from datetime import datetime, timezone

from .repositories import StockMovementRepository


class StockMovementService:
    """
    Service untuk business logic Stock Movement.
    """

    MOVEMENT_TYPES = {
        "IN",
        "OUT",
        "ADJUSTMENT",
    }

    REFERENCE_TYPES = {
        "GOODS_RECEIPT",
        "SALE",
        "STOCK_OPNAME",
        "STOCK_ADJUSTMENT",
        "OTHER",
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
        """
        Membuat stock movement baru.
        """

        # ==========================
        # VALIDASI PRODUCT ID
        # ==========================

        if not product_id:
            raise ValueError("productId wajib diisi.")

        # ==========================
        # VALIDASI MOVEMENT TYPE
        # ==========================

        movement_type = movement_type.upper()

        if movement_type not in self.MOVEMENT_TYPES:
            raise ValueError(
                "movementType harus berupa IN, OUT, atau ADJUSTMENT."
            )

        # ==========================
        # VALIDASI QUANTITY
        # ==========================

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Quantity harus berupa angka.")

        if quantity <= 0:
            raise ValueError("Quantity harus lebih besar dari 0.")

        # ==========================
        # VALIDASI REFERENCE TYPE
        # ==========================

        reference_type = reference_type.upper()

        if reference_type not in self.REFERENCE_TYPES:
            raise ValueError(
                "referenceType tidak valid."
            )

        # ==========================
        # VALIDASI STOCK UNTUK OUT
        # ==========================

        current_stock = self.repository.get_stock_balance(product_id)

        if movement_type == "OUT":
            if quantity > current_stock:
                raise ValueError(
                    f"Stok tidak mencukupi. "
                    f"Stok tersedia: {current_stock}."
                )

        # ==========================
        # DATA MOVEMENT
        # ==========================

        movement_data = {
            "productId": product_id,
            "movementType": movement_type,
            "quantity": quantity,
            "referenceType": reference_type,
            "referenceId": reference_id,
            "notes": notes,
            "createdBy": created_by,
            "createdAt": datetime.now(timezone.utc),
        }

        # ==========================
        # ADJUSTMENT
        # ==========================

        if movement_type == "ADJUSTMENT":

            if adjustment_quantity is None:
                raise ValueError(
                    "adjustmentQuantity wajib diisi untuk adjustment."
                )

            try:
                adjustment_quantity = int(adjustment_quantity)
            except (TypeError, ValueError):
                raise ValueError(
                    "adjustmentQuantity harus berupa angka."
                )

            new_stock = current_stock + adjustment_quantity

            if new_stock < 0:
                raise ValueError(
                    "Hasil adjustment tidak boleh membuat stok negatif."
                )

            movement_data["adjustmentQuantity"] = adjustment_quantity

        # ==========================
        # SIMPAN
        # ==========================

        return self.repository.create(movement_data)

    def get_all_movements(self):
        """
        Mengambil semua stock movement.
        """

        return self.repository.find_all()

    def get_movement_by_id(self, movement_id):
        """
        Mengambil satu movement berdasarkan ID.
        """

        return self.repository.find_by_id(movement_id)

    def get_product_movements(self, product_id):
        """
        Mengambil histori movement suatu produk.
        """

        if not product_id:
            raise ValueError("productId wajib diisi.")

        return self.repository.find_by_product(product_id)

    def get_current_stock(self, product_id):
        """
        Mengambil saldo stok produk.
        """

        if not product_id:
            raise ValueError("productId wajib diisi.")

        return self.repository.get_stock_balance(product_id)