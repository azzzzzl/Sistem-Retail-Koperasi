from database.mongodb import get_database


class ReturnsRepository:
    def __init__(self):
        self.db = get_database()
        self.returns = self.db["returns"]

    def create_return(self, return_data):
        result = self.returns.insert_one(return_data)
        return result.inserted_id

    def get_return(self, return_id):
        return self.returns.find_one({
            "_id": return_id
        })

    def get_returns(self, limit=50):
        return list(
            self.returns.find()
            .sort("returnDate", -1)
            .limit(limit)
        )

    def delete_return(self, return_id):
        return self.returns.delete_one({"_id": return_id})

    def claim_for_approval(self, return_id):
        from datetime import datetime, timezone
        return self.returns.find_one_and_update(
            {"_id": return_id, "status": "PENDING"},
            {"$set": {"status": "PROCESSING", "processingAt": datetime.now(timezone.utc)}},
            return_document=__import__("pymongo").ReturnDocument.AFTER,
        )

    def update_return(self, return_id, data):
        return self.returns.update_one({"_id": return_id}, {"$set": data})

    def get_returns_by_sale(self, sale_id):
        return list(
            self.returns.find({
                "saleId": sale_id
            }).sort("returnDate", -1)
        )