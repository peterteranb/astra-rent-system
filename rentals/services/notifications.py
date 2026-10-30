"""Correos al cliente: bienvenida, crear la contraseña, renta confirmada, reserva modificada por la tienda, renta cancelada y deuda creada (ENT-85).

Se mandan cuando la transacción se confirma, así nunca avisan algo que se deshizo; los de las rentas y deudas,
en un hilo aparte para que la pantalla no espere al servidor de correo. Si el envío falla, la operación no se cae:
el log escribe EMAIL_FAILED.
"""
import logging
import smtplib
import threading
from urllib.parse import urljoin

from django.conf import settings
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
        payment = f"{rental.payment_label} ({rental.get_payment_method_display()}): {money_text(rental.total_price)}."
    else:
        payment = (
            f"Pago pendiente: paga {money_text(rental.total_price)} en la tienda al recoger el equipo."
        )
    send_in_background_after_commit(
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
    send_in_background_after_commit(
        rental.client,
        f"Reserva modificada: {rental.equipment.inventory_id}",
        f"Hola {rental.client.first_name}:\n\n"
        f"La tienda cambió las fechas de tu reserva de {rental.equipment}.\n"
        f"Recojo desde: {local_text(rental.start_datetime)}\n"
        f"Devolución hasta: {local_text(rental.end_datetime)}\n",
    )


def send_rental_cancelled(rental, reason):
    """Avisa al cliente que su reserva se canceló y por qué (ENT-82: el dinero se devuelve en la tienda)."""
    send_in_background_after_commit(
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
    send_in_background_after_commit(
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


def send_in_background_after_commit(user, subject, body):
    """Como send_after_commit, pero con EMAIL_IN_BACKGROUND el envío corre en otro hilo y la petición no lo espera."""
    transaction.on_commit(lambda: start_sending(user, subject, body))


def start_sending(user, subject, body):
    """Manda el correo en un hilo aparte si EMAIL_IN_BACKGROUND está activo; si no, en este mismo."""
    if not settings.EMAIL_IN_BACKGROUND:
        send_safely(user, subject, body)
        return
    # El hilo no toca la base: el asunto y el cuerpo ya están armados. daemon: no frena el apagado del servidor.
    threading.Thread(target=send_safely, args=(user, subject, body), daemon=True).start()


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
