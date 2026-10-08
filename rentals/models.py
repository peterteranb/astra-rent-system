"""Database models for equipment and rentals (PRE-CU-01)."""
from django.conf import settings
from django.db import models


class EquipmentStatus(models.TextChoices):
    """Equipment states agreed with the client (ENT-33)."""

    AVAILABLE = "available", "Disponible"
    RENTED = "rented", "Rentado"
    IN_REVIEW = "in_review", "En revisión"
    IN_REPAIR = "in_repair", "En reparación"
    RETIRED = "retired", "Baja"


class Equipment(models.Model):
    """One physical unit of the inventory (ENT-09), e.g. a single table."""

    # The system identifies a unit by its inventory number (Sesión 04).
    inventory_id = models.CharField(max_length=20, unique=True)
    serial_number = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.AVAILABLE,
    )

    class Meta:
        ordering = ["inventory_id"]

    def __str__(self):
        return f"{self.inventory_id} - {self.description}"


class Rental(models.Model):
    """A confirmed rental of one unit for one period.

    There is no status field: a rental is confirmed the moment it is
    saved (ENT-16), and a rejected request is never saved.
    """

    # PROTECT: deleting a user or a unit must not silently erase rental
    # history (P01 asks to keep history, see Sesión 04).
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rentals",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="rentals",
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    class Meta:
        ordering = ["start_datetime"]
        constraints = [
            # Last line of defence: the database itself refuses a period
            # that ends before it starts, even if the service is bypassed.
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="rental_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.equipment.inventory_id} -> {self.client.username}"
