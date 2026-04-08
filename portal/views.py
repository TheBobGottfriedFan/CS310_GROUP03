from __future__ import annotations
import bcrypt
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .db import get_connection
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


def _get_placeholder_messages() -> list[dict]:
    return [
        {
            "subject": "Welcome to the Black Mesa Herd Patient Portal",
            "from": "Portal Support",
            "date": "Today",
            "preview": "This is a Inbox. Inbox. INBOX.",
        },
        {
            "subject": "Appointment Reminder",
            "from": "Care Team",
            "date": "Yesterday",
            "preview": "Reminder: This is a Placeholder. Placeholder. PLACEHOLDER.",
        },
    ]

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == "GET":
        if request.user.is_authenticated and request.session.get("user_id"):
            return redirect("portal:dashboard")
        return render(request, "portal/signup.html")
    email = (request.POST.get("email") or "").strip().lower()
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    password = request.POST.get("password") or ""
    confirm_password = request.POST.get("confirm_password") or ""
    if not email or not password or not confirm_password:
        return render(
            request,
            "portal/signup.html",
            {"error": "Email, password, and confirm password are required."},
        )
    if password != confirm_password:
        return render(
            request,
            "portal/signup.html",
            {"error": "Passwords do not match."},
        )
    if len(password) < 8:
        return render(
            request,
            "portal/signup.html",
            {"error": "Password must be at least 8 characters."},
        )
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            (email,),
        )
        existing_user = cur.fetchone()
        if existing_user:
            return render(
                request,
                "portal/signup.html",
                {"error": "An account with that email already exists."},
            )
        cur.execute(
            """
            SELECT id
            FROM roles
            WHERE name = 'patient'
            LIMIT 1
            """
        )
        patient_role = cur.fetchone()
        if not patient_role:
            return render(
                request,
                "portal/signup.html",
                {"error": "Patient role is not configured in the database."},
            )
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (role_id, email, password_hash, first_name, last_name, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                int(patient_role["id"]),
                email,
                password_hash,
                first_name or None,
                last_name or None,
                True,
            ),
        )
        user_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO profiles (user_id)
            VALUES (%s)
            """,
            (user_id,),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    messages.success(request, "Account created successfully. Please log in.")
    return redirect("portal:login")

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
        if len(new_password) < 9:
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
    sender_id = int(request.session["user_id"])
    receiver_id = int(request.POST.get("receiver_id", "0") or 0)
    subject = (request.POST.get("subject") or "").strip()
    body = (request.POST.get("body") or "").strip()
    if not receiver_id or not body:
        return JsonResponse(
            {"ok": False, "error": "receiver_id and body are required."},
            status=400,
        )
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        thread_id = None
        if subject:
            cur.execute(
                """
                INSERT INTO message_threads (subject, created_by)
                VALUES (%s, %s)
                """,
                (subject, sender_id),
            )
            thread_id = cur.lastrowid
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (thread_id, sender_id, receiver_id, body)
            VALUES (%s, %s, %s, %s)
            """,
            (thread_id, sender_id, receiver_id, body),
        )
        message_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'message', %s)
            """,
            (receiver_id, f"New message from user {sender_id}."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": SEND_MESSAGES,
            "message_id": message_id,
        }
    )


@require_permission(REQUEST_APPOINTMENT)
@require_http_methods(["POST"])
def request_appointment_view(request):
    user_id = int(request.session["user_id"])
    slot_id_raw = (request.POST.get("slot_id") or "").strip()
    reason = (request.POST.get("reason") or "").strip()
    appointment_type = (request.POST.get("appointment_type") or "new").strip()
    if not slot_id_raw:
        return JsonResponse({"ok": False, "error": "slot_id is required."}, status=400)
    try:
        slot_id = int(slot_id_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "slot_id must be an integer."}, status=400)
    if appointment_type not in {"new", "follow_up", "visit"}:
        appointment_type = "new"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
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
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO appointments (
                patient_id, provider_id, slot_id, appointment_type,
                start_time, end_time, status, reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'scheduled', %s)
            """,
            (
                user_id,
                int(slot["provider_id"]),
                int(slot["id"]),
                appointment_type,
                slot["start_time"],
                slot["end_time"],
                reason or None,
            ),
        )
        appointment_id = cur.lastrowid
        cur.execute(
            """
            UPDATE availability_slots
            SET status = 'booked'
            WHERE id = %s
            """,
            (slot_id,),
        )
        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'appointment', %s)
            """,
            (int(slot["provider_id"]), f"Appointment #{appointment_id} has been scheduled."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": REQUEST_APPOINTMENT,
            "appointment_id": appointment_id,
            "slot_id": slot_id,
            "status": "scheduled",
        }
    )

@require_permission(CANCEL_APPOINTMENT)
@require_http_methods(["POST"])
def cancel_appointment_view(request, appointment_id: int):
    user_id = int(request.session["user_id"])
    role_id = int(request.session.get("role_id", 0))
    cancel_note = (request.POST.get("cancel_note") or "").strip()
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, patient_id, provider_id, slot_id, status
            FROM appointments
            WHERE id = %s
            LIMIT 1
            """,
            (appointment_id,),
        )
        appointment = cur.fetchone()
        if not appointment:
            return JsonResponse({"ok": False, "error": "Appointment not found."}, status=404)
        if role_id == 1 and int(appointment["patient_id"]) != user_id:
            return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
        if appointment["status"] == "cancelled":
            return JsonResponse({"ok": False, "error": "Appointment already cancelled."}, status=400)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE appointments
            SET status = 'cancelled', cancel_note = %s
            WHERE id = %s
            """,
            (cancel_note or None, appointment_id),
        )
        cur.execute(
            """
            UPDATE availability_slots
            SET status = 'open'
            WHERE id = %s
            """,
            (int(appointment["slot_id"]),),
        )
        notify_user_id = int(appointment["provider_id"]) if role_id == 1 else int(appointment["patient_id"])
        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'appointment', %s)
            """,
            (notify_user_id, f"Appointment #{appointment_id} was cancelled."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
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


@require_login
def appointments_filtered_view(request):
    user_id = int(request.session["user_id"])
    role_id = int(request.session.get("role_id", 0))
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()
    sql = """
        SELECT id, patient_id, provider_id, appointment_type, start_time, end_time, status, reason
        FROM appointments
        WHERE
    """
    params = []
    if role_id == 1:
        sql += " patient_id = %s "
        params.append(user_id)
    else:
        sql += " provider_id = %s "
        params.append(user_id)
    if date_from:
        sql += " AND DATE(start_time) >= %s "
        params.append(date_from)
    if date_to:
        sql += " AND DATE(start_time) <= %s "
        params.append(date_to)
    sql += " ORDER BY start_time DESC "
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return render(
        request,
        "portal/appointments.html",
        {
            "username": request.session.get("display_name") or request.session.get("email"),
            "appointments": rows,
        },
    )

@require_login
def appointment_detail_view(request, appointment_id: int):
    user_id = int(request.session["user_id"])
    role_id = int(request.session.get("role_id", 0))
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, patient_id, provider_id, slot_id, parent_appointment_id,
                   appointment_type, start_time, end_time, status, reason,
                   cancel_note, created_at
            FROM appointments
            WHERE id = %s
            LIMIT 1
            """,
            (appointment_id,),
        )
        appointment = cur.fetchone()
    finally:
        if conn:
            conn.close()
    if not appointment:
        return JsonResponse({"ok": False, "error": "Appointment not found."}, status=404)
    if role_id == 1 and int(appointment["patient_id"]) != user_id:
        return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
    if role_id != 1 and int(appointment["provider_id"]) != user_id and int(appointment["patient_id"]) != user_id:
        return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
    return render(
        request,
        "portal/appointment_detail.html",
        {
            "username": request.session.get("display_name") or request.session.get("email"),
            "appointment": appointment,
        },
    )


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
    user_id = int(request.session["user_id"])
    note = (request.POST.get("note") or "").strip()
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, patient_id, medication_name
            FROM prescriptions
            WHERE id = %s
            LIMIT 1
            """,
            (prescription_id,),
        )
        prescription = cur.fetchone()
        if not prescription:
            return JsonResponse({"ok": False, "error": "Prescription not found."}, status=404)
        if int(prescription["patient_id"]) != user_id:
            return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO refill_requests (prescription_id, requested_by, note, status)
            VALUES (%s, %s, %s, 'requested')
            """,
            (prescription_id, user_id, note or None),
        )
        refill_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'medication', %s)
            """,
            (user_id, f"Refill request #{refill_id} submitted for prescription #{prescription_id}."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": REQUEST_REFILL,
            "prescription_id": prescription_id,
            "refill_id": refill_id,
        }
    )


