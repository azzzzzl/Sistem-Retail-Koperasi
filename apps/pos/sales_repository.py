from database.mongodb import get_database


class SalesRepository:
    def __init__(self):
        self.db = get_database()
        self.sales = self.db["sales"]

    def create_sale(self, sale_data):
        result = self.sales.insert_one(sale_data)
        return result.inserted_id

    def get_sale(self, sale_id):
        return self.sales.find_one({
            "_id": sale_id
        })

    def get_sales(self, limit=50):
        return list(
            self.sales.find()
            .sort("saleDate", -1)
            .limit(limit)
        )