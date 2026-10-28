"""Correos al cliente: bienvenida, renta confirmada, reserva modificada por la tienda, renta cancelada y deuda creada (ENT-85).

Se mandan cuando la transacción se confirma, así nunca avisan algo que se deshizo.
Si el envío falla, la operación no se cae: el log escribe EMAIL_FAILED.
"""
import logging
import smtplib

from django.core.mail import send_mail
from django.db import transaction

from .events import log_event
from .formatting import local_text, money_text


def send_welcome(user):
    """Avisa al cliente que su cuenta ya está lista."""
    send_after_commit(
        user,
        "Bienvenido a SergioCorp",
        f"Hola {user.first_name}:\n\n"
        f"Tu cuenta {user.username} ya está lista. Ya puedes rentar mesas y sillas en línea.\n",
    )


def send_rental_confirmed(rental):
    """Confirma la renta al cliente, pagada o con el pago pendiente (ENT-67)."""
    if rental.is_paid:
        payment = f"{rental.payment_label}: {money_text(rental.total_price)}."
    else:
        payment = (
            f"Pago pendiente: paga {money_text(rental.total_price)} en la tienda al recoger el equipo."
        )
    send_after_commit(
        rental.client,
        f"Renta confirmada: {rental.equipment.inventory_id}",
        f"Hola {rental.client.first_name}:\n\n"
        f"Tu renta de {rental.equipment} está confirmada.\n"
        f"Recojo desde: {local_text(rental.start_datetime)}\n"
        f"Devolución hasta: {local_text(rental.end_datetime)}\n"
        f"{payment}\n",
    )


def send_rental_modified(rental):
    """Avisa al cliente las fechas nuevas de la reserva que cambió la tienda (ENT-95)."""
    send_after_commit(
        rental.client,
        f"Reserva modificada: {rental.equipment.inventory_id}",
        f"Hola {rental.client.first_name}:\n\n"
        f"La tienda cambió las fechas de tu reserva de {rental.equipment}.\n"
        f"Recojo desde: {local_text(rental.start_datetime)}\n"
        f"Devolución hasta: {local_text(rental.end_datetime)}\n",
    )


def send_rental_cancelled(rental, reason):
    """Avisa al cliente que su reserva se canceló y por qué (ENT-82: el dinero se devuelve en la tienda)."""
    send_after_commit(
        rental.client,
        f"Renta cancelada: {rental.equipment.inventory_id}",
        f"Hola {rental.client.first_name}:\n\n"
        f"Tu reserva de {rental.equipment} del {local_text(rental.start_datetime)} "
        f"al {local_text(rental.end_datetime)} fue cancelada.\n"
        f"Motivo: {reason}\n"
        "Si ya pagaste, la tienda te devolverá el dinero.\n",
    )


def send_debt_created(debt):
    """Avisa al cliente la deuda, su motivo y que no podrá rentar hasta pagarla (ENT-77)."""
    rental = debt.rental
    send_after_commit(
        rental.client,
        f"Tienes una deuda de {money_text(debt.amount)}",
        f"Hola {rental.client.first_name}:\n\n"
        f"Se registró una deuda de {money_text(debt.amount)} por "
        f"«{debt.get_reason_display()}» de tu renta de {rental.equipment}.\n"
        "Págala en la tienda; mientras tanto no podrás hacer nuevas rentas.\n",
    )


def send_after_commit(user, subject, body):
    """Manda el correo cuando la transacción se confirme; si se deshace, no se manda."""
    transaction.on_commit(lambda: send_safely(user, subject, body))


def send_safely(user, subject, body):
    """Manda el correo; si el servidor de correo falla, escribe EMAIL_FAILED y sigue."""
    try:
        send_mail(subject, f"{body}\nSergioCorp · Mesas y sillas para eventos", None, [user.email])
    except (smtplib.SMTPException, OSError) as error:
        log_event(
            "EMAIL_FAILED", logging.ERROR, to=user.username, subject=subject, error=type(error).__name__
        )
