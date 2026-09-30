from django.shortcuts import render, redirect
from django.contrib import messages

from apps.authentication.decorators import permission_required_custom
from .services import MasterDataService


service = MasterDataService()


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

        service.create_category(data)

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

        service.update_category(
            category_id,
            data
        )

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
        service.delete_category(category_id)
        messages.success(request, "Kategori berhasil dihapus.")

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
        stock = request.POST.get("stock", "0").strip()

        if not sku:
            messages.error(request, "SKU wajib diisi.")
            return render(
                request,
                "master_data/products/form.html",
                {"categories": categories}
            )

        if service.product_sku_exists(sku):
            messages.error(request, "SKU sudah digunakan.")
            return render(
                request,
                "master_data/products/form.html",
                {"categories": categories}
            )

        if barcode and service.product_barcode_exists(barcode):
            messages.error(request, "Barcode sudah digunakan.")
            return render(
                request,
                "master_data/products/form.html",
                {"categories": categories}
            )

        data = {
            "sku": sku,
            "barcode": barcode,
            "name": name,
            "category_id": category_id,
            "purchase_price": float(purchase_price),
            "selling_price": float(selling_price),
            "stock": int(stock),
            "status": "active",
        }

        service.create_product(data)
        messages.success(request, "Produk berhasil ditambahkan.")
        return redirect("master_data:product_list")

    return render(
        request,
        "master_data/products/form.html",
        {"categories": categories}
    )

@permission_required_custom("product_management")
def product_update(request, product_id):
    product = service.get_product_by_id(product_id)
    categories = service.get_categories()

    if not product:
        messages.error(
            request,
            "Produk tidak ditemukan."
        )
        return redirect(
            "master_data:product_list"
        )

    if request.method == "POST":
        sku = request.POST.get("sku", "").strip()
        barcode = request.POST.get("barcode", "").strip()
        name = request.POST.get("name", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        purchase_price = request.POST.get(
            "purchase_price",
            "0"
        ).strip()
        selling_price = request.POST.get(
            "selling_price",
            "0"
        ).strip()
        stock = request.POST.get(
            "stock",
            "0"
        ).strip()

        if not sku:
            messages.error(
                request,
                "SKU wajib diisi."
            )
            return render(
                request,
                "master_data/products/form.html",
                {
                    "product": product
                }
            )

        if service.product_sku_exists(
            sku,
            exclude_id=product_id
        ):
            messages.error(
                request,
                "SKU sudah digunakan."
            )
            return render(
                request,
                "master_data/products/form.html",
                {
                    "product": product
                }
            )

        if barcode and service.product_barcode_exists(
            barcode,
            exclude_id=product_id
        ):
            messages.error(request, "Barcode sudah digunakan.")
            return render(
                request,
                "master_data/products/form.html",
                {"product": product}
    )

        data = {
            "sku": sku,
            "barcode": barcode,
            "name": name,
            "category_id": category_id,
            "purchase_price": float(purchase_price),
            "selling_price": float(selling_price),
            "stock": int(stock),
        }

        service.update_product(
            product_id,
            data
        )

        messages.success(
            request,
            "Produk berhasil diperbarui."
        )

        return redirect(
            "master_data:product_list"
        )

    return render(
    request,
    "master_data/products/form.html",
    {
        "product": product,
        "categories": categories,
    }
)


@permission_required_custom("product_management")
def product_delete(request, product_id):
    if request.method == "POST":
        service.delete_product(product_id)

        messages.success(
            request,
            "Produk berhasil dihapus."
        )

    return redirect(
        "master_data:product_list"
    )

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

        service.create_supplier(data)

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

        service.update_supplier(
            supplier_id,
            data
        )

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
        service.delete_supplier(supplier_id)

        messages.success(
            request,
            "Supplier berhasil dihapus."
        )

    return redirect("master_data:supplier_list")

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
            "purchase_price": float(purchase_price),
            "status": "active",
        }

        service.create_product_supplier(data)

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

        data = {
            "product_id": product_id,
            "supplier_id": supplier_id,
            "supplier_product_code": supplier_product_code,
            "purchase_price": float(purchase_price),
        }

        service.update_product_supplier(
            product_supplier_id,
            data
        )

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
        service.delete_product_supplier(
            product_supplier_id
        )

        messages.success(
            request,
            "Produk supplier berhasil dihapus."
        )

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

        service.create_member(data)

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

        service.update_member(
            member_id,
            data
        )

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
        service.delete_member(member_id)

        messages.success(
            request,
            "Anggota berhasil dihapus."
        )

    return redirect(
        "master_data:member_list"
    )
