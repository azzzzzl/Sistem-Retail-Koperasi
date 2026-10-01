from bson import ObjectId
from database.mongodb import get_database


class SalesRepository:
    def __init__(self):
        self.db = get_database()
        self.sales = self.db["sales"]

    def create_sale(self, sale_data):
        result = self.sales.insert_one(sale_data)
        return result.inserted_id

    def get_sale(self, sale_id):
        return self.sales.find_one({"_id": sale_id})

    def get_sales(self, limit=50):
        return list(self.sales.find().sort("saleDate", -1).limit(limit))

    def get_sales_by_member(self, member_id, limit=200):
        return list(
            self.sales.find({"memberId": str(member_id)})
            .sort("saleDate", -1)
            .limit(limit)
        )

    def claim_for_cancel(self, sale_id):
        from datetime import datetime, timezone
        return self.sales.find_one_and_update(
            {"_id": sale_id, "status": "COMPLETED"},
            {"$set": {"status": "CANCELLING", "cancellingAt": datetime.now(timezone.utc)}},
            return_document=__import__("pymongo").ReturnDocument.AFTER,
        )

    def update_sale(self, sale_id, data):
        return self.sales.update_one({"_id": sale_id}, {"$set": data})

    def delete_sale(self, sale_id):
        return self.sales.delete_one({"_id": sale_id})
