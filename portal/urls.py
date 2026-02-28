# portal/urls.py
from django.urls import path
from . import views

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

    # Remove Later.
    path("admin/login-history/", views.view_login_history_view, name="view_login_history"),
    path("admin/users/", views.manage_users_view, name="manage_users"),
    path("admin/roles/", views.manage_roles_permissions_view, name="manage_roles_permissions")
]
