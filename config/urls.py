from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from apps.reports import views as reports

def health_check(request):
    return JsonResponse({"success": True, "service": "koperasi", "status": "ok"})


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    # Authentication, dashboard and user management use the PRD root URLs.
    path("", include("apps.authentication.urls")),
    # Master-data UI keeps PRD-friendly root URLs.
    path("", include("apps.master_data.urls")),
    # Inventory/procurement HTML UI owns the user-facing root routes.
    path("", include("apps.inventory.ui_urls")),
    path("pos/", include("apps.pos.urls")),
    path("sales/", include("apps.pos.root_urls")),
    path("returns/", include("apps.inventory.root_return_urls")),
    path("reports/", include("apps.reports.urls")),
    path("expenses/", include("apps.finance.urls")),
    path("finance/", include("apps.finance.urls")),
    path("audit-logs/", reports.audit_logs, name="audit_logs_root"),
    # Raw JSON endpoints are separated from HTML routes.
    path("api/inventory/", include("apps.inventory.urls")),
]
