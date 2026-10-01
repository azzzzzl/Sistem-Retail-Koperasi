from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseForbidden
from .decorators import (login_required_custom, role_required, permission_required_custom)
from .services import AuthenticationService
from .repositories import UserRepository
from .audit_service import AuditLogService
from .constants import ROLES

from apps.reports.services import ReportService

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        rate_key = f"login-attempts:{client_ip}:{username.lower()}"
        failed_attempts = int(cache.get(rate_key, 0) or 0)

        if failed_attempts >= 5:
            messages.error(request, "Terlalu banyak percobaan login. Coba lagi beberapa menit lagi.")
            return render(request, "authentication/login.html")

        if not username or not password:
            messages.error(
                request,
                "Username dan password wajib diisi."
            )

            return render(
                request,
                "authentication/login.html"
            )

        service = AuthenticationService()

        user, error = service.login(
            username=username,
            password=password,
        )

        if error:
            cache.set(rate_key, failed_attempts + 1, timeout=600)
            messages.error(request, error)

            return render(
                request,
                "authentication/login.html"
            )

        cache.delete(rate_key)
        request.session["user_id"] = str(user["_id"])
        request.session["username"] = user["username"]
        request.session["name"] = user["name"]
        request.session["role"] = user["role"]

        audit_service = AuditLogService()

        audit_service.log(
            request=request,
            action="login",
            description="User berhasil login.",
            target_type="user",
            target_id=str(user["_id"]),
            module="authentication",
            reference_id=str(user["_id"]),
            after={"username": user.get("username"), "role": user.get("role")},
        )

        return redirect("/dashboard/")

    return render(
        request,
        "authentication/login.html"
    )


@login_required_custom
def logout_view(request):
    audit_service = AuditLogService()

    audit_service.log(
        request=request,
        action="logout",
        description="User berhasil logout.",
        target_type="user",
        target_id=request.session.get("user_id"),
        module="authentication",
        reference_id=request.session.get("user_id"),
    )

    request.session.flush()

    return redirect("/login/")

@login_required_custom
def dashboard_view(request):
    context = {
        "username": request.session.get("username"),
        "name": request.session.get("name"),
        "role": request.session.get("role"),
    }
    try:
        role = request.session.get("role")
        if role in {"Admin", "Pengurus"}:
            context["analytics"] = ReportService().dashboard(low_stock_threshold=5)
    except Exception as exc:
        context["dashboard_error"] = f"Analytics belum dapat dimuat: {exc}"

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )

@role_required("Admin")
def admin_test_view(request):
    return render(
        request,
        "authentication/admin_test.html"
    )

@permission_required_custom("user_management")
def user_management_test_view(request):
    return render(
        request,
        "authentication/user_management_test.html"
    )

@permission_required_custom("sales")
def sales_test_view(request):
    return render(
        request,
        "authentication/sales_test.html"
    )

@login_required_custom
def profile_view(request):
    user_id = request.session.get("user_id")

    repository = UserRepository()
    user = repository.find_by_id(user_id)

    if not user:
        request.session.flush()
        return redirect("/login/")

    context = {
        "user": user,
    }

    return render(
        request,
        "authentication/profile.html",
        context
    )

@login_required_custom
def password_change_view(request):
    if request.method == "POST":
        current_password = request.POST.get(
            "current_password",
            ""
        )

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not current_password or not new_password or not confirm_password:
            messages.error(
                request,
                "Semua field password wajib diisi."
            )

            return render(
                request,
                "authentication/password_change.html"
            )

        if new_password != confirm_password:
            messages.error(
                request,
                "Konfirmasi password baru tidak cocok."
            )

            return render(
                request,
                "authentication/password_change.html"
            )

        service = AuthenticationService()

        success, error = service.change_password(
            user_id=request.session.get("user_id"),
            current_password=current_password,
            new_password=new_password,
        )

        if not success:
            messages.error(request, error)

            return render(
                request,
                "authentication/password_change.html"
            )

        messages.success(
            request,
            "Password berhasil diubah."
        )

        return redirect("/profile/")

    return render(
        request,
        "authentication/password_change.html"
    )

@permission_required_custom("user_management")
def user_list_view(request):
    repository = UserRepository()
    users = repository.find_all()

    for user in users:
        user["id"] = str(user["_id"])

    return render(
        request,
        "authentication/users/list.html",
        {
            "users": users,
        }
    )

@permission_required_custom("user_management")
def user_create_view(request):
    if not request.session.get("user_id"):
        return redirect("/login/")

    if request.session.get("role") != "Admin":
        return HttpResponseForbidden(
            "Anda tidak memiliki akses ke halaman ini."
        )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "")

        if not username or not name or not email or not password or not role:
            messages.error(
                request,
                "Semua field wajib diisi."
            )

            return render(
                request,
                "authentication/users/create.html",
                {"roles": ROLES}
            )

        if role not in ROLES:
            messages.error(request, "Role tidak valid.")
            return render(request, "authentication/users/create.html", {"roles": ROLES})

        service = AuthenticationService()

        try:
            service.create_user(
                username=username,
                name=name,
                email=email,
                password=password,
                role=role,
            )

            AuditLogService().log(
                request=request,
                action="create_user",
                description=f"Admin membuat user {username}.",
                target_type="user",
                target_id=username,
            )

            messages.success(
                request,
                "User berhasil dibuat."
            )

            return redirect("/users/")

        except ValueError as error:
            messages.error(request, str(error))

    return render(
        request,
        "authentication/users/create.html",
        {"roles": ROLES}
    )

