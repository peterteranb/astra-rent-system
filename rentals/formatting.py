"""Textos para el usuario que comparten varios casos de uso: fechas en hora de La Paz y el estado de una renta."""
from django.utils import timezone

from . import rules
from .statuses import RentalStatus


def local_text(moment):
    """Escribe un momento como «dd/mm/aaaa hh:mm» en hora de La Paz."""
    return f"{timezone.localtime(moment):%d/%m/%Y %H:%M}"


def rental_state_message(rental, status):
    """Dice por qué la renta ya no está «Reservada», con el momento en que dejó de estarlo."""
    inventory_id = rental.equipment.inventory_id
    if status == RentalStatus.CANCELLED:
        return f"La renta de {inventory_id} ya fue cancelada el {local_text(rental.cancelled_at)}."
    if status == RentalStatus.RETURNED:
        return f"La renta de {inventory_id} ya fue devuelta el {local_text(rental.returned_at)}."
    if status == RentalStatus.RENTED:
        return f"La renta de {inventory_id} ya fue entregada el {local_text(rental.picked_up_at)}."
    return f"La reserva de {inventory_id} venció a las {rules.PICKUP_DEADLINE:%H:%M}."
