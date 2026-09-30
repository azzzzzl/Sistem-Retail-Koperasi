from datetime import datetime, timezone

from database.mongodb import db


class StockMovementRepository:
    """
    Repository untuk mengelola data stock_movements di MongoDB.
    """

    COLLECTION_NAME = "stock_movements"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, movement_data):
        """
        Menyimpan satu stock movement.
        """

        result = self.collection.insert_one(movement_data)

        return self.collection.find_one({
            "_id": result.inserted_id
        })

    def find_all(self):
        """
        Mengambil seluruh stock movement.
        Data terbaru ditampilkan lebih dahulu.
        """

        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, movement_id):
        """
        Mengambil stock movement berdasarkan ID.
        """

        from bson import ObjectId

        try:
            object_id = ObjectId(movement_id)
        except Exception:
            return None

        return self.collection.find_one({
            "_id": object_id
        })

    def find_by_product(self, product_id):
        """
        Mengambil seluruh movement berdasarkan productId.
        """

        return list(
            self.collection.find({
                "productId": product_id
            }).sort("createdAt", -1)
        )

    def get_stock_balance(self, product_id):
        """
        Menghitung stok berdasarkan seluruh stock movement.

        IN  = menambah stok
        OUT = mengurangi stok
        ADJUSTMENT = mengikuti adjustmentQuantity
        """

        movements = self.collection.find({
            "productId": product_id
        })

        balance = 0

        for movement in movements:
            movement_type = movement.get("movementType")

            if movement_type == "IN":
                balance += movement.get("quantity", 0)

            elif movement_type == "OUT":
                balance -= movement.get("quantity", 0)

            elif movement_type == "ADJUSTMENT":
                balance += movement.get("adjustmentQuantity", 0)

        return balance