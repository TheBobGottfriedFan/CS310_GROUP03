from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    # Home (root)
    path("", views.login_view, name="home"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Main Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Account Pages
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("data-control/", views.data_control_view, name="data_control"),

    # Communication
    path("messages/", views.messages_view, name="messages"),
]