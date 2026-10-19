"""Estados de un equipo, de una renta y de una devolución, que comparten los modelos y las reglas."""
from django.db import models


class EquipmentStatus(models.TextChoices):
    """Estados físicos del equipo (ENT-33, ENT-61); «reservado» y «rentado» salen de las fechas de cada renta."""

    AVAILABLE = "available", "Disponible"
    IN_REVIEW = "in_review", "En revisión"
    IN_REPAIR = "in_repair", "En reparación"
    RETIRED = "retired", "Baja"


class RentalStatus(models.TextChoices):
    """Estados de la renta: se calculan desde sus momentos y nunca se guardan (RF-07)."""

    RESERVED = "reserved", "Reservada"
    RENTED = "rented", "Rentada"
    NOT_PICKED_UP = "not_picked_up", "No recogida"
    RETURNED = "returned", "Devuelta"
    CANCELLED = "cancelled", "Cancelada"


class ReturnResult(models.TextChoices):
    """Cómo llegó una devolución comparada con las 09:00 del día de vencimiento (ENT-63)."""

    ON_TIME = "on_time", "A tiempo"
    WITH_FINE = "with_fine", "Con multa"
    EXTRA_DAY = "extra_day", "Se cobra un día más"
