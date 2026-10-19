"""Database models for equipment and rentals (PRE-CU-01)."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from . import rules
from .statuses import EquipmentStatus, RentalStatus


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

    A rental is confirmed the moment it is saved (ENT-16), and a rejected
    request is never saved. Its status is not stored: status_at()
    calculates it from the pickup, return and cancellation moments.
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
    # The client may pick up the unit from this moment.
    start_datetime = models.DateTimeField()
    # The client must return the unit by this moment.
    end_datetime = models.DateTimeField()
    # When the client took the unit away; the operator registers it.
    picked_up_at = models.DateTimeField(verbose_name="Recogido el", null=True, blank=True)
    # Operator who handed the unit over to the client (client: "tiene que estar todo inventariado").
    handed_over_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="handed_over_rentals",
        verbose_name="Entregado por",
    )
    # When the client brought the unit back; the operator registers it.
    returned_at = models.DateTimeField(verbose_name="Devuelto el", null=True, blank=True)
    # Operator who received the unit back from the client.
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_rentals",
        verbose_name="Recibido por",
    )
    # When the rental was cancelled; the operator (or the admin) registers it.
    cancelled_at = models.DateTimeField(verbose_name="Cancelado el", null=True, blank=True)
    # Operator or admin who cancelled the rental; clients cannot cancel in the MVP.
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_rentals",
        verbose_name="Cancelado por",
    )
    # What the operator noticed when receiving the unit back.
    return_note = models.CharField(
        verbose_name="Observación de la devolución", max_length=200, blank=True
    )
    # Empty when the client registered the rental online.
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registered_rentals",
        verbose_name="Registrado por",
    )

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

    def status_at(self, now):
        """Return the status of the rental at the moment now."""
        if self.cancelled_at is not None:
            return RentalStatus.CANCELLED
        if self.returned_at is not None:
            return RentalStatus.RETURNED
        if self.picked_up_at is not None:
            return RentalStatus.RENTED
        start = timezone.localtime(self.start_datetime)
        if rules.is_pickup_expired(start, timezone.localtime(now)):
            return RentalStatus.NOT_PICKED_UP
        return RentalStatus.RESERVED

    @property
    def status(self):
        """Return the status of the rental right now."""
        return self.status_at(timezone.now())

    @property
    def return_result(self):
        """Return how the return arrived, or None while the unit is not back (C4)."""
        if self.returned_at is None:
            return None
        # Local time: the limits are La Paz clock times (09:00, 12:00).
        due_date = timezone.localtime(self.end_datetime).date()
        return rules.classify_return(timezone.localtime(self.returned_at), due_date)


class StatusChange(models.Model):
    """One change of state of a unit: who, when, from which state to which and why (ENT-34)."""

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="status_changes",
    )
    old_status = models.CharField(max_length=20, choices=EquipmentStatus.choices)
    new_status = models.CharField(max_length=20, choices=EquipmentStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="status_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.equipment.inventory_id}: {self.old_status} -> {self.new_status}"
