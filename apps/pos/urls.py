from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path("", views.pos_page, name="pos"),
    path("produk/", views.product_search, name="product-search"),
    path("keranjang/", views.cart_detail, name="cart-detail"),
    path("keranjang/tambah/", views.cart_add, name="cart-add"),
    path("keranjang/<int:product_id>/", views.cart_update, name="cart-update"),
    path("checkout/", views.checkout, name="checkout"),
    path("struk/<int:pk>/", views.receipt, name="receipt"),
    path("riwayat/", views.sales_history, name="history"),
    path("retur/<int:pk>/", views.sales_return, name="return"),
]