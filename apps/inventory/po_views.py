from apps.authentication.decorators import permission_required_custom
import json

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .po_services import PurchaseOrderService


purchase_order_service = PurchaseOrderService()


def serialize_document(document):
    if document is None:
        return None

    if isinstance(document, list):
        return [
            serialize_document(item)
            if isinstance(item, (dict, list))
            else item
            for item in document
        ]

    if not isinstance(document, dict):
        return document

    result = {}

    for key, value in document.items():

        if isinstance(value, ObjectId):
            result[key] = str(value)

        elif hasattr(value, "isoformat"):
            result[key] = value.isoformat()

        elif isinstance(value, (dict, list)):
            result[key] = serialize_document(value)

        else:
            result[key] = value

    return result


@require_http_methods(["GET"])
@permission_required_custom("procurement")
def purchase_order_list(request):
    try:
        purchase_orders = (
            purchase_order_service
            .get_all_purchase_orders()
        )

        data = [
            serialize_document(po)
            for po in purchase_orders
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
@permission_required_custom("procurement")
def purchase_order_create(request):
    try:
        body = json.loads(request.body)

        po_number = body.get(
            "poNumber"
        )

        supplier_id = body.get(
            "supplierId"
        )

        order_date = body.get(
            "orderDate"
        )

        items = body.get(
            "items"
        )

        discount = body.get(
            "discount",
            0
        )

        notes = body.get(
            "notes",
            ""
        )

        created_by = request.session.get(
            "username",
            "system"
        )

        po = (
            purchase_order_service
            .create_purchase_order(
                po_number=po_number,
                supplier_id=supplier_id,
                order_date=order_date,
                items=items,
                discount=discount,
                notes=notes,
                created_by=created_by,
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Purchase Order berhasil dibuat."
            ),
            "data": serialize_document(po),
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
@permission_required_custom("procurement")
def purchase_order_detail(
    request,
    po_id,
):
    try:
        po = (
            purchase_order_service
            .get_purchase_order_by_id(
                po_id
            )
        )

        if not po:
            return JsonResponse({
                "success": False,
                "message": (
                    "Purchase Order tidak ditemukan."
                ),
            }, status=404)

        return JsonResponse({
            "success": True,
            "data": serialize_document(po),
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)


@require_http_methods(["POST"])
@permission_required_custom("procurement")
def purchase_order_submit(
    request,
    po_id,
):
    try:
        po = (
            purchase_order_service
            .submit_purchase_order(
                po_id
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Purchase Order berhasil "
                "disubmit."
            ),
            "data": serialize_document(po),
        })

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


@require_http_methods(["POST"])
@permission_required_custom("procurement")
def purchase_order_cancel(
    request,
    po_id,
):
    try:
        po = (
            purchase_order_service
            .cancel_purchase_order(
                po_id
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Purchase Order berhasil "
                "dibatalkan."
            ),
            "data": serialize_document(po),
        })

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

@require_http_methods(["POST"])
@permission_required_custom("procurement")
def purchase_order_approve(
    request,
    po_id,
):
    try:
        approved_by = request.session.get(
            "username",
            "system"
        )

        po = (
            purchase_order_service
            .approve_purchase_order(
                po_id=po_id,
                approved_by=approved_by,
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Purchase Order berhasil "
                "disetujui."
            ),
            "data": serialize_document(po),
        })

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
