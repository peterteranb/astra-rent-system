"""Prueba accounts/registration.py: register_store_client() manda «Crea tu contraseña» después de guardar la
cuenta y dice si salió; y que un cliente bloqueado no puede restablecer su contraseña (ENT-79, ENT-102)."""
import re
import smtplib
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.http import urlsafe_base64_decode
from pytest_django.asserts import assertRedirects

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


def test_si_el_envio_falla_la_cuenta_existe_y_el_caso_de_uso_lo_avisa(op01, caplog):
    # El servidor de correo no responde al registrar a Lucía -> email_sent es False, la cuenta queda y el log dice EMAIL_FAILED
    sin_conexion = smtplib.SMTPException("sin conexión")
    with mock.patch("rentals.services.notifications.send_mail", side_effect=sin_conexion):
        registro = register_store_client(LUCIA, op01, "http://testserver/")
    # Comprueba lo que recibe la vista para avisar al operador
    assert registro.email_sent is False
    # Comprueba que la cuenta quedó guardada y el log del fallo
    assert get_user_model().objects.filter(username="cl03").exists() is True
    assert caplog.messages[-1] == 'EMAIL_FAILED to=cl03 subject="Crea tu contraseña de SergioCorp" error=SMTPException'


def test_un_cliente_bloqueado_no_recibe_el_enlace_para_restablecer(client, cl01, caplog):
    # El admin desactivó a cl01 y alguien pide «Olvidé mi contraseña» con su correo -> la misma página y ningún correo
    cl01.is_active = False
    cl01.save()
    respuesta = client.post("/password-reset/", {"email": "cl01@correo.com"})
    # Comprueba que la página no dice nada distinto
    assertRedirects(respuesta, "/password-reset/sent/")
    # Comprueba que no salió ningún correo y que el log no encontró cuentas
    assert mail.outbox == []
    assert caplog.messages == ["PASSWORD_RESET_REQUESTED email=cl01@correo.com users=- by=web"]
