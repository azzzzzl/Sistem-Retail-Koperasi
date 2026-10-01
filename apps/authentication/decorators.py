from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .permissions import has_permission
from .repositories import UserRepository


def _refresh_session_user(request):
    """Validate the signed session against MongoDB and refresh role/status."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = UserRepository().find_by_id(user_id)
    if not user or user.get("status") != "active":
        request.session.flush()
        return None
    request.session["user_id"] = str(user["_id"])
    request.session["username"] = user.get("username", "")
    request.session["name"] = user.get("name", "")
    request.session["role"] = user.get("role", "")
    request.session.modified = True
    return user


def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _refresh_session_user(request):
            return redirect("/login/")
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = _refresh_session_user(request)
            if not user:
                return redirect("/login/")
            if user.get("role") not in allowed_roles:
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
            user = _refresh_session_user(request)
            if not user:
                return redirect("/login/")
            if not has_permission(user.get("role"), permission):
                return HttpResponseForbidden(
                    "Anda tidak memiliki izin untuk mengakses fitur ini."
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