@permission_required_custom("user_management")
def user_detail_view(request, user_id):
    repository = UserRepository()

    user = repository.find_by_id(user_id)

    if not user:
        return HttpResponseForbidden(
            "User tidak ditemukan."
        )

    user["id"] = str(user["_id"])

    return render(
        request,
        "authentication/users/detail.html",
        {
            "user": user,
        }
    )

@permission_required_custom("user_management")
def user_edit_view(request, user_id):
    repository = UserRepository()

    user = repository.find_by_id(user_id)

    if not user:
        return HttpResponseForbidden(
            "User tidak ditemukan."
        )

    user["id"] = str(user["_id"])

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "")

        if not name or not email or not role:
            messages.error(
                request,
                "Nama, email, dan role wajib diisi."
            )

            return render(
                request,
                "authentication/users/edit.html",
                {
                    "user": user,
                    "roles": ROLES,
                }
            )

        service = AuthenticationService()

        try:
            service.update_user(
                user_id=user_id,
                name=name,
                email=email,
                role=role,
            )

            AuditLogService().log(
                request=request,
                action="update_user",
                description=f"Data user {user['username']} diperbarui.",
                target_type="user",
                target_id=user_id,
            )

            messages.success(
                request,
                "Data user berhasil diperbarui."
            )

            return redirect(
                f"/users/{user_id}/"
            )

        except ValueError as error:
            messages.error(request, str(error))

    return render(
        request,
        "authentication/users/edit.html",
        {
            "user": user,
            "roles": ROLES,
        }
    )

@permission_required_custom("user_management")
def user_status_view(request, user_id):
    if request.method != "POST":
        return HttpResponseForbidden(
            "Metode request tidak diizinkan."
        )

    repository = UserRepository()
    user = repository.find_by_id(user_id)

    if not user:
        return HttpResponseForbidden(
            "User tidak ditemukan."
        )

    current_status = user.get("status")

    if current_status == "active":
        new_status = "inactive"
    else:
        new_status = "active"

    service = AuthenticationService()

    try:
        service.update_user_status(
            user_id=user_id,
            status=new_status,
        )

        AuditLogService().log(
            request=request,
            action="update_user_status",
            description=(
                f"Status user {user['username']} "
                f"diubah menjadi {new_status}."
            ),
            target_type="user",
            target_id=user_id,
        )

        if new_status == "active":
            messages.success(
                request,
                "User berhasil diaktifkan."
            )
        else:
            messages.success(
                request,
                "User berhasil dinonaktifkan."
            )

    except ValueError as error:
        messages.error(request, str(error))

    return redirect(f"/users/{user_id}/")

@permission_required_custom("user_management")
def user_reset_password_view(request, user_id):
    repository = UserRepository()
    user = repository.find_by_id(user_id)

    if not user:
        return HttpResponseForbidden(
            "User tidak ditemukan."
        )

    user["id"] = str(user["_id"])

    if request.method == "POST":
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not new_password or not confirm_password:
            messages.error(
                request,
                "Password baru dan konfirmasi password wajib diisi."
            )
            return render(
                request,
                "authentication/users/reset_password.html",
                {"user": user},
            )

        if new_password != confirm_password:
            messages.error(
                request,
                "Konfirmasi password tidak cocok."
            )
            return render(
                request,
                "authentication/users/reset_password.html",
                {"user": user},
            )

        service = AuthenticationService()

        try:
            service.reset_password(
                user_id=user_id,
                new_password=new_password,
            )

            AuditLogService().log(
                request=request,
                action="reset_password",
                description=f"Password user {user['username']} direset.",
                target_type="user",
                target_id=user_id,
            )

            messages.success(
                request,
                "Password user berhasil direset."
            )

            return redirect(f"/users/{user_id}/")

        except ValueError as error:
            messages.error(request, str(error))

    return render(
        request,
        "authentication/users/reset_password.html",
        {"user": user},
    )

@permission_required_custom("user_management")
def user_role_view(request, user_id):
    repository = UserRepository()
    user = repository.find_by_id(user_id)

    if not user:
        return HttpResponseForbidden(
            "User tidak ditemukan."
        )

    user["id"] = str(user["_id"])

    if request.method == "POST":
        role = request.POST.get("role", "")

        if not role:
            messages.error(
                request,
                "Role wajib dipilih."
            )
            return render(
                request,
                "authentication/users/role.html",
                {
                    "user": user,
                    "roles": ROLES,
                },
            )

        service = AuthenticationService()

        try:
            service.update_user_role(
                user_id=user_id,
                role=role,
            )

            AuditLogService().log(
                request=request,
                action="update_user_role",
                description=(
                    f"Role user {user['username']} "
                    f"diubah menjadi {role}."
                ),
                target_type="user",
                target_id=user_id,
            )

            messages.success(
                request,
                "Role user berhasil diperbarui."
            )

            return redirect(f"/users/{user_id}/")

        except ValueError as error:
            messages.error(request, str(error))

    return render(
        request,
        "authentication/users/role.html",
        {
            "user": user,
            "roles": ROLES,
        },
    )

@permission_required_custom("procurement")
def procurement_test_view(request):
    return HttpResponse("Procurement test berhasil diakses.")