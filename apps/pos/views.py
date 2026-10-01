from datetime import datetime, timezone
from decimal import Decimal
import uuid

from bson import ObjectId

from django.contrib import messages
from django.shortcuts import render, redirect

from apps.authentication.decorators import permission_required_custom
from apps.inventory.services import StockMovementService
from apps.authentication.audit_service import AuditLogService
from apps.master_data.services import MasterDataService

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
            "purchasePrice": float(product.get("purchase_price", product.get("purchasePrice", 0))),
            "costPrice": float(product.get("purchase_price", product.get("purchasePrice", 0))),
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
            reference_type="SALES_RETURN",
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

    members = MasterDataService().search_members(status="active")
    return render(
        request,
        "pos/index.html",
        {
            "products": products,
            "members": members,
            "payment_methods": ["CASH", "TRANSFER", "QRIS", "OTHER"],
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

    if not product or product.get("status", "active") not in {"active", True}:
        messages.error(request, "Produk tidak ditemukan atau sudah tidak aktif.")
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

    if not product or product.get("status", "active") not in {"active", True}:
        messages.error(request, "Produk tidak ditemukan atau sudah tidak aktif.")
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
    cart = get_cart(request)
    if not cart:
        messages.error(request, "Keranjang masih kosong.")
        return redirect("pos")

    product_repository = PosProductRepository()
    sales_repository = SalesRepository()
    payment_repository = PaymentRepository()
    stock_service = StockMovementService()
    cart_items, subtotal = build_cart_items(request, product_repository)
    if not cart_items:
        messages.error(request, "Tidak ada produk valid di keranjang.")
        return redirect("pos")

    try:
        discount = Decimal(request.POST.get("discount", "0"))
        tax = Decimal(request.POST.get("tax", "0"))
        payment_amount = Decimal(request.POST.get("payment_amount", "0"))
    except (TypeError, ValueError):
        messages.error(request, "Diskon, pajak, dan pembayaran harus berupa angka.")
        return redirect("pos")
    if min(discount, tax, payment_amount) < 0:
        messages.error(request, "Diskon, pajak, dan pembayaran tidak boleh negatif.")
        return redirect("pos")
    if discount > subtotal:
        messages.error(request, "Diskon tidak boleh melebihi subtotal.")
        return redirect("pos")
    total = subtotal - discount + tax
    if total < 0:
        messages.error(request, "Total transaksi tidak valid.")
        return redirect("pos")
    if payment_amount < total:
        messages.error(request, "Jumlah pembayaran kurang dari total transaksi.")
        return redirect("pos")

    payment_method = request.POST.get("payment_method", "CASH").strip().upper()
    if payment_method not in {"CASH", "TRANSFER", "QRIS", "OTHER"}:
        messages.error(request, "Metode pembayaran tidak valid.")
        return redirect("pos")
    member_id = request.POST.get("member_id", "").strip() or None
    if member_id:
        member = MasterDataService().get_member_by_id(member_id)
        if not member or member.get("status", "active") != "active":
            messages.error(request, "Anggota tidak ditemukan atau tidak aktif.")
            return redirect("pos")
    reference_number = request.POST.get("reference_number", "").strip() or None
    if payment_method != "CASH" and payment_amount != total:
        messages.error(request, "Untuk pembayaran non-tunai, jumlah pembayaran harus sama dengan total transaksi.")
        return redirect("pos")

    # Always validate against latest stock just before mutation.
    refreshed_items = []
    for item in cart_items:
        latest = product_repository.get_product(item["product_id"])
        if not latest:
            messages.error(request, f"Produk {item['product'].get('name')} sudah tidak tersedia.")
            return redirect("pos")
        latest_stock = int(latest.get("stock", 0))
        if item["quantity"] > latest_stock:
            messages.error(request, f"Stok {latest.get('name')} tidak mencukupi. Tersedia {latest_stock}.")
            return redirect("pos")
        item["product"] = latest
        refreshed_items.append(item)

    now = datetime.now(timezone.utc)
    invoice_number = generate_invoice_number(sales_repository.sales)
    sale_items = build_sale_items(refreshed_items)
    sale_data = {
        "invoiceNumber": invoice_number,
        "memberId": member_id,
        "cashierId": request.session.get("user_id"),
        "saleDate": now,
        "items": sale_items,
        "subtotal": float(subtotal),
        "discount": float(discount),
        "tax": float(tax),
        "total": float(total),
        "payment": float(payment_amount),
        "change": float(payment_amount - total) if payment_method == "CASH" else 0.0,
        "paymentMethod": payment_method,
        "referenceNumber": reference_number,
        "status": "COMPLETED",
        "createdAt": now,
        "updatedAt": now,
    }

    sale_id = None
    payment_id = None
    movements = []
    try:
        sale_id = sales_repository.create_sale(sale_data)
        for item in refreshed_items:
            movement = stock_service.create_movement(
                product_id=item["product_id"], movement_type="OUT", quantity=item["quantity"],
                reference_type="SALE", reference_id=sale_id,
                notes="Pengurangan stok dari transaksi penjualan.", created_by=request.session.get("user_id"),
            )
            movements.append(movement)
        payment_id = payment_repository.create_payment({
            "saleId": sale_id,
            "paymentMethod": payment_method,
            "amount": float(payment_amount),
            "referenceNumber": reference_number,
            "paidAt": now,
        })
    except Exception as error:
        # Compensating rollback for standalone MongoDB; stock changes are guarded by expected stock.
        for movement in reversed(movements):
            stock_service.repository.rollback_movement(movement)
        if payment_id is not None:
            payment_repository.delete_payment(payment_id)
        if sale_id is not None:
            sales_repository.delete_sale(sale_id)
        messages.error(request, f"Transaksi dibatalkan karena terjadi kesalahan: {error}")
        return redirect("pos")

    save_cart(request, {})
    AuditLogService().log(
        request=request,
        action="CREATE",
        description=f"Transaksi penjualan {invoice_number} berhasil dibuat dengan total Rp {float(total):,.0f}.",
        target_type="sale", target_id=str(sale_id), module="sales", reference_id=str(sale_id), after=sale_data,
    )
    return redirect("pos_receipt", sale_id=str(sale_id))

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
    if sale.get("status") != "COMPLETED":
        messages.error(request, "Retur hanya dapat diajukan untuk transaksi COMPLETED.")
        return redirect("sale_detail", sale_id=sale_id)

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

    return_number = f"RET-{now.year}-{uuid.uuid4().hex[:8].upper()}"
    return_data = {
        "returnNumber": return_number,
        "saleId": sale_object_id,
        "memberId": sale.get("memberId"),
        "invoiceNumber": sale.get("invoiceNumber"),
        "cashierId": request.session.get("user_id"),
        "createdBy": request.session.get("user_id"),
        "returnDate": now,
        "items": return_items,
        "reason": request.POST.get("reason", "").strip(),
        "refundAmount": float(total_return),
        "total": float(total_return),
        "refundStatus": "PENDING",
        "status": "PENDING",
        "createdAt": now,
        "updatedAt": now,
    }

    # Retur diajukan terlebih dahulu; stok baru dikembalikan setelah approval.
    return_id = returns_repository.create_return(return_data)

    AuditLogService().log(
        request=request,
        action="CREATE",
        description=(
            f"Retur penjualan untuk invoice {sale.get('invoiceNumber')} "
            f"diajukan dengan total Rp {total_return:,.0f}."
        ),
        target_type="sales_return",
        target_id=str(return_id),
        module="returns",
        reference_id=str(return_id),
        after=return_data,
    )

    messages.success(
        request,
        "Retur berhasil diajukan dan menunggu approval.",
    )

    return redirect("sale_detail", sale_id=sale["sale_id"])

@permission_required_custom("sales_cancel")
def sale_cancel(request, sale_id):
    if request.method != "POST":
        return redirect("sale_detail", sale_id=sale_id)
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
    if sale.get("status") != "COMPLETED":
        messages.error(request, "Hanya transaksi COMPLETED yang dapat dibatalkan.")
        return redirect("sale_detail", sale_id=sale_id)
    existing_returns = ReturnsRepository().get_returns_by_sale(sale_object_id)
    if existing_returns:
        messages.error(request, "Transaksi yang sudah memiliki retur tidak dapat dibatalkan penuh.")
        return redirect("sale_detail", sale_id=sale_id)
    sale = sales_repository.claim_for_cancel(sale_object_id)
    if not sale:
        messages.error(request, "Transaksi sedang atau sudah diproses pembatalannya.")
        return redirect("sale_detail", sale_id=sale_id)
    stock_service = StockMovementService()
    movements=[]
    try:
        for item in sale.get("items", []):
            movements.append(stock_service.create_movement(
                product_id=item.get("productId"), movement_type="IN", quantity=int(item.get("quantity", 0)),
                reference_type="SALE_CANCEL", reference_id=sale_id,
                notes=f"Pembatalan transaksi {sale.get('invoiceNumber')}", created_by=request.session.get("user_id"),
            ))
        cancelled = sales_repository.update_sale(
            sale_object_id,
            {
                "status": "CANCELLED",
                "cancelledAt": datetime.now(timezone.utc),
                "cancelledBy": request.session.get("user_id"),
                "updatedAt": datetime.now(timezone.utc),
            },
        )
        if getattr(cancelled, "modified_count", 0) != 1:
            raise RuntimeError("Status transaksi gagal diperbarui menjadi CANCELLED.")
        refunded = PaymentRepository().mark_sale_refunded(sale_object_id, request.session.get("user_id"))
        if getattr(refunded, "matched_count", 0) < 1:
            raise RuntimeError("Pembayaran transaksi tidak ditemukan sehingga pembatalan dibatalkan.")
    except Exception as error:
        for movement in reversed(movements):
            try:
                stock_service.repository.rollback_movement(movement)
            except Exception:
                pass
        sales_repository.sales.update_one({"_id": sale_object_id, "status": "CANCELLING"}, {"$set": {"status": "COMPLETED", "updatedAt": datetime.now(timezone.utc)}})
        messages.error(request, f"Pembatalan gagal: {error}")
        return redirect("sale_detail", sale_id=sale_id)
    AuditLogService().log(request,"CANCEL",f"Transaksi {sale.get('invoiceNumber')} dibatalkan.","sale",sale_id,module="sales",reference_id=sale_id,before={"status":"COMPLETED"},after={"status":"CANCELLED"})
    messages.success(request, "Transaksi dibatalkan dan stok dikembalikan.")
    return redirect("sale_detail", sale_id=sale_id)

@permission_required_custom("return_management")
def sales_return_approve(request, return_id):
    if request.method != "POST":
        return redirect("returns_history")

    returns_repository = ReturnsRepository()
    stock_service = StockMovementService()
    try:
        return_object_id = ObjectId(return_id)
    except Exception:
        messages.error(request, "ID retur tidak valid.")
        return redirect("returns_history")

    ret = returns_repository.claim_for_approval(return_object_id)
    if not ret:
        messages.error(request, "Retur penjualan tidak ditemukan atau sedang/telah diproses.")
        return redirect("returns_history")

    movements = []
    refund_id = None
    try:
        for item in ret.get("items", []):
            # Product may explicitly opt out of restocking returned goods.
            product_doc = PosProductRepository().get_product(str(item.get("productId")))
            is_resellable = True if not product_doc else product_doc.get("isResellable", product_doc.get("resellable", True))
            if is_resellable:
                movements.append(stock_service.create_movement(
                    product_id=item.get("productId"),
                    movement_type="IN",
                    quantity=int(item.get("quantity", 0)),
                    reference_type="SALES_RETURN",
                    reference_id=return_id,
                    notes=f"Pengembalian stok retur penjualan {ret.get('invoiceNumber', '')}",
                    created_by=request.session.get("user_id"),
                ))
        refund = PaymentRepository().create_refund(
            sale_id=ret.get("saleId"),
            return_id=return_object_id,
            amount=ret.get("refundAmount", ret.get("total", 0)),
            refunded_by=request.session.get("user_id"),
        )
        refund_id = refund.get("_id") if refund else None
        updated = returns_repository.update_return(return_object_id, {
            "status": "APPROVED",
            "approvedBy": request.session.get("user_id"),
            "approvedAt": datetime.now(timezone.utc),
            "refundStatus": "COMPLETED",
            "refundPaymentId": refund_id,
            "updatedAt": datetime.now(timezone.utc),
        })
        if getattr(updated, "modified_count", 0) != 1:
            raise RuntimeError("Status retur gagal diperbarui menjadi APPROVED.")
        AuditLogService().log(
            request=request, action="APPROVE",
            description=f"Retur penjualan {return_id} disetujui dan stok dikembalikan.",
            target_type="sales_return", target_id=return_id,
            module="returns", reference_id=return_id,
            before={"status": "PENDING"}, after={"status": "APPROVED"},
        )
        messages.success(request, "Retur penjualan disetujui dan stok telah dikembalikan.")
    except Exception as exc:
        for movement in reversed(movements):
            try:
                stock_service.repository.rollback_movement(movement)
            except Exception:
                pass
        if refund_id is not None:
            try:
                PaymentRepository().delete_refund(refund_id)
            except Exception:
                pass
        returns_repository.update_return(return_object_id, {"status": "PENDING", "refundStatus": "PENDING"})
        messages.error(request, f"Approval retur gagal: {exc}")
    return redirect("returns_history")

@permission_required_custom("return_view")
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