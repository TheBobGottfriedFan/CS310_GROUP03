from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # All main application routes handled inside portal app
    path("", include("portal.urls")),
]