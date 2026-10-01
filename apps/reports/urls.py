from django.urls import path
from . import views

app_name = "reports"
urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("sales/", views.sales_report, name="sales"),
    path("purchases/", views.purchase_report, name="purchases"),
    path("inventory/", views.inventory_report, name="inventory"),
    path("suppliers/", views.supplier_report, name="suppliers"),
    path("payables/", views.payable_report, name="payables"),
    path("profit/", views.profit_report, name="profit"),
    path("audit-logs/", views.audit_logs, name="audit_logs"),
    path("export/<str:report_type>/<str:file_format>/", views.export_report, name="export"),
]
