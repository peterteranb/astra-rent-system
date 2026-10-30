"""Correos al cliente: bienvenida, crear la contraseña, renta confirmada, reserva modificada por la tienda, renta cancelada y deuda creada (ENT-85).

Se mandan cuando la transacción se confirma, así nunca avisan algo que se deshizo.
Si el envío falla, la operación no se cae: el log escribe EMAIL_FAILED.
"""
import logging
import smtplib
from urllib.parse import urljoin

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

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


def send_create_password(user, site_url) -> bool:
    """Manda al cliente creado en la tienda el enlace de Django para crear su contraseña; False si el correo falló (ENT-102).

    Sale en el momento y no al confirmar la transacción: el operador tiene que saber si llegó a salir.
    """
    return send_safely(
        user,
        "Crea tu contraseña de SergioCorp",
        f"Hola {user.first_name}:\n\n"
        f"La tienda creó tu cuenta {user.username}. Para entrar, crea tu contraseña en este enlace:\n"
        f"{create_password_link(user, site_url)}\n\n"
        "Si el enlace ya no sirve, usa «Olvidé mi contraseña» con tu correo.\n",
    )


def create_password_link(user, site_url):
    """Arma el enlace de restablecimiento de Django para user, con su token de un solo uso."""
    path = reverse(
        "password_reset_confirm",
        kwargs={"uidb64": urlsafe_base64_encode(force_bytes(user.pk)), "token": default_token_generator.make_token(user)},
    )
    return urljoin(site_url, path)


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


def send_safely(user, subject, body) -> bool:
    """Manda el correo y devuelve True; si el servidor de correo falla, escribe EMAIL_FAILED y devuelve False."""
    try:
        send_mail(subject, f"{body}\nSergioCorp · Mesas y sillas para eventos", None, [user.email])
    except (smtplib.SMTPException, OSError) as error:
        log_event(
            "EMAIL_FAILED", logging.ERROR, to=user.username, subject=subject, error=type(error).__name__
        )
        return False
    return True
