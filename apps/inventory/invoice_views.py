from apps.authentication.decorators import permission_required_custom
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .invoice_services import SupplierInvoiceService


def serialize_invoice(invoice):
    if not invoice:
        return None

    data = dict(invoice)

    if "_id" in data:
        data["_id"] = str(data["_id"])

    for field in [
        "invoiceDate",
        "dueDate",
        "createdAt",
        "updatedAt",
    ]:
        if field in data and data[field] is not None:
            data[field] = data[field].isoformat()

    return data


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def supplier_invoice_list(request):
    service = SupplierInvoiceService()

    invoices = service.get_all_invoices()

    return JsonResponse(
        {
            "success": True,
            "data": [
                serialize_invoice(invoice)
                for invoice in invoices
            ],
        }
    )


@require_http_methods(["POST"])
@permission_required_custom("procurement")
def supplier_invoice_create(request):
    try:
        data = json.loads(
            request.body or "{}"
        )

        username = request.session.get(
            "username",
            "system",
        )

        service = SupplierInvoiceService()

        invoice = service.create_invoice(
            invoice_number=data.get(
                "invoiceNumber"
            ),
            purchase_id=data.get(
                "purchaseId"
            ),
            invoice_date=data.get(
                "invoiceDate"
            ),
            due_date=data.get(
                "dueDate"
            ),
            created_by=username,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Supplier Invoice berhasil dibuat.",
                "data": serialize_invoice(
                    invoice
                ),
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

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "JSON request tidak valid.",
            },
            status=400,
        )


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def supplier_invoice_detail(
    request,
    invoice_id,
):
    service = SupplierInvoiceService()

    invoice = service.get_invoice_by_id(
        invoice_id
    )

    if not invoice:
        return JsonResponse(
            {
                "success": False,
                "message": "Supplier Invoice tidak ditemukan.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_invoice(
                invoice
            ),
        }
    )


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def supplier_invoice_by_supplier(
    request,
    supplier_id,
):
    try:
        service = SupplierInvoiceService()

        invoices = (
            service.get_invoices_by_supplier(
                supplier_id
            )
        )

        return JsonResponse(
            {
                "success": True,
                "data": [
                    serialize_invoice(invoice)
                    for invoice in invoices
                ],
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


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def supplier_invoice_by_purchase(
    request,
    purchase_id,
):
    try:
        service = SupplierInvoiceService()

        invoices = (
            service.get_invoices_by_purchase(
                purchase_id
            )
        )

        return JsonResponse(
            {
                "success": True,
                "data": [
                    serialize_invoice(invoice)
                    for invoice in invoices
                ],
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


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def supplier_debt(
    request,
    supplier_id,
):
    try:
        service = SupplierInvoiceService()

        invoices = service.get_supplier_debt(
            supplier_id
        )

        total_debt = sum(
            invoice.get(
                "remainingAmount",
                0,
            )
            for invoice in invoices
        )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "supplierId": supplier_id,
                    "totalDebt": total_debt,
                    "invoices": [
                        serialize_invoice(invoice)
                        for invoice in invoices
                    ],
                },
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
