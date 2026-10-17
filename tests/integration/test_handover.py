"""Pruebas de INTEGRACION de la entrega del equipo al cliente (rentals/handover.py).

Las fechas son relativas a hoy: con las fechas fijas de los documentos
(09/10/2026) la reserva ya estaria vencida y no se podria entregar.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from rentals.errors import AlreadyPickedUpError, ReservationExpiredError
from rentals.handover import register_pickup
from rentals.renting import create_rental
from rentals.statuses import RentalStatus
from tests.helpers import foto_de_la_base, local_datetime

pytestmark = pytest.mark.django_db


def reserva_de_c01(c01, eq01, dias_desde_hoy):
    """Reserva de EQ-01 para C-01: empieza a las 18:00 de hoy + dias_desde_hoy y dura una noche."""
    dia = timezone.localdate() + timedelta(days=dias_desde_hoy)
    inicio = local_datetime(dia.year, dia.month, dia.day, 18)
    fin = inicio + timedelta(hours=15)
    return create_rental(c01, eq01, inicio, fin)


def test_el_operador_entrega_una_reserva_y_queda_rentada(op01, c01, eq01):
    """Requisito: C1 (#54), registrar el recojo guarda cuando y quien entrego.
    Caso:      OP-01 entrega a C-01 la reserva de EQ-01 que empieza manana.
    Esperado:  la renta queda "Rentada" con picked_up_at y handed_over_by; nada mas cambia.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01, dias_desde_hoy=1)
    rentas, equipos, historial = foto_de_la_base()
    antes_de_entregar = timezone.now()

    # Ejecutar
    renta = register_pickup(reserva, op01)

    # Comprobar: la respuesta
    assert renta.status == RentalStatus.RENTED

    # Comprobar: lo guardado (solo cambian los dos campos del recojo)
    reserva.refresh_from_db()
    assert antes_de_entregar <= reserva.picked_up_at <= timezone.now()
    rentas[0].update(picked_up_at=reserva.picked_up_at, handed_over_by_id=op01.pk)
    assert foto_de_la_base() == (rentas, equipos, historial)


def test_un_recojo_repetido_se_rechaza_con_la_fecha_del_primero(op01, c01, eq01):
    """Requisito: C1 (#54), una renta se entrega una sola vez.
    Caso:      OP-01 ya entrego la reserva de EQ-01 e intenta entregarla otra vez.
    Esperado:  AlreadyPickedUpError con la fecha del primer recojo; la base queda igual.
    """
    # Preparar
    reserva = register_pickup(reserva_de_c01(c01, eq01, dias_desde_hoy=1), op01)
    entregada = timezone.localtime(reserva.picked_up_at)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(AlreadyPickedUpError) as error:
        register_pickup(reserva, op01)

    # Comprobar: la respuesta
    assert str(error.value) == (
        f"La renta de EQ-01 ya fue entregada el {entregada:%d/%m/%Y %H:%M}."
    )

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes


def test_una_reserva_vencida_no_se_puede_entregar(op01, c01, eq01):
    """Requisito: C1 (#54) y cliente 17/10, sin recojo hasta las 12:00 del dia siguiente vence.
    Caso:      OP-01 intenta entregar una reserva de EQ-01 que empezo hace 3 dias.
    Esperado:  ReservationExpiredError con la hora limite; la base queda igual.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01, dias_desde_hoy=-3)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(ReservationExpiredError) as error:
        register_pickup(reserva, op01)

    # Comprobar: la respuesta
    assert str(error.value) == "La reserva de EQ-01 venció a las 12:00."

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes
