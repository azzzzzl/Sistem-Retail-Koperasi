from datetime import datetime, timezone
from decimal import Decimal

from bson import ObjectId

from django.contrib import messages
from django.shortcuts import render, redirect

from apps.authentication.decorators import permission_required_custom
from apps.inventory.services import StockMovementService
from apps.authentication.audit_service import AuditLogService

from .repositories import PosProductRepository
from .sales_repository import SalesRepository
from .payment_repository import PaymentRepository
from .returns_repository import ReturnsRepository
from .utils import generate_invoice_number


# =========================================================
# CART
# =========================================================

def get_cart(request):
    return request.session.get("pos_cart", {})


def save_cart(request, cart):
    request.session["pos_cart"] = cart
    request.session.modified = True


# =========================================================
# BUILD CART ITEMS
# =========================================================

def build_cart_items(request, repository):
    cart = get_cart(request)

    items = []
    subtotal = Decimal("0")

    for product_id, cart_item in cart.items():
        product = repository.get_product(product_id)

        if not product:
            continue

        quantity = int(cart_item["quantity"])

        price = Decimal(
            str(product.get("selling_price", 0))
        )

        item_subtotal = price * quantity
        subtotal += item_subtotal

        items.append({
            "product": product,
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "subtotal": item_subtotal,
        })

    return items, subtotal


# =========================================================
# BUILD SALES ITEMS / SNAPSHOT
# =========================================================

def build_sale_items(cart_items):
    sale_items = []

    for item in cart_items:
        product = item["product"]

        sale_items.append({
            "productId": item["product_id"],
            "sku": product.get("sku", ""),
            "barcode": product.get("barcode", ""),
            "name": product.get("name", ""),
            "quantity": item["quantity"],
            "sellingPrice": float(item["price"]),
            "discount": 0.0,
            "subtotal": float(item["subtotal"]),
        })

    return sale_items


# =========================================================
# STOCK MOVEMENT
# =========================================================

def create_sale_stock_movements(
    cart_items,
    stock_movement_service,
    reference_id,
    created_by,
):
    for item in cart_items:
        stock_movement_service.create_movement(
            product_id=item["product_id"],
            movement_type="OUT",
            quantity=item["quantity"],
            reference_type="SALE",
            reference_id=reference_id,
            notes="Pengurangan stok dari transaksi penjualan.",
            created_by=created_by,
        )

def create_return_stock_movements(
    return_items,
    stock_movement_service,
    reference_id,
    created_by,
):
    for item in return_items:
        stock_movement_service.create_movement(
            product_id=item["productId"],
            movement_type="IN",
            quantity=item["quantity"],
            reference_type="OTHER",
            reference_id=reference_id,
            notes="Penambahan stok dari retur penjualan.",
            created_by=created_by,
        )


# =========================================================
# POS PAGE
# =========================================================

@permission_required_custom("sales")
def pos_page(request):
    search = request.GET.get("search", "").strip()

    repository = PosProductRepository()

    products = repository.search_products(search)

    for product in products:
        product["product_id"] = str(product["_id"])

    cart_items, subtotal = build_cart_items(
        request,
        repository,
    )

    discount = Decimal("0")
    total = subtotal - discount

    return render(
        request,
        "pos/index.html",
        {
            "products": products,
            "search": search,
            "cart_items": cart_items,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
        },
    )


# =========================================================
# ADD TO CART
# =========================================================

@permission_required_custom("sales")
def add_to_cart(request, product_id):
    repository = PosProductRepository()

    product = repository.get_product(product_id)

    if not product:
        messages.error(
            request,
            "Produk tidak ditemukan.",
        )
        return redirect("pos")

    if request.method != "POST":
        return redirect("pos")

    stock = int(product.get("stock", 0))

    if stock <= 0:
        messages.error(
            request,
            f"Stok produk {product.get('name')} habis.",
        )
        return redirect("pos")

    cart = get_cart(request)

    product_id = str(product["_id"])

    current_quantity = int(
        cart.get(product_id, {}).get("quantity", 0)
    )

    new_quantity = current_quantity + 1

    if new_quantity > stock:
        messages.error(
            request,
            f"Stok {product.get('name')} hanya tersedia {stock}.",
        )
        return redirect("pos")

    cart[product_id] = {
        "product_id": product_id,
        "quantity": new_quantity,
    }

    save_cart(request, cart)

    messages.success(
        request,
        f"{product.get('name')} ditambahkan ke keranjang.",
    )

    return redirect("pos")


