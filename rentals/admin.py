"""Admin screens: the superuser manages equipment and rentals here (ENT-13)."""
from django.contrib import admin

from .models import Equipment, Rental


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["inventory_id", "description", "serial_number", "status"]
    list_filter = ["status"]
    search_fields = ["inventory_id", "serial_number", "description"]


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ["equipment", "client", "start_datetime", "end_datetime"]
    list_filter = ["equipment"]
