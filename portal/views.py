import bcrypt
import secrets
from __future__ import annotations
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from .db import get_connection
from .rbac import require_login, require_permission, require_any_permission
from datetime import timedelta
from django.utils import timezone

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


def _get_placeholder_messages() -> list[dict]:
    return [
        {
            "subject": "Welcome to the Patient Portal",
            "from": "Portal Support",
            "date": "Today",
            "preview": "This is a Inbox.",
        },
        {
            "subject": "Appointment Reminder",
            "from": "Care Team",
            "date": "Yesterday",
            "preview": "Reminder: You have an upcoming appointment scheduled.",
        },
    ]


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        if request.user.is_authenticated and request.session.get("user_id"):
            return redirect("portal:dashboard")
        return render(request, "portal/login.html")
    email_or_username = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""
    if not email_or_username or not password:
        return render(
            request,
            "portal/login.html",
            {"error": "An email + password are required NOOB."},
        )
    user = authenticate(request, username=email_or_username, password=password)
    if not user:
        return render(
            request,
            "portal/login.html",
            {"error": "Either an invalid email or password."},
        )
    login(request, user)
    sql_user_id = getattr(user, "sql_user_id", None)
    sql_role_id = getattr(user, "sql_role_id", None)
    if not sql_user_id or not sql_role_id:
        logout(request)
        return render(
            request,
            "portal/login.html",
            {"error": "Login System MIGHT NOT BE configured properly. KINDLY configure it again. KINDLY. "},
        )
    request.session["user_id"] = int(sql_user_id)
    request.session["role_id"] = int(sql_role_id)
    request.session["email"] = getattr(user, "email", "") or user.get_username()
    request.session["display_name"] = (user.get_full_name() or user.get_username()).strip()
    request.session["sql_user_id"] = int(sql_user_id)
    request.session["permissions"] = get_permissions_for_role(int(sql_role_id))
    if not request.session.session_key:
        request.session.save()
    create_sql_session(
        user_id=int(sql_user_id),
        session_token=request.session.session_key,
        hours_valid=2,
    )
    return redirect("portal:dashboard")

@require_login
def dashboard_view(request):
    user_id = int(request.session["user_id"])
    portal_messages = _get_placeholder_messages()
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "appointments": [],
        "portal_messages": portal_messages,
        "notif_unread_count": get_unread_count(user_id),
        "notif_preview": list_notifications(user_id, limit=5),
    }
    return render(request, "portal/dashboard.html", context)


@require_login
def logout_view(request):
    token = request.session.session_key
    if token:
        revoke_sql_session(token)
    logout(request)
    request.session.flush()
    return redirect("portal:login")


@require_login
@require_http_methods(["GET", "POST"])
def settings_view(request):
    username = request.session.get("display_name") or request.session.get("email")
    context = {"username": username}
    if request.method == "POST":
        current_password = request.POST.get("current_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        if not current_password or not new_password or not confirm_password:
            context["pw_error"] = "All password fields are required."
            return render(request, "portal/settings.html", context)
        if new_password != confirm_password:
            context["pw_error"] = "New passwords do not match."
            return render(request, "portal/settings.html", context)
        if len(new_password) < 8:
            context["pw_error"] = "New password must be at least 9 characters."
            return render(request, "portal/settings.html", context)
        email = (request.session.get("email") or "").strip().lower()
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT id, password_hash
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()
        finally:
            if conn:
                conn.close()
        if not row:
            context["pw_error"] = "User has not been found."
            return render(request, "portal/settings.html", context)
        stored_hash = row.get("password_hash", "")
        try:
            ok = bcrypt.checkpw(current_password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            ok = False
        if not ok:
            context["pw_error"] = "Password is incorrect."
            return render(request, "portal/settings.html", context)
        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (new_hash, row["id"]),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()
        context["pw_success"] = "SUCCESSFULL PASSWORD CHANGE"
        return render(request, "portal/settings.html", context)
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
        "portal_messages": _get_placeholder_messages(),
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
    return redirect("portal:notifications")


@require_login
@require_http_methods(["POST"])
def notifications_mark_all_read(request):
    user_id = int(request.session["user_id"])
    mark_all_read(user_id=user_id)
    return redirect("portal:notifications")


@require_permission(VIEW_LOGIN_HISTORY)
def login_history_view(request):
    return JsonResponse({"ok": True, "permission": VIEW_LOGIN_HISTORY})


@require_permission(MANAGE_USERS)
def manage_users_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_USERS})


@require_permission(MANAGE_ROLES_PERMISSIONS)
def manage_roles_permissions_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_ROLES_PERMISSIONS})


@require_permission(MANAGE_SESSIONS)
def manage_sessions_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_SESSIONS})


@require_permission(MANAGE_NOTIFICATIONS)
def manage_notifications_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_NOTIFICATIONS})


@require_permission(VIEW_MESSAGES)
def view_messages_view(request):
    return JsonResponse({"ok": True, "permission": VIEW_MESSAGES})


@require_permission(SEND_MESSAGES)
@require_http_methods(["POST"])
def send_messages_view(request):
    return JsonResponse({"ok": True, "permission": SEND_MESSAGES})


@require_permission(REQUEST_APPOINTMENT)
@require_http_methods(["POST"])
def request_appointment_view(request):
    return JsonResponse({"ok": True, "permission": REQUEST_APPOINTMENT})


@require_permission(CANCEL_APPOINTMENT)
@require_http_methods(["POST"])
def cancel_appointment_view(request, appointment_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": CANCEL_APPOINTMENT,
            "appointment_id": appointment_id,
        }
    )


@require_permission(MANAGE_APPOINTMENTS)
def manage_appointments_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_APPOINTMENTS})


@require_permission(MANAGE_AVAILABILITY)
@require_http_methods(["POST"])
def manage_availability_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_AVAILABILITY})


@require_permission(VIEW_PATIENT_PROFILE)
def view_patient_profile_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own profile NOOB."},
            status=403,
        )
    return JsonResponse(
        {
            "ok": True,
            "permission": VIEW_PATIENT_PROFILE,
            "patient_id": patient_id,
        }
    )


@require_permission(UPDATE_PATIENT_PROFILE)
@require_http_methods(["POST"])
def update_patient_profile_view(request):
    return JsonResponse({"ok": True, "permission": UPDATE_PATIENT_PROFILE})


@require_permission(ACCESS_PATIENT_FILE)
def access_patient_file_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only access their own file LMAO."},
            status=403,
        )
    return JsonResponse(
        {
            "ok": True,
            "permission": ACCESS_PATIENT_FILE,
            "patient_id": patient_id,
        }
    )


@require_permission(CREATE_MEDICAL_RECORD)
@require_http_methods(["POST"])
def create_medical_record_view(request, patient_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": CREATE_MEDICAL_RECORD,
            "patient_id": patient_id,
        }
    )


@require_permission(UPDATE_MEDICAL_RECORD)
@require_http_methods(["POST"])
def update_medical_record_view(request, record_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": UPDATE_MEDICAL_RECORD,
            "record_id": record_id,
        }
    )


@require_permission(VIEW_PRESCRIPTIONS)
def view_prescriptions_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])

    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own prescriptions ROSH."},
            status=403,
        )

    return JsonResponse(
        {
            "ok": True,
            "permission": VIEW_PRESCRIPTIONS,
            "patient_id": patient_id,
        }
    )


@require_permission(MANAGE_PRESCRIPTIONS)
@require_http_methods(["POST"])
def manage_prescriptions_view(request):
    return JsonResponse({"ok": True, "permission": MANAGE_PRESCRIPTIONS})


@require_permission(REQUEST_REFILL)
@require_http_methods(["POST"])
def request_refill_view(request, prescription_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": REQUEST_REFILL,
            "prescription_id": prescription_id,
        }
    )


@require_permission(APPROVE_REFILL)
@require_http_methods(["POST"])
def approve_refill_view(request, refill_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": APPROVE_REFILL,
            "refill_id": refill_id,
        }
    )


@require_permission(VIEW_INSURANCE)
def view_insurance_view(request, patient_id: int):
    role_id = int(request.session.get("role_id", 0))
    user_id = int(request.session["user_id"])
    if role_id == 1 and patient_id != user_id:
        return JsonResponse(
            {"ok": False, "error": "Patients can only view their own insurance PEASANT."},
            status=403,
        )
    return JsonResponse(
        {
            "ok": True,
            "permission": VIEW_INSURANCE,
            "patient_id": patient_id,
        }
    )


@require_permission(MANAGE_INSURANCE)
@require_http_methods(["POST"])
def manage_insurance_view(request, patient_id: int):
    return JsonResponse(
        {
            "ok": True,
            "permission": MANAGE_INSURANCE,
            "patient_id": patient_id,
        }
    )

@require_login
@require_http_methods(["GET", "POST"])
def health_info_view(request):
    user_id = int(request.session["user_id"])
    username = request.session.get("display_name") or request.session.get("email")
    if request.method == "POST":
        height_cm = (request.POST.get("height_cm") or "").strip() or None
        weight_kg = (request.POST.get("weight_kg") or "").strip() or None
        blood_type = (request.POST.get("blood_type") or "").strip() or None
        conditions = (request.POST.get("conditions") or "").strip() or None
        medications = (request.POST.get("medications") or "").strip() or None
        emergency_contact_name = (request.POST.get("emergency_contact_name") or "").strip() or None
        emergency_contact_phone = (request.POST.get("emergency_contact_phone") or "").strip() or None
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO health_info (
                    patient_id, height_cm, weight_kg, blood_type, conditions,
                    medications, emergency_contact_name, emergency_contact_phone
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    height_cm = VALUES(height_cm),
                    weight_kg = VALUES(weight_kg),
                    blood_type = VALUES(blood_type),
                    conditions = VALUES(conditions),
                    medications = VALUES(medications),
                    emergency_contact_name = VALUES(emergency_contact_name),
                    emergency_contact_phone = VALUES(emergency_contact_phone)
                """,
                (
                    user_id,
                    height_cm,
                    weight_kg,
                    blood_type,
                    conditions,
                    medications,
                    emergency_contact_name,
                    emergency_contact_phone,
                ),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()
        return JsonResponse({"ok": True, "message": "Health info saved."})
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT height_cm, weight_kg, blood_type, conditions,
                   medications, emergency_contact_name, emergency_contact_phone
            FROM health_info
            WHERE patient_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone() or {}
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "username": username,
            "health_info": row,
        }
    )


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    if request.method == "GET":
        return render(request, "portal/forgot_password.html")

    email = (request.POST.get("email") or "").strip().lower()
    if not email:
        return render(
            request,
            "portal/forgot_password.html",
            {"error": "Email is required."},
        )
    conn = None
    user_row = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, email
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            (email,),
        )
        user_row = cur.fetchone()
    finally:
        if conn:
            conn.close()
    if not user_row:
        return render(
            request,
            "portal/forgot_password.html",
            {"message": "If that account exists, a reset token was created."},
        )
    token = secrets.token_urlsafe(32)
    expires_at = (timezone.now() + timedelta(hours=1)).replace(tzinfo=None)
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reset_password_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (int(user_row["id"]), token, expires_at),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return render(
        request,
        "portal/forgot_password.html",
        {
            "message": "Reset token created.",
            "reset_token": token,
        },
    )


@require_http_methods(["GET", "POST"])
def reset_password_view(request, token: str):
    if request.method == "GET":
        return render(request, "portal/reset_password.html", {"token": token})

    new_password = request.POST.get("new_password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()
    if not new_password or not confirm_password:
        return render(
            request,
            "portal/reset_password.html",
            {"token": token, "error": "All password fields are required."},
        )
    if new_password != confirm_password:
        return render(
            request,
            "portal/reset_password.html",
            {"token": token, "error": "Passwords do not match."},
        )
    if len(new_password) < 8:
        return render(
            request,
            "portal/reset_password.html",
            {"token": token, "error": "Password must be at least 8 characters."},
        )
    now_naive = timezone.now().replace(tzinfo=None)
    conn = None
    token_row = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, user_id, expires_at, used_at
            FROM reset_password_tokens
            WHERE token = %s
            LIMIT 1
            """,
            (token,),
        )
        token_row = cur.fetchone()
    finally:
        if conn:
            conn.close()
    if not token_row or token_row["used_at"] is not None or token_row["expires_at"] <= now_naive:
        return render(
            request,
            "portal/reset_password.html",
            {"token": token, "error": "This reset link is invalid or expired."},
        )
    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, int(token_row["user_id"])),
        )
        cur.execute(
            "UPDATE reset_password_tokens SET used_at = NOW() WHERE id = %s",
            (int(token_row["id"]),),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return render(
        request,
        "portal/reset_password.html",
        {"token": token, "success": "Password reset successfully."},
    )


@require_login
def appointments_filtered_view(request):
    user_id = int(request.session["user_id"])
    role_id = int(request.session.get("role_id", 0))
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()
    base_sql = """
        SELECT id, patient_id, provider_id, appointment_type, start_time, end_time, status, reason
        FROM appointments
        WHERE {owner_filter}
    """
    params = []
    if role_id == 1:
        owner_filter = "patient_id = %s"
        params.append(user_id)
    else:
        owner_filter = "provider_id = %s"
        params.append(user_id)
    sql = base_sql.format(owner_filter=owner_filter)
    if date_from:
        sql += " AND DATE(start_time) >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(start_time) <= %s"
        params.append(date_to)
    sql += " ORDER BY start_time DESC"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "date_from": date_from,
            "date_to": date_to,
            "appointments": rows,
        }
    )


