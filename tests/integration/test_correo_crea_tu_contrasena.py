"""Prueba accounts/registration.py: register_store_client() manda «Crea tu contraseña» después de guardar la
cuenta (ENT-102: el operador nunca conoce la contraseña del cliente)."""
import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode

from accounts.registration import SignUpData, register_store_client

LUCIA = SignUpData("Lucía", "Quispe", "lucia@correo.com", "71234567", "cl03")


def anotar_al_enviar(vistos):
    """Hace de send_mail: anota el cuerpo y si la cuenta del enlace ya existía en la base al salir el correo."""

    def enviar(asunto, cuerpo, *args, **kwargs):
        """Lee el uid del enlace y busca esa cuenta en ese momento."""
        uid = urlsafe_base64_decode(re.search(r"/reset/([^/]+)/", cuerpo).group(1)).decode()
        vistos.append((cuerpo, get_user_model().objects.filter(pk=uid, username="cl03").exists()))

    return enviar


def test_el_correo_sale_con_la_cuenta_ya_guardada_y_trae_el_usuario(op01):
    # op01 registra a Lucía -> cuando sale el correo, la cuenta del enlace ya existe y el cuerpo dice «cl03»
    vistos = []
    with mock.patch("rentals.services.notifications.send_mail", side_effect=anotar_al_enviar(vistos)):
        registro = register_store_client(LUCIA, op01, "http://testserver/")
    [(cuerpo, la_cuenta_existia)] = vistos
    # Comprueba que salió el correo y que, al salir, el enlace ya apuntaba a la cuenta guardada
    assert (registro.email_sent, la_cuenta_existia) == (True, True)
    # Comprueba que el correo nombra el usuario con el que va a entrar
    assert "La tienda creó tu cuenta cl03." in cuerpo
