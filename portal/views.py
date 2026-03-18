from __future__ import annotations
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .rbac import require_login, require_permission, require_any_permission
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
)
from .authentication_service import (
    create_sql_session,
    revoke_sql_session,
    get_permissions_for_role,
)
from .notification_service import (
    get_unread_count,
    list_notifications,
    mark_read,
    mark_all_read,
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


@login_required
def logout_view(request):
    token = request.session.session_key
    if token:
        revoke_sql_session(token)
    logout(request) 
    request.session.flush() 
    return redirect("login")

@login_required
def settings_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/settings.html", context)


@login_required
def privacy_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/privacy.html", context)


@login_required
def messages_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "messages": [],  # placeholder until messaging is implemented
    }
    return render(request, "portal/messages.html", context)


@login_required
def data_control_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/data_control.html", context)


@login_required
def profile_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
    }
    return render(request, "portal/profile.html", context)

@login_required
def dashboard_view(request):
    user_id = int(request.session["user_id"])

    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "appointments": [],  # placeholder
        "notif_unread_count": get_unread_count(user_id),
        "notif_preview": list_notifications(user_id, limit=5),
    }
    return render(request, "portal/dashboard.html", context)
    

@login_required
def notifications_view(request):
    user_id = int(request.session["user_id"])
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "notif_unread_count": get_unread_count(user_id),
        "notifications": list_notifications(user_id),
    }
    return render(request, "portal/notifications.html", context)


@login_required
@require_http_methods(["POST"])
def notification_mark_read(request, notif_id: int):
    user_id = int(request.session["user_id"])
    mark_read(user_id=user_id, notif_id=notif_id)
    return redirect("notifications")
    

@login_required
@require_http_methods(["POST"])
def notifications_mark_all_read(request):
    user_id = int(request.session["user_id"])
    mark_all_read(user_id=user_id)
    return redirect("notifications")


# permission granting.
@require_permission("view_login_history")
def login_history_view(request):
 return JsonResponse({"ok": True, "permission": "view_login_history"})



@require_permission("manage_users")
def manage_users_view(request):
 return JsonResponse({"ok": True, "permission": "manage_users"})

@require_permission("manage_roles_permissions")
def manage_roles_permissions_view(request):
 return JsonResponse({"ok": True, "permission": "manage_roles_permissions"})

@require_permission("manage_sessions")
def manage_sessions_view(request):
 return JsonResponse({"ok": True, "permission": "manage_sessions"})

@require_permission("manage_notifications")
def manage_notifications_view(request):
 return JsonResponse({"ok": True, "permission": "manage_notifications"})

@require_permission("view_messages")
def view_messages_view(request):
 return JsonResponse({"ok": True, "permission": "view_messages"})

@require_permission("send_messages")
@require_http_methods(["POST"])
def send_messages_view(request):
 return JsonResponse({"ok": True, "permission": "send_messages"})

@require_permission("request_appointment")
@require_http_methods(["POST"])
def request_appointment_view(request):
 return JsonResponse({"ok": True, "permission": "request_appointment"})

@require_permission("cancel_appointment")
@require_http_methods(["POST"])
def cancel_appointment_view(request, appointment_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "cancel_appointment",
  "appointment_id": appointment_id
 })

@require_permission("manage_appointments")
def manage_appointments_view(request):
 return JsonResponse({"ok": True, "permission": "manage_appointments"})


@require_permission("manage_availability")
@require_http_methods(["POST"])
def manage_availability_view(request):
 return JsonResponse({"ok": True, "permission": "manage_availability"})

@require_permission("view_patient_profile")
def view_patient_profile_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own profile."},
            status=403
        )
    return JsonResponse({
        "ok": True,
        "permission": "view_patient_profile",
        "patient_id": patient_id
    })

@require_permission("update_patient_profile")
@require_http_methods(["POST"])
def update_patient_profile_view(request):
 return JsonResponse({"ok": True, "permission": "update_patient_profile"})

@require_permission("access_patient_file")
def access_patient_file_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only access their own file."},
            status=403
        )
    return JsonResponse({
        "ok": True,
        "permission": "access_patient_file",
        "patient_id": patient_id
    })

@require_permission("create_medical_record")
@require_http_methods(["POST"])
def create_medical_record_view(request, patient_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "create_medical_record",
  "patient_id": patient_id
 })

@require_permission("update_medical_record")
@require_http_methods(["POST"])
def update_medical_record_view(request, record_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "update_medical_record",
  "record_id": record_id
 })

@require_permission("view_prescriptions")
def view_prescriptions_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own prescriptions."},
            status=403
        )
    return JsonResponse({
        "ok": True,
        "permission": "view_prescriptions",
        "patient_id": patient_id
    })

@require_permission("manage_prescriptions")
@require_http_methods(["POST"])
def manage_prescriptions_view(request):
 return JsonResponse({"ok": True, "permission": "manage_prescriptions"})

@require_permission("request_refill")
@require_http_methods(["POST"])
def request_refill_view(request, prescription_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "request_refill",
  "prescription_id": prescription_id
 })

@require_permission("approve_refill")
@require_http_methods(["POST"])
def approve_refill_view(request, refill_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "approve_refill",
  "refill_id": refill_id
 })

@require_permission("view_insurance")
def view_insurance_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own insurance."},
            status=403
        )
    return JsonResponse({
        "ok": True,
        "permission": "view_insurance",
        "patient_id": patient_id
    })

@require_permission("manage_insurance")
@require_http_methods(["POST"])
def manage_insurance_view(request, patient_id: int):
 return JsonResponse({
  "ok": True,
  "permission": "manage_insurance",
  "patient_id": patient_id
 })
