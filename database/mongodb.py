"""Central MongoDB connection and lightweight schema/index bootstrap."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "koperasi_db")
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "2000"))

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS)
db = client[MONGODB_DATABASE]


@lru_cache(maxsize=1)
def ensure_indexes() -> bool:
    """Create application indexes independently so one legacy conflict cannot stop the rest."""
    operations = [
        (db.users, [("username", ASCENDING)], {"unique": True, "name": "uniq_users_username"}),
        (db.categories, [("code", ASCENDING)], {"unique": True, "name": "uniq_categories_code"}),
        (db.products, [("sku", ASCENDING)], {"unique": True, "name": "uniq_products_sku"}),
        (db.products, [("barcode", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_products_barcode"}),
        (db.suppliers, [("code", ASCENDING)], {"unique": True, "name": "uniq_suppliers_code"}),
        (db.members, [("member_code", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_members_code_legacy"}),
        (db.members, [("memberCode", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_members_code"}),
        (db.product_suppliers, [("product_id", ASCENDING), ("supplier_id", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_product_supplier_legacy"}),
        (db.product_suppliers, [("productId", ASCENDING), ("supplierId", ASCENDING)], {"unique": True, "name": "uniq_product_supplier"}),
        (db.purchase_orders, [("poNumber", ASCENDING)], {"unique": True, "name": "uniq_po_number"}),
        (db.goods_receipts, [("receiptNumber", ASCENDING)], {"unique": True, "name": "uniq_gr_number"}),
        (db.purchases, [("purchaseNumber", ASCENDING)], {"unique": True, "name": "uniq_purchase_number"}),
        (db.purchases, [("purchaseDate", DESCENDING)], {"name": "idx_purchase_date"}),
        (db.supplier_invoices, [("invoiceNumber", ASCENDING)], {"unique": True, "name": "uniq_supplier_invoice"}),
        (db.supplier_invoices, [("invoiceDate", DESCENDING)], {"name": "idx_supplier_invoice_date"}),
        (db.supplier_payments, [("paymentNumber", ASCENDING)], {"unique": True, "name": "uniq_supplier_payment"}),
        (db.stock_adjustments, [("adjustmentNumber", ASCENDING)], {"unique": True, "name": "uniq_stock_adjustment"}),
        (db.stock_opnames, [("opnameNumber", ASCENDING)], {"unique": True, "name": "uniq_stock_opname"}),
        (db.stock_movements, [("productId", ASCENDING), ("createdAt", DESCENDING)], {"name": "idx_stock_movement_product_date"}),
        (db.sales, [("invoiceNumber", ASCENDING)], {"unique": True, "name": "uniq_sales_invoice"}),
        (db.sales, [("saleDate", DESCENDING)], {"name": "idx_sales_date"}),
        (db.payments, [("saleId", ASCENDING), ("paidAt", DESCENDING)], {"name": "idx_sale_payments"}),
        (db.returns, [("saleId", ASCENDING), ("returnDate", DESCENDING)], {"name": "idx_sales_returns"}),
        (db.returns, [("returnNumber", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_sales_return_number"}),
        (db.purchase_returns, [("purchaseId", ASCENDING), ("returnDate", DESCENDING)], {"name": "idx_purchase_returns"}),
        (db.expenses, [("expenseNumber", ASCENDING)], {"unique": True, "name": "uniq_expense_number"}),
        (db.expenses, [("date", DESCENDING)], {"name": "idx_expenses_date"}),
        (db.audit_logs, [("createdAt", DESCENDING)], {"name": "idx_audit_created"}),
        (db.audit_logs, [("module", ASCENDING), ("createdAt", DESCENDING)], {"name": "idx_audit_module"}),
    ]
    try:
        client.admin.command("ping")
    except Exception:
        return False
    successes = 0
    for collection, keys, options in operations:
        try:
            collection.create_index(keys, **options)
            successes += 1
        except Exception:
            pass
    return successes == len(operations)


def get_database():
    return db


def atomic_stock_update(product_id, delta):
    """Compatibility helper for callers that need one conditional stock increment."""
    from bson import ObjectId
    oid = ObjectId(product_id)
    delta = int(delta)
    query = {"_id": oid}
    if delta < 0:
        query["stock"] = {"$gte": abs(delta)}
    return db.products.find_one_and_update(query, {"$inc": {"stock": delta}}, return_document=ReturnDocument.AFTER)
