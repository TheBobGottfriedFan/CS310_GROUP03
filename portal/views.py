from __future__ import annotations
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

from .rbac import require_login
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
