ffrom django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portal.urls")),  # send site root to portal app
]
