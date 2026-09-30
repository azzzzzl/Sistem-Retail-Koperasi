import json

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .adjustment_services import StockAdjustmentService


stock_adjustment_service = StockAdjustmentService()


def serialize_document(document):
    if document is None:
        return None

    result = {}

    for key, value in document.items():

        if isinstance(value, ObjectId):
            result[key] = str(value)

        elif hasattr(value, "isoformat"):
            result[key] = value.isoformat()

        elif isinstance(value, list):
            result[key] = [
                serialize_document(item)
                if isinstance(item, dict)
                else item
                for item in value
            ]

        elif isinstance(value, dict):
            result[key] = serialize_document(value)

        else:
            result[key] = value

    return result


@require_http_methods(["GET"])
def stock_adjustment_list(request):
    try:
        adjustments = (
            stock_adjustment_service
            .get_all_adjustments()
        )

        data = [
            serialize_document(adjustment)
            for adjustment in adjustments
        ]

        return JsonResponse({
            "success": True,
            "data": data,
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)


@require_http_methods(["POST"])
def stock_adjustment_create(request):
    try:
        body = json.loads(request.body)

        adjustment_number = body.get(
            "adjustmentNumber"
        )

        product_id = body.get(
            "productId"
        )

        adjustment_type = body.get(
            "adjustmentType"
        )

        quantity = body.get(
            "quantity"
        )

        reason = body.get(
            "reason",
            ""
        )

        notes = body.get(
            "notes",
            ""
        )

        created_by = request.session.get(
            "username",
            "system"
        )

        adjustment = (
            stock_adjustment_service
            .create_adjustment(
                adjustment_number=adjustment_number,
                product_id=product_id,
                adjustment_type=adjustment_type,
                quantity=quantity,
                reason=reason,
                notes=notes,
                created_by=created_by,
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Stock adjustment berhasil dibuat."
            ),
            "data": serialize_document(adjustment),
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Format JSON tidak valid.",
        }, status=400)

    except ValueError as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=400)

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)


@require_http_methods(["GET"])
def stock_adjustment_detail(
    request,
    adjustment_id,
):
    try:
        adjustment = (
            stock_adjustment_service
            .get_adjustment_by_id(
                adjustment_id
            )
        )

        if not adjustment:
            return JsonResponse({
                "success": False,
                "message": (
                    "Stock adjustment tidak ditemukan."
                ),
            }, status=404)

        return JsonResponse({
            "success": True,
            "data": serialize_document(adjustment),
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)