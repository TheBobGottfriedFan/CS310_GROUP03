# to prevent a loop with rbac and authentication_service

from __future__ import annotations

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


ALL_PERMISSIONS = (
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

