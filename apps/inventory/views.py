import json

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .services import StockMovementService


stock_movement_service = StockMovementService()


def serialize_document(document):
    """
    Mengubah ObjectId dan datetime agar dapat dikirim sebagai JSON.
    """

    if document is None:
        return None

    result = {}

    for key, value in document.items():

        if isinstance(value, ObjectId):
            result[key] = str(value)

        elif hasattr(value, "isoformat"):
            result[key] = value.isoformat()

        else:
            result[key] = value

    return result


@require_http_methods(["GET"])
def stock_movement_list(request):
    """
    GET /inventory/stock-movements/

    Mengambil seluruh stock movement.
    """

    try:
        movements = stock_movement_service.get_all_movements()

        data = [
            serialize_document(movement)
            for movement in movements
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
def stock_movement_create(request):
    """
    POST /inventory/stock-movements/create/

    Membuat stock movement baru.
    """

    try:
        body = json.loads(request.body)

        product_id = body.get("productId")
        movement_type = body.get("movementType")
        quantity = body.get("quantity")
        reference_type = body.get("referenceType")
        reference_id = body.get("referenceId")
        notes = body.get("notes", "")

        adjustment_quantity = body.get(
            "adjustmentQuantity"
        )

        # Untuk sementara menggunakan session username.
        created_by = request.session.get(
            "username",
            "system"
        )

        movement = stock_movement_service.create_movement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by,
            adjustment_quantity=adjustment_quantity,
        )

        return JsonResponse({
            "success": True,
            "message": "Stock movement berhasil dibuat.",
            "data": serialize_document(movement),
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
def stock_movement_detail(request, movement_id):
    """
    GET /inventory/stock-movements/<id>/

    Mengambil satu movement.
    """

    try:
        movement = stock_movement_service.get_movement_by_id(
            movement_id
        )

        if not movement:
            return JsonResponse({
                "success": False,
                "message": "Stock movement tidak ditemukan.",
            }, status=404)

        return JsonResponse({
            "success": True,
            "data": serialize_document(movement),
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)


@require_http_methods(["GET"])
def product_stock(request, product_id):
    """
    GET /inventory/stock/<product_id>/

    Mengambil stok saat ini untuk sebuah produk.
    """

    try:
        stock = stock_movement_service.get_current_stock(
            product_id
        )

        return JsonResponse({
            "success": True,
            "productId": product_id,
            "stock": stock,
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


@require_http_methods(["GET"])
def product_movement_history(request, product_id):
    """
    GET /inventory/stock-movements/product/<product_id>/

    Mengambil histori movement berdasarkan produk.
    """

    try:
        movements = (
            stock_movement_service
            .get_product_movements(product_id)
        )

        data = [
            serialize_document(movement)
            for movement in movements
        ]

        return JsonResponse({
            "success": True,
            "productId": product_id,
            "data": data,
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