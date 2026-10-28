"""Casos de uso de pagos: el QR simulado de la renta en línea (CU-04)."""
from django.db import transaction
from django.utils import timezone

from .errors import RentalStateError
from .formatting import rental_state_message
from .models import Rental
from .statuses import PaymentMethod, RentalStatus


def pay_with_qr(rental, approved) -> Rental:
    """Guarda el resultado del QR simulado de una reserva y la devuelve (ENT-66, ENT-67).

    approved es la respuesta de la pasarela: así una pasarela real se conecta sin
    tocar la renta (ENT-48). Si no se aprueba, la reserva sigue hecha con el pago
    pendiente. Lanza RentalStateError si la renta no es una reserva sin pagar.
    """
    with transaction.atomic():
        # Bloquea la fila: dos clics en el QR no guardan dos pagos.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_pay_online(locked_rental, now)
        if approved:
            locked_rental.paid_at = now
            locked_rental.payment_method = PaymentMethod.QR
            locked_rental.save(update_fields=["paid_at", "payment_method"])
        return locked_rental


def check_can_pay_online(rental, now):
    """Lanza RentalStateError si en now la renta ya está pagada o ya no está «Reservada»."""
    if rental.is_paid:
        raise RentalStateError(f"La renta de {rental.equipment.inventory_id} ya está pagada.")
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))
