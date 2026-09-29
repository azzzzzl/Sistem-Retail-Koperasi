from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .permissions import has_permission


def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("/login/")

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.session.get("user_id"):
                return redirect("/login/")

            role = request.session.get("role")

            if role not in allowed_roles:
                return HttpResponseForbidden(
                    "Anda tidak memiliki akses ke halaman ini."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required_custom(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.session.get("user_id"):
                return redirect("/login/")

            role = request.session.get("role")

            if not has_permission(role, permission):
                return HttpResponseForbidden(
                    "Anda tidak memiliki izin untuk mengakses fitur ini."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator