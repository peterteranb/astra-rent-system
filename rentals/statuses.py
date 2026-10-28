"""Estados y opciones que comparten los modelos y las reglas: equipo, renta, devolución, pago y deuda."""
from django.db import models


class EquipmentStatus(models.TextChoices):
    """Estados físicos del equipo (ENT-33, ENT-61); «reservado» y «rentado» salen de las fechas de cada renta."""

    AVAILABLE = "available", "Disponible"
    IN_REVIEW = "in_review", "En revisión"
    IN_REPAIR = "in_repair", "En reparación"
    RETIRED = "retired", "Baja"


class RentalStatus(models.TextChoices):
    """Estados de la renta: se calculan desde sus momentos y nunca se guardan (RF-08)."""

    RESERVED = "reserved", "Reservada"
    RENTED = "rented", "Rentada"
    NOT_PICKED_UP = "not_picked_up", "No recogida"
    RETURNED = "returned", "Devuelta"
    CANCELLED = "cancelled", "Cancelada"


class ReturnResult(models.TextChoices):
    """Cómo llegó una devolución comparada con el día de vencimiento (ENT-73)."""

    ON_TIME = "on_time", "A tiempo"
    TOLERANCE = "tolerance", "En tolerancia, sin cobro"
    LATE = "late", "Con atraso"


class PaymentMethod(models.TextChoices):
    """Cómo se pagó una renta: QR en línea (ENT-66) o efectivo en la tienda (ENT-70)."""

    QR = "qr", "QR"
    CASH = "cash", "Efectivo"


class DebtReason(models.TextChoices):
    """Por qué se debe: atraso en la devolución (ENT-73), reparación o baja del equipo (ENT-74)."""

    LATE_RETURN = "late_return", "Devolución tardía"
    REPAIR = "repair", "Reparación"
    RETIRED = "retired", "Baja del equipo"
