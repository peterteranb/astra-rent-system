"""URLs raíz: el admin, el login y el cierre de sesión, y las páginas de renta."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("rentals.urls")),
]
