from django.urls import path

from .views import (
    pos_page,
    add_to_cart,
    update_cart,
    checkout,
    receipt,
    sales_history,
    sale_detail,
    sales_return,
    returns_history,
)

urlpatterns = [
    path("", pos_page, name="pos"),

    path(
        "cart/add/<str:product_id>/",
        add_to_cart,
        name="pos_add_to_cart",
    ),

    path(
        "cart/update/<str:product_id>/",
        update_cart,
        name="pos_update_cart",
    ),

    path(
        "checkout/",
        checkout,
        name="pos_checkout",
    ),

    path(
        "receipt/<str:sale_id>/",
        receipt,
        name="pos_receipt",
    ),

    path(
        "sales/",
        sales_history,
        name="sales_history",
    ),

    path(
        "sales/<str:sale_id>/",
        sale_detail,
        name="sale_detail",
    ),

    path(
        "sales/<str:sale_id>/return/",
        sales_return,
        name="sales_return",
    ),

    path(
        "returns/",
        returns_history,
        name="returns_history",
    ),
]