"""Tablas de la base: equipos, rentas, deudas e historial de estados."""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from . import rules
from .statuses import DebtReason, EquipmentStatus, PaymentMethod, RentalStatus


class Equipment(models.Model):
    """Una unidad física del inventario, por ejemplo una sola mesa (ENT-09, ENT-83)."""

    inventory_id = models.CharField(
        verbose_name="Código",
        max_length=9,
        unique=True,
        validators=[
            RegexValidator(
                settings.INVENTORY_ID_FORMAT,
                "El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001.",
            )
        ],
        error_messages={
            "unique": "Ya existe un equipo con este código.",
            "blank": "Falta el campo Código.",
        },
    )
    serial_number = models.CharField(
        verbose_name="Número de serie",
        max_length=50,
        unique=True,
        error_messages={
            "unique": "Ya existe un equipo con este número de serie.",
            "blank": "Falta el campo Número de serie.",
        },
    )
    name = models.CharField(
        verbose_name="Nombre", max_length=100, error_messages={"blank": "Falta el campo Nombre."}
    )
    # Precio de compra: de aquí salen el precio por día y los cargos por daño (ENT-71, ENT-74).
    value = models.DecimalField(
        verbose_name="Valor (Bs)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"), "El valor debe ser mayor que 0.")],
        error_messages={"null": "Falta el campo Valor."},
    )
    status = models.CharField(
        verbose_name="Estado",
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.AVAILABLE,
    )
    created_at = models.DateTimeField(verbose_name="Registrado el", auto_now_add=True)

    class Meta:
        ordering = ["inventory_id"]
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__gt=0), name="equipment_value_positive"
            ),
        ]

    def __str__(self):
        """Muestra el código y el nombre, por ejemplo «MES-00001 · Mesa plegable 1,80 m»."""
        return f"{self.inventory_id} · {self.name}"

    @property
    def daily_price(self):
        """Devuelve lo que costaría hoy un día de renta de este equipo (ENT-71)."""
        return rules.daily_price_for(self.value)


class RentalQuerySet(models.QuerySet):
    """Filtra las rentas por su estado calculado; repite en SQL las reglas de Rental.status_at."""

    def reserved_at(self, now):
        """Rentas «Reservadas» en now: sin cancelar, recoger ni devolver, y con su día de inicio sin cerrar (ENT-69)."""
        return self.filter(
            cancelled_at__isnull=True,
            picked_up_at__isnull=True,
            returned_at__isnull=True,
            start_datetime__gte=rules.start_of_day(timezone.localtime(now)),
        )

    def rented(self):
        """Rentas «Rentadas»: el cliente se llevó el equipo y todavía no lo devolvió."""
        return self.filter(
            cancelled_at__isnull=True, returned_at__isnull=True, picked_up_at__isnull=False
        )

    def occupying_at(self, now):
        """Rentas que en now ocupan las fechas de su equipo: las «Reservadas» y las «Rentadas»."""
        return self.reserved_at(now) | self.rented()

    def active_at(self, now):
        """Rentas «Rentadas» que en now todavía están a tiempo."""
        return self.rented().filter(end_datetime__gte=now)

    def overdue_at(self, now):
        """Rentas «Rentadas» cuya devolución ya pasó en now: el equipo no volvió (PRE-06)."""
        return self.rented().filter(end_datetime__lt=now)

    def reserved_for_today_at(self, now):
        """Reservas cuyo recojo es el día de now."""
        today = rules.start_of_day(timezone.localtime(now))
        return self.reserved_at(now).filter(start_datetime__lt=today + timedelta(days=1))

    def pending_payment_at(self, now):
        """Reservas con el pago pendiente: se cobran al recoger o se cancelan (ENT-68)."""
        return self.reserved_at(now).filter(paid_at__isnull=True)


