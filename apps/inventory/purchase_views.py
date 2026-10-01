from apps.authentication.decorators import permission_required_custom
import json
from datetime import datetime

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .purchase_services import PurchaseService


def serialize_data(data):
    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, datetime):
        return data.isoformat()

    if isinstance(data, list):
        return [
            serialize_data(item)
            for item in data
        ]

    if isinstance(data, dict):
        return {
            key: serialize_data(value)
            for key, value in data.items()
        }

    return data


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def purchase_list(request):
    service = PurchaseService()

    purchases = service.get_all_purchases()

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                purchases
            ),
        },
        status=200,
    )


@require_http_methods(["POST"])
@permission_required_custom("procurement")
def purchase_create(request):
    try:
        data = json.loads(
            request.body
        )

        created_by = (
            request.session.get(
                "username"
            )
            or data.get("createdBy")
            or "system"
        )

        service = PurchaseService()

        purchase = service.create_purchase(
            purchase_number=data.get(
                "purchaseNumber"
            ),
            po_id=data.get(
                "poId"
            ),
            goods_receipt_id=data.get(
                "goodsReceiptId"
            ),
            purchase_date=data.get(
                "purchaseDate"
            ),
            discount=data.get(
                "discount",
                0,
            ),
            tax=data.get(
                "tax",
                0,
            ),
            created_by=created_by,
        )

        return JsonResponse(
            {
                "success": True,
                "message": (
                    "Pembelian berhasil dibuat."
                ),
                "data": serialize_data(
                    purchase
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
                "message": (
                    "Format JSON tidak valid."
                ),
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
@permission_required_custom("procurement")
def purchase_detail(
    request,
    purchase_id,
):
    service = PurchaseService()

    purchase = service.get_purchase_by_id(
        purchase_id
    )

    if not purchase:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Pembelian tidak ditemukan."
                ),
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                purchase
            ),
        },
        status=200,
    )


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def purchase_by_po(
    request,
    po_id,
):
    service = PurchaseService()

    purchases = service.get_purchases_by_po(
        po_id
    )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                purchases
            ),
        },
        status=200,
    )


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def purchase_by_goods_receipt(
    request,
    goods_receipt_id,
):
    service = PurchaseService()

    purchases = (
        service.get_purchases_by_goods_receipt(
            goods_receipt_id
        )
    )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                purchases
            ),
        },
        status=200,
    )
