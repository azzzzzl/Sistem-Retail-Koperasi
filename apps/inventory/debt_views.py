import json
from datetime import date, datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .debt_services import SupplierDebtService


def serialize_document(document):
    if isinstance(document, dict):
        return {
            key: serialize_document(value)
            for key, value in document.items()
        }

    if isinstance(document, list):
        return [
            serialize_document(value)
            for value in document
        ]

    try:
        from bson import ObjectId

        if isinstance(document, ObjectId):
            return str(document)
    except Exception:
        pass

    if isinstance(document, (datetime, date)):
        return document.isoformat()

    return document


@require_http_methods(["GET"])
def supplier_debt_detail(
    request,
    supplier_id,
):
    try:
        service = SupplierDebtService()

        debt = service.get_supplier_debt(
            supplier_id
        )

        return JsonResponse(
            {
                "success": True,
                "data": serialize_document(debt),
            }
        )

    except ValueError as error:
        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=400,
        )

    except Exception as error:
        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=500,
        )


@require_http_methods(["GET"])
def supplier_outstanding_invoices(
    request,
):
    try:
        supplier_id = request.GET.get(
            "supplierId"
        )

        service = SupplierDebtService()

        invoices = (
            service.get_all_outstanding_invoices(
                supplier_id=supplier_id
            )
        )

        return JsonResponse(
            {
                "success": True,
                "data": serialize_document(
                    invoices
                ),
            }
        )

    except ValueError as error:
        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=400,
        )

    except Exception as error:
        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=500,
        )