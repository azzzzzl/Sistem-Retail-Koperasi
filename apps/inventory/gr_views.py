import json
from datetime import datetime

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .gr_services import GoodsReceiptService


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
def goods_receipt_list(request):
    service = GoodsReceiptService()

    receipts = service.get_all_goods_receipts()

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(receipts),
        },
        status=200,
    )


@require_http_methods(["POST"])
def goods_receipt_create(request):
    try:
        data = json.loads(
            request.body
        )

        received_by = (
            request.session.get(
                "username"
            )
            or data.get("receivedBy")
            or "system"
        )

        service = GoodsReceiptService()

        receipt = service.create_goods_receipt(
            receipt_number=data.get(
                "receiptNumber"
            ),
            po_id=data.get(
                "poId"
            ),
            receipt_date=data.get(
                "receiptDate"
            ),
            items=data.get(
                "items"
            ),
            received_by=received_by,
            notes=data.get(
                "notes",
                "",
            ),
        )

        return JsonResponse(
            {
                "success": True,
                "message": (
                    "Goods Receipt berhasil dibuat."
                ),
                "data": serialize_data(
                    receipt
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
def goods_receipt_detail(
    request,
    receipt_id,
):
    service = GoodsReceiptService()

    receipt = service.get_goods_receipt_by_id(
        receipt_id
    )

    if not receipt:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Goods Receipt tidak ditemukan."
                ),
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                receipt
            ),
        },
        status=200,
    )


@require_http_methods(["GET"])
def goods_receipt_by_po(
    request,
    po_id,
):
    service = GoodsReceiptService()

    receipts = service.get_goods_receipts_by_po(
        po_id
    )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_data(
                receipts
            ),
        },
        status=200,
    )

