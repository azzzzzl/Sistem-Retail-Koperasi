from django.urls import path
from . import views


urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-test/", views.admin_test_view, name="admin_test"),
    path(
        "user-management-test/",
        views.user_management_test_view,
        name="user_management_test",
    ),
    path("sales-test/", views.sales_test_view, name="sales_test"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.password_change_view, name="password_change"),
    path("users/", views.user_list_view, name="user_list"),
    path("users/create/", views.user_create_view, name="user_create"),
    path("users/<str:user_id>/", views.user_detail_view, name="user_detail"),
    path("users/<str:user_id>/edit/", views.user_edit_view,name="user_edit"),
    path("users/<str:user_id>/status/", views.user_status_view, name="user_status"),
    path("users/<str:user_id>/reset-password/", views.user_reset_password_view, name="user_reset_password"),
    path("users/<str:user_id>/role/", views.user_role_view, name="user_role"),
    path("procurement-test/", views.procurement_test_view, name="procurement_test"),
]