"""States of an equipment unit and of a rental, shared by models and rules."""
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
