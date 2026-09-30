from bson import ObjectId

from database.mongodb import get_database


class PosProductRepository:
    def __init__(self):
        self.db = get_database()
        self.products = self.db["products"]

    def search_products(self, search=""):
        query = {}

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"sku": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}},
            ]

        return list(
            self.products.find(query).limit(20)
        )

    def get_product(self, product_id):
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        return self.products.find_one({
            "_id": object_id
        })