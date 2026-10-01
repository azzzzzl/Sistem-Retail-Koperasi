from datetime import datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation

from bson import ObjectId

from .repositories import ReportsRepository


class ReportService:
    def __init__(self, repository=None):
        self.repository = repository or ReportsRepository()

    @staticmethod
    def parse_period(start_date=None, end_date=None):
        start = end = None
        try:
            if start_date:
                start = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time.min, tzinfo=timezone.utc)
            if end_date:
                end = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
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

    @classmethod
    def clean_document(cls, document):
        if isinstance(document, dict):
            return {key: cls.clean_document(value) for key, value in document.items()}
        if isinstance(document, list):
            return [cls.clean_document(x) for x in document]
        if isinstance(document, Decimal):
            return cls.output_number(document)
        if isinstance(document, (datetime,)):
            return document.isoformat()
        if isinstance(document, ObjectId):
            return str(document)
        return document

    def _period_query(self, fields, start, end):
        if start is None and end is None:
            return {}
        return self.repository.find_first_available_period(self.repository.sales, start, end, fields) if len(fields) > 1 else self.repository._period(fields[0], start, end)

    def _get_product_map(self):
        return {str(p["_id"]): p for p in self.repository.products.find({})}

    def dashboard(self, low_stock_threshold=5, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        sales_query = self.repository._period("saleDate", start, end)
        sales_query["status"] = "COMPLETED"
        purchase_query = self.repository._period("purchaseDate", start, end)
        invoice_query = self.repository._period("invoiceDate", start, end)
        product_docs = self.repository.find(self.repository.products, sort=[("name", 1)])
        low_stock = []
        for p in product_docs:
            if p.get("status", "active") != "active":
                continue
            stock = self.number(p.get("stock", 0))
            minimum = self.number(p.get("minimumStock", p.get("minimum_stock", low_stock_threshold)))
            if stock <= minimum:
                low_stock.append({"productId": str(p["_id"]), "name": p.get("name", ""), "stock": self.output_number(stock), "minimumStock": self.output_number(minimum)})
        sales = self.repository.find(self.repository.sales, sales_query)
        purchases = self.repository.find(self.repository.purchases, purchase_query)
        invoices = self.repository.find(self.repository.invoices, invoice_query)
        expenses = self.repository.find(self.repository.expenses, self.repository._period("date", start, end))
        sale_total = sum((self.number(x.get("total")) for x in sales), Decimal("0"))
        purchase_total = sum((self.number(x.get("total")) for x in purchases), Decimal("0"))
        debt_docs = self.repository.find(self.repository.invoices, {"remainingAmount": {"$gt": 0}})
        debt = sum((self.number(x.get("remainingAmount")) for x in debt_docs), Decimal("0"))
        expense_total = sum((self.number(x.get("amount")) for x in expenses), Decimal("0"))
        return {
            "period": {"startDate": start_date, "endDate": end_date},
            "totals": {
                "products": self.repository.count(self.repository.products, {"status": "active"}),
                "suppliers": self.repository.count(self.repository.suppliers, {"status": "active"}),
                "members": self.repository.count(self.repository.members, {"status": "active"}),
                "categories": self.repository.count(self.repository.categories, {"status": "active"}),
                "lowStockProducts": len(low_stock),
            },
            "sales": {"transactionCount": len(sales), "total": self.output_number(sale_total)},
            "purchases": {"transactionCount": len(purchases), "total": self.output_number(purchase_total)},
            "supplierDebt": self.output_number(debt),
            "expenses": self.output_number(expense_total),
            "lowStock": low_stock,
            "recentTransactions": [self.clean_document(x) for x in self.repository.recent_transactions(10)],
        }

    def sales_report(self, start_date=None, end_date=None, product_id=None, cashier_id=None, member_id=None):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("saleDate", start, end)
        if product_id:
            query["items.productId"] = str(product_id)
        if cashier_id:
            query["cashierId"] = str(cashier_id)
        if member_id:
            query["memberId"] = str(member_id)
        query["status"] = {"$ne": "CANCELLED"}
        sales = self.repository.find(self.repository.sales, query, sort=[("saleDate", -1)])
        total = sum((self.number(s.get("total")) for s in sales), Decimal("0"))
        return {"period": {"startDate": start_date, "endDate": end_date}, "filters": {"productId": product_id, "cashierId": cashier_id, "memberId": member_id}, "summary": {"transactionCount": len(sales), "total": self.output_number(total)}, "data": [self.clean_document(x) for x in sales]}

    def purchase_report(self, start_date=None, end_date=None, supplier_id=None, product_id=None):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("purchaseDate", start, end)
        if supplier_id:
            query["supplierId"] = str(supplier_id)
        if product_id:
            query["items.productId"] = str(product_id)
        purchases = self.repository.find(self.repository.purchases, query, sort=[("purchaseDate", -1)])
        total = sum((self.number(x.get("total")) for x in purchases), Decimal("0"))
        return {"period": {"startDate": start_date, "endDate": end_date}, "summary": {"transactionCount": len(purchases), "total": self.output_number(total)}, "data": [self.clean_document(x) for x in purchases]}

    def inventory_report(self, low_stock_threshold=5, product_id=None, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        query = {}
        if product_id:
            query["_id"] = ObjectId(product_id) if ObjectId.is_valid(product_id) else None
        products = self.repository.find(self.repository.products, query, sort=[("name", 1)])
        movements_query = self.repository._period("createdAt", start, end)
        if product_id:
            movements_query["productId"] = str(product_id)
        movements = self.repository.find(self.repository.stock_movements, movements_query, sort=[("createdAt", -1)])
        opname_query = self.repository._period("opnameDate", start, end)
        if product_id:
            opname_query["items.productId"] = str(product_id)
        opnames = self.repository.find(self.repository.stock_opnames, opname_query, sort=[("opnameDate", -1)])
        rows = []
        for p in products:
            stock = self.number(p.get("stock", 0))
            rows.append({"productId": str(p["_id"]), "sku": p.get("sku", ""), "barcode": p.get("barcode", ""), "name": p.get("name", ""), "stock": self.output_number(stock), "minimumStock": self.output_number(self.number(p.get("minimumStock", p.get("minimum_stock", low_stock_threshold)))), "lowStock": stock <= self.number(p.get("minimumStock", p.get("minimum_stock", low_stock_threshold)))})
        return {"summary": {"productCount": len(rows), "lowStockCount": sum(1 for r in rows if r["lowStock"]), "movementCount": len(movements), "opnameCount": len(opnames)}, "stock": rows, "movements": [self.clean_document(x) for x in movements], "opnames": [self.clean_document(x) for x in opnames]}

    def supplier_report(self, supplier_id=None, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        supplier_query = {"_id": ObjectId(supplier_id)} if supplier_id and ObjectId.is_valid(supplier_id) else {}
        suppliers = self.repository.find(self.repository.suppliers, supplier_query, sort=[("name", 1)])
        purchase_query = self.repository._period("purchaseDate", start, end)
        invoice_query = self.repository._period("invoiceDate", start, end)
        payment_query = self.repository._period("paymentDate", start, end)
        data = []
        for s in suppliers:
            sid = str(s["_id"])
            purchases = self.repository.find(self.repository.purchases, dict(purchase_query, supplierId=sid), sort=[("purchaseDate", -1)])
            invoices = self.repository.find(self.repository.invoices, dict(invoice_query, supplierId=sid), sort=[("invoiceDate", -1)])
            payments = self.repository.find(self.repository.payments, dict(payment_query, supplierId=sid), sort=[("paymentDate", -1)])
            all_invoices = self.repository.find(self.repository.invoices, {"supplierId": sid})
            period_outstanding = sum((self.number(x.get("remainingAmount")) for x in invoices), Decimal("0"))
            current_outstanding = sum((self.number(x.get("remainingAmount")) for x in all_invoices), Decimal("0"))
            data.append({"supplier": self.clean_document(s), "purchaseCount": len(purchases), "purchaseTotal": self.output_number(sum((self.number(x.get("total")) for x in purchases), Decimal("0"))), "purchases": [self.clean_document(x) for x in purchases], "invoices": [self.clean_document(x) for x in invoices], "payments": [self.clean_document(x) for x in payments], "outstanding": self.output_number(period_outstanding), "currentOutstanding": self.output_number(current_outstanding)})
        return {"data": data}

    def payable_report(self, start_date=None, end_date=None, supplier_id=None, outstanding_only=False):
        from apps.inventory.invoice_services import SupplierInvoiceService
        SupplierInvoiceService().refresh_overdue_statuses()
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("invoiceDate", start, end)
        if supplier_id:
            query["supplierId"] = str(supplier_id)
        if outstanding_only:
            query["remainingAmount"] = {"$gt": 0}
        invoices = self.repository.find(self.repository.invoices, query, sort=[("invoiceDate", -1)])
        total = sum((self.number(x.get("total")) for x in invoices), Decimal("0"))
        paid = sum((self.number(x.get("paidAmount")) for x in invoices), Decimal("0"))
        remaining = sum((self.number(x.get("remainingAmount")) for x in invoices), Decimal("0"))
        return {"period": {"startDate": start_date, "endDate": end_date}, "summary": {"invoiceCount": len(invoices), "total": self.output_number(total), "paid": self.output_number(paid), "remaining": self.output_number(remaining)}, "data": [self.clean_document(x) for x in invoices]}

    def profit_report(self, start_date=None, end_date=None):
        start, end = self.parse_period(start_date, end_date)
        sales_query = self.repository._period("saleDate", start, end)
        sales_query["status"] = "COMPLETED"
        sales = self.repository.find(self.repository.sales, sales_query, sort=[("saleDate", -1)])
        expenses = self.repository.find(self.repository.expenses, self.repository._period("date", start, end), sort=[("date", -1)])
        product_map = self._get_product_map()
        revenue = sum((self.number(x.get("total")) for x in sales), Decimal("0"))
        cost = Decimal("0")
        snapshot_count = 0
        fallback_count = 0
        for sale in sales:
            for item in sale.get("items", []) or []:
                qty = self.number(item.get("quantity"))
                cost_value = item.get("purchasePrice", item.get("costPrice"))
                if cost_value is None:
                    product = product_map.get(str(item.get("productId")), {})
                    cost_value = product.get("purchase_price", product.get("purchasePrice", 0))
                    fallback_count += 1
                else:
                    snapshot_count += 1
                cost += qty * self.number(cost_value)
        expense_total = sum((self.number(x.get("amount")) for x in expenses), Decimal("0"))
        gross = revenue - cost
        return {"period": {"startDate": start_date, "endDate": end_date}, "summary": {"revenue": self.output_number(revenue), "costOfGoodsSold": self.output_number(cost), "grossProfit": self.output_number(gross), "expenses": self.output_number(expense_total), "netProfit": self.output_number(gross-expense_total)}, "costBasis": {"snapshotItems": snapshot_count, "currentMasterFallbackItems": fallback_count}}

    def audit_logs(self, start_date=None, end_date=None, action=None, module=None, user_id=None, limit=100):
        start, end = self.parse_period(start_date, end_date)
        query = self.repository._period("createdAt", start, end)
        if action:
            query["action"] = {"$regex": f"^{action}$", "$options": "i"}
        if module:
            legacy_targets = {
                "authentication": "user", "master_data": {"product", "supplier", "member", "category"},
                "sales": "sale", "procurement": {"purchase", "purchase_order", "goods_receipt", "invoice", "supplier_payment"},
                "inventory": {"stock", "stock_adjustment", "stock_opname"}, "returns": {"sales_return", "purchase_return"}, "finance": "expense",
            }
            target = legacy_targets.get(module)
            if isinstance(target, set):
                query["$or"] = [{"module": module}, {"targetType": {"$in": list(target)}}]
            elif target:
                query["$or"] = [{"module": module}, {"targetType": target}]
            else:
                query["module"] = module
        if user_id:
            query["userId"] = str(user_id)
        docs = self.repository.find(self.repository.audit_logs, query, sort=[("createdAt", -1)], limit=limit)
        return {"count": len(docs), "data": [self.clean_document(x) for x in docs]}
