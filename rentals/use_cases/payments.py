"""Pago con el QR simulado de una renta en línea (CU-04): el cliente presiona «pago exitoso» o «pago fallido»."""
from django.db import transaction
from django.utils import timezone

from ..errors import RentalStateError
from ..models import Rental
from ..services.events import log_event, logs_rejection, rental_context
from ..services.formatting import rental_state_message
from ..services.notifications import send_rental_confirmed
from ..statuses import PaymentMethod, RentalStatus


def online_rentals_of(client):
    """Devuelve las rentas que el cliente hizo en línea: solo esas se pagan con el QR (CU-04)."""
    return Rental.objects.filter(client=client, registered_by__isnull=True)


def attempted_payment(rental, approved):
    """La renta que el cliente quiso pagar con el QR, para el log del rechazo."""
    return rental_context(rental, rental.client.username)


@logs_rejection("PAYMENT_REJECTED", attempted_payment)
def pay_with_qr(rental, approved) -> Rental:
    """Guarda el resultado del QR simulado de una reserva y la devuelve (ENT-66, ENT-67).

    approved es la respuesta de la pasarela: así una pasarela real se conecta sin tocar la renta (ENT-48).
    Si no se aprueba, la reserva sigue hecha con el pago pendiente.
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
    event = "PAYMENT_APPROVED" if approved else "PAYMENT_FAILED"
    log_event(event, **rental_context(locked_rental, locked_rental.client.username))
    send_rental_confirmed(locked_rental)
    return locked_rental


def check_can_pay_online(rental, now):
    """Lanza RentalStateError si en now la renta ya está pagada o ya no está «Reservada»."""
    if rental.is_paid:
        raise RentalStateError(f"La renta de {rental.equipment.inventory_id} ya está pagada.")
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))
