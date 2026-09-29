from django.urls import path

from . import views


app_name = "master_data"


urlpatterns = [
    path(
        "categories/",
        views.category_list,
        name="category_list"
    ),

    path(
        "categories/create/",
        views.category_create,
        name="category_create"
    ),

    path(
        "categories/<str:category_id>/edit/",
        views.category_update,
        name="category_update"
    ),

    path(
        "categories/<str:category_id>/delete/",
        views.category_delete,
        name="category_delete"
    ),

    path(
        "products/",
        views.product_list,
        name="product_list"
    ),
    
    path(
        "products/create/",
        views.product_create,
        name="product_create"
    ),
    
    path(
        "products/<str:product_id>/edit/",
        views.product_update,
        name="product_update"
    ),
    
    path(
        "products/<str:product_id>/delete/",
        views.product_delete,
        name="product_delete"
    ),

    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/create/", views.supplier_create, name="supplier_create"),
    path(
        "suppliers/<str:supplier_id>/edit/",
        views.supplier_update,
        name="supplier_update"
    ),
    path(
        "suppliers/<str:supplier_id>/delete/",
        views.supplier_delete,
        name="supplier_delete"
    ),
    path(
    "product-suppliers/",
    views.product_supplier_list,
    name="product_supplier_list"
    ),
    path(
        "product-suppliers/create/",
        views.product_supplier_create,
        name="product_supplier_create"
    ),
    path(
        "product-suppliers/<str:product_supplier_id>/edit/",
        views.product_supplier_update,
        name="product_supplier_update"
    ),
    path(
        "product-suppliers/<str:product_supplier_id>/delete/",
        views.product_supplier_delete,
        name="product_supplier_delete"
    ),
    path(
    "members/",
    views.member_list,
    name="member_list"
    ),
    path(
        "members/create/",
        views.member_create,
        name="member_create"
    ),
    path(
        "members/<str:member_id>/edit/",
        views.member_update,
        name="member_update"
    ),
    path(
        "members/<str:member_id>/delete/",
        views.member_delete,
        name="member_delete"
    ),
]