"""Prueba que el operador crea la cuenta sin conocer la contraseña y que el cliente la crea con el enlace
de Django, al registrarse en la tienda o con «Olvidé mi contraseña» (CU-02, CU-17, ENT-102)."""
import re
import smtplib
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from pytest_django.asserts import assertContains, assertRedirects

TIENDA = {
    "first_name": "Lucía",
    "last_name": "Quispe",
    "email": "lucia.quispe@correo.com",
    "phone": "71234567",
    "username": "cl03",
}


def enlace_del_correo(correo):
    """Devuelve la ruta del enlace para crear la contraseña que trae el correo."""
    return re.search(r"http://testserver(/reset/\S+/)", correo.body).group(1)


def test_el_operador_crea_la_cuenta_sin_contrasena_y_el_cliente_recibe_el_enlace(client, op01, caplog):
    # op01 registra a Lucía sin escribir contraseña -> la cuenta no tiene contraseña y Lucía recibe «Crea tu contraseña»
    client.force_login(op01)
    client.post("/staff/clients/new/", TIENDA)
    lucia = get_user_model().objects.get(username="cl03")
    [correo] = mail.outbox
    # Comprueba que la cuenta nace sin contraseña utilizable
    assert lucia.has_usable_password() is False
    # Comprueba el correo con el enlace de Django
    assert (correo.to, correo.subject, "/reset/" in correo.body) == (
        ["lucia.quispe@correo.com"], "Crea tu contraseña de SergioCorp", True
    )
    # Comprueba la línea del log con el canal y quién la creó
    assert caplog.messages[-1] == (
        'ACCOUNT_CREATED user=cl03 "Lucía Quispe" email=lucia.quispe@correo.com role=cliente channel=store by=op01'
    )


def test_si_el_correo_falla_el_operador_ve_que_use_olvide_mi_contrasena(client, op01, caplog):
    # El servidor de correo no responde al registrar a Lucía -> la cuenta queda, el log dice EMAIL_FAILED y el operador ve qué hacer
    client.force_login(op01)
    sin_conexion = smtplib.SMTPException("sin conexión")
    with mock.patch("rentals.services.notifications.send_mail", side_effect=sin_conexion):
        respuesta = client.post("/staff/clients/new/", TIENDA, follow=True)
    # Comprueba el aviso al operador
    assertContains(
        respuesta,
        "La cuenta se creó, pero no se pudo enviar el correo. "
        "Pide al cliente que use &quot;Olvidé mi contraseña&quot; con su correo.",
    )
    # Comprueba que la cuenta quedó creada y el log del fallo
    assert get_user_model().objects.filter(username="cl03").exists() is True
    assert caplog.messages[-1] == 'EMAIL_FAILED to=cl03 subject="Crea tu contraseña de SergioCorp" error=SMTPException'


def test_el_cliente_de_la_tienda_crea_su_contrasena_con_el_enlace_y_entra(client, op01, caplog):
    # Lucía abre el enlace del correo y escribe su contraseña dos veces -> la guarda y ya puede iniciar sesión
    client.force_login(op01)
    client.post("/staff/clients/new/", TIENDA)
    client.logout()
    formulario = client.get(enlace_del_correo(mail.outbox[0]), follow=True)
    guardada = client.post(
        formulario.redirect_chain[-1][0], {"new_password1": "Montaña2026", "new_password2": "Montaña2026"}
    )
    # Comprueba que llegó a «Contraseña guardada»
    assertRedirects(guardada, "/reset/done/")
    # Comprueba que la contraseña sirve para entrar y el log lo dice
    assert client.login(username="cl03", password="Montaña2026") is True
    assert caplog.messages[-1] == 'PASSWORD_CHANGED user=cl03 "Lucía Quispe" channel=reset by=cl03'


def test_olvide_mi_contrasena_manda_el_enlace_y_escribe_el_log(client, cl01, caplog):
    # cl01 pide «Olvidé mi contraseña» con su correo -> recibe el enlace y el log dice el correo y la cuenta
    respuesta = client.post("/password-reset/", {"email": "cl01@correo.com"})
    [correo] = mail.outbox
    # Comprueba que va a «Revisa tu correo» y que el correo trae el enlace
    assertRedirects(respuesta, "/password-reset/sent/")
    assert (correo.to, "/reset/" in correo.body) == (["cl01@correo.com"], True)
    # Comprueba la línea del log
    assert caplog.messages == ["PASSWORD_RESET_REQUESTED email=cl01@correo.com users=cl01 by=web"]


@pytest.mark.parametrize(("correo", "activa"), [("nadie@correo.com", True), ("cl01@correo.com", False)])
def test_olvide_mi_contrasena_sin_una_cuenta_activa_no_manda_nada(client, cl01, caplog, correo, activa):
    # Se pide el enlace para un correo de nadie o de cl01 desactivada (ENT-79) -> la misma página y ningún correo
    cl01.is_active = activa
    cl01.save()
    respuesta = client.post("/password-reset/", {"email": correo})
    # Comprueba que la página no dice si la cuenta existe
    assertRedirects(respuesta, "/password-reset/sent/")
    # Comprueba que no salió ningún correo y que el log no encontró cuentas
    assert mail.outbox == []
    assert caplog.messages == [f"PASSWORD_RESET_REQUESTED email={correo} users=- by=web"]
