from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

from apps.authentication.decorators import permission_required_custom
from apps.inventory.services import StockMovementService
from apps.inventory.purchase_services import PurchaseService
from apps.inventory.invoice_services import SupplierInvoiceService
from apps.inventory.payment_services import SupplierPaymentService
from apps.pos.sales_repository import SalesRepository
from apps.authentication.audit_service import AuditLogService
from .services import MasterDataService


service = MasterDataService()
purchase_service = PurchaseService()
invoice_service = SupplierInvoiceService()
payment_service = SupplierPaymentService()
sales_repository = SalesRepository()


@permission_required_custom("category_management")
def category_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    categories = service.search_categories(
        search=search,
        status=status
    )

    return render(
        request,
        "master_data/categories/list.html",
        {
            "categories": categories,
            "search": search,
            "status": status,
        }
    )

@permission_required_custom("category_management")
def category_create(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not code:
            messages.error(
                request,
                "Kode kategori wajib diisi."
            )
            return render(
                request,
                "master_data/categories/form.html"
            )

        if not name:
            messages.error(
                request,
                "Nama kategori wajib diisi."
            )
            return render(
                request,
                "master_data/categories/form.html"
            )

        if service.category_code_exists(code):
            messages.error(
                request,
                "Kode kategori sudah digunakan."
            )
            return render(
                request,
                "master_data/categories/form.html"
            )

        data = {
            "code": code,
            "name": name,
            "description": description,
            "status": "active",
        }

        result = service.create_category(data)
        category_id = str(result.inserted_id)
        AuditLogService().log(request, "CREATE", f"Kategori {name} dibuat.", "category", category_id, module="master_data", reference_id=category_id, after=data)

        messages.success(
            request,
            "Kategori berhasil ditambahkan."
        )

        return redirect(
            "master_data:category_list"
        )

    return render(
        request,
        "master_data/categories/form.html"
    )

@permission_required_custom("category_management")
def category_update(request, category_id):
    category = service.get_category_by_id(category_id)

    if not category:
        messages.error(
            request,
            "Kategori tidak ditemukan."
        )
        return redirect(
            "master_data:category_list"
        )

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not code:
            messages.error(
                request,
                "Kode kategori wajib diisi."
            )
            return render(
                request,
                "master_data/categories/form.html",
                {
                    "category": category
                }
            )

        if not name:
            messages.error(
                request,
                "Nama kategori wajib diisi."
            )
            return render(
                request,
                "master_data/categories/form.html",
                {
                    "category": category
                }
            )

        if service.category_code_exists(
            code,
            exclude_id=category_id
        ):
            messages.error(
                request,
                "Kode kategori sudah digunakan."
            )
            return render(
                request,
                "master_data/categories/form.html",
                {
                    "category": category
                }
            )

        data = {
            "code": code,
            "name": name,
            "description": description,
        }

        before = dict(category)
        service.update_category(category_id, data)
        AuditLogService().log(request, "UPDATE", f"Kategori {name} diperbarui.", "category", category_id, module="master_data", reference_id=category_id, before=before, after=data)

        messages.success(
            request,
            "Kategori berhasil diperbarui."
        )

        return redirect(
            "master_data:category_list"
        )

    return render(
        request,
        "master_data/categories/form.html",
        {
            "category": category
        }
    )

@permission_required_custom("category_management")
def category_delete(request, category_id):
    if request.method == "POST":
        category = service.get_category_by_id(category_id)
        if category:
            service.update_category(category_id, {"status": "inactive"})
            AuditLogService().log(request, "UPDATE", f"Kategori {category.get('name','')} dinonaktifkan.", "category", category_id, module="master_data", reference_id=category_id, before={"status": category.get("status")}, after={"status": "inactive"})
            messages.success(request, "Kategori dinonaktifkan. Data historis tetap dipertahankan.")
        else:
            messages.error(request, "Kategori tidak ditemukan.")

    return redirect("master_data:category_list")

@permission_required_custom("product_management")
def product_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    products = service.search_products(
        search=search,
        status=status
    )

    return render(
        request,
        "master_data/products/list.html",
        {
            "products": products,
            "search": search,
            "status": status,
        }
    )


@permission_required_custom("product_management")
def product_create(request):
    categories = service.get_categories()
    if request.method == "POST":
        sku = request.POST.get("sku", "").strip()
        barcode = request.POST.get("barcode", "").strip()
        name = request.POST.get("name", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        purchase_price = request.POST.get("purchase_price", "0").strip()
        selling_price = request.POST.get("selling_price", "0").strip()
        stock_value = request.POST.get("stock", "0").strip()
        minimum_stock_value = request.POST.get("minimum_stock", "0").strip()
        errors = []
        if not sku: errors.append("SKU wajib diisi.")
        if not name: errors.append("Nama produk wajib diisi.")
        if not category_id: errors.append("Kategori wajib dipilih.")
        elif not service.get_category_by_id(category_id): errors.append("Kategori tidak ditemukan.")
        try:
            purchase = Decimal(purchase_price)
            selling = Decimal(selling_price)
            opening_stock = int(stock_value)
            minimum_stock = int(minimum_stock_value)
        except (InvalidOperation, TypeError, ValueError):
            errors.append("Harga, stok, dan stok minimum harus berupa angka yang valid.")
            purchase = selling = Decimal("0"); opening_stock = 0; minimum_stock = 0
        if purchase < 0 or selling < 0 or opening_stock < 0 or minimum_stock < 0:
            errors.append("Harga, stok, dan stok minimum tidak boleh negatif.")
        if selling < purchase:
            errors.append("Harga jual tidak boleh lebih kecil dari harga beli.")
        if service.product_sku_exists(sku): errors.append("SKU sudah digunakan.")
        if barcode and service.product_barcode_exists(barcode): errors.append("Barcode sudah digunakan.")
        if errors:
            for error in errors: messages.error(request, error)
            return render(request, "master_data/products/form.html", {"categories": categories})
        data = {
            "sku": sku, "barcode": barcode, "name": name, "category_id": category_id,
            "purchase_price": float(purchase), "selling_price": float(selling),
            "stock": 0, "minimumStock": minimum_stock, "status": "active",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        }
        result = service.create_product(data)
        product_id = str(result.inserted_id)
        if opening_stock:
            StockMovementService().create_movement(
                product_id=product_id, movement_type="IN", quantity=opening_stock,
                reference_type="OPENING_BALANCE", reference_id=product_id,
                notes="Stok awal produk saat pembuatan.", created_by=request.session.get("user_id"),
            )
        AuditLogService().log(request, "CREATE", f"Produk {name} dibuat.", "product", product_id, module="master_data", reference_id=product_id, after=data)
        messages.success(request, "Produk berhasil ditambahkan.")
        return redirect("master_data:product_list")
    return render(request, "master_data/products/form.html", {"categories": categories})


@permission_required_custom("product_management")
def product_update(request, product_id):
    product = service.get_product_by_id(product_id)
    categories = service.get_categories()
    if not product:
        messages.error(request, "Produk tidak ditemukan.")
        return redirect("master_data:product_list")
    if request.method == "POST":
        sku = request.POST.get("sku", "").strip()
        barcode = request.POST.get("barcode", "").strip()
        name = request.POST.get("name", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        purchase_price = request.POST.get("purchase_price", "0").strip()
        selling_price = request.POST.get("selling_price", "0").strip()
        stock_value = request.POST.get("stock", str(product.get("stock", 0))).strip()
        minimum_stock_value = request.POST.get("minimum_stock", str(product.get("minimumStock", product.get("minimum_stock", 0)))).strip()
        errors=[]
        try:
            purchase=Decimal(purchase_price); selling=Decimal(selling_price); target_stock=int(stock_value); minimum_stock=int(minimum_stock_value)
        except (InvalidOperation, TypeError, ValueError):
            errors.append("Harga, stok, dan stok minimum harus berupa angka yang valid."); purchase=selling=Decimal("0"); target_stock=0; minimum_stock=0
        if not sku: errors.append("SKU wajib diisi.")
        if not name: errors.append("Nama produk wajib diisi.")
        if not category_id: errors.append("Kategori wajib dipilih.")
        elif not service.get_category_by_id(category_id): errors.append("Kategori tidak ditemukan.")
        if purchase < 0 or selling < 0 or target_stock < 0 or minimum_stock < 0: errors.append("Harga, stok, dan stok minimum tidak boleh negatif.")
        if selling < purchase: errors.append("Harga jual tidak boleh lebih kecil dari harga beli.")
        if service.product_sku_exists(sku, exclude_id=product_id): errors.append("SKU sudah digunakan.")
        if barcode and service.product_barcode_exists(barcode, exclude_id=product_id): errors.append("Barcode sudah digunakan.")
        if errors:
            for error in errors: messages.error(request,error)
            product.update({"sku":sku,"barcode":barcode,"name":name,"category_id":category_id,"purchase_price":str(purchase_price),"selling_price":str(selling_price),"stock":target_stock})
            return render(request,"master_data/products/form.html",{"categories":categories,"product":product})
        before=dict(product)
        current_stock=int(product.get("stock",0))
        service.update_product(product_id,{"sku":sku,"barcode":barcode,"name":name,"category_id":category_id,"purchase_price":float(purchase),"selling_price":float(selling),"minimumStock":minimum_stock,"status":product.get("status","active")})
        if target_stock != current_stock:
            StockMovementService().create_movement(
                product_id=product_id, movement_type="ADJUSTMENT", quantity=abs(target_stock-current_stock),
                adjustment_quantity=target_stock-current_stock, reference_type="MASTER_DATA", reference_id=product_id,
                notes="Penyesuaian stok melalui form produk.", created_by=request.session.get("user_id"),
            )
        AuditLogService().log(request,"UPDATE",f"Produk {name} diperbarui.","product",product_id,module="master_data",reference_id=product_id,before=before,after={"sku":sku,"barcode":barcode,"name":name,"category_id":category_id,"purchase_price":float(purchase),"selling_price":float(selling),"stock":target_stock,"minimumStock":minimum_stock})
        messages.success(request,"Produk berhasil diperbarui.")
        return redirect("master_data:product_list")
    return render(request,"master_data/products/form.html",{"product":product,"categories":categories})


@permission_required_custom("product_management")
def product_delete(request, product_id):
    product = service.get_product_by_id(product_id)
    if request.method != "POST":
        return redirect("master_data:product_list")
    if not product:
        messages.error(request,"Produk tidak ditemukan.")
        return redirect("master_data:product_list")
    # Soft-delete to preserve historical references.
    service.update_product(product_id,{"status":"inactive"})
    AuditLogService().log(request,"UPDATE",f"Produk {product.get('name','')} dinonaktifkan.","product",product_id,module="master_data",reference_id=product_id,before={"status":product.get("status")},after={"status":"inactive"})
    messages.success(request,"Produk dinonaktifkan. Data historis tetap dipertahankan.")
    return redirect("master_data:product_list")

@permission_required_custom("supplier_management")
def supplier_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    suppliers = service.search_suppliers(
        search=search,
        status=status
    )

    return render(
        request,
        "master_data/suppliers/list.html",
        {
            "suppliers": suppliers,
            "search": search,
            "status": status,
        }
    )

@permission_required_custom("supplier_management")
def supplier_create(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        if not code:
            messages.error(request, "Kode supplier wajib diisi.")
            return render(
                request,
                "master_data/suppliers/form.html"
            )

        if not name:
            messages.error(request, "Nama supplier wajib diisi.")
            return render(
                request,
                "master_data/suppliers/form.html"
            )

        if service.supplier_code_exists(code):
            messages.error(request, "Kode supplier sudah digunakan.")
            return render(
                request,
                "master_data/suppliers/form.html"
            )

        data = {
            "code": code,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
            "status": "active",
        }

        result = service.create_supplier(data)
        supplier_id = str(result.inserted_id)
        AuditLogService().log(request, "CREATE", f"Supplier {name} dibuat.", "supplier", supplier_id, module="master_data", reference_id=supplier_id, after=data)

        messages.success(
            request,
            "Supplier berhasil ditambahkan."
        )

        return redirect("master_data:supplier_list")

    return render(
        request,
        "master_data/suppliers/form.html"
    )


@permission_required_custom("supplier_management")
def supplier_update(request, supplier_id):
    supplier = service.get_supplier_by_id(supplier_id)

    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        if not code:
            messages.error(request, "Kode supplier wajib diisi.")
            return render(
                request,
                "master_data/suppliers/form.html",
                {"supplier": supplier}
            )

        if not name:
            messages.error(request, "Nama supplier wajib diisi.")
            return render(
                request,
                "master_data/suppliers/form.html",
                {"supplier": supplier}
            )

        if service.supplier_code_exists(
            code,
            exclude_id=supplier_id
        ):
            messages.error(
                request,
                "Kode supplier sudah digunakan."
            )
            return render(
                request,
                "master_data/suppliers/form.html",
                {"supplier": supplier}
            )

        data = {
            "code": code,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
        }

        before = dict(supplier)
        service.update_supplier(supplier_id, data)
        AuditLogService().log(request, "UPDATE", f"Supplier {name} diperbarui.", "supplier", supplier_id, module="master_data", reference_id=supplier_id, before=before, after=data)

        messages.success(
            request,
            "Supplier berhasil diperbarui."
        )

        return redirect("master_data:supplier_list")

    return render(
        request,
        "master_data/suppliers/form.html",
        {"supplier": supplier}
    )


@permission_required_custom("supplier_management")
def supplier_delete(request, supplier_id):
    if request.method == "POST":
        supplier = service.get_supplier_by_id(supplier_id)
        if supplier:
            service.update_supplier(supplier_id, {"status": "inactive"})
            AuditLogService().log(request, "UPDATE", f"Supplier {supplier.get('name','')} dinonaktifkan.", "supplier", supplier_id, module="master_data", reference_id=supplier_id, before={"status": supplier.get("status")}, after={"status": "inactive"})
            messages.success(request, "Supplier dinonaktifkan. Data historis tetap dipertahankan.")
        else:
            messages.error(request, "Supplier tidak ditemukan.")
    return redirect("master_data:supplier_list")

@permission_required_custom("product_management")
def product_detail(request, product_id):
    product = service.get_product_by_id(product_id)
    if not product:
        messages.error(request, "Produk tidak ditemukan.")
        return redirect("master_data:product_list")
    movements = StockMovementService().get_product_movements(product_id)[:100]
    suppliers = [x for x in service.get_product_suppliers() if str(x.get("product_id", x.get("productId", ""))) == str(product_id)]
    product["product_id"] = str(product["_id"])
    return render(request, "master_data/products/detail.html", {"product": product, "movements": movements, "suppliers": suppliers})


@permission_required_custom("supplier_management")
def supplier_detail(request, supplier_id):
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")
    purchases = purchase_service.repository.find_by_supplier_id(supplier_id) if hasattr(purchase_service.repository, "find_by_supplier_id") else [p for p in purchase_service.get_all_purchases() if str(p.get("supplierId")) == str(supplier_id)]
    invoices = invoice_service.get_invoices_by_supplier(supplier_id) if hasattr(invoice_service, "get_invoices_by_supplier") else []
    payments = payment_service.get_payments_by_supplier(supplier_id)
    supplier["supplier_id"] = str(supplier["_id"])
    return render(request, "master_data/suppliers/detail.html", {"supplier": supplier, "purchases": purchases, "invoices": invoices, "payments": payments})


@permission_required_custom("supplier_management")
def supplier_products(request, supplier_id):
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")
    links = [
        x for x in service.get_product_suppliers()
        if str(x.get("supplierId", x.get("supplier_id", ""))) == str(supplier_id)
    ]
    products = {str(x["_id"]): x for x in service.get_products()}
    rows = []
    for link in links:
        product = products.get(str(link.get("productId", link.get("product_id", ""))), {})
        rows.append({"link": link, "product": product})
    return render(request, "master_data/suppliers/related.html", {
        "supplier": supplier, "title": "Produk Supplier", "kind": "products", "rows": rows,
    })


@permission_required_custom("supplier_management")
def supplier_purchase_orders(request, supplier_id):
    from apps.inventory.po_repositories import PurchaseOrderRepository
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")
    rows = [
        x for x in PurchaseOrderRepository().find_all()
        if str(x.get("supplierId", x.get("supplier_id", ""))) == str(supplier_id)
    ]
    return render(request, "master_data/suppliers/related.html", {
        "supplier": supplier, "title": "Purchase Order Supplier", "kind": "purchase_orders", "rows": rows,
    })


@permission_required_custom("supplier_management")
def supplier_invoices(request, supplier_id):
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")
    rows = invoice_service.get_invoices_by_supplier(supplier_id)
    return render(request, "master_data/suppliers/related.html", {
        "supplier": supplier, "title": "Invoice Supplier", "kind": "invoices", "rows": rows,
    })


@permission_required_custom("supplier_management")
def supplier_payments(request, supplier_id):
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        messages.error(request, "Supplier tidak ditemukan.")
        return redirect("master_data:supplier_list")
    rows = payment_service.get_payments_by_supplier(supplier_id)
    return render(request, "master_data/suppliers/related.html", {
        "supplier": supplier, "title": "Pembayaran Supplier", "kind": "payments", "rows": rows,
    })


@permission_required_custom("member_management")
def member_detail(request, member_id):
    member = service.get_member_by_id(member_id)
    if not member:
        messages.error(request, "Anggota tidak ditemukan.")
        return redirect("master_data:member_list")
    sales = sales_repository.get_sales_by_member(member_id, limit=200)
    member["member_id"] = str(member["_id"])
    return render(request, "master_data/members/detail.html", {"member": member, "sales": sales})


@permission_required_custom("member_management")
def member_transactions(request, member_id):
    member = service.get_member_by_id(member_id)
    if not member:
        messages.error(request, "Anggota tidak ditemukan.")
        return redirect("master_data:member_list")
    sales = sales_repository.get_sales_by_member(member_id, limit=200)
    return render(request, "master_data/members/transactions.html", {"member": member, "sales": sales})


@permission_required_custom("supplier_management")
def product_supplier_list(request):
    product_suppliers = service.get_product_suppliers()

    return render(
        request,
        "master_data/product_suppliers/list.html",
        {
            "product_suppliers": product_suppliers,
        }
    )


@permission_required_custom("supplier_management")
def product_supplier_create(request):
    products = service.get_products()
    suppliers = service.get_suppliers()

    if request.method == "POST":
        product_id = request.POST.get("product_id", "").strip()
        supplier_id = request.POST.get("supplier_id", "").strip()
        supplier_product_code = request.POST.get(
            "supplier_product_code",
            ""
        ).strip()
        purchase_price = request.POST.get(
            "purchase_price",
            "0"
        ).strip()

        if not product_id:
            messages.error(
                request,
                "Produk wajib dipilih."
            )
            return render(
                request,
                "master_data/product_suppliers/form.html",
                {
                    "products": products,
                    "suppliers": suppliers,
                }
            )

        if not supplier_id:
            messages.error(
                request,
                "Supplier wajib dipilih."
            )
            return render(
                request,
                "master_data/product_suppliers/form.html",
                {
                    "products": products,
                    "suppliers": suppliers,
                }
            )

        if not service.get_product_by_id(product_id):
            messages.error(request, "Produk tidak ditemukan.")
            return render(request, "master_data/product_suppliers/form.html", {"products": products, "suppliers": suppliers})
        if not service.get_supplier_by_id(supplier_id):
            messages.error(request, "Supplier tidak ditemukan.")
            return render(request, "master_data/product_suppliers/form.html", {"products": products, "suppliers": suppliers})
        try:
            purchase_price_value = Decimal(purchase_price)
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Harga beli supplier harus berupa angka yang valid.")
            return render(request, "master_data/product_suppliers/form.html", {"products": products, "suppliers": suppliers})
        if purchase_price_value < 0:
            messages.error(request, "Harga beli supplier tidak boleh negatif.")
            return render(request, "master_data/product_suppliers/form.html", {"products": products, "suppliers": suppliers})

        if service.product_supplier_exists(
            product_id,
            supplier_id
        ):
            messages.error(
                request,
                "Produk dan supplier tersebut sudah terdaftar."
            )
            return render(
                request,
                "master_data/product_suppliers/form.html",
                {
                    "products": products,
                    "suppliers": suppliers,
                }
            )

        data = {
            "product_id": product_id,
            "supplier_id": supplier_id,
            "supplier_product_code": supplier_product_code,
            "purchase_price": float(purchase_price_value),
            "status": "active",
        }

        result = service.create_product_supplier(data)
        product_supplier_id = str(result.inserted_id)
        AuditLogService().log(request, "CREATE", "Produk supplier dibuat.", "product_supplier", product_supplier_id, module="master_data", reference_id=product_supplier_id, after=data)

        messages.success(
            request,
            "Produk supplier berhasil ditambahkan."
        )

        return redirect(
            "master_data:product_supplier_list"
        )

    return render(
        request,
        "master_data/product_suppliers/form.html",
        {
            "products": products,
            "suppliers": suppliers,
        }
    )


@permission_required_custom("supplier_management")
def product_supplier_update(request, product_supplier_id):
    request,
    product_supplier_id

    product_supplier = service.get_product_supplier_by_id(
        product_supplier_id
    )

    if not product_supplier:
        messages.error(
            request,
            "Data product supplier tidak ditemukan."
        )
        return redirect(
            "master_data:product_supplier_list"
        )

    products = service.get_products()
    suppliers = service.get_suppliers()

    if request.method == "POST":
        product_id = request.POST.get(
            "product_id",
            ""
        ).strip()

        supplier_id = request.POST.get(
            "supplier_id",
            ""
        ).strip()

        supplier_product_code = request.POST.get(
            "supplier_product_code",
            ""
        ).strip()

        purchase_price = request.POST.get(
            "purchase_price",
            "0"
        ).strip()

        if not product_id or not supplier_id:
            messages.error(
                request,
                "Produk dan supplier wajib dipilih."
            )

            return render(
                request,
                "master_data/product_suppliers/form.html",
                {
                    "product_supplier": product_supplier,
                    "products": products,
                    "suppliers": suppliers,
                }
            )

        if service.product_supplier_exists(
            product_id,
            supplier_id,
            exclude_id=product_supplier_id
        ):
            messages.error(
                request,
                "Produk dan supplier tersebut sudah terdaftar."
            )

            return render(
                request,
                "master_data/product_suppliers/form.html",
                {
                    "product_supplier": product_supplier,
                    "products": products,
                    "suppliers": suppliers,
                }
            )

        if not service.get_product_by_id(product_id):
            messages.error(request, "Produk tidak ditemukan.")
            return render(request, "master_data/product_suppliers/form.html", {"product_supplier": product_supplier, "products": products, "suppliers": suppliers})
        if not service.get_supplier_by_id(supplier_id):
            messages.error(request, "Supplier tidak ditemukan.")
            return render(request, "master_data/product_suppliers/form.html", {"product_supplier": product_supplier, "products": products, "suppliers": suppliers})
        try:
            purchase_price_value = Decimal(purchase_price)
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Harga beli supplier harus berupa angka yang valid.")
            return render(request, "master_data/product_suppliers/form.html", {"product_supplier": product_supplier, "products": products, "suppliers": suppliers})
        if purchase_price_value < 0:
            messages.error(request, "Harga beli supplier tidak boleh negatif.")
            return render(request, "master_data/product_suppliers/form.html", {"product_supplier": product_supplier, "products": products, "suppliers": suppliers})

        data = {
            "product_id": product_id,
            "supplier_id": supplier_id,
            "supplier_product_code": supplier_product_code,
            "purchase_price": float(purchase_price_value),
        }

        before = dict(product_supplier)
        service.update_product_supplier(
            product_supplier_id,
            data
        )
        AuditLogService().log(request, "UPDATE", "Produk supplier diperbarui.", "product_supplier", product_supplier_id, module="master_data", reference_id=product_supplier_id, before=before, after=data)

        messages.success(
            request,
            "Produk supplier berhasil diperbarui."
        )

        return redirect(
            "master_data:product_supplier_list"
        )

    return render(
        request,
        "master_data/product_suppliers/form.html",
        {
            "product_supplier": product_supplier,
            "products": products,
            "suppliers": suppliers,
        }
    )


@permission_required_custom("supplier_management")
def product_supplier_delete(request, product_supplier_id):
    request,
    product_supplier_id

    if request.method == "POST":
        product_supplier = service.get_product_supplier_by_id(product_supplier_id)
        if product_supplier:
            service.update_product_supplier(product_supplier_id, {"status": "inactive"})
            AuditLogService().log(request, "UPDATE", "Produk supplier dinonaktifkan.", "product_supplier", product_supplier_id, module="master_data", reference_id=product_supplier_id, before={"status": product_supplier.get("status")}, after={"status": "inactive"})
            messages.success(request, "Produk supplier dinonaktifkan.")
        else:
            messages.error(request, "Data product supplier tidak ditemukan.")

    return redirect(
        "master_data:product_supplier_list"
    )

@permission_required_custom("member_management")
def member_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    members = service.search_members(
        search=search,
        status=status
    )

    return render(
        request,
        "master_data/members/list.html",
        {
            "members": members,
            "search": search,
            "status": status,
        }
    )


@permission_required_custom("member_management")
def member_create(request):
    if request.method == "POST":
        member_code = request.POST.get(
            "member_code",
            ""
        ).strip()

        name = request.POST.get(
            "name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        if not member_code:
            messages.error(
                request,
                "Kode anggota wajib diisi."
            )

            return render(
                request,
                "master_data/members/form.html"
            )

        if not name:
            messages.error(
                request,
                "Nama anggota wajib diisi."
            )

            return render(
                request,
                "master_data/members/form.html"
            )

        if service.member_code_exists(member_code):
            messages.error(
                request,
                "Kode anggota sudah digunakan."
            )

            return render(
                request,
                "master_data/members/form.html"
            )

        data = {
            "member_code": member_code,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
            "status": "active",
        }

        result = service.create_member(data)
        member_id = str(result.inserted_id)
        AuditLogService().log(request, "CREATE", f"Anggota {name} dibuat.", "member", member_id, module="master_data", reference_id=member_id, after=data)

        messages.success(
            request,
            "Anggota berhasil ditambahkan."
        )

        return redirect(
            "master_data:member_list"
        )

    return render(
        request,
        "master_data/members/form.html"
    )


@permission_required_custom("member_management")
def member_update(request, member_id):
    member = service.get_member_by_id(member_id)

    if not member:
        messages.error(
            request,
            "Anggota tidak ditemukan."
        )

        return redirect(
            "master_data:member_list"
        )

    if request.method == "POST":
        member_code = request.POST.get(
            "member_code",
            ""
        ).strip()

        name = request.POST.get(
            "name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        if not member_code:
            messages.error(
                request,
                "Kode anggota wajib diisi."
            )

            return render(
                request,
                "master_data/members/form.html",
                {"member": member}
            )

        if not name:
            messages.error(
                request,
                "Nama anggota wajib diisi."
            )

            return render(
                request,
                "master_data/members/form.html",
                {"member": member}
            )

        if service.member_code_exists(
            member_code,
            exclude_id=member_id
        ):
            messages.error(
                request,
                "Kode anggota sudah digunakan."
            )

            return render(
                request,
                "master_data/members/form.html",
                {"member": member}
            )

        data = {
            "member_code": member_code,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
        }

        before = dict(member)
        service.update_member(member_id, data)
        AuditLogService().log(request, "UPDATE", f"Anggota {name} diperbarui.", "member", member_id, module="master_data", reference_id=member_id, before=before, after=data)

        messages.success(
            request,
            "Anggota berhasil diperbarui."
        )

        return redirect(
            "master_data:member_list"
        )

    return render(
        request,
        "master_data/members/form.html",
        {"member": member}
    )


@permission_required_custom("member_management")
def member_delete(request, member_id):
    if request.method == "POST":
        member = service.get_member_by_id(member_id)
        if member:
            service.update_member(member_id, {"status": "inactive"})
            AuditLogService().log(request, "UPDATE", f"Anggota {member.get('name','')} dinonaktifkan.", "member", member_id, module="master_data", reference_id=member_id, before={"status": member.get("status")}, after={"status": "inactive"})
            messages.success(request, "Anggota dinonaktifkan. Data historis tetap dipertahankan.")
        else:
            messages.error(request, "Anggota tidak ditemukan.")
    return redirect("master_data:member_list")
