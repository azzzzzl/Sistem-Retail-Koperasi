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
        Membuat stock movement baru dan memperbarui products.stock.
        """

        # ==========================
        # VALIDASI PRODUCT ID
        # ==========================

        if not product_id:
            raise ValueError("productId wajib diisi.")

        # Pastikan product benar-benar ada
        product = self.repository.get_product(product_id)

        if not product:
            raise ValueError(
                f"Product dengan ID {product_id} tidak ditemukan."
            )

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
        # AMBIL STOCK AKTUAL
        # ==========================

        current_stock = product.get("stock", 0)

        try:
            current_stock = int(current_stock)
        except (TypeError, ValueError):
            raise ValueError(
                "Stock produk harus berupa angka."
            )

        if current_stock < 0:
            raise ValueError(
                "Stock produk tidak boleh negatif."
            )

        # ==========================
        # HITUNG STOCK BARU
        # ==========================

        if movement_type == "IN":

            new_stock = current_stock + quantity

        elif movement_type == "OUT":

            if quantity > current_stock:
                raise ValueError(
                    f"Stok tidak mencukupi. "
                    f"Stok tersedia: {current_stock}."
                )

            new_stock = current_stock - quantity

        else:
            # ADJUSTMENT
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

        # ==========================
        # DATA MOVEMENT
        # ==========================

        movement_data = {
            "productId": product_id,
            "movementType": movement_type,
            "quantity": quantity,
            "beforeStock": current_stock,
            "afterStock": new_stock,
            "referenceType": reference_type,
            "referenceId": reference_id,
            "notes": notes,
            "createdBy": created_by,
            "createdAt": datetime.now(timezone.utc),
        }

        if movement_type == "ADJUSTMENT":
            movement_data["adjustmentQuantity"] = adjustment_quantity

        # ==========================
        # UPDATE PRODUCT STOCK
        # ==========================

        update_result = self.repository.update_product_stock(
            product_id,
            new_stock
        )

        if not update_result:
            raise ValueError(
                "Gagal memperbarui stok produk."
            )

        if update_result.matched_count == 0:
            raise ValueError(
                f"Product dengan ID {product_id} tidak ditemukan."
            )

        # ==========================
        # SIMPAN STOCK MOVEMENT
        # ==========================

        try:
            return self.repository.create(movement_data)

        except Exception:
            # Rollback stock jika movement gagal disimpan
            self.repository.update_product_stock(
                product_id,
                current_stock
            )

            raise

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
        Mengambil saldo stok aktual dari products.stock.
        """

        if not product_id:
            raise ValueError("productId wajib diisi.")

        stock = self.repository.get_product_stock(product_id)

        if stock is None:
            raise ValueError(
                f"Product dengan ID {product_id} tidak ditemukan."
            )

        return stock