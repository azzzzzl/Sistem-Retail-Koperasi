from django.urls import path
from . import ui_views

app_name="inventory_ui"
urlpatterns=[
    path("inventory/",ui_views.inventory_home,name="inventory_home"),
    path("inventory/movements/",ui_views.stock_movement_list_ui,name="stock_movement_list"),
    path("inventory/stock-opname/",ui_views.stock_opname_list_ui,name="stock_opname_list"),
    path("inventory/stock-opname/create/",ui_views.stock_opname_create_ui,name="stock_opname_create"),
    path("inventory/stock-opname/<str:opname_id>/submit/",ui_views.stock_opname_submit_ui,name="stock_opname_submit"),
    path("inventory/stock-opname/<str:opname_id>/approve/",ui_views.stock_opname_approve_ui,name="stock_opname_approve"),
    path("inventory/stock-adjustment/",ui_views.stock_adjustment_list_ui,name="stock_adjustment_list"),
    path("inventory/stock-adjustment/create/",ui_views.stock_adjustment_create_ui,name="stock_adjustment_create"),
    path("purchase-orders/",ui_views.purchase_order_list_ui,name="purchase_order_list"),
    path("purchase-orders/create/",ui_views.purchase_order_create_ui,name="purchase_order_create"),
    path("purchase-orders/<str:po_id>/",ui_views.purchase_order_detail_ui,name="purchase_order_detail"),
    path("purchase-orders/<str:po_id>/<str:action>/",ui_views.purchase_order_action_ui,name="purchase_order_action"),
    path("goods-receipts/",ui_views.goods_receipt_list_ui,name="goods_receipt_list"),
    path("goods-receipts/create/",ui_views.goods_receipt_create_ui,name="goods_receipt_create"),
    path("goods-receipts/<str:receipt_id>/",ui_views.goods_receipt_detail_ui,name="goods_receipt_detail"),
    path("purchases/",ui_views.purchase_list_ui,name="purchase_list"),
    path("purchases/create/",ui_views.purchase_create_ui,name="purchase_create"),
    path("purchases/<str:purchase_id>/",ui_views.purchase_detail_ui,name="purchase_detail"),
    path("supplier-invoices/",ui_views.supplier_invoice_list_ui,name="supplier_invoice_list"),
    path("supplier-invoices/create/",ui_views.supplier_invoice_create_ui,name="supplier_invoice_create"),
    path("supplier-invoices/<str:invoice_id>/",ui_views.supplier_invoice_detail_ui,name="supplier_invoice_detail"),
    path("supplier-payments/",ui_views.supplier_payment_list_ui,name="supplier_payment_list"),
    path("supplier-payments/create/",ui_views.supplier_payment_create_ui,name="supplier_payment_create"),
    path("purchase-returns/",ui_views.purchase_return_list,name="purchase_return_list"),
    path("purchase-returns/create/",ui_views.purchase_return_create,name="purchase_return_create"),
    path("purchase-returns/<str:return_id>/approve/",ui_views.purchase_return_approve,name="purchase_return_approve"),
]