@require_permission(APPROVE_REFILL)
@require_http_methods(["POST"])
def approve_refill_view(request, refill_id: int):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT rr.id, rr.status, rr.requested_by, rr.prescription_id
            FROM refill_requests rr
            WHERE rr.id = %s
            LIMIT 1
            """,
            (refill_id,),
        )
        refill = cur.fetchone()
        if not refill:
            return JsonResponse({"ok": False, "error": "Refill request not found."}, status=404)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE refill_requests
            SET status = 'approved'
            WHERE id = %s
            """,
            (refill_id,),
        )
        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'medication', %s)
            """,
            (int(refill["requested_by"]), f"Refill request #{refill_id} was approved."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": APPROVE_REFILL,
            "refill_id": refill_id,
        }
    )


@require_permission(MANAGE_INSURANCE)
@require_http_methods(["POST"])
def manage_insurance_view(request, patient_id: int):
    user_id = int(request.session["user_id"])
    role_id = int(request.session.get("role_id", 0))
    if role_id == 1 and patient_id != user_id:
        return JsonResponse({"ok": False, "error": "Not allowed."}, status=403)
    payer_name = (request.POST.get("payer_name") or "").strip()
    member_id = (request.POST.get("member_id") or "").strip()
    plan_name = (request.POST.get("plan_name") or "").strip() or None
    group_number = (request.POST.get("group_number") or "").strip() or None
    relationship_to_patient = (request.POST.get("relationship_to_patient") or "self").strip()
    policyholder_name = (request.POST.get("policyholder_name") or "").strip() or None
    policyholder_dob = (request.POST.get("policyholder_dob") or "").strip() or None
    effective_start = (request.POST.get("effective_start") or "").strip() or None
    effective_end = (request.POST.get("effective_end") or "").strip() or None
    phone = (request.POST.get("phone") or "").strip() or None
    address = (request.POST.get("address") or "").strip() or None
    is_primary = 1 if (request.POST.get("is_primary") or "1").strip() in {"1", "true", "True", "yes"} else 0

    if not payer_name or not member_id:
        return JsonResponse(
            {"ok": False, "error": "payer_name and member_id are required."},
            status=400,
        )

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO insurance_policies (
                patient_id, payer_name, plan_name, member_id, group_number,
                relationship_to_patient, policyholder_name, policyholder_dob,
                effective_start, effective_end, phone, address, is_primary
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                payer_name,
                plan_name,
                member_id,
                group_number,
                relationship_to_patient,
                policyholder_name,
                policyholder_dob,
                effective_start,
                effective_end,
                phone,
                address,
                is_primary,
            ),
        )
        policy_id = cur.lastrowid
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": MANAGE_INSURANCE,
            "patient_id": patient_id,
            "policy_id": policy_id,
        }
    )


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
            SELECT patient_id, provider_id, reason
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
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO appointments (
                patient_id, provider_id, slot_id, parent_appointment_id,
                appointment_type, start_time, end_time, status, reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled', %s)
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
        new_appointment_id = cur.lastrowid
        cur.execute(
            """
            UPDATE availability_slots
            SET status = 'booked'
            WHERE id = %s
            """,
            (int(slot["id"]),),
        )
        cur.execute(
            """
            INSERT INTO notifications (user_id, category, message)
            VALUES (%s, 'appointment', %s)
            """,
            (int(parent["provider_id"]), f"New follow-up appointment request #{new_appointment_id}."),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()
    return JsonResponse(
        {
            "ok": True,
            "permission": REQUEST_APPOINTMENT,
            "appointment_id": new_appointment_id,
            "parent_appointment_id": appointment_id,
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
        messages.success(request, "Health information saved.")
        return redirect("portal:health_info")
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

    return render(
        request,
        "portal/health_info.html",
        {
            "username": username,
            "health_info": row,
        },
    )


@require_login
@require_http_methods(["GET", "POST"])
def contact_info_view(request):
    user_id = int(request.session["user_id"])
    username = request.session.get("display_name") or request.session.get("email")
    if request.method == "POST":
        phone = (request.POST.get("phone") or "").strip() or None
        address1 = (request.POST.get("address1") or "").strip() or None
        address2 = (request.POST.get("address2") or "").strip() or None
        city = (request.POST.get("city") or "").strip() or None
        state = (request.POST.get("state") or "").strip() or None
        zip_code = (request.POST.get("zip") or "").strip() or None
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE users
                SET phone = %s
                WHERE id = %s
                """,
                (phone, user_id),
            )
            cur.execute(
                """
                INSERT INTO profiles (user_id, address1, address2, city, state, zip)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    address1 = VALUES(address1),
                    address2 = VALUES(address2),
                    city = VALUES(city),
                    state = VALUES(state),
                    zip = VALUES(zip)
                """,
                (user_id, address1, address2, city, state, zip_code),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()
        messages.success(request, "Contact information updated.")
        return redirect("portal:contact_info")
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT u.phone, p.address1, p.address2, p.city, p.state, p.zip
            FROM users u
            LEFT JOIN profiles p ON p.user_id = u.id
            WHERE u.id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone() or {}
    finally:
        if conn:
            conn.close()

    return render(
        request,
        "portal/contact_info.html",
        {
            "username": username,
            "contact_info": row,
        },
    )


@require_login
@require_http_methods(["GET", "POST"])
def security_questions_view(request):
    user_id = int(request.session["user_id"])
    username = request.session.get("display_name") or request.session.get("email")
    if request.method == "POST":
        question_id = (request.POST.get("question_id") or "").strip()
        answer = (request.POST.get("answer") or "").strip()
        if not question_id or not answer:
            messages.error(request, "Question and answer are required.")
            return redirect("portal:security_questions")
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
        messages.success(request, "Security question saved.")
        return redirect("portal:security_questions")
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
    return render(
        request,
        "portal/security_questions.html",
        {
            "username": username,
            "questions": questions,
            "saved_questions": saved_questions,
        },
    )


@require_login
def accessibility_view(request):
    return render(
        request,
        "portal/accessibility.html",
        {
            "username": request.session.get("display_name") or request.session.get("email"),
            "guidelines": [
                "You MUST KINDLY use clear, readable text on every single forum.",
                "Messages with images must also have some short sentence description.",
                "Use strong color contrast for text and controls.",
                "Keep yoiur layouts consistent, dont clutter your screens, don't go crazy like vishu",
            ],
        },
    )


@require_login
def maintenance_notices_view(request):
    return render(
        request,
        "portal/maintenance_notices.html",
        {
            "username": request.session.get("display_name") or request.session.get("email"),
            "notices": [
                {
                    "title": "Planned Maintenance Window",
                    "detail": "Routine maintenance may occur during low-traffic evening hours.",
                },
                {
                    "title": "Messaging Delays",
                    "detail": "Portal messaging responses may occasionally be delayed during maintenance.",
                },
            ],
        },
    )


@require_login
def notification_preferences_view(request):
    return render(
        request,
        "portal/notification_preferences.html",
        {
            "username": request.session.get("display_name") or request.session.get("email"),
            "preferences": {
                "email_notifications": True,
                "sms_notifications": False,
                "appointment_updates": True,
                "prescription_updates": True,
                "system_notices": True,
            },
        },
    )
