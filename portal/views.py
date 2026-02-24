from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .rbac import require_login
from .authentication_service import (
    authenticate_user,
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
        if request.session.get("user_id"):
            return redirect("dashboard")
        return render(request, "portal/login.html")
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""
    if not email or not password:
        return render(request, "portal/login.html", {"error": "AN EMAIL AND A PASSWORD ARE REQUIRED."})
    ip_address = _get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    user = authenticate_user(
        email=email,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if not user:
        return render(request, "portal/login.html", {"error": "INVALID EMAIL or maybe PASSWORD."})
    request.session["user_id"] = user.id
    request.session["role_id"] = user.role_id
    request.session["email"] = user.email
    display_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    request.session["display_name"] = display_name or user.email
    request.session["permissions"] = get_permissions_for_role(user.role_id)
    if not request.session.session_key:
        request.session.save()
    session_token = request.session.session_key
    create_sql_session(user_id=user.id, session_token=session_token, hours_valid=2)
    return redirect("dashboard")


@require_login
def dashboard_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "appointments": [],
    }
    return render(request, "portal/dashboard.html", context)


@require_login
def logout_view(request):
    token = request.session.session_key
    if token:
        revoke_sql_session(token)
    request.session.flush()
    return redirect("login")
