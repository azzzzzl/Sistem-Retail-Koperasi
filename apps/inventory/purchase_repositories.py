from datetime import datetime, timezone

from database.mongodb import db


class PurchaseRepository:
    COLLECTION_NAME = "purchases"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, purchase_data):
        result = self.collection.insert_one(
            purchase_data
        )

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

    def find_by_id(self, purchase_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(purchase_id)
        except Exception:
            return None

        return self.collection.find_one(
            {"_id": object_id}
        )

    def find_by_number(self, purchase_number):
        return self.collection.find_one(
            {
                "purchaseNumber": purchase_number
            }
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

    def find_by_goods_receipt_id(
        self,
        goods_receipt_id,
    ):
        return list(
            self.collection.find(
                {
                    "goodsReceiptId": goods_receipt_id
                }
            ).sort(
                "createdAt",
                -1,
            )
        )

    def update(self, purchase_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(purchase_id)
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