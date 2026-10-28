"""Pantallas del admin de Django: el administrador gestiona equipos, rentas, deudas e historial (ENT-13, ENT-50)."""
from django.contrib import admin, messages
from django.utils import timezone

from .errors import OperationRejectedError
from .forms import EquipmentAdminForm
from .history import change_status
from .inventory import log_equipment_registered
from .models import Debt, Equipment, Rental, StatusChange
from .payments import pay_debt
from .renting import cancel_rental
from .statuses import EquipmentStatus

admin.site.site_header = "SergioCorp · Administración"
admin.site.site_title = "SergioCorp"
admin.site.index_title = "Panel del administrador"

# Con unos 1000 equipos (ENT-02), cada lista del admin se lee de 50 en 50.
ADMIN_PAGE_SIZE = 50


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """Equipos: el admin los registra con las reglas del modelo (CU-12) y corrige su estado con acciones (CU-13)."""

    form = EquipmentAdminForm
    list_display = ["inventory_id", "name", "serial_number", "value", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["inventory_id", "serial_number", "name"]
    list_per_page = ADMIN_PAGE_SIZE
    # El estado solo cambia con las acciones, que pasan por history.change_status
    # y dejan cada cambio en el historial (ENT-34).
    readonly_fields = ["status", "created_at"]
    actions = ["mark_available", "send_to_repair", "retire"]

    def save_model(self, request, obj, form, change):
        """Guarda el equipo y, si es nuevo, escribe EQUIPMENT_REGISTERED como la página de registro."""
        super().save_model(request, obj, form, change)
        if not change:
            log_equipment_registered(obj, request.user)

    @admin.action(description="Marcar disponible")
    def mark_available(self, request, queryset):
        """Deja disponibles los equipos marcados y guarda cada cambio."""
        self.change_selected(request, queryset, EquipmentStatus.AVAILABLE)

    @admin.action(description="Mandar a reparación")
    def send_to_repair(self, request, queryset):
        """Manda a reparación los equipos marcados y guarda cada cambio."""
        self.change_selected(request, queryset, EquipmentStatus.IN_REPAIR)

    @admin.action(description="Dar de baja")
    def retire(self, request, queryset):
        """Da de baja los equipos marcados y guarda cada cambio."""
        self.change_selected(request, queryset, EquipmentStatus.RETIRED)

    def change_selected(self, request, queryset, new_status):
        """Cambia cada equipo marcado y avisa cuántos cambiaron y cuáles no.

        Es una corrección: no crea deudas ni cancela reservas (ENT-75).
        """
        changed = 0
        skipped = []
        for equipment in queryset:
            try:
                change_status(equipment, new_status, request.user)
            except OperationRejectedError:
                skipped.append(equipment.inventory_id)
            else:
                changed += 1
        self.message_user(request, f"Equipos actualizados: {changed}.")
        if skipped:
            self.message_user(
                request,
                f"No se cambiaron: {', '.join(skipped)}.",
                level=messages.WARNING,
            )


class SituationFilter(admin.SimpleListFilter):
    """Filtra las rentas por su situación calculada; el panel del responsable enlaza aquí (CU-15)."""

    title = "situación"
    parameter_name = "situacion"

    def lookups(self, request, model_admin):
        """Opciones del filtro."""
        return [
            ("activas", "Rentadas a tiempo"),
            ("vencidas", "Vencidas"),
            ("hoy", "Reservas de hoy"),
            ("pago_pendiente", "Reservas con pago pendiente"),
        ]

    def queryset(self, request, queryset):
        """Aplica la opción elegida con las mismas consultas del panel."""
        situations = {
            "activas": queryset.active_at,
            "vencidas": queryset.overdue_at,
            "hoy": queryset.reserved_for_today_at,
            "pago_pendiente": queryset.pending_payment_at,
        }
        situation = situations.get(self.value())
        return situation(timezone.now()) if situation else queryset


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """Lista de rentas que el admin solo consulta y cancela (CU-07)."""

    list_display = [
        "equipment",
        "client",
        "start_datetime",
        "end_datetime",
        "rental_total",
        "payment",
        "rental_status",
        "registered_by",
    ]
    list_select_related = ["equipment", "client", "registered_by"]
    search_fields = [
        "equipment__inventory_id",
        "client__first_name",
        "client__last_name",
        "client__username",
    ]
    list_filter = [SituationFilter, "payment_method"]
    list_per_page = ADMIN_PAGE_SIZE
    date_hierarchy = "start_datetime"
    actions = ["cancel_reservations"]

    @admin.display(description="Estado")
    def rental_status(self, rental):
        """Muestra el estado calculado de la renta (no se guarda en la base)."""
        return rental.status.label

    @admin.display(description="Total (Bs)")
    def rental_total(self, rental):
        """Muestra días × precio por día (ENT-72)."""
        return rental.total_price

    @admin.display(description="Pago")
    def payment(self, rental):
        """Muestra si está pagada y cómo."""
        return rental.payment_label

    # Una renta creada o editada a mano se saltaría el cruce de fechas (RF-01) y una
    # borrada perdería historia: el admin solo las lista y las cancela (RF-21).
    def has_add_permission(self, request):
        """No deja crear rentas a mano."""
        return False

    def has_change_permission(self, request, obj=None):
        """No deja editar rentas a mano."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No deja borrar rentas."""
        return False

    @admin.action(description="Cancelar reserva")
    def cancel_reservations(self, request, queryset):
        """Cancela las reservas marcadas y avisa cuántas se cancelaron y cuáles no."""
        cancelled = 0
        skipped = []
        for rental in queryset:
            try:
                cancel_rental(rental, request.user)
            except OperationRejectedError:
                skipped.append(f"#{rental.pk} {rental}")
            else:
                cancelled += 1
        self.message_user(request, f"Reservas canceladas: {cancelled}.")
        if skipped:
            self.message_user(
                request,
                f"No se cancelaron: {', '.join(skipped)}.",
                level=messages.WARNING,
            )


class PaidFilter(admin.SimpleListFilter):
    """Filtra las deudas pagadas o pendientes; el panel del responsable enlaza a las pendientes."""

    title = "pagada"
    parameter_name = "pagada"

    def lookups(self, request, model_admin):
        """Opciones del filtro."""
        return [("no", "Pendientes"), ("si", "Pagadas")]

    def queryset(self, request, queryset):
        """Aplica la opción elegida."""
        if self.value() == "no":
            return queryset.filter(paid_at__isnull=True)
        if self.value() == "si":
            return queryset.filter(paid_at__isnull=False)
        return queryset


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    """Deudas: las crea el sistema; el admin las consulta y registra su pago (ENT-76)."""

    list_display = [
        "client",
        "equipment",
        "reason",
        "amount",
        "created_at",
        "paid_at",
        "paid_received_by",
    ]
    list_select_related = ["rental__client", "rental__equipment", "paid_received_by"]
    list_filter = [PaidFilter, "reason"]
    search_fields = [
        "rental__client__username",
        "rental__client__first_name",
        "rental__client__last_name",
        "rental__equipment__inventory_id",
    ]
    list_per_page = ADMIN_PAGE_SIZE
    ordering = ["-created_at"]
    actions = ["register_payments"]

    @admin.display(description="Cliente")
    def client(self, debt):
        """Muestra el cliente de la renta que generó la deuda."""
        return debt.rental.client

    @admin.display(description="Equipo")
    def equipment(self, debt):
        """Muestra el equipo de la renta que generó la deuda."""
        return debt.rental.equipment.inventory_id

    # Una deuda creada, editada o borrada a mano cambiaría lo que debe un cliente
    # sin una devolución o una revisión que lo explique.
    def has_add_permission(self, request):
        """No deja crear deudas a mano."""
        return False

    def has_change_permission(self, request, obj=None):
        """No deja editar deudas."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No deja borrar deudas."""
        return False

    @admin.action(description="Registrar pago")
    def register_payments(self, request, queryset):
        """Registra el pago de las deudas marcadas y avisa cuántas se cobraron y cuáles ya estaban pagadas."""
        paid = 0
        skipped = []
        for debt in queryset:
            try:
                pay_debt(debt, request.user)
            except OperationRejectedError:
                skipped.append(f"#{debt.pk}")
            else:
                paid += 1
        self.message_user(request, f"Deudas cobradas: {paid}.")
        if skipped:
            self.message_user(
                request, f"Ya estaban pagadas: {', '.join(skipped)}.", level=messages.WARNING
            )


@admin.register(StatusChange)
class StatusChangeAdmin(admin.ModelAdmin):
    """Historial de cambios de estado, solo para leer (CU-14, ENT-34)."""

    list_display = ["equipment", "old_status", "new_status", "changed_by", "changed_at", "comment"]
    list_filter = ["new_status", "changed_by"]
    search_fields = ["equipment__inventory_id", "comment"]
    list_select_related = ["equipment", "changed_by"]
    list_per_page = ADMIN_PAGE_SIZE
    ordering = ["-changed_at"]
    readonly_fields = ["equipment", "old_status", "new_status", "changed_by", "changed_at", "comment"]

    # El historial es evidencia: el admin no lo crea, ni lo edita, ni lo borra.
    def has_add_permission(self, request):
        """No deja crear filas de historial a mano."""
        return False

    def has_change_permission(self, request, obj=None):
        """No deja editar filas de historial."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No deja borrar filas de historial."""
        return False
