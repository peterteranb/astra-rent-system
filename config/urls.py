"""Root URL configuration: admin, login/logout and the rental pages."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("rentals.urls")),
]
