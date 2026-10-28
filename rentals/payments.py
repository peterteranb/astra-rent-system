"""Casos de uso de pagos: el QR simulado de la renta en línea (CU-04) y las deudas (CU-11).

Las deudas nacen en la devolución (atraso) y en la revisión (daño); aquí se crean, se suman y se cobran.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .errors import DebtStateError, RentalStateError
from .formatting import local_text, rental_state_message
from .models import Debt, Rental
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


def charge_debt(rental, reason, amount):
    """Crea la deuda de la renta por ese motivo y la devuelve; None si ya existía (ENT-76: una por motivo)."""
    debt, created = Debt.objects.get_or_create(
        rental=rental, reason=reason, defaults={"amount": amount}
    )
    return debt if created else None


def pending_debts():
    """Devuelve todas las deudas sin pagar con su cliente y su equipo, agrupadas por cliente."""
    return (
        Debt.objects.pending()
        .select_related("rental__client", "rental__equipment")
        .order_by("rental__client__username", "created_at")
    )


def pending_debts_of(client):
    """Devuelve las deudas sin pagar del cliente, la más antigua primero (CU-16)."""
    return pending_debts().filter(rental__client=client)


def debt_total_of(client) -> Decimal:
    """Suma las deudas sin pagar del cliente; se calcula, no se guarda (ENT-76)."""
    total = pending_debts_of(client).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0.00")


def pending_totals_by_client():
    """Devuelve el usuario, el nombre y la deuda total de cada cliente que debe, el que más debe primero."""
    return (
        Debt.objects.pending()
        .values("rental__client__username", "rental__client__first_name", "rental__client__last_name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def pay_debt(debt, staff_user) -> Debt:
    """Guarda que el cliente pagó esta deuda en la tienda y qué operador la cobró (ENT-76).

    Lanza DebtStateError si ya estaba pagada; entonces nada cambia.
    """
    with transaction.atomic():
        # Bloquea la fila: dos operadores no cobran la misma deuda dos veces.
        locked_debt = Debt.objects.select_for_update().get(pk=debt.pk)
        check_debt_is_pending(locked_debt)
        locked_debt.paid_at = timezone.now()
        locked_debt.paid_received_by = staff_user
        locked_debt.save(update_fields=["paid_at", "paid_received_by"])
        return locked_debt


def check_debt_is_pending(debt):
    """Lanza DebtStateError si la deuda ya se pagó."""
    if debt.is_paid:
        raise DebtStateError(f"Esta deuda ya se pagó el {local_text(debt.paid_at)}.")
