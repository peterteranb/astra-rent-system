"""Prueba rentals/roles.py: role_required() en las páginas del personal (RF-19), la página de
inicio de cada rol y accounts/forms.py: LoginForm, el mensaje de un login incorrecto (RC-04)."""
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


def test_el_administrador_entra_al_panel_del_responsable(client, ad01):
    # ad01 inicia sesión -> llega al panel del responsable
    client.force_login(ad01)
    respuesta = client.get("/home/", follow=True)
    assertContains(respuesta, "Panel del responsable")


def test_el_operador_no_abre_el_panel_del_responsable(client, op01):
    # op01 abre el panel del responsable -> 403
    client.force_login(op01)
    assert client.get("/manager/").status_code == 403


def test_un_usuario_bloqueado_no_puede_iniciar_sesion(client, cl01):
    # El admin desactivó a cl01 -> no puede entrar (ENT-79)
    cl01.is_active = False
    cl01.save()
    respuesta = client.post("/login/", {"username": "cl01", "password": "Demo1234"})
    assertContains(respuesta, "Usuario o contraseña incorrectos.")