# =========================================================
# UPDATE CART
# =========================================================

@permission_required_custom("sales")
def update_cart(request, product_id):
    if request.method != "POST":
        return redirect("pos")

    repository = PosProductRepository()

    product = repository.get_product(product_id)

    if not product:
        messages.error(
            request,
            "Produk tidak ditemukan.",
        )
        return redirect("pos")

    try:
        quantity = int(
            request.POST.get("quantity", 0)
        )
    except (TypeError, ValueError):
        messages.error(
            request,
            "Quantity tidak valid.",
        )
        return redirect("pos")

    if quantity < 1:
        messages.error(
            request,
            "Quantity minimal 1.",
        )
        return redirect("pos")

    stock = int(product.get("stock", 0))

    if quantity > stock:
        messages.error(
            request,
            f"Stok {product.get('name')} hanya tersedia {stock}.",
        )
        return redirect("pos")

    cart = get_cart(request)

    product_id = str(product["_id"])

    if product_id not in cart:
        messages.error(
            request,
            "Produk tidak ada di keranjang.",
        )
        return redirect("pos")

    cart[product_id]["quantity"] = quantity

    save_cart(request, cart)

    messages.success(
        request,
        f"Quantity {product.get('name')} diperbarui.",
    )

    return redirect("pos")


# =========================================================
# CHECKOUT
# =========================================================

