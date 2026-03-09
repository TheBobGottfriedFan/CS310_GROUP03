from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    # HOME [root]
    path("", views.login_view, name="home"),
    # AUTHENTICATION
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # DASHBOARD
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # ACCOUNT PROFILE PAGES
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("data-control/", views.data_control_view, name="data_control"),
    # COMMUNICATION CHANNELS
    path("messages/", views.messages_view, name="messages"),
]
