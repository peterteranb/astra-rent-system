"""Admin screens: the superuser manages equipment and rentals here (ENT-13)."""
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
    # The status only changes with the actions below, which go through
    # history.change_status, so every change is recorded (ENT-34).
    readonly_fields = ["status"]
    actions = ["mark_available", "send_to_repair", "retire"]

    @admin.action(description="Marcar disponible")
    def mark_available(self, request, queryset):
        """Set the selected units to available and record each change."""
        self.change_selected(request, queryset, EquipmentStatus.AVAILABLE)

    @admin.action(description="Mandar a reparación")
    def send_to_repair(self, request, queryset):
        """Set the selected units to in repair and record each change."""
        self.change_selected(request, queryset, EquipmentStatus.IN_REPAIR)

    @admin.action(description="Dar de baja")
    def retire(self, request, queryset):
        """Retire the selected units and record each change."""
        self.change_selected(request, queryset, EquipmentStatus.RETIRED)

    def change_selected(self, request, queryset, new_status):
        """Change each selected unit and report how many changed and which were skipped."""
        changed = 0
        skipped = []
        for equipment in queryset:
            # A change to the same status would only add noise to the history.
            if equipment.status == new_status:
                skipped.append(equipment.inventory_id)
                continue
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
        """Show the calculated status of the rental (it is not stored)."""
        return rental.status.label

    # A rental made or edited by hand would skip the overlap rule (PRE-RF-01),
    # and a deleted one would erase history (RF-09), so the admin only lists
    # rentals and cancels them with the action below.
    def has_add_permission(self, request):
        """Do not let the admin create rentals by hand."""
        return False

    def has_change_permission(self, request, obj=None):
        """Do not let the admin edit rentals by hand."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Do not let the admin delete rentals."""
        return False

    @admin.action(description="Cancelar reserva")
    def cancel_reservations(self, request, queryset):
        """Cancel the selected reservations and report how many were cancelled and which were skipped."""
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
        """Show the unit whose status changed."""
        return change.equipment.inventory_id

    @admin.display(description="De")
    def from_status(self, change):
        """Show the status before the change."""
        return change.get_old_status_display()

    @admin.display(description="A")
    def to_status(self, change):
        """Show the status after the change."""
        return change.get_new_status_display()

    @admin.display(description="Quién", ordering="changed_by")
    def author(self, change):
        """Show who made the change."""
        return change.changed_by

    @admin.display(description="Cuándo", ordering="changed_at")
    def moment(self, change):
        """Show when the change was made."""
        return change.changed_at

    @admin.display(description="Comentario")
    def note(self, change):
        """Show the optional comment of the change."""
        return change.comment

    # The history is evidence (RF-09): the admin only reads it.
    def has_add_permission(self, request):
        """Do not let the admin create history rows by hand."""
        return False

    def has_change_permission(self, request, obj=None):
        """Do not let the admin edit history rows."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Do not let the admin delete history rows."""
        return False