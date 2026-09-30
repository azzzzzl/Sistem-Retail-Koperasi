from datetime import datetime, timezone

from database.mongodb import db


class PurchaseOrderRepository:
    """
    Repository untuk mengelola purchase_orders di MongoDB.
    """

    COLLECTION_NAME = "purchase_orders"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, po_data):
        result = self.collection.insert_one(po_data)

        return self.collection.find_one({
            "_id": result.inserted_id
        })

    def find_all(self):
        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, po_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(po_id)
        except Exception:
            return None

        return self.collection.find_one({
            "_id": object_id
        })

    def find_by_number(self, po_number):
        return self.collection.find_one({
            "poNumber": po_number
        })

    def update(self, po_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(po_id)
        except Exception:
            return None

        update_data["updatedAt"] = datetime.now(timezone.utc)

        self.collection.update_one(
            {"_id": object_id},
            {"$set": update_data},
        )

        return self.collection.find_one({
            "_id": object_id
        })