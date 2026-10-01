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
        self.returns = self.db["returns"]
        self.purchase_returns = self.db["purchase_returns"]

    @staticmethod
    def _period(field, start, end):
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

    def find_first_available_period(self, collection, start, end, fields):
        clauses = []
        for field in fields:
            clause = self._period(field, start, end)
            if clause:
                clauses.append(clause)
        if not clauses:
            return {}
        return {"$or": clauses}

    def recent_transactions(self, limit=10):
        sales = [dict(x, kind="SALE") for x in self.sales.find().sort("saleDate", -1).limit(limit)]
        purchases = [dict(x, kind="PURCHASE") for x in self.purchases.find().sort("purchaseDate", -1).limit(limit)]
        rows = sales + purchases
        rows.sort(key=lambda x: x.get("saleDate") or x.get("purchaseDate") or x.get("createdAt"), reverse=True)
        return rows[:limit]
