from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

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
        return list(self.collection.find().sort("createdAt", -1))

    def find_by_id(self, movement_id):
        try:
            object_id = ObjectId(movement_id)
        except Exception:
            return None
        return self.collection.find_one({"_id": object_id})

    def find_by_product(self, product_id):
        return list(self.collection.find({"productId": str(product_id)}).sort("createdAt", -1))

    def get_stock_balance(self, product_id):
        movements = self.collection.find({"productId": str(product_id)})
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
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None
        return self.products.find_one({"_id": object_id})

    def get_product_stock(self, product_id):
        product = self.get_product(product_id)
        return product.get("stock", 0) if product else None

    def update_product_stock(self, product_id, new_stock):
        """Backward-compatible non-conditional update."""
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None
        return self.products.update_one(
            {"_id": object_id},
            {"$set": {"stock": int(new_stock), "updatedAt": datetime.now(timezone.utc)}},
        )

    def apply_stock_change(self, product_id, delta):
        """Atomically apply a stock delta, preventing negative stock and races."""
        try:
            object_id = ObjectId(product_id)
            delta = int(delta)
        except (Exception, TypeError, ValueError):
            return None

        query = {"_id": object_id}
        if delta < 0:
            query["stock"] = {"$gte": abs(delta)}
        else:
            query["stock"] = {"$gte": 0}

        updated = self.products.find_one_and_update(
            query,
            {
                "$inc": {"stock": delta},
                "$set": {"updatedAt": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
        if not updated:
            return None
        return {
            "product": updated,
            "afterStock": int(updated.get("stock", 0)),
            "beforeStock": int(updated.get("stock", 0)) - delta,
        }

    def rollback_movement(self, movement):
        product_id = str(movement.get("productId"))
        before_stock = int(movement.get("beforeStock", 0))
        after_stock = int(movement.get("afterStock", 0))
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return False
        result = self.products.update_one(
            {"_id": object_id, "stock": after_stock},
            {"$set": {"stock": before_stock, "updatedAt": datetime.now(timezone.utc)}},
        )
        if result.modified_count != 1:
            return False
        self.collection.delete_one({"_id": movement.get("_id")})
        return True

    def restore_stock(self, product_id, expected_stock, restore_to):
        """Compensating rollback guarded by the stock value we changed."""
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None
        return self.products.update_one(
            {"_id": object_id, "stock": int(expected_stock)},
            {
                "$set": {
                    "stock": int(restore_to),
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
        )
