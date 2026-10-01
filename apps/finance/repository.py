from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import get_database


class ExpenseRepository:
    def __init__(self):
        self.collection = get_database()["expenses"]

    def create(self, data):
        result = self.collection.insert_one(data)
        return self.collection.find_one({"_id": result.inserted_id})

    def find_all(self):
        return list(self.collection.find().sort("date", -1))

    def find_by_id(self, item_id):
        try: oid=ObjectId(item_id)
        except Exception: return None
        return self.collection.find_one({"_id":oid})

    def update(self, item_id, data):
        try: oid=ObjectId(item_id)
        except Exception: return None
        data=dict(data); data["updatedAt"]=datetime.now(timezone.utc)
        self.collection.update_one({"_id":oid},{"$set":data})
        return self.find_by_id(item_id)

    def exists_number(self, number, exclude_id=None):
        q={"expenseNumber":number}
        if exclude_id and ObjectId.is_valid(exclude_id): q["_id"]={"$ne":ObjectId(exclude_id)}
        return self.collection.find_one(q) is not None

    def count_by_category(self):
        return list(self.collection.aggregate([{"$group":{"_id":"$category","total":{"$sum":{"$ifNull":["$amount",0]}},"count":{"$sum":1}}},{"$sort":{"total":-1}}]))
