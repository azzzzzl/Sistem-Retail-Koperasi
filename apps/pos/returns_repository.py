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

    def get_returns_by_sale(self, sale_id):
        return list(
            self.returns.find({
                "saleId": sale_id
            }).sort("returnDate", -1)
        )