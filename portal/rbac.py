from __future__ import annotations
from functools import wraps
from typing import Callable, Any, Iterable
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .db import get_connection
from .permissions import (
    ACCESS_PATIENT_FILE,
    UPDATE_PATIENT_PROFILE,
    VIEW_LOGIN_HISTORY,
    VIEW_MESSAGES,
    REQUEST_APPOINTMENT,
    VIEW_PATIENT_PROFILE,
    MANAGE_SESSIONS,
    MANAGE_AVAILABILITY,
    MANAGE_APPOINTMENTS,
    CANCEL_APPOINTMENT,
    CREATE_MEDICAL_RECORD,
    UPDATE_MEDICAL_RECORD,
    SEND_MESSAGES,
    MANAGE_NOTIFICATIONS,
    VIEW_PRESCRIPTIONS,
    MANAGE_PRESCRIPTIONS,
    REQUEST_REFILL,
    APPROVE_REFILL,
    VIEW_INSURANCE,
    MANAGE_INSURANCE,
    MANAGE_USERS,
    MANAGE_ROLES_PERMISSIONS,
    ALL_PERMISSIONS,
)


def _normalize_permissions(perms: Any) -> list[str]:
    if not perms:
        return []
    if isinstance(perms, (list, tuple, set)):
        return [str(p).strip() for p in perms if str(p).strip()]
    return []


def _session_user_is_present(request) -> bool:
    return bool(request.session.get("user_id"))


def _is_sql_session_valid(session_token: str) -> bool:
    if not session_token:
        return False
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, expires_at, revoked_at
            FROM sessions
            WHERE session_token = %s
            LIMIT 1
            """,
            (session_token,),
        )
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False
    if row.get("revoked_at") is not None:
        return False
    expires_at = row.get("expires_at")
    if expires_at is None:
        return False
    from django.utils import timezone
    now_naive = timezone.now().replace(tzinfo=None)
    return now_naive < expires_at


def _forbidden_response(message: str):
    return HttpResponseForbidden(message)


def get_current_permissions(request) -> list[str]:
    return _normalize_permissions(request.session.get("permissions"))


def has_permission(request, permission_name: str) -> bool:
    return permission_name in get_current_permissions(request)


def has_any_permission(request, permission_names: Iterable[str]) -> bool:
    perms = set(get_current_permissions(request))
    return any(permission in perms for permission in permission_names)


def has_all_permissions(request, permission_names: Iterable[str]) -> bool:
    perms = set(get_current_permissions(request))
    return all(permission in perms for permission in permission_names)


def require_login(view_func: Callable[..., Any]):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _session_user_is_present(request):
            request.session.flush()
            return redirect("portal:login")
        token = request.session.session_key
        if not token:
            request.session.flush()
            return redirect("portal:login")
        if not _is_sql_session_valid(token):
            request.session.flush()
            return redirect("portal:login")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_permission(permission_name: str, *, forbidden_message: str = "Permission denied."):
    def decorator(view_func: Callable[..., Any]):
        @require_login
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if permission_name not in ALL_PERMISSIONS:
                return _forbidden_response("Unknown permission requested.")
            if not has_permission(request, permission_name):
                return _forbidden_response(forbidden_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_names: str, forbidden_message: str = "Permission denied."):
    def decorator(view_func: Callable[..., Any]):
        @require_login
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not permission_names:
                return _forbidden_response("No permissions were provided.")
            invalid_permissions = [p for p in permission_names if p not in ALL_PERMISSIONS]
            if invalid_permissions:
                return _forbidden_response("Unknown permission requested.")
            if not has_any_permission(request, permission_names):
                return _forbidden_response(forbidden_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*permission_names: str, forbidden_message: str = "Permission denied."):
    def decorator(view_func: Callable[..., Any]):
        @require_login
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not permission_names:
                return _forbidden_response("No permissions were provided.")
            invalid_permissions = [p for p in permission_names if p not in ALL_PERMISSIONS]
            if invalid_permissions:
                return _forbidden_response("Unknown permission requested.")
            if not has_all_permissions(request, permission_names):
                return _forbidden_response(forbidden_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
