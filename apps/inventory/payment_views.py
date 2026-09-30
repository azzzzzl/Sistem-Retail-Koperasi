import json
from datetime import date, datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .payment_services import SupplierPaymentService


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
def supplier_payment_list(request):
    service = SupplierPaymentService()

    payments = service.get_all_payments()

    return JsonResponse(
        {
            "success": True,
            "data": serialize_document(payments),
        }
    )


@require_http_methods(["POST"])
def supplier_payment_create(request):
    try:
        data = json.loads(
            request.body.decode("utf-8")
        )

        service = SupplierPaymentService()

        result = service.create_payment(
            payment_number=data.get("paymentNumber"),
            invoice_id=data.get("invoiceId"),
            amount=data.get("amount"),
            payment_date=data.get("paymentDate"),
            payment_method=data.get(
                "paymentMethod",
                "TRANSFER",
            ),
            reference_number=data.get(
                "referenceNumber",
                "",
            ),
            notes=data.get(
                "notes",
                "",
            ),
            created_by=data.get(
                "createdBy"
            ),
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Supplier Payment berhasil dibuat.",
                "data": serialize_document(result),
            },
            status=201,
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
def supplier_payment_detail(
    request,
    payment_id,
):
    service = SupplierPaymentService()

    payment = service.get_payment_by_id(
        payment_id
    )

    if not payment:
        return JsonResponse(
            {
                "success": False,
                "message": "Supplier Payment tidak ditemukan.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_document(payment),
        }
    )


@require_http_methods(["GET"])
def supplier_payment_by_invoice(
    request,
    invoice_id,
):
    service = SupplierPaymentService()

    payments = service.get_payments_by_invoice(
        invoice_id
    )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_document(payments),
        }
    )


@require_http_methods(["GET"])
def supplier_payment_by_supplier(
    request,
    supplier_id,
):
    service = SupplierPaymentService()

    payments = service.get_payments_by_supplier(
        supplier_id
    )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_document(payments),
        }
    )