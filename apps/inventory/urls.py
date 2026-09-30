from django.urls import path

from .views import (
    product_movement_history,
    product_stock,
    stock_movement_create,
    stock_movement_detail,
    stock_movement_list,
)

from .opname_views import (
    stock_opname_approve,
    stock_opname_create,
    stock_opname_detail,
    stock_opname_list,
    stock_opname_submit,
)

from .adjustment_views import (
    stock_adjustment_create,
    stock_adjustment_detail,
    stock_adjustment_list,
)

from .po_views import (
    purchase_order_cancel,
    purchase_order_create,
    purchase_order_detail,
    purchase_order_list,
    purchase_order_submit,
)

from .po_views import (
    purchase_order_approve,
    purchase_order_cancel,
    purchase_order_create,
    purchase_order_detail,
    purchase_order_list,
    purchase_order_submit,
)

from .gr_views import (
    goods_receipt_list,
    goods_receipt_create,
    goods_receipt_detail,
    goods_receipt_by_po,
)

from .purchase_views import (
    purchase_list,
    purchase_create,
    purchase_detail,
    purchase_by_po,
    purchase_by_goods_receipt,
)

from .invoice_views import (
    supplier_invoice_list,
    supplier_invoice_create,
    supplier_invoice_detail,
    supplier_invoice_by_supplier,
    supplier_invoice_by_purchase,
    supplier_debt,
)

from .payment_views import (
    supplier_payment_list,
    supplier_payment_create,
    supplier_payment_detail,
    supplier_payment_by_invoice,
    supplier_payment_by_supplier,
)

from .debt_views import (
    supplier_debt_detail,
    supplier_outstanding_invoices,
)

app_name = "inventory"


urlpatterns = [
    # ==================================================
    # STOCK MOVEMENT
    # ==================================================

    path(
        "stock-movements/",
        stock_movement_list,
        name="stock_movement_list",
    ),

    path(
        "stock-movements/create/",
        stock_movement_create,
        name="stock_movement_create",
    ),

    path(
        "stock-movements/<str:movement_id>/",
        stock_movement_detail,
        name="stock_movement_detail",
    ),

    path(
        "stock-movements/product/<str:product_id>/",
        product_movement_history,
        name="product_movement_history",
    ),

    path(
        "stock/<str:product_id>/",
        product_stock,
        name="product_stock",
    ),

    # ==================================================
    # STOCK OPNAME
    # ==================================================

    path(
        "stock-opnames/",
        stock_opname_list,
        name="stock_opname_list",
    ),

    path(
        "stock-opnames/create/",
        stock_opname_create,
        name="stock_opname_create",
    ),

    path(
        "stock-opnames/<str:opname_id>/",
        stock_opname_detail,
        name="stock_opname_detail",
    ),

    path(
        "stock-opnames/<str:opname_id>/submit/",
        stock_opname_submit,
        name="stock_opname_submit",
    ),

    path(
        "stock-opnames/<str:opname_id>/approve/",
        stock_opname_approve,
        name="stock_opname_approve",
    ),

    # ==================================================
    # STOCK ADJUSTMENT
    # ==================================================

    path(
        "stock-adjustments/",
        stock_adjustment_list,
        name="stock_adjustment_list",
    ),

    path(
        "stock-adjustments/create/",
        stock_adjustment_create,
        name="stock_adjustment_create",
    ),

    path(
        "stock-adjustments/<str:adjustment_id>/",
        stock_adjustment_detail,
        name="stock_adjustment_detail",
    ),

        # ==================================================
    # PURCHASE ORDER
    # ==================================================

    path(
        "purchase-orders/",
        purchase_order_list,
        name="purchase_order_list",
    ),

    path(
        "purchase-orders/create/",
        purchase_order_create,
        name="purchase_order_create",
    ),

    path(
        "purchase-orders/<str:po_id>/",
        purchase_order_detail,
        name="purchase_order_detail",
    ),

    path(
        "purchase-orders/<str:po_id>/submit/",
        purchase_order_submit,
        name="purchase_order_submit",
    ),

    path(
        "purchase-orders/<str:po_id>/cancel/",
        purchase_order_cancel,
        name="purchase_order_cancel",
    ),

        path(
        "purchase-orders/<str:po_id>/approve/",
        purchase_order_approve,
        name="purchase_order_approve",
    ),

    path(
    "goods-receipts/",
    goods_receipt_list,
    ),
    path(
        "goods-receipts/create/",
        goods_receipt_create,
    ),
    path(
        "goods-receipts/<str:receipt_id>/",
        goods_receipt_detail,
    ),
    path(
        "goods-receipts/po/<str:po_id>/",
        goods_receipt_by_po,
    ),

    path(
    "purchases/",
    purchase_list,
    ),
    path(
        "purchases/create/",
        purchase_create,
    ),
    path(
        "purchases/<str:purchase_id>/",
        purchase_detail,
    ),
    path(
        "purchases/po/<str:po_id>/",
        purchase_by_po,
    ),
    path(
        "purchases/goods-receipt/<str:goods_receipt_id>/",
        purchase_by_goods_receipt,
    ),

    path(
    "supplier-invoices/",
    supplier_invoice_list,
    ),
    path(
        "supplier-invoices/create/",
        supplier_invoice_create,
    ),
    path(
        "supplier-invoices/<str:invoice_id>/",
        supplier_invoice_detail,
    ),
    path(
        "supplier-invoices/supplier/<str:supplier_id>/",
        supplier_invoice_by_supplier,
    ),
    path(
        "supplier-invoices/purchase/<str:purchase_id>/",
        supplier_invoice_by_purchase,
    ),
    path(
        "supplier-debt/<str:supplier_id>/",
        supplier_debt,
    ),

    path(
    "supplier-payments/",
    supplier_payment_list,
    name="supplier-payment-list",
    ),

    path(
        "supplier-payments/create/",
        supplier_payment_create,
        name="supplier-payment-create",
    ),

    path(
        "supplier-payments/<str:payment_id>/",
        supplier_payment_detail,
        name="supplier-payment-detail",
    ),

    path(
        "supplier-payments/invoice/<str:invoice_id>/",
        supplier_payment_by_invoice,
        name="supplier-payment-by-invoice",
    ),

    path(
        "supplier-payments/supplier/<str:supplier_id>/",
        supplier_payment_by_supplier,
        name="supplier-payment-by-supplier",
    ),

    path(
    "supplier-debt/<str:supplier_id>/",
    supplier_debt_detail,
    name="supplier-debt-detail",
    ),

    path(
        "supplier-debt/",
        supplier_outstanding_invoices,
        name="supplier-outstanding-invoices",
    ),
    
]