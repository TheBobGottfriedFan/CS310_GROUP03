from __future__ import annotations

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import bcrypt
from .db import get_connection


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("portal:dashboard")
        return render(request, "portal/login.html")

    email_or_username = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""

    if not email_or_username or not password:
        return render(
            request,
            "portal/login.html",
            {"error": "An email/username and a password are required."},
        )

    user = authenticate(request, username=email_or_username, password=password)

    if not user:
        return render(request, "portal/login.html", {"error": "Invalid login."})

    login(request, user)
    request.session["display_name"] = user.get_username()
    request.session["email"] = getattr(user, "email", "") or user.get_username()

    # Store the SQL user id in session for password change
    sql_user_id = getattr(user, "sql_user_id", None)
    if sql_user_id:
        request.session["sql_user_id"] = sql_user_id

    return redirect("portal:dashboard")


@login_required
def dashboard_view(request):
    context = {
        "username": request.session.get("display_name") or request.user.get_username(),
        "appointments": [],
    }
    return render(request, "portal/dashboard.html", context)


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("portal:login")


@login_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    username = request.session.get("display_name") or request.user.get_username()
    context = {"username": username}

    if request.method == "POST":
        current_password = request.POST.get("current_password", "").strip()
        new_password     = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Basic validation
        if not current_password or not new_password or not confirm_password:
            context["pw_error"] = "All password fields are required."
            return render(request, "portal/settings.html", context)

        if new_password != confirm_password:
            context["pw_error"] = "New passwords do not match."
            return render(request, "portal/settings.html", context)

        if len(new_password) < 8:
            context["pw_error"] = "New password must be at least 8 characters."
            return render(request, "portal/settings.html", context)

        # Get current hash from DB
        email = request.session.get("email") or request.user.get_username()
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, password_hash FROM users WHERE email = %s LIMIT 1",
                (email.strip().lower(),),
            )
            row = cur.fetchone()
        finally:
            if conn:
                conn.close()

        if not row:
            context["pw_error"] = "User not found."
            return render(request, "portal/settings.html", context)

        # Verify current password
        stored_hash = row.get("password_hash", "")
        try:
            ok = bcrypt.checkpw(current_password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            ok = False

        if not ok:
            context["pw_error"] = "Current password is incorrect."
            return render(request, "portal/settings.html", context)

        # Hash + save new password
        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, row["id"]),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()

        context["pw_success"] = "Password changed successfully!"
        return render(request, "portal/settings.html", context)

    return render(request, "portal/settings.html", context)


@login_required
def privacy_view(request):
    context = {
        "username": request.session.get("display_name") or request.user.get_username(),
    }
    return render(request, "portal/privacy.html", context)


@login_required
def messages_view(request):
    context = {
        "username": request.session.get("display_name") or request.user.get_username(),
        "portal_messages": [
            {
                "subject": "Welcome to the Patient Portal",
                "from": "Portal Support",
                "date": "Today",
                "preview": "This is a prototype inbox. Messaging will be enabled soon.",
            },
            {
                "subject": "Appointment Reminder (Prototype)",
                "from": "Care Team",
                "date": "Yesterday",
                "preview": "Reminder: You have an upcoming appointment scheduled.",
            },
        ],
    }
    return render(request, "portal/messages.html", context)


@login_required
def data_control_view(request):
    context = {
        "username": request.session.get("display_name") or request.user.get_username(),
    }
    return render(request, "portal/data_control.html", context)


@login_required
def profile_view(request):
    context = {
        "username": request.session.get("display_name") or request.user.get_username(),
    }
    return render(request, "portal/profile.html", context)