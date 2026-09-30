from datetime import datetime, timezone

from database.mongodb import db


class GoodsReceiptRepository:
    COLLECTION_NAME = "goods_receipts"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, receipt_data):
        result = self.collection.insert_one(receipt_data)

        return self.collection.find_one(
            {"_id": result.inserted_id}
        )

    def find_all(self):
        return list(
            self.collection.find().sort(
                "createdAt",
                -1,
            )
        )

    def find_by_id(self, receipt_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(receipt_id)
        except Exception:
            return None

        return self.collection.find_one(
            {"_id": object_id}
        )

    def find_by_number(self, receipt_number):
        return self.collection.find_one(
            {"receiptNumber": receipt_number}
        )

    def find_by_po_id(self, po_id):
        return list(
            self.collection.find(
                {"poId": po_id}
            ).sort(
                "createdAt",
                -1,
            )
        )

    def delete(self, receipt_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(receipt_id)
        except Exception:
            return False

        result = self.collection.delete_one(
            {"_id": object_id}
        )

        return result.deleted_count > 0

    def update(self, receipt_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(receipt_id)
        except Exception:
            return None

        update_data["updatedAt"] = datetime.now(
            timezone.utc
        )

        self.collection.update_one(
            {"_id": object_id},
            {"$set": update_data},
        )

        return self.collection.find_one(
            {"_id": object_id}
        )
