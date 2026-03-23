# portal/urls.py
from django.urls import path
from . import views

app_name = "portal"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("settings/", views.settings_view, name="settings"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("messages/", views.messages_view, name="messages"),
    path("data-control/", views.data_control_view, name="data_control"),
    path("profile/", views.profile_view, name="profile"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:notif_id>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("notifications/read-all/", views.notifications_mark_all_read, name="notifications_mark_all_read"),
    path("patient/profile/<int:patient_id>/", views.view_patient_profile_view, name="view_patient_profile"),
    path("patient/file/<int:patient_id>/", views.access_patient_file_view, name="access_patient_file"),
    path("appointments/request/", views.request_appointment_view, name="request_appointment"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment_view, name="cancel_appointment"),
    path("appointments/filter/", views.appointments_filtered_view, name="appointments_filtered"),
    path("appointments/<int:appointment_id>/", views.appointment_detail_view, name="appointment_detail"),
    path("health-info/", views.health_info_view, name="health_info"),
    path("contact-info/", views.contact_info_view, name="contact_info"),
    path("security-questions/", views.security_questions_view, name="security_questions"),
    path("accessibility/", views.accessibility_view, name="accessibility"),
    path("maintenance-notices/", views.maintenance_notices_view, name="maintenance_notices"),
    path("notification-preferences/", views.notification_preferences_view, name="notification_preferences"),
    path(
        "appointments/<int:appointment_id>/follow-up/",
        views.schedule_follow_up_appointment_view,
        name="schedule_follow_up_appointment",
    ),
    path("messages/send/", views.send_messages_view, name="send_messages"),
    path(
        "prescriptions/<int:prescription_id>/refill-request/",
        views.request_refill_view,
        name="request_refill",
    ),
    path("refills/<int:refill_id>/approve/", views.approve_refill_view, name="approve_refill"),
    path(
        "patient/insurance/<int:patient_id>/manage/",
        views.manage_insurance_view,
        name="manage_insurance",
    ),

    # Remove Later.
    path("admin/login-history/", views.login_history_view, name="view_login_history"),
    path("admin/users/", views.manage_users_view, name="manage_users"),
    path("admin/sessions/", views.manage_sessions_view, name="manage_sessions"),
    path("admin/roles/", views.manage_roles_permissions_view, name="manage_roles_permissions"),
]
