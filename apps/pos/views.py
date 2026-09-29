import json
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.authentication.decorators import permission_required_custom

from .models import DetailPenjualan, Penjualan, Product, ReturPenjualan


def _cart(request):
    return request.session.get("pos_cart", {})


def _save_cart(request, cart):
    request.session["pos_cart"] = cart
    request.session.modified = True


def _money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _product_json(product, quantity=0):
    return {
        "id": product.pk,
        "sku": product.sku,
        "barcode": product.barcode,
        "name": product.name,
        "price": str(product.selling_price),
        "stock": product.stock,
        "quantity": quantity,
    }


def _cart_data(request):
    cart = _cart(request)
    products = Product.objects.filter(pk__in=cart.keys(), is_active=True)
    items = []
    subtotal = Decimal("0.00")
    for product in products:
        quantity = int(cart.get(str(product.pk), 0))
        if quantity < 1:
            continue
        item = _product_json(product, quantity)
        item["line_total"] = str(_money(product.selling_price * quantity))
        subtotal += _money(product.selling_price * quantity)
        items.append(item)
    return items, subtotal


def _sale_queryset_for_user(request):
    sales = Penjualan.objects.prefetch_related("detail")
    if request.session.get("role") != "Admin":
        sales = sales.filter(kasir_id=request.session.get("user_id", ""))
    return sales


@permission_required_custom("sales")
def pos_page(request):
    return render(request, "pos/pos.html")


@permission_required_custom("product_search")
@require_GET
def product_search(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.filter(is_active=True)
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(barcode__icontains=query)
        )
    return JsonResponse({"products": [_product_json(product) for product in products[:40]]})


@permission_required_custom("sales")
@require_GET
def cart_detail(request):
    items, subtotal = _cart_data(request)
    return JsonResponse({"items": items, "subtotal": str(subtotal)})


@permission_required_custom("sales")
@require_POST
def cart_add(request):
    try:
        payload = json.loads(request.body or "{}")
        product_id = str(payload["product_id"])
        quantity = int(payload.get("quantity", 1))
        if quantity < 1:
            raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Produk dan quantity tidak valid."}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _cart(request).copy()
    new_quantity = int(cart.get(product_id, 0)) + quantity
    if new_quantity > product.stock:
        return JsonResponse({"error": "Quantity melebihi stok tersedia."}, status=400)
    cart[product_id] = new_quantity
    _save_cart(request, cart)
    return cart_detail(request)


@permission_required_custom("sales")
@require_POST
def cart_update(request, product_id):
    try:
        quantity = int(json.loads(request.body or "{}").get("quantity", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Quantity tidak valid."}, status=400)
    if quantity < 0:
        return JsonResponse({"error": "Quantity tidak valid."}, status=400)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if quantity > product.stock:
        return JsonResponse({"error": "Quantity melebihi stok tersedia."}, status=400)
    cart = _cart(request).copy()
    if quantity:
        cart[str(product_id)] = quantity
    else:
        cart.pop(str(product_id), None)
    _save_cart(request, cart)
    return cart_detail(request)


@permission_required_custom("sales")
@require_POST
@transaction.atomic
def checkout(request):
    try:
        payload = json.loads(request.body or "{}")
        payment = _money(payload.get("bayar", "0"))
        discount = _money(payload.get("diskon", "0"))
        method = str(payload.get("metode_bayar", "CASH")).upper()[:20]
    except (InvalidOperation, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Data pembayaran tidak valid."}, status=400)
    if payment < 0 or discount < 0:
        return JsonResponse({"error": "Pembayaran dan diskon tidak boleh negatif."}, status=400)

    cart = _cart(request)
    if not cart:
        return JsonResponse({"error": "Keranjang masih kosong."}, status=400)
    products = list(Product.objects.select_for_update().filter(pk__in=cart.keys(), is_active=True))
    if len(products) != len(cart):
        return JsonResponse({"error": "Ada produk di keranjang yang sudah tidak tersedia."}, status=400)
    quantities = {product.pk: int(cart[str(product.pk)]) for product in products}
    for product in products:
        if quantities[product.pk] < 1 or quantities[product.pk] > product.stock:
            return JsonResponse({"error": f"Stok {product.name} tidak mencukupi."}, status=400)

    subtotal = sum(
        (_money(product.selling_price * quantities[product.pk]) for product in products),
        Decimal("0.00"),
    )
    total = subtotal - discount
    if total < 0:
        return JsonResponse({"error": "Diskon tidak boleh melebihi subtotal."}, status=400)
    if payment < total:
        return JsonResponse({"error": "Uang pelanggan belum mencukupi."}, status=400)

    sale = Penjualan.objects.create(
        no_nota=f"TRX-{timezone.localdate():%Y%m%d}-{uuid4().hex[:6].upper()}",
        kasir_id=request.session["user_id"],
        kasir_nama=request.session.get("name", request.session.get("username", "Kasir")),
        subtotal=subtotal,
        diskon=discount,
        total=total,
        bayar=payment,
        kembalian=payment - total,
        metode_bayar=method,
    )
    for product in products:
        quantity = quantities[product.pk]
        line_total = _money(product.selling_price * quantity)
        DetailPenjualan.objects.create(
            transaksi=sale,
            produk=product,
            nama_produk=product.name,
            sku=product.sku,
            harga=product.selling_price,
            qty=quantity,
            subtotal=line_total,
        )
        product.stock -= quantity
        product.save(update_fields=["stock"])

    request.session.pop("pos_cart", None)
    return JsonResponse({"success": True, "redirect": f"/pos/struk/{sale.pk}/"})


@permission_required_custom("transaction_history")
def receipt(request, pk):
    sale = get_object_or_404(_sale_queryset_for_user(request), pk=pk)
    return render(request, "pos/struk.html", {"sale": sale})


@permission_required_custom("transaction_history")
def sales_history(request):
    sales = _sale_queryset_for_user(request)
    return render(request, "pos/riwayat.html", {"sales": sales[:100]})


@permission_required_custom("sales")
@require_POST
@transaction.atomic
def sales_return(request, pk):
    sale = get_object_or_404(_sale_queryset_for_user(request), pk=pk)
    try:
        payload = json.loads(request.body or "{}")
        detail = sale.detail.select_for_update().get(pk=payload["detail_id"])
        quantity = int(payload["quantity"])
        reason = str(payload.get("alasan", "LAINNYA"))[:120]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, DetailPenjualan.DoesNotExist):
        return JsonResponse({"error": "Data retur tidak valid."}, status=400)
    returned = sum(item.qty for item in detail.retur.all())
    if quantity < 1 or returned + quantity > detail.qty:
        return JsonResponse({"error": "Quantity retur melebihi quantity terjual."}, status=400)
    product = Product.objects.select_for_update().get(pk=detail.produk_id)
    product.stock += quantity
    product.save(update_fields=["stock"])
    record = ReturPenjualan.objects.create(
        transaksi=sale,
        detail=detail,
        qty=quantity,
        alasan=reason,
        dibuat_oleh=request.session.get("name", request.session.get("username", "Kasir")),
    )
    return JsonResponse({"success": True, "return_id": record.pk})