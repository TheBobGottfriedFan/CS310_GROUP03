from __future__ import annotations
from functools import wraps
from typing import Callable, Any
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def require_login(view_func: Callable[..., Any]):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper
    
def require_permission(permission_name: str, *, forbidden_message: str = "Permission denied."):
    def decorator(view_func: Callable[..., Any]):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.session.get("user_id"):
                return redirect("login")
            perms = request.session.get("permissions") or []
            if permission_name not in perms:
                return HttpResponseForbidden(forbidden_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
