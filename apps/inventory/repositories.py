from datetime import datetime, timezone

from bson import ObjectId

from database.mongodb import db


class StockMovementRepository:
    COLLECTION_NAME = "stock_movements"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]
        self.products = db["products"]

    def create(self, movement_data):
        result = self.collection.insert_one(movement_data)
        return self.collection.find_one({"_id": result.inserted_id})

    def find_all(self):
        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, movement_id):
        try:
            object_id = ObjectId(movement_id)
        except Exception:
            return None

        return self.collection.find_one({
            "_id": object_id
        })

    def find_by_product(self, product_id):
        return list(
            self.collection.find({
                "productId": product_id
            }).sort("createdAt", -1)
        )

    def get_stock_balance(self, product_id):
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

    def get_product(self, product_id):
        """
        Mengambil product dari collection products.
        product_id berasal dari sistem sebagai string,
        kemudian dikonversi menjadi ObjectId untuk query MongoDB.
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        return self.products.find_one({
            "_id": object_id
        })

    def get_product_stock(self, product_id):
        """
        Mengambil stock aktual dari collection products.
        """
        product = self.get_product(product_id)

        if not product:
            return None

        return product.get("stock", 0)

    def update_product_stock(self, product_id, new_stock):
        """
        Mengubah stock pada collection products.
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        return self.products.update_one(
            {
                "_id": object_id
            },
            {
                "$set": {
                    "stock": new_stock
                }
            }
        )