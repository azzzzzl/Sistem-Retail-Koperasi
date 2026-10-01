from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("", views.expense_list, name="expenses"),
    path("create/", views.expense_create, name="expense_create"),
    path("<str:expense_id>/", views.expense_detail, name="expense_detail"),
    path("<str:expense_id>/edit/", views.expense_edit, name="expense_edit"),
]
