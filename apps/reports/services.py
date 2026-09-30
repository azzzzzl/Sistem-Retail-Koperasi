from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation

from bson import ObjectId

from .repositories import ReportsRepository


class ReportService:
    def __init__(self, repository=None):
        self.repository = repository or ReportsRepository()

    @staticmethod
    def parse_period(start_date=None, end_date=None):
        start = None
        end = None
        try:
            if start_date:
                start = datetime.combine(
                    datetime.strptime(start_date, "%Y-%m-%d").date(),
                    time.min,
                    tzinfo=timezone.utc,
                )
            if end_date:
                end = datetime.combine(
                    datetime.strptime(end_date, "%Y-%m-%d").date() + timedelta(days=1),
                    time.min,
                    tzinfo=timezone.utc,
                )
        except ValueError as exc:
            raise ValueError("Format tanggal harus YYYY-MM-DD.") from exc
        if start and end and start >= end:
            raise ValueError("start_date harus lebih kecil atau sama dengan end_date.")
        return start, end

    @staticmethod
    def number(value):
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    @staticmethod
    def output_number(value):
        value = Decimal(value)
        return int(value) if value == value.to_integral_value() else float(value)

    @staticmethod
    def serialize_id(value):
        return str(value) if value is not None else None

    def dashboard(self, low_stock_threshold=5, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        period_query = self.repository._period("createdAt", start, end)
        latest = self.repository.latest_stock_movements()
        latest_stock = {str(row["_id"]): row["movement"].get("afterStock", 0) for row in latest if row.get("_id") is not None}

        products = self.repository.find(self.repository.products, projection={"name": 1, "stock": 1, "status": 1})
        low_stock = []
        for product in products:
            product_id = str(product["_id"])
            stock = latest_stock.get(product_id, product.get("stock", 0))
            if self.number(stock) <= self.number(low_stock_threshold):
                low_stock.append({
                    "productId": product_id,
                    "name": product.get("name"),
                    "stock": self.output_number(self.number(stock)),
                })

        sales = self.repository.aggregate_sales(period_query)
        purchases = self.repository.aggregate_purchases(period_query)
        sale_summary = sales[0] if sales else {"transactionCount": 0, "total": 0}
        purchase_summary = purchases[0] if purchases else {"transactionCount": 0, "total": 0}

        outstanding = self.repository.find(
            self.repository.invoices,
            {"remainingAmount": {"$gt": 0}},
            projection={"remainingAmount": 1},
        )
        supplier_debt = sum((self.number(x.get("remainingAmount")) for x in outstanding), Decimal("0"))

        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "totals": {
                "products": self.repository.count(self.repository.products),
                "suppliers": self.repository.count(self.repository.suppliers),
                "members": self.repository.count(self.repository.members),
                "categories": self.repository.count(self.repository.categories),
                "lowStockProducts": len(low_stock),
            },
            "sales": {
                "transactionCount": sale_summary.get("transactionCount", 0),
                "total": self.output_number(self.number(sale_summary.get("total"))),
            },
            "purchases": {
                "transactionCount": purchase_summary.get("transactionCount", 0),
                "total": self.output_number(self.number(purchase_summary.get("total"))),
            },
            "supplierDebt": self.output_number(supplier_debt),
            "lowStock": sorted(low_stock, key=lambda x: self.number(x["stock"])),
            "recentTransactions": self.sales_recent(10),
        }

    def sales_recent(self, limit=10):
        docs = self.repository.find(self.repository.sales, sort=[("createdAt", -1)], limit=limit)
        return [self.clean_document(x) for x in docs]

    def sales_report(self, start_date=None, end_date=None, product_id=None, cashier=None):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        if product_id:
            query["items.productId"] = product_id
        if cashier:
            query["cashier"] = cashier
        docs = self.repository.find(self.repository.sales, query, sort=[("createdAt", -1)])
        total = sum((self.number(d.get("total")) for d in docs), Decimal("0"))
        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "summary": {"transactionCount": len(docs), "total": self.output_number(total)},
            "data": [self.clean_document(d) for d in docs],
        }

    def purchase_report(self, start_date=None, end_date=None, supplier_id=None):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        if supplier_id:
            query["supplierId"] = supplier_id
        docs = self.repository.find(self.repository.purchases, query, sort=[("createdAt", -1)])
        total = sum((self.number(d.get("total")) for d in docs), Decimal("0"))
        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "summary": {"transactionCount": len(docs), "total": self.output_number(total)},
            "data": [self.clean_document(d) for d in docs],
        }

    def inventory_report(self, low_stock_threshold=5, product_id=None):
        latest = self.repository.latest_stock_movements()
        latest_stock = {str(row["_id"]): row["movement"].get("afterStock", 0) for row in latest if row.get("_id") is not None}
        query = {"_id": {"$exists": True}}
        if product_id:
            try:
                query["_id"] = ObjectId(product_id)
            except Exception:
                return {"summary": {"productCount": 0, "lowStockCount": 0}, "data": []}
        products = self.repository.find(self.repository.products, query, sort=[("name", 1)])
        rows = []
        for p in products:
            pid = str(p["_id"])
            stock = self.number(latest_stock.get(pid, p.get("stock", 0)))
            rows.append({
                "productId": pid,
                "sku": p.get("sku"),
                "barcode": p.get("barcode"),
                "name": p.get("name"),
                "categoryId": p.get("category_id"),
                "stock": self.output_number(stock),
                "status": p.get("status"),
                "lowStock": stock <= self.number(low_stock_threshold),
            })
        return {
            "summary": {"productCount": len(rows), "lowStockCount": sum(1 for x in rows if x["lowStock"])},
            "data": rows,
        }

    def supplier_report(self, supplier_id=None):
        query = {}
        if supplier_id:
            try:
                query["_id"] = ObjectId(supplier_id)
            except Exception:
                return {"summary": {"supplierCount": 0}, "data": []}
        suppliers = self.repository.find(self.repository.suppliers, query, sort=[("name", 1)])
        invoices = self.repository.find(self.repository.invoices)
        grouped = defaultdict(lambda: {"invoiceCount": 0, "invoiceTotal": Decimal("0"), "outstanding": Decimal("0")})
        for inv in invoices:
            sid = str(inv.get("supplierId"))
            grouped[sid]["invoiceCount"] += 1
            grouped[sid]["invoiceTotal"] += self.number(inv.get("total"))
            grouped[sid]["outstanding"] += self.number(inv.get("remainingAmount"))
        rows = []
        for s in suppliers:
            sid = str(s["_id"])
            g = grouped[sid]
            rows.append({
                "supplierId": sid,
                "code": s.get("code"),
                "name": s.get("name"),
                "phone": s.get("phone"),
                "email": s.get("email"),
                "status": s.get("status"),
                "invoiceCount": g["invoiceCount"],
                "invoiceTotal": self.output_number(g["invoiceTotal"]),
                "outstanding": self.output_number(g["outstanding"]),
            })
        return {"summary": {"supplierCount": len(rows)}, "data": rows}

    def payable_report(self, start_date=None, end_date=None, supplier_id=None, outstanding_only=False):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        if supplier_id:
            query["supplierId"] = supplier_id
        if outstanding_only:
            query["remainingAmount"] = {"$gt": 0}
        invoices = self.repository.find(self.repository.invoices, query, sort=[("createdAt", -1)])
        total = sum((self.number(x.get("total")) for x in invoices), Decimal("0"))
        paid = sum((self.number(x.get("paidAmount")) for x in invoices), Decimal("0"))
        remaining = sum((self.number(x.get("remainingAmount")) for x in invoices), Decimal("0"))
        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "summary": {
                "invoiceCount": len(invoices),
                "total": self.output_number(total),
                "paid": self.output_number(paid),
                "remaining": self.output_number(remaining),
            },
            "data": [self.clean_document(x) for x in invoices],
        }

    def profit_report(self, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        sales = self.repository.find(self.repository.sales, query)
        expenses = self.repository.find(self.repository.expenses, query)
        revenue = sum((self.number(x.get("total")) for x in sales), Decimal("0"))
        cost = Decimal("0")
        for sale in sales:
            for item in sale.get("items", []) or []:
                qty = self.number(item.get("quantity"))
                purchase_price = self.number(item.get("purchasePrice", item.get("costPrice", 0)))
                cost += qty * purchase_price
        expense_total = sum((self.number(x.get("amount", x.get("total", 0))) for x in expenses), Decimal("0"))
        gross = revenue - cost
        net = gross - expense_total
        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "summary": {
                "revenue": self.output_number(revenue),
                "costOfGoodsSold": self.output_number(cost),
                "grossProfit": self.output_number(gross),
                "expenses": self.output_number(expense_total),
                "netProfit": self.output_number(net),
            },
        }

    def audit_logs(self, start_date=None, end_date=None, action=None, module=None, user_id=None, limit=100):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        if action:
            query["action"] = action.lower()
        if module:
            query["module"] = module
        if user_id:
            query["userId"] = user_id
        docs = self.repository.find(self.repository.audit_logs, query, sort=[("createdAt", -1)], limit=limit)
        return {"count": len(docs), "data": [self.clean_document(x) for x in docs]}

    @classmethod
    def clean_document(cls, document):
        if isinstance(document, dict):
            return {key: cls.clean_document(value) for key, value in document.items()}
        if isinstance(document, list):
            return [cls.clean_document(x) for x in document]
        if hasattr(document, "isoformat"):
            return document.isoformat()
        if isinstance(document, Decimal):
            return cls.output_number(document)
        try:
            from bson import ObjectId
            if isinstance(document, ObjectId):
                return str(document)
        except ImportError:
            pass
        return document
