"""Prueba rentals/roles.py: role_required() en las páginas del personal (RF-11)
y accounts/forms.py: LoginForm, el mensaje de un login incorrecto (RC-01)."""
from pytest_django.asserts import assertContains, assertRedirects


def test_un_visitante_sin_sesion_va_al_login(client, db):
    # Alguien sin sesión abre «Reservas por entregar» -> va al login y vuelve ahí después
    respuesta = client.get("/staff/reservations/")
    assertRedirects(respuesta, "/login/?next=/staff/reservations/")


def test_un_cliente_recibe_403_en_una_pagina_del_operador(client, cl01):
    # cl01 es cliente y abre «Reservas por entregar» -> 403
    client.force_login(cl01)
    respuesta = client.get("/staff/reservations/")
    assert respuesta.status_code == 403


def test_un_login_incorrecto_muestra_el_mensaje(client, cl01):
    # cl01 escribe una contraseña equivocada -> ve «Usuario o contraseña incorrectos.»
    respuesta = client.post("/login/", {"username": "cl01", "password": "equivocada"})
    assertContains(respuesta, "Usuario o contraseña incorrectos.")
