"""Tablas de la base: equipos, rentas e historial de estados."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from . import rules
from .statuses import EquipmentStatus, RentalStatus


class Equipment(models.Model):
    """Una unidad física del inventario, por ejemplo una sola mesa (ENT-09, RF-05)."""

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
        """Muestra el código y la descripción, por ejemplo «EQ-01 - Mesa plegable 1,80 m»."""
        return f"{self.inventory_id} - {self.description}"


class Rental(models.Model):
    """Una renta confirmada de un equipo para un periodo.

    Se confirma al guardarse (ENT-16) y un pedido rechazado nunca se guarda.
    Su estado no se guarda: status_at() lo calcula desde sus momentos (RF-07).
    """

    # PROTECT: borrar un usuario o un equipo no puede borrar en silencio la
    # historia de sus rentas.
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
    picked_up_at = models.DateTimeField(verbose_name="Recogido el", null=True, blank=True)
    # ENT-56: se registra quién entregó «porque tiene q estar todo inventariado».
    handed_over_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="handed_over_rentals",
        verbose_name="Entregado por",
    )
    returned_at = models.DateTimeField(verbose_name="Devuelto el", null=True, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_rentals",
        verbose_name="Recibido por",
    )
    cancelled_at = models.DateTimeField(verbose_name="Cancelado el", null=True, blank=True)
    # ENT-55: cancela el operador o el admin; el cliente no cancela en el MVP.
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_rentals",
        verbose_name="Cancelado por",
    )
    return_note = models.CharField(
        verbose_name="Observación de la devolución", max_length=200, blank=True
    )
    # Vacío cuando el cliente rentó en línea.
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
            # Última defensa: la base misma rechaza un periodo que termina antes
            # de empezar, aunque alguien se salte el caso de uso.
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="rental_end_after_start",
            ),
        ]

    def __str__(self):
        """Muestra el equipo y el cliente, por ejemplo «EQ-01 -> cl01»."""
        return f"{self.equipment.inventory_id} -> {self.client.username}"

    def status_at(self, now):
        """Devuelve el estado de la renta en el momento now (RF-07)."""
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

    def occupies_equipment_at(self, now):
        """Devuelve True si en now la renta todavía ocupa las fechas de su equipo.

        Solo las «Reservadas» y «Rentadas»: las canceladas, devueltas y no
        recogidas dejan las fechas libres para otros (ENT-55, ENT-59).
        """
        return self.status_at(now) in (RentalStatus.RESERVED, RentalStatus.RENTED)

    @property
    def status(self):
        """Devuelve el estado de la renta en este momento."""
        return self.status_at(timezone.now())

    @property
    def return_result(self):
        """Devuelve cómo llegó la devolución, o None mientras el equipo no vuelve (RF-02)."""
        if self.returned_at is None:
            return None
        # Hora local: los límites son horas de reloj de La Paz (09:00, 12:00).
        due_date = timezone.localtime(self.end_datetime).date()
        return rules.classify_return(timezone.localtime(self.returned_at), due_date)


class StatusChange(models.Model):
    """Un cambio de estado de un equipo: quién, cuándo, de cuál a cuál y por qué (ENT-34)."""

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
        """Muestra el equipo y el cambio, por ejemplo «EQ-01: in_review -> available»."""
        return f"{self.equipment.inventory_id}: {self.old_status} -> {self.new_status}"