class Rental(models.Model):
    """Una renta confirmada de un equipo para un periodo.

    Se confirma al guardarse (ENT-16) y un pedido rechazado nunca se guarda.
    Su estado no se guarda: status_at() lo calcula desde sus momentos (RF-08).
    """

    # PROTECT: borrar un usuario o un equipo no puede borrar en silencio la
    # historia de sus rentas.
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rentals",
        verbose_name="Cliente",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="rentals",
        verbose_name="Equipo",
    )
    start_datetime = models.DateTimeField(verbose_name="Recojo desde")
    end_datetime = models.DateTimeField(verbose_name="Devolución hasta")
    # ENT-71: el precio de ese momento; si el valor del equipo cambia, esta renta no cambia.
    daily_price = models.DecimalField(
        verbose_name="Precio por día (Bs)", max_digits=10, decimal_places=2
    )
    paid_at = models.DateTimeField(verbose_name="Pagado el", null=True, blank=True)
    payment_method = models.CharField(
        verbose_name="Forma de pago", max_length=10, choices=PaymentMethod.choices, blank=True
    )
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
    created_at = models.DateTimeField(verbose_name="Creada el", auto_now_add=True)

    objects = RentalQuerySet.as_manager()

    class Meta:
        ordering = ["start_datetime"]
        verbose_name = "Renta"
        verbose_name_plural = "Rentas"
        constraints = [
            # Última defensa: la base misma rechaza un periodo que termina antes
            # de empezar, aunque alguien se salte el caso de uso.
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F("start_datetime")),
                name="rental_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(daily_price__gte=0), name="rental_daily_price_not_negative"
            ),
        ]

    def __str__(self):
        """Muestra el equipo y el cliente, por ejemplo «MES-00001 -> cl01»."""
        return f"{self.equipment.inventory_id} -> {self.client.username}"

    def status_at(self, now):
        """Devuelve el estado de la renta en el momento now (RF-08)."""
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
        recogidas dejan las fechas libres para otros (ENT-55, ENT-69).
        """
        return self.status_at(now) in (RentalStatus.RESERVED, RentalStatus.RENTED)

    @property
    def status(self):
        """Devuelve el estado de la renta en este momento."""
        return self.status_at(timezone.now())

    @property
    def rental_days(self):
        """Devuelve los días que se cobran, contados en hora de La Paz (ENT-72)."""
        return rules.rental_days(
            timezone.localtime(self.start_datetime), timezone.localtime(self.end_datetime)
        )

    @property
    def total_price(self):
        """Devuelve el total de la renta: días × precio por día; se calcula, no se guarda (ENT-72)."""
        return self.rental_days * self.daily_price

    @property
    def is_paid(self):
        """Devuelve True si la renta ya se pagó, con QR o en efectivo."""
        return self.paid_at is not None

    @property
    def payment_label(self):
        """Dice solo si está «Pagado» o con «Pago pendiente»; la forma de pago se ve en el detalle (ENT-104)."""
        return "Pagado" if self.is_paid else "Pago pendiente"

    @property
    def client_can_change(self):
        """Devuelve True si el cliente todavía puede cancelar o modificar esta reserva en línea (ENT-80)."""
        now = timezone.now()
        return self.status_at(now) == RentalStatus.RESERVED and rules.can_client_change(
            self.start_datetime, now
        )

    @property
    def due_date(self):
        """Devuelve el día de vencimiento en hora de La Paz: los límites de la devolución son horas de ese día."""
        return timezone.localtime(self.end_datetime).date()

    @property
    def return_result(self):
        """Devuelve cómo llegó la devolución, o None mientras el equipo no vuelve (RF-09)."""
        if self.returned_at is None:
            return None
        return rules.classify_return(timezone.localtime(self.returned_at), self.due_date)

    @property
    def late_days(self):
        """Devuelve los días de atraso de la devolución, o 0 mientras el equipo no vuelve (ENT-73)."""
        if self.returned_at is None:
            return 0
        return rules.late_days(timezone.localtime(self.returned_at), self.due_date)

    @property
    def late_charge(self):
        """Devuelve lo que se cobra por el atraso: días de atraso × precio por día (ENT-73)."""
        return self.late_days * self.daily_price


class DebtQuerySet(models.QuerySet):
    """Consultas de deudas que usan el cliente, el operador y el panel."""

    def pending(self):
        """Deudas que todavía no se pagaron."""
        return self.filter(paid_at__isnull=True)

    def total(self) -> Decimal:
        """Suma los montos de estas deudas; se calcula, no se guarda (ENT-76)."""
        return self.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


class Debt(models.Model):
    """Un cargo de una renta por atraso, reparación o baja; se paga una por una (ENT-76)."""

    rental = models.ForeignKey(
        Rental, on_delete=models.PROTECT, related_name="debts", verbose_name="Renta"
    )
    reason = models.CharField(verbose_name="Motivo", max_length=20, choices=DebtReason.choices)
    # El cargo de ese momento: no cambia si después cambia el valor del equipo.
    amount = models.DecimalField(verbose_name="Monto (Bs)", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(verbose_name="Creada el", auto_now_add=True)
    paid_at = models.DateTimeField(verbose_name="Pagada el", null=True, blank=True)
    paid_received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_debt_payments",
        verbose_name="Cobrada por",
    )

    objects = DebtQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Deuda"
        verbose_name_plural = "Deudas"
        constraints = [
            # Una renta no se cobra dos veces por el mismo motivo.
            models.UniqueConstraint(
                fields=["rental", "reason"], name="debt_one_per_rental_and_reason"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0), name="debt_amount_not_negative"
            ),
        ]

    def __str__(self):
        """Muestra el cliente, el motivo y el monto, por ejemplo «cl02 · Devolución tardía · 40.00 Bs»."""
        return f"{self.rental.client.username} · {self.get_reason_display()} · {self.amount} Bs"

    @property
    def is_paid(self):
        """Devuelve True si la deuda ya se pagó."""
        return self.paid_at is not None


class StatusChange(models.Model):
    """Un cambio de estado de un equipo: quién, cuándo, de cuál a cuál y por qué (ENT-34)."""

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="status_changes",
        verbose_name="Equipo",
    )
    old_status = models.CharField(
        verbose_name="Estado anterior", max_length=20, choices=EquipmentStatus.choices
    )
    new_status = models.CharField(
        verbose_name="Estado nuevo", max_length=20, choices=EquipmentStatus.choices
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="status_changes",
        verbose_name="Cambiado por",
    )
    changed_at = models.DateTimeField(verbose_name="Fecha", auto_now_add=True)
    comment = models.TextField(verbose_name="Comentario", blank=True)

    class Meta:
        ordering = ["changed_at"]
        verbose_name = "Cambio de estado"
        verbose_name_plural = "Cambios de estado"

    def __str__(self):
        """Muestra el equipo y el cambio, por ejemplo «MES-00001: in_review -> available»."""
        return f"{self.equipment.inventory_id}: {self.old_status} -> {self.new_status}"