@require_login
@require_http_methods(["GET", "POST"])
def security_questions_view(request):
    user_id = int(request.session["user_id"])
    if request.method == "POST":
        question_id = (request.POST.get("question_id") or "").strip()
        answer = (request.POST.get("answer") or "").strip()
        if not question_id or not answer:
            return JsonResponse(
                {"ok": False, "error": "Question and answer are required."},
                status=400,
            )
        answer_hash = bcrypt.hashpw(answer.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_security_qa (user_id, question_id, answer_hash)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE answer_hash = VALUES(answer_hash)
                """,
                (user_id, int(question_id), answer_hash),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()
        return JsonResponse({"ok": True, "message": "Security question saved."})
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, question_text
            FROM security_questions
            WHERE is_active = 1
            ORDER BY id
            """
        )
        questions = cur.fetchall()
        cur.execute(
            """
            SELECT usq.question_id, sq.question_text
            FROM user_security_qa usq
            JOIN security_questions sq ON sq.id = usq.question_id
            WHERE usq.user_id = %s
            ORDER BY usq.question_id
            """,
            (user_id,),
        )
        saved_questions = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "questions": questions,
            "saved_questions": saved_questions,
        }
    )


@require_login
def accessibility_view(request):
    context = {
        "username": request.session.get("display_name") or request.session.get("email"),
        "guidelines": [
            "Use high-contrast mode where possible.",
            "All portal pages should support keyboard navigation.",
            "Images should include descriptive alt text.",
            "Form fields should use clear labels and error messages.",
            "Videos should provide captions when applicable.",
        ],
    }
    return render(request, "portal/accessibility.html", context)


@require_permission(REQUEST_APPOINTMENT)
@require_http_methods(["POST"])
def schedule_follow_up_appointment_view(request, appointment_id: int):
    user_id = int(request.session["user_id"])

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT patient_id, provider_id, appointment_type, reason
            FROM appointments
            WHERE id = %s
            LIMIT 1
            """,
            (appointment_id,),
        )
        parent = cur.fetchone()
        if not parent:
            return JsonResponse({"ok": False, "error": "Appointment not found."}, status=404)
        if int(parent["patient_id"]) != user_id:
            return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
        slot_id = int(request.POST.get("slot_id", "0") or 0)
        reason = (request.POST.get("reason") or parent.get("reason") or "Follow-up appointment").strip()
        if not slot_id:
            return JsonResponse({"ok": False, "error": "slot_id is required."}, status=400)
        cur.execute(
            """
            SELECT id, provider_id, start_time, end_time, status
            FROM availability_slots
            WHERE id = %s
            LIMIT 1
            """,
            (slot_id,),
        )
        slot = cur.fetchone()
        if not slot:
            return JsonResponse({"ok": False, "error": "Slot not found."}, status=404)
        if slot["status"] != "open":
            return JsonResponse({"ok": False, "error": "Slot is not available."}, status=400)
        if int(slot["provider_id"]) != int(parent["provider_id"]):
            return JsonResponse({"ok": False, "error": "Slot must belong to the same provider."}, status=400)
        cur.execute(
            """
            INSERT INTO appointments (
                patient_id, provider_id, slot_id, parent_appointment_id,
                appointment_type, start_time, end_time, status, reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'requested', %s)
            """,
            (
                int(parent["patient_id"]),
                int(parent["provider_id"]),
                int(slot["id"]),
                appointment_id,
                "follow_up",
                slot["start_time"],
                slot["end_time"],
                reason,
            ),
        )
        cur.execute(
            """
            UPDATE availability_slots
            SET status = 'booked'
            WHERE id = %s
            """,
            (int(slot["id"]),),
        )
        conn.commit()
        return JsonResponse({"ok": True, "message": "Follow-up appointment requested."})
    finally:
        if conn:
            conn.close()


@require_login
def doctor_availability_view(request):
    provider_id = int(request.GET.get("provider_id", "0") or 0)
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()
    if not provider_id:
        return JsonResponse({"ok": False, "error": "provider_id is required."}, status=400)
    sql = """
        SELECT id, provider_id, start_time, end_time, status
        FROM availability_slots
        WHERE provider_id = %s AND status = 'open'
    """
    params = [provider_id]
    if date_from:
        sql += " AND DATE(start_time) >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(start_time) <= %s"
        params.append(date_to)
    sql += " ORDER BY start_time ASC"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return JsonResponse({"ok": True, "availability": rows})