@permission_required_custom("sales")
def checkout(request):
    if request.method != "POST":
        return redirect("pos")

    # -----------------------------------------------------
    # AMBIL CART DARI SESSION
    # -----------------------------------------------------

    cart = get_cart(request)

    if not cart:
        messages.error(
            request,
            "Keranjang masih kosong.",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # REPOSITORY & SERVICE
    # -----------------------------------------------------

    product_repository = PosProductRepository()
    sales_repository = SalesRepository()
    payment_repository = PaymentRepository()
    stock_service = StockMovementService()

    # -----------------------------------------------------
    # BUILD CART
    # -----------------------------------------------------

    cart_items, subtotal = build_cart_items(
        request,
        product_repository,
    )

    if not cart_items:
        messages.error(
            request,
            "Tidak ada produk valid di keranjang.",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------

    discount = Decimal("0")
    total = subtotal - discount

    # -----------------------------------------------------
    # VALIDASI PEMBAYARAN
    # -----------------------------------------------------

    try:
        payment_amount = Decimal(
            request.POST.get(
                "payment_amount",
                "0",
            )
        )
    except (TypeError, ValueError):
        messages.error(
            request,
            "Jumlah pembayaran tidak valid.",
        )
        return redirect("pos")

    if payment_amount < total:
        messages.error(
            request,
            "Jumlah pembayaran kurang dari total transaksi.",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # VALIDASI STOK TERBARU
    # -----------------------------------------------------

    for item in cart_items:
        product_id = item["product_id"]

        latest_product = product_repository.get_product(
            product_id
        )

        if not latest_product:
            messages.error(
                request,
                f"Produk {item['product'].get('name')} "
                f"sudah tidak tersedia.",
            )
            return redirect("pos")

        latest_stock = int(
            latest_product.get("stock", 0)
        )

        requested_quantity = int(
            item["quantity"]
        )

        if requested_quantity > latest_stock:
            messages.error(
                request,
                f"Stok {latest_product.get('name')} "
                f"tidak mencukupi. "
                f"Stok tersedia: {latest_stock}, "
                f"jumlah yang dibeli: "
                f"{requested_quantity}.",
            )
            return redirect("pos")

    # -----------------------------------------------------
    # GENERATE INVOICE
    # -----------------------------------------------------

    invoice_number = generate_invoice_number(
        sales_repository.sales
    )

    # -----------------------------------------------------
    # SNAPSHOT ITEM
    # -----------------------------------------------------

    sale_items = build_sale_items(
        cart_items
    )

    # -----------------------------------------------------
    # DATA TRANSAKSI
    # -----------------------------------------------------

    now = datetime.now(timezone.utc)

    sale_data = {
        "invoiceNumber": invoice_number,
        "memberId": None,
        "cashierId": request.session.get("user_id"),
        "saleDate": now,
        "items": sale_items,
        "subtotal": float(subtotal),
        "discount": float(discount),
        "tax": 0.0,
        "total": float(total),
        "payment": float(payment_amount),
        "change": float(payment_amount - total),
        "status": "COMPLETED",
        "createdAt": now,
        "updatedAt": now,
    }

    # -----------------------------------------------------
    # SIMPAN SALES
    # -----------------------------------------------------

    try:
        sale_id = sales_repository.create_sale(
            sale_data
        )
    except Exception as error:
        messages.error(
            request,
            f"Transaksi penjualan gagal disimpan: {error}",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # KURANGI STOK
    # -----------------------------------------------------

    try:
        create_sale_stock_movements(
            cart_items=cart_items,
            stock_movement_service=stock_service,
            reference_id=sale_id,
            created_by=request.session.get("user_id"),
        )
    except Exception as error:
        messages.error(
            request,
            f"Stok gagal diperbarui: {error}",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # SIMPAN PAYMENT
    # -----------------------------------------------------

    payment_data = {
        "saleId": sale_id,
        "paymentMethod": "CASH",
        "amount": float(payment_amount),
        "referenceNumber": None,
        "paidAt": now,
    }

    try:
        payment_id = payment_repository.create_payment(
            payment_data
        )
    except Exception as error:
        messages.error(
            request,
            f"Pembayaran gagal disimpan: {error}",
        )
        return redirect("pos")

    # -----------------------------------------------------
    # KOSONGKAN CART
    # -----------------------------------------------------

    save_cart(request, {})

    audit_service = AuditLogService()

    audit_service.log(
        request=request,
        action="CREATE_SALE",
        description=(
            f"Transaksi penjualan {invoice_number} "
            f"berhasil dibuat dengan total "
            f"Rp {float(total):,.0f}."
        ),
        target_type="sale",
        target_id=str(sale_id),
    )

    return redirect(
        "pos_receipt",
        sale_id=str(sale_id),
    )


# =========================================================
# RECEIPT
# =========================================================

@permission_required_custom("sales")
def receipt(request, sale_id):
    sales_repository = SalesRepository()

    try:
        sale_object_id = ObjectId(sale_id)
    except Exception:
        messages.error(
            request,
            "ID transaksi tidak valid.",
        )
        return redirect("pos")

    sale = sales_repository.get_sale(
        sale_object_id
    )

    if not sale:
        messages.error(
            request,
            "Transaksi tidak ditemukan.",
        )
        return redirect("pos")

    return render(
        request,
        "pos/receipt.html",
        {
            "sale": sale,
        },
    )

@permission_required_custom("sales")
def sales_history(request):
    sales_repository = SalesRepository()

    sales = sales_repository.get_sales(limit=50)

    for sale in sales:
        sale["sale_id"] = str(sale["_id"])

    return render(
        request,
        "pos/sales_history.html",
        {
            "sales": sales,
        },
    )

@permission_required_custom("sales")
def sale_detail(request, sale_id):
    sales_repository = SalesRepository()

    try:
        sale_object_id = ObjectId(sale_id)
    except Exception:
        messages.error(request, "ID transaksi tidak valid.")
        return redirect("sales_history")

    sale = sales_repository.get_sale(sale_object_id)

    if not sale:
        messages.error(request, "Transaksi tidak ditemukan.")
        return redirect("sales_history")

    sale["sale_id"] = str(sale["_id"])

    return render(
        request,
        "pos/sale_detail.html",
        {
            "sale": sale,
        },
    )

@permission_required_custom("sales")
def sales_return(request, sale_id):
    sales_repository = SalesRepository()
    returns_repository = ReturnsRepository()
    stock_service = StockMovementService()

    # Validasi sale_id
    try:
        sale_object_id = ObjectId(sale_id)
    except Exception:
        messages.error(request, "ID transaksi tidak valid.")
        return redirect("sales_history")

    # Ambil transaksi
    sale = sales_repository.get_sale(sale_object_id)

    if not sale:
        messages.error(request, "Transaksi tidak ditemukan.")
        return redirect("sales_history")

    sale["sale_id"] = str(sale["_id"])

    # Ambil seluruh retur yang sudah pernah dilakukan
    existing_returns = returns_repository.get_returns_by_sale(
        sale_object_id
    )

    # Hitung quantity yang sudah diretur untuk setiap produk
    returned_quantities = {}

    for existing_return in existing_returns:
        for item in existing_return.get("items", []):
            product_id = item.get("productId")
            quantity = int(item.get("quantity", 0))

            returned_quantities[product_id] = (
                returned_quantities.get(product_id, 0)
                + quantity
            )

    # =========================
    # GET
    # =========================
    if request.method == "GET":
        return render(
            request,
            "pos/sales_return.html",
            {
                "sale": sale,
                "return_items": [],
            },
        )

    # =========================
    # POST
    # =========================
    if request.method != "POST":
        return redirect(
            "sales_return",
            sale_id=sale["sale_id"],
        )

    return_items = []
    validation_errors = []

    sale_items = sale.get("items", [])

    for index, item in enumerate(sale_items):

        # Quantity yang dibeli
        purchased_quantity = int(
            item.get("quantity", 0)
        )

        # Quantity yang sudah pernah diretur
        already_returned = returned_quantities.get(
            item.get("productId"),
            0,
        )

        # Sisa quantity yang masih boleh diretur
        remaining_quantity = (
            purchased_quantity - already_returned
        )

        # Ambil input quantity retur
        quantity_input = request.POST.get(
            f"return_quantity_{index}",
            "0",
        )

        try:
            return_quantity = int(quantity_input)
        except (ValueError, TypeError):
            validation_errors.append(
                f"Quantity retur {item.get('name')} tidak valid."
            )
            continue

        # Tidak boleh negatif
        if return_quantity < 0:
            validation_errors.append(
                f"Quantity retur {item.get('name')} tidak boleh negatif."
            )
            continue

        # Tidak boleh melebihi sisa quantity yang dapat diretur
        if return_quantity > remaining_quantity:
            validation_errors.append(
                (
                    f"Quantity retur {item.get('name')} "
                    f"melebihi sisa quantity yang dapat diretur. "
                    f"Sisa yang dapat diretur: {remaining_quantity}."
                )
            )
            continue

        # Tidak perlu dimasukkan jika quantity 0
        if return_quantity == 0:
            continue

        # Hitung subtotal retur
        selling_price = float(
            item.get("sellingPrice", 0)
        )

        subtotal = (
            selling_price * return_quantity
        )

        return_items.append(
            {
                "productId": item.get("productId"),
                "sku": item.get("sku", ""),
                "barcode": item.get("barcode", ""),
                "name": item.get("name", ""),
                "quantity": return_quantity,
                "sellingPrice": selling_price,
                "subtotal": subtotal,
            }
        )

    # Jika terdapat error validasi
    if validation_errors:
        for error in validation_errors:
            messages.error(request, error)

        return render(
            request,
            "pos/sales_return.html",
            {
                "sale": sale,
                "return_items": [],
            },
        )

    # Minimal harus ada satu barang yang diretur
    if not return_items:
        messages.error(
            request,
            "Minimal satu barang harus memiliki quantity retur lebih dari 0.",
        )

        return render(
            request,
            "pos/sales_return.html",
            {
                "sale": sale,
                "return_items": [],
            },
        )

    # =========================
    # SIMPAN RETUR
    # =========================

    now = datetime.now(timezone.utc)

    total_return = sum(
        item["subtotal"]
        for item in return_items
    )

    return_data = {
        "saleId": sale_object_id,
        "invoiceNumber": sale.get("invoiceNumber"),
        "cashierId": request.session.get("user_id"),
        "returnDate": now,
        "items": return_items,
        "total": total_return,
        "status": "COMPLETED",
        "createdAt": now,
        "updatedAt": now,
    }

    # Simpan data retur
    return_id = returns_repository.create_return(
        return_data
    )

    # Kembalikan stok
    create_return_stock_movements(
        return_items=return_items,
        stock_movement_service=stock_service,
        reference_id=return_id,
        created_by=request.session.get("user_id"),
    )

    # Audit log
    audit_service = AuditLogService()

    audit_service.log(
        request=request,
        action="CREATE_SALES_RETURN",
        description=(
            f"Retur penjualan untuk invoice "
            f"{sale.get('invoiceNumber')} berhasil diproses "
            f"dengan total retur "
            f"Rp {total_return:,.0f}."
        ),
        target_type="sales_return",
        target_id=str(return_id),
    )

    messages.success(
        request,
        "Retur berhasil diproses dan stok telah dikembalikan.",
    )

    return redirect(
        "sale_detail",
        sale_id=sale["sale_id"],
    )

@permission_required_custom("sales")
def returns_history(request):
    returns_repository = ReturnsRepository()

    returns = returns_repository.get_returns(limit=50)

    for return_data in returns:
        return_data["return_id"] = str(
            return_data["_id"]
        )

    return render(
        request,
        "pos/returns_history.html",
        {
            "returns": returns,
        },
    )