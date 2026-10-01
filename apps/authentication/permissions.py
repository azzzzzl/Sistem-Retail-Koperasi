ROLE_PERMISSIONS = {
    "Admin": [
        "user_management", "product_management", "category_management",
        "supplier_management", "member_management", "sales", "sales_cancel", "payments",
        "product_search", "transaction_history", "procurement", "goods_receipt",
        "inventory", "reports", "audit_log", "expenses", "return_management", "return_view",
    ],
    "Kasir": [
        "product_search", "sales", "payments", "transaction_history", "return_view",
    ],
    "Pengurus": [
        "procurement", "goods_receipt", "inventory", "supplier_management",
        "member_management", "reports", "expenses", "return_management", "return_view",
    ],
    "Anggota": ["profile", "own_transactions"],
}


def has_permission(role, permission):
    return permission in ROLE_PERMISSIONS.get(role, [])
