"""Pantallas del admin de Django: el superusuario gestiona equipos, rentas e historial (ENT-13, ENT-50)."""
from django.contrib import admin, messages

from .errors import OperationRejectedError
from .history import change_status
from .models import Equipment, Rental, StatusChange
from .renting import cancel_rental
from .statuses import EquipmentStatus

admin.site.site_header = "SergioCorp · Administración"
admin.site.site_title = "SergioCorp"
admin.site.index_title = "Panel del administrador"


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["inventory_id", "description", "serial_number", "status"]
    list_filter = ["status"]
    search_fields = ["inventory_id", "serial_number", "description"]
    # El estado solo cambia con las acciones, que pasan por history.change_status
    # y dejan cada cambio en el historial (ENT-34).
    readonly_fields = ["status"]
    actions = ["mark_available", "send_to_repair", "retire"]

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
        """Cambia cada equipo marcado y avisa cuántos cambiaron y cuáles no."""
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


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = [
        "equipment",
        "client",
        "start_datetime",
        "end_datetime",
        "rental_status",
        "picked_up_at",
        "returned_at",
        "registered_by",
    ]
    list_filter = ["equipment"]
    actions = ["cancel_reservations"]

    @admin.display(description="Estado")
    def rental_status(self, rental):
        """Muestra el estado calculado de la renta (no se guarda en la base)."""
        return rental.status.label

    # Una renta creada o editada a mano se saltaría el cruce de fechas (RF-01) y una
    # borrada perdería historia: el admin solo las lista y las cancela (RF-09).
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


@admin.register(StatusChange)
class StatusChangeAdmin(admin.ModelAdmin):
    list_display = ["unit", "from_status", "to_status", "author", "moment", "note"]
    list_filter = ["equipment"]
    list_select_related = ["equipment", "changed_by"]
    ordering = ["-changed_at"]

    @admin.display(description="Equipo", ordering="equipment")
    def unit(self, change):
        """Muestra el equipo que cambió de estado."""
        return change.equipment.inventory_id

    @admin.display(description="De")
    def from_status(self, change):
        """Muestra el estado antes del cambio."""
        return change.get_old_status_display()

    @admin.display(description="A")
    def to_status(self, change):
        """Muestra el estado después del cambio."""
        return change.get_new_status_display()

    @admin.display(description="Quién", ordering="changed_by")
    def author(self, change):
        """Muestra quién hizo el cambio."""
        return change.changed_by

    @admin.display(description="Cuándo", ordering="changed_at")
    def moment(self, change):
        """Muestra cuándo se hizo el cambio."""
        return change.changed_at

    @admin.display(description="Comentario")
    def note(self, change):
        """Muestra el comentario opcional del cambio."""
        return change.comment

    # El historial es evidencia (ENT-34): el admin solo lo lee.
    def has_add_permission(self, request):
        """No deja crear filas de historial a mano."""
        return False

    def has_change_permission(self, request, obj=None):
        """No deja editar filas de historial."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No deja borrar filas de historial."""
        return False
