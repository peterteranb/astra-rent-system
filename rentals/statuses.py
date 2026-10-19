"""States of an equipment unit, of a rental and of a return, shared by models and rules."""
from django.db import models


class EquipmentStatus(models.TextChoices):
    """Equipment states agreed with the client (ENT-33); reserved and rented come from rental dates."""

    AVAILABLE = "available", "Disponible"
    IN_REVIEW = "in_review", "En revisión"
    IN_REPAIR = "in_repair", "En reparación"
    RETIRED = "retired", "Baja"


class RentalStatus(models.TextChoices):
    """Rental states; they are calculated from the rental moments, never stored."""

    RESERVED = "reserved", "Reservada"
    RENTED = "rented", "Rentada"
    NOT_PICKED_UP = "not_picked_up", "No recogida"
    RETURNED = "returned", "Devuelta"
    CANCELLED = "cancelled", "Cancelada"


class ReturnResult(models.TextChoices):
    """How a return arrived compared with 09:00 of the return day (ENT-63, ENT-65)."""

    ON_TIME = "on_time", "A tiempo"
    WITH_FINE = "with_fine", "Con multa"
    EXTRA_DAY = "extra_day", "Se cobra un día más"
