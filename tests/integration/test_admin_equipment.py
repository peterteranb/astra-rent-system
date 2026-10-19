"""Pruebas de INTEGRACION de las acciones de estado del admin de equipos."""
import pytest
from pytest_django.asserts import assertContains

from rentals.models import Equipment, StatusChange
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base

pytestmark = pytest.mark.django_db

LISTA = "/admin/rentals/equipment/"


def aplicar(client, accion, *equipos):
    """Envia una accion del admin de equipos para las unidades dadas."""
    return client.post(
        LISTA,
        {"action": accion, "_selected_action": [e.pk for e in equipos]},
        follow=True,
    )


def test_mandar_a_reparacion_deja_una_fila_de_historial_con_el_admin(client, admin, eq01):
    """Requisito: D5 (#NN) y ENT-34, el admin cambia estados y siempre queda anotado.
    Caso:      el admin selecciona EQ-01 y aplica «Mandar a reparación».
    Esperado:  EQ-01 queda "en reparación" y hay UNA fila de historial con el admin como autor.
    """
    # Preparar
    client.force_login(admin)

    # Ejecutar
    respuesta = aplicar(client, "send_to_repair", eq01)

    # Comprobar: la respuesta
    assertContains(respuesta, "Equipos actualizados: 1.")

    # Comprobar: lo guardado
    eq01.refresh_from_db()
    assert eq01.status == EquipmentStatus.IN_REPAIR
    cambio = StatusChange.objects.get()
    assert (cambio.equipment, cambio.changed_by) == (eq01, admin)
    assert (cambio.old_status, cambio.new_status) == (
        EquipmentStatus.AVAILABLE,
        EquipmentStatus.IN_REPAIR,
    )


def test_marcar_disponible_a_un_equipo_que_ya_lo_esta_no_deja_historial(client, admin, eq01):
    """Requisito: D5 (#NN), el historial solo guarda cambios reales.
    Caso:      el admin aplica «Marcar disponible» a EQ-01, que ya esta disponible.
    Esperado:  informa que no lo cambio y no se guarda ninguna fila de historial.
    """
    # Preparar
    antes = foto_de_la_base()
    client.force_login(admin)

    # Ejecutar
    respuesta = aplicar(client, "mark_available", eq01)

    # Comprobar
    assertContains(respuesta, "Equipos actualizados: 0.")
    assertContains(respuesta, "No se cambiaron: EQ-01.")
    assert foto_de_la_base() == antes


def test_marcar_disponible_a_un_equipo_de_baja_no_cambia_nada(client, admin, eq01):
    """Requisito: D5 (#NN) y ENT-34, la baja es definitiva.
    Caso:      EQ-01 esta de baja y el admin aplica «Marcar disponible».
    Esperado:  informa que no lo cambio; el equipo y el historial quedan igual.
    """
    # Preparar
    Equipment.objects.filter(pk=eq01.pk).update(status=EquipmentStatus.RETIRED)
    antes = foto_de_la_base()
    client.force_login(admin)

    # Ejecutar
    respuesta = aplicar(client, "mark_available", eq01)

    # Comprobar
    assertContains(respuesta, "No se cambiaron: EQ-01.")
    assert foto_de_la_base() == antes