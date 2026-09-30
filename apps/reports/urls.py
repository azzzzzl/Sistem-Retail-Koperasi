from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/", views.dashboard, name="reports_dashboard"),
    path("sales/", views.sales_report, name="reports_sales"),
    path("purchases/", views.purchase_report, name="reports_purchases"),
    path("inventory/", views.inventory_report, name="reports_inventory"),
    path("suppliers/", views.supplier_report, name="reports_suppliers"),
    path("payables/", views.payable_report, name="reports_payables"),
    path("profit/", views.profit_report, name="reports_profit"),
    path("audit-logs/", views.audit_logs, name="reports_audit_logs"),
]
