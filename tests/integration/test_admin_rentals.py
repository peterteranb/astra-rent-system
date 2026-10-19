"""Pruebas de INTEGRACION del admin de rentas (/admin/rentals/rental/)."""
from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.asserts import assertContains

from rentals.models import Rental
from rentals.renting import create_rental
from rentals.statuses import RentalStatus
from tests.helpers import local_datetime

pytestmark = pytest.mark.django_db

LISTA = "/admin/rentals/rental/"


def reserva_de_c01(c01, eq01):
    """Reserva de EQ-01 para C-01: empieza a las 18:00 de manana y dura una noche."""
    dia = timezone.localdate() + timedelta(days=1)
    inicio = local_datetime(dia.year, dia.month, dia.day, 18)
    return create_rental(c01, eq01, inicio, inicio + timedelta(hours=15))


def cancelar(client, *rentas):
    """Envia la accion «Cancelar reserva» del admin para las rentas dadas."""
    return client.post(
        LISTA,
        {"action": "cancel_reservations", "_selected_action": [r.pk for r in rentas]},
        follow=True,
    )


def test_el_admin_cancela_una_reserva(client, admin, c01, eq01):
    """Requisito: D4 (#64), el administrador cancela reservas desde el admin.
    Caso:      el admin selecciona la reserva de EQ-01 y aplica «Cancelar reserva».
    Esperado:  la renta queda "Cancelada" por el admin y el admin informa que cancelo 1.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01)
    client.force_login(admin)

    # Ejecutar
    respuesta = cancelar(client, reserva)

    # Comprobar: la respuesta
    assertContains(respuesta, "Reservas canceladas: 1.")

    # Comprobar: lo guardado
    reserva.refresh_from_db()
    assert reserva.status == RentalStatus.CANCELLED
    assert reserva.cancelled_by == admin


def test_una_renta_ya_recogida_se_salta_y_se_informa(client, admin, c01, eq01):
    """Requisito: D4 (#64) y #49, solo se cancela una reserva que no se recogio.
    Caso:      el admin aplica «Cancelar reserva» a una renta de EQ-01 que ya se recogio.
    Esperado:  el admin informa que no la cancelo y la renta no cambia.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01)
    Rental.objects.filter(pk=reserva.pk).update(picked_up_at=timezone.now())
    client.force_login(admin)

    # Ejecutar
    respuesta = cancelar(client, reserva)

    # Comprobar: la respuesta
    assertContains(respuesta, "Reservas canceladas: 0.")
    assertContains(respuesta, "No se cancelaron: #")

    # Comprobar: lo guardado
    reserva.refresh_from_db()
    assert reserva.cancelled_at is None
    assert reserva.status == RentalStatus.RENTED


def test_el_admin_no_puede_agregar_ni_editar_rentas_a_mano(client, admin, c01, eq01):
    """Requisito: D4 (#64), crear o editar a mano se saltaria la regla de cruce.
    Caso:      el admin abre el formulario de agregar y envia el de editar una renta.
    Esperado:  403 en los dos casos y la renta no cambia.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01)
    client.force_login(admin)

    # Ejecutar
    agregar = client.get(f"{LISTA}add/")
    editar = client.post(f"{LISTA}{reserva.pk}/change/", {"return_note": "cambio a mano"})

    # Comprobar
    assert agregar.status_code == 403
    assert editar.status_code == 403
    reserva.refresh_from_db()
    assert reserva.return_note == ""