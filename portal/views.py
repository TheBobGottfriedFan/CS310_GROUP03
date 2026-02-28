from __future__ import annotations
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from .rbac import (
    require_login, require_permission, require_any_permission, ACCESS_PATIENT_FILE, UPDATE_PATIENT_PROFILE, VIEW_LOGIN_HISTORY, VIEW_MESSAGES, REQUEST_APPOINTMENT, VIEW_PATIENT_PROFILE, MANAGE_SESSIONS, MANAGE_AVAILABILITY, MANAGE_APPOINTMENTS, CANCEL_APPOINTMENT, CREATE_MEDICAL_RECORD, UPDATE_MEDICAL_RECORD, SEND_MESSAGES, MANAGE_NOTIFICATIONS, VIEW_PRESCRIPTIONS, MANAGE_PRESCRIPTIONS, REQUEST_REFILL, APPROVE_REFILL, VIEW_INSURANCE, MANAGE_INSURANCE, MANAGE_USERS, MANAGE_ROLES_PERMISSIONS,
)
from .authentication_service import (
    create_sql_session,
    revoke_sql_session,
    get_permissions_for_role,
)


def _get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        if request.user.is_authenticated and request.session.get("user_id"):
            return redirect("dashboard")
        return render(request, "portal/login.html")
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""
    if not email or not password:
        return render(request, "portal/login.html", {"error": "An email and a password are required."})
    _ip_address = _get_client_ip(request)
    _user_agent = request.META.get("HTTP_USER_AGENT", "")
    user = authenticate(request, email=email, password=password)
    if not user:
        return render(request, "portal/login.html", {"error": "INVALID EMAIL/PASSWORD."})
    login(request, user)
    sql_user_id = getattr(user, "sql_user_id", None)
    sql_role_id = getattr(user, "sql_role_id", None)
    if not sql_user_id or not sql_role_id:
        logout(request)
        return render(request, "portal/login.html", {"error": "THE LOGIN SYSTEM IS NOT PROPERLY CONFIGURED."})
    request.session["user_id"] = int(sql_user_id)
    request.session["role_id"] = int(sql_role_id)
    request.session["email"] = email
    request.session["display_name"] = (user.get_full_name() or email).strip()
    request.session["permissions"] = get_permissions_for_role(int(sql_role_id))
    if not request.session.session_key:
        request.session.save()
    create_sql_session(
        user_id=int(sql_user_id),
        session_token=request.session.session_key,
        hours_valid=2,
    )
    return redirect("dashboard")


@require_login
def dashboard_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "appointments": [], #once we implement appointments, we will use this.
    }
    return render(request, "portal/dashboard.html", context)


@require_login
def logout_view(request):
    token = request.session.session_key
    if token:
        revoke_sql_session(token)
    logout(request) 
    request.session.flush() 
    return redirect("login")

@require_login
def settings_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/settings.html", context)


@require_login
def privacy_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/privacy.html", context)


@require_login
def messages_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "messages": [],  # placeholder until messaging is implemented
    }
    return render(request, "portal/messages.html", context)


@require_login
def data_control_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/data_control.html", context)


@require_login
def profile_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/profile.html", context)


from django.views.decorators.http import require_http_methods
from .notification_service import (
    get_unread_count,
    list_notifications,
    mark_read,
    mark_all_read,
)

@require_login
def dashboard_view(request):
    user_id = int(request.session["user_id"])

    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "appointments": [],  # placeholder
        "notif_unread_count": get_unread_count(user_id),
        "notif_preview": list_notifications(user_id, limit=5),
    }
    return render(request, "portal/dashboard.html", context)
    

@require_login
def notifications_view(request):
    user_id = int(request.session["user_id"])
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "notif_unread_count": get_unread_count(user_id),
        "notifications": list_notifications(user_id),
    }
    return render(request, "portal/notifications.html", context)


@require_login
@require_http_methods(["POST"])
def notification_mark_read(request, notif_id: int):
    user_id = int(request.session["user_id"])
    mark_read(user_id=user_id, notif_id=notif_id)
    return redirect("notifications")
    

@require_login
@require_http_methods(["POST"])
def notifications_mark_all_read(request):
    user_id = int(request.session["user_id"])
    mark_all_read(user_id=user_id)
    return redirect("notifications")

