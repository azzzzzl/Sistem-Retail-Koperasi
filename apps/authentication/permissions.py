ROLE_PERMISSIONS = {
    "Admin": [
        "user_management",
        "product_management",
        "category_management",
        "supplier_management",
        "member_management",
        "sales",
        "procurement",
        "inventory",
        "reports",
        "audit_log",
    ],

    "Kasir": [
        "product_search",
        "sales",
        "payments",
        "transaction_history",
    ],

    "Pengurus": [
        "procurement",
        "goods_receipt",
        "inventory",
        "supplier_management",
        "member_management",
        "reports",
    ],

    "Anggota": [
        "profile",
        "own_transactions",
    ],
}


def has_permission(role, permission):
    permissions = ROLE_PERMISSIONS.get(role, [])
    return permission in permissions