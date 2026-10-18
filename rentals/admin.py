"""Admin screens: the superuser manages equipment and rentals here (ENT-13)."""
from django.contrib import admin, messages

from .errors import OperationRejectedError
from .models import Equipment, Rental
from .renting import cancel_rental

admin.site.site_header = "SergioCorp · Administración"
admin.site.site_title = "SergioCorp"
admin.site.index_title = "Panel del administrador"

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["inventory_id", "description", "serial_number", "status"]
    list_filter = ["status"]
    search_fields = ["inventory_id", "serial_number", "description"]


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