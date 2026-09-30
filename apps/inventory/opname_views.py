import json

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .opname_services import StockOpnameService


stock_opname_service = StockOpnameService()


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
def stock_opname_list(request):
    try:
        opnames = (
            stock_opname_service
            .get_all_opnames()
        )

        data = [
            serialize_document(opname)
            for opname in opnames
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
def stock_opname_create(request):
    try:
        body = json.loads(request.body)

        opname_number = body.get(
            "opnameNumber"
        )

        items = body.get(
            "items"
        )

        created_by = request.session.get(
            "username",
            "system"
        )

        opname = (
            stock_opname_service
            .create_opname(
                opname_number=opname_number,
                items=items,
                created_by=created_by,
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Stock opname berhasil dibuat."
            ),
            "data": serialize_document(opname),
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
def stock_opname_detail(
    request,
    opname_id,
):
    try:
        opname = (
            stock_opname_service
            .get_opname_by_id(
                opname_id
            )
        )

        if not opname:
            return JsonResponse({
                "success": False,
                "message": (
                    "Stock opname tidak ditemukan."
                ),
            }, status=404)

        return JsonResponse({
            "success": True,
            "data": serialize_document(opname),
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=500)


@require_http_methods(["POST"])
def stock_opname_submit(
    request,
    opname_id,
):
    try:
        opname = (
            stock_opname_service
            .submit_opname(
                opname_id
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Stock opname berhasil disubmit."
            ),
            "data": serialize_document(opname),
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
def stock_opname_approve(
    request,
    opname_id,
):
    try:
        approved_by = request.session.get(
            "username",
            "system"
        )

        opname = (
            stock_opname_service
            .approve_opname(
                opname_id=opname_id,
                approved_by=approved_by,
            )
        )

        return JsonResponse({
            "success": True,
            "message": (
                "Stock opname berhasil disetujui "
                "dan stok telah disesuaikan."
            ),
            "data": serialize_document(opname),
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