from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.authentication.decorators import permission_required_custom

from .services import ReportService

service = ReportService()


def _error_response(exc):
    status = 400 if isinstance(exc, ValueError) else 500
    return JsonResponse({"success": False, "message": str(exc)}, status=status)


def _params(request):
    return request.GET.get("start_date"), request.GET.get("end_date")


@require_GET
@permission_required_custom("reports")
def dashboard(request):
    try:
        start, end = _params(request)
        threshold = int(request.GET.get("low_stock_threshold", 5))
        return JsonResponse({"success": True, "data": service.dashboard(threshold, start, end)}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def sales_report(request):
    try:
        start, end = _params(request)
        data = service.sales_report(start, end, request.GET.get("product_id"), request.GET.get("cashier"))
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def purchase_report(request):
    try:
        start, end = _params(request)
        data = service.purchase_report(start, end, request.GET.get("supplier_id"))
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def inventory_report(request):
    try:
        threshold = int(request.GET.get("low_stock_threshold", 5))
        data = service.inventory_report(threshold, request.GET.get("product_id"))
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def supplier_report(request):
    try:
        data = service.supplier_report(request.GET.get("supplier_id"))
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def payable_report(request):
    try:
        start, end = _params(request)
        data = service.payable_report(
            start,
            end,
            request.GET.get("supplier_id"),
            request.GET.get("outstanding_only", "false").lower() == "true",
        )
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("reports")
def profit_report(request):
    try:
        start, end = _params(request)
        data = service.profit_report(start, end)
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)


@require_GET
@permission_required_custom("audit_log")
def audit_logs(request):
    try:
        limit = min(max(int(request.GET.get("limit", 100)), 1), 500)
        start, end = _params(request)
        data = service.audit_logs(
            start,
            end,
            request.GET.get("action"),
            request.GET.get("module"),
            request.GET.get("user_id"),
            limit,
        )
        return JsonResponse({"success": True, "data": data}, json_dumps_params={"default": str})
    except Exception as exc:
        return _error_response(exc)
