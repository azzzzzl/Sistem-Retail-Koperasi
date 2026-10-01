from django.urls import path
from .views import returns_history, sales_history, sales_return, sales_return_approve

app_name = "pos_root"
urlpatterns = [
    path("sales/", sales_history, name="sales"),
    path("returns/", returns_history, name="returns"),
    path("returns/sales/", returns_history, name="sales_returns"),
    path("returns/sales/<str:sale_id>/", sales_return, name="sales_return"),
    path("returns/sales/approve/<str:return_id>/", sales_return_approve, name="sales_return_approve"),
]
