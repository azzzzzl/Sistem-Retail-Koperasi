from datetime import datetime, timezone

from database.mongodb import db


class StockOpnameRepository:
    """
    Repository untuk mengelola data stock_opnames di MongoDB.
    """

    COLLECTION_NAME = "stock_opnames"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, opname_data):
        result = self.collection.insert_one(opname_data)

        return self.collection.find_one({
            "_id": result.inserted_id
        })

    def find_all(self):
        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, opname_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(opname_id)
        except Exception:
            return None

        return self.collection.find_one({
            "_id": object_id
        })

    def find_by_number(self, opname_number):
        return self.collection.find_one({
            "opnameNumber": opname_number
        })

    def update(self, opname_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(opname_id)
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