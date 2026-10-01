from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import get_database


class PurchaseReturnRepository:
    def __init__(self): self.collection=get_database()["purchase_returns"]
    def create(self,data):
        result=self.collection.insert_one(data); return self.collection.find_one({"_id":result.inserted_id})
    def find_all(self): return list(self.collection.find().sort("returnDate",-1))
    def find_by_id(self, id):
        try: oid=ObjectId(id)
        except Exception: return None
        return self.collection.find_one({"_id":oid})
    def find_by_number(self, number): return self.collection.find_one({"returnNumber":number})
    def find_by_purchase(self,purchase_id): return list(self.collection.find({"purchaseId":purchase_id}))
    def claim_for_approval(self, id):
        try: oid=ObjectId(id)
        except Exception: return None
        return self.collection.find_one_and_update(
            {"_id":oid,"status":"PENDING"},
            {"$set":{"status":"PROCESSING","processingAt":datetime.now(timezone.utc)}},
            return_document=__import__("pymongo").ReturnDocument.AFTER,
        )

    def update(self,id,data):
        try: oid=ObjectId(id)
        except Exception: return None
        data=dict(data); data["updatedAt"]=datetime.now(timezone.utc)
        self.collection.update_one({"_id":oid},{"$set":data}); return self.find_by_id(id)
