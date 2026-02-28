from __future__ import annotations
from functools import wraps
from typing import Callable, Any
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


ACCESS_PATIENT_FILE = "access_patient_file"
UPDATE_PATIENT_PROFILE = "update_patient_profile"
VIEW_LOGIN_HISTORY = "view_login_history"
VIEW_MESSAGES = "view_messages"
REQUEST_APPOINTMENT = "request_appointment"
VIEW_PATIENT_PROFILE = "view_patient_profile"
MANAGE_SESSIONS = "manage_sessions"
MANAGE_AVAILABILITY = "manage_availability"
MANAGE_APPOINTMENTS = "manage_appointments"
CANCEL_APPOINTMENT = "cancel_appointment"
CREATE_MEDICAL_RECORD = "create_medical_record"
UPDATE_MEDICAL_RECORD = "update_medical_record"
SEND_MESSAGES = "send_messages"
MANAGE_NOTIFICATIONS = "manage_notifications"
VIEW_PRESCRIPTIONS = "view_prescriptions"
MANAGE_PRESCRIPTIONS = "manage_prescriptions"
REQUEST_REFILL = "request_refill"
APPROVE_REFILL = "approve_refill"
VIEW_INSURANCE = "view_insurance"
MANAGE_INSURANCE = "manage_insurance"
MANAGE_USERS = "manage_users"
MANAGE_ROLES_PERMISSIONS = "manage_roles_permissions"



def require_login(view_func: Callable[..., Any]):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper
    
def require_any_permission(permission_names: Iterable[str], *, forbidden_message: str = "Permission denied."):
    perm_set = set(permission_names)
    def decorator(view_func: Callable[..., Any]):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.session.get("user_id"):
                return redirect("login")
            perms = set(request.session.get("permissions") or [])
            if perm_set.isdisjoint(perms):
                return HttpResponseForbidden(forbidden_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
