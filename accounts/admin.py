"""Pantallas del admin de Django para los usuarios y los roles (ENT-50, ENT-79)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserChangeAdminForm, UserCreationAdminForm
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Lista de roles; los crea la migración de datos."""

    list_display = ["code", "name", "description"]
    search_fields = ["code", "name"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Usuarios con su rol; el admin bloquea a uno quitándole «Activo» (ENT-79)."""

    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
    list_display = ["username", "first_name", "last_name", "email", "phone", "role", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "phone"]
    list_select_related = ["role"]
    list_per_page = 50
    # is_staff e is_superuser no se muestran: User.save() los pone según el rol.
    fieldsets = [
        (None, {"fields": ["username", "password"]}),
        ("Datos personales", {"fields": ["first_name", "last_name", "email", "phone"]}),
        ("Rol y acceso", {"fields": ["role", "is_active"]}),
        ("Fechas", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "username", "first_name", "last_name", "email", "phone", "role",
                    "password1", "password2",
                ],
            },
        ),
    ]
    filter_horizontal = []
