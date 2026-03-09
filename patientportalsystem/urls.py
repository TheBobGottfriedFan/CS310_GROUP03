from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # DJANGO ADMIN
    path("admin/", admin.site.urls),
    # ROUTES HANDLED INSIDE PORTAL
    path("", include("portal.urls")),
]
