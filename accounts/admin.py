"""Pantallas del admin de Django para los usuarios y los roles (ENT-50, ENT-79)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Q, Sum

from rentals.services.events import log_event
from rentals.use_cases.renting import cancel_reservations_of_deactivated

from .forms import UserChangeAdminForm, UserCreationAdminForm
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Lista de roles; los crea la migración de datos."""

    list_display = ["code", "name", "description"]
    search_fields = ["code", "name"]

    def has_delete_permission(self, request, obj=None):
        """No deja borrar roles: cada usuario tiene uno (ENT-97: nunca se borra nada)."""
        return False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Usuarios con su rol; el admin bloquea a uno quitándole «Activo» y nunca lo borra (ENT-79, ENT-97)."""

    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
    list_display = [
        "username", "first_name", "last_name", "email", "phone", "role", "is_active", "pending_debt",
    ]
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

    def get_queryset(self, request):
        """Agrega a cada usuario la suma de sus deudas sin pagar, en la misma consulta (ENT-76)."""
        pending = Q(rentals__debts__paid_at__isnull=True)
        return super().get_queryset(request).annotate(
            pending_debt_total=Sum("rentals__debts__amount", filter=pending)
        )

    def has_delete_permission(self, request, obj=None):
        """No deja borrar usuarios: se desactivan y su historia queda (ENT-97)."""
        return False

    def save_model(self, request, obj, form, change):
        """Guarda el usuario y, si cambió «Activo», escribe en el log quién lo bloqueó o lo desbloqueó (ENT-79).

        Al desactivarlo se cancelan sus reservas todavía no recogidas (D-27).
        """
        super().save_model(request, obj, form, change)
        if not (change and "is_active" in form.changed_data):
            return
        event = "ACCOUNT_REACTIVATED" if obj.is_active else "ACCOUNT_DEACTIVATED"
        log_event(event, user=obj.username, by=request.user.username)
        if not obj.is_active:
            cancel_reservations_of_deactivated(obj, request.user)

    @admin.display(description="Deuda pendiente (Bs)", ordering="pending_debt_total")
    def pending_debt(self, user):
        """Muestra lo que debe el usuario; se calcula, no se guarda."""
        return user.pending_debt_total or 0
