"""Pruebas de INTEGRACION de la pagina de mantenimiento (/maintenance/)."""
import pytest
from pytest_django.asserts import assertContains, assertRedirects

from rentals.models import StatusChange
from rentals.review import review_equipment
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base

pytestmark = pytest.mark.django_db


def test_mt01_deja_disponible_a_eq03_y_vuelve_al_catalogo(client, mt01, eq03_in_review):
    """Requisito: D2 (#62), mantenimiento guarda su decision desde /maintenance/.
    Caso:      MT-01 abre la pagina, ve EQ-03 "en revision" y lo deja "disponible" con un comentario.
    Esperado:  vuelve a la lista con el mensaje de exito, EQ-03 ya no aparece ahi,
               el historial guarda a MT-01 y el comentario, y EQ-03 vuelve al catalogo.
    """
    # Preparar
    client.force_login(mt01)

    # Ejecutar
    pagina = client.get("/maintenance/")
    respuesta = client.post(
        "/maintenance/EQ-03/",
        {"status": EquipmentStatus.AVAILABLE.value, "comment": "Revisada, sin daños"},
        follow=True,
    )

    # Comprobar: la respuesta
    assert list(pagina.context["equipment_list"]) == [eq03_in_review]
    assertContains(pagina, 'action="/maintenance/EQ-03/"')
    assertRedirects(respuesta, "/maintenance/")
    assertContains(respuesta, "EQ-03 ahora está «Disponible».")
    assert list(respuesta.context["equipment_list"]) == []

    # Comprobar: lo guardado
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.AVAILABLE
    cambio = StatusChange.objects.get()
    assert (cambio.changed_by, cambio.comment) == (mt01, "Revisada, sin daños")
    catalogo = client.get("/").context["catalog_entries"]
    assert [entrada.equipment for entrada in catalogo] == [eq03_in_review]


def test_una_baja_no_se_puede_cambiar_desde_la_pagina(client, mt01, eq03_in_review):
    """Requisito: D2 (#62) y ENT-34, la baja es definitiva.
    Caso:      EQ-03 esta de baja y MT-01 envia el formulario para dejarlo "disponible".
    Esperado:  vuelve a la lista con la causa del rechazo y la base queda igual.
    """
    # Preparar
    review_equipment(eq03_in_review, mt01, EquipmentStatus.RETIRED, "No enciende")
    antes = foto_de_la_base()
    client.force_login(mt01)

    # Ejecutar
    respuesta = client.post(
        "/maintenance/EQ-03/", {"status": EquipmentStatus.AVAILABLE.value}, follow=True
    )

    # Comprobar: la respuesta
    assertRedirects(respuesta, "/maintenance/")
    assertContains(
        respuesta, "El equipo EQ-03 está dado de baja; su estado ya no puede cambiar."
    )

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes


@pytest.mark.parametrize("usuario", ["c01", "op01"], ids=["cliente", "operador"])
def test_cliente_y_operador_reciben_403_en_mantenimiento(
    request, client, eq03_in_review, usuario
):
    """Requisito: D2 (#62), la pagina de mantenimiento es solo del rol mantenimiento.
    Caso:      un cliente y un operador abren /maintenance/ y envian el formulario de EQ-03.
    Esperado:  403 en los dos casos y la base queda igual.
    """
    # Preparar
    client.force_login(request.getfixturevalue(usuario))
    antes = foto_de_la_base()

    # Ejecutar
    pagina = client.get("/maintenance/")
    respuesta = client.post("/maintenance/EQ-03/", {"status": EquipmentStatus.AVAILABLE.value})

    # Comprobar
    assert pagina.status_code == 403
    assert respuesta.status_code == 403
    assert foto_de_la_base() == antes