from datetime import datetime, timezone

from bson import ObjectId

from database.mongodb import get_database


class ReportsRepository:
    def __init__(self):
        self.db = get_database()
        self.products = self.db["products"]
        self.categories = self.db["categories"]
        self.suppliers = self.db["suppliers"]
        self.members = self.db["members"]
        self.sales = self.db["sales"]
        self.purchases = self.db["purchases"]
        self.purchase_orders = self.db["purchase_orders"]
        self.goods_receipts = self.db["goods_receipts"]
        self.invoices = self.db["supplier_invoices"]
        self.payments = self.db["supplier_payments"]
        self.stock_movements = self.db["stock_movements"]
        self.stock_opnames = self.db["stock_opnames"]
        self.expenses = self.db["expenses"]
        self.audit_logs = self.db["audit_logs"]

    @staticmethod
    def _period(field, start, end):
        if start is None and end is None:
            return {}
        query = {}
        if start is not None:
            query[field] = {"$gte": start}
        if end is not None:
            query.setdefault(field, {})["$lt"] = end
        return query

    def count(self, collection, query=None):
        return collection.count_documents(query or {})

    def find(self, collection, query=None, projection=None, sort=None, limit=0):
        cursor = collection.find(query or {}, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def latest_stock_movements(self):
        pipeline = [
            {"$sort": {"productId": 1, "createdAt": -1}},
            {"$group": {
                "_id": "$productId",
                "movement": {"$first": "$$ROOT"},
            }},
        ]
        return list(self.stock_movements.aggregate(pipeline))

    def aggregate_sales(self, query):
        pipeline = [{"$match": query}] if query else []
        pipeline.append({"$group": {
            "_id": None,
            "transactionCount": {"$sum": 1},
            "total": {"$sum": {"$ifNull": ["$total", 0]}},
        }})
        return list(self.sales.aggregate(pipeline))

    def aggregate_purchases(self, query):
        pipeline = [{"$match": query}] if query else []
        pipeline.append({"$group": {
            "_id": None,
            "transactionCount": {"$sum": 1},
            "total": {"$sum": {"$ifNull": ["$total", 0]}},
        }})
        return list(self.purchases.aggregate(pipeline))
