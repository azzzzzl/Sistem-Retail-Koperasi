from django.shortcuts import redirect
from django.urls import path

from .purchase_return_views import (
    purchase_return_list, purchase_return_create, purchase_return_approve,
)
from apps.pos.views import returns_history, sales_return, sales_return_approve

app_name = "returns_root"


def returns_home(request):
    return redirect("returns_root:sales_returns")


urlpatterns = [
    path("", returns_home, name="home"),
    path("sales/", returns_history, name="sales_returns"),
    path("sales/<str:sale_id>/", sales_return, name="sales_return"),
    path("sales/<str:sale_id>/approve/<str:return_id>/", sales_return_approve, name="sales_return_approve"),
    path("sales/approve/<str:return_id>/", sales_return_approve, name="sales_return_approve_direct"),
    path("purchases/", purchase_return_list, name="purchase_returns"),
    path("purchases/create/", purchase_return_create, name="purchase_return_create"),
    path("purchases/<str:return_id>/approve/", purchase_return_approve, name="purchase_return_approve"),
]
