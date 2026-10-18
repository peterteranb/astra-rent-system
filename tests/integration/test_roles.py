"""Pruebas de INTEGRACION de los roles: cada pagina del personal solo la abre su rol."""
import pytest
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from tests.conftest import DEMO_PASSWORD
from tests.helpers import foto_de_la_base

pytestmark = pytest.mark.django_db

PAGINA_DEL_OPERADOR = "/staff/reservations/"


@pytest.mark.parametrize(
    "usuario, destino",
    [
        ("op01", "/staff/reservations/"),
        ("mt01", "/maintenance/"),
        ("c01", "/"),
    ],
    ids=["operador", "mantenimiento", "cliente"],
)
def test_al_iniciar_sesion_cada_rol_llega_a_su_pagina(request, client, usuario, destino):
    """Requisito: A3 (#44), cada rol empieza en su pagina.
    Caso:      cada uno de los 4 usuarios inicia sesion con su usuario y clave.
    Esperado:  pasa por /home/ y termina en su pagina (200), con la sesion abierta para el.
    """
    # Preparar
    persona = request.getfixturevalue(usuario)

    # Ejecutar
    respuesta = client.post(
        "/login/", {"username": usuario, "password": DEMO_PASSWORD}, follow=True
    )

    # Comprobar
    assert respuesta.redirect_chain[0] == ("/home/", 302)
    assertRedirects(respuesta, destino)
    assert client.session["_auth_user_id"] == str(persona.pk)


def test_el_operador_abre_su_pagina_y_ve_sus_enlaces(client, op01):
    """Requisito: A3 (#44), cada pagina del personal la usa su rol.
    Caso:      OP-01, del grupo operador, abre /staff/reservations/.
    Esperado:  200 con la pagina "Reservas por entregar" y sus enlaces Reservas y Devoluciones.
    """
    # Preparar
    client.force_login(op01)

    # Ejecutar
    respuesta = client.get(PAGINA_DEL_OPERADOR)

    # Comprobar
    assert respuesta.status_code == 200
    assertTemplateUsed(respuesta, "rentals/staff_reservations.html")
    assertContains(respuesta, 'href="/staff/reservations/"')
    assertContains(respuesta, 'href="/staff/returns/"')


def test_un_cliente_recibe_403_en_la_pagina_del_operador(client, c01):
    """Requisito: A3 (#44), sin el rol la pagina se niega con 403 (no se redirige al login).
    Caso:      C-01, un cliente con sesion, abre /staff/reservations/.
    Esperado:  403 y la base queda igual.
    """
    # Preparar
    client.force_login(c01)
    antes = foto_de_la_base()

    # Ejecutar
    respuesta = client.get(PAGINA_DEL_OPERADOR)

    # Comprobar
    assert respuesta.status_code == 403
    assert foto_de_la_base() == antes


def test_sin_sesion_la_pagina_del_operador_lleva_al_login(client, db):
    """Requisito: A3 (#44), quien no inicio sesion primero entra.
    Caso:      un visitante sin sesion abre /staff/reservations/.
    Esperado:  redirige a /login/?next=/staff/reservations/ y la base queda igual.
    """
    # Preparar
    antes = foto_de_la_base()

    # Ejecutar
    respuesta = client.get(PAGINA_DEL_OPERADOR)

    # Comprobar
    assertRedirects(respuesta, f"/login/?next={PAGINA_DEL_OPERADOR}")
    assert foto_de_la_base() == antes
