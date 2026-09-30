from datetime import datetime, timezone

from database.mongodb import db


class StockAdjustmentRepository:
    """
    Repository untuk mengelola data stock_adjustments di MongoDB.
    """

    COLLECTION_NAME = "stock_adjustments"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, adjustment_data):
        result = self.collection.insert_one(adjustment_data)

        return self.collection.find_one({
            "_id": result.inserted_id
        })

    def find_all(self):
        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, adjustment_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(adjustment_id)
        except Exception:
            return None

        return self.collection.find_one({
            "_id": object_id
        })

    def find_by_number(self, adjustment_number):
        return self.collection.find_one({
            "adjustmentNumber": adjustment_number
        })