"""Pruebas de INTEGRACION de la entrega y la devolucion del equipo (rentals/handover.py y su pagina).

Las fechas son relativas a hoy: con las fechas fijas de los documentos
(09/10/2026) la reserva ya estaria vencida y no se podria entregar.
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects

from rentals.errors import (
    AlreadyPickedUpError,
    AlreadyReturnedError,
    IncompleteReturnError,
    ReservationExpiredError,
)
from rentals.handover import register_pickup, register_return
from rentals.models import StatusChange
from rentals.renting import create_rental
from rentals.statuses import EquipmentStatus, RentalStatus
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


def test_op01_registra_un_recojo_desde_la_pagina_de_reservas(client, op01, c01, eq01):
    """Requisito: C2 (#55), el operador registra el recojo desde /staff/reservations/.
    Caso:      OP-01 abre la pagina, ve la reserva de EQ-01 de C-01 y presiona "Registrar recojo".
    Esperado:  vuelve a la lista con el mensaje de exito y la renta queda "Rentada" por OP-01.
    """
    # Preparar
    reserva = reserva_de_c01(c01, eq01, dias_desde_hoy=1)
    client.force_login(op01)

    # Ejecutar
    pagina = client.get("/staff/reservations/")
    respuesta = client.post(f"/staff/reservations/{reserva.pk}/pickup/", follow=True)

    # Comprobar: la respuesta
    assert list(pagina.context["reservations"]) == [reserva]
    assertContains(pagina, f'action="/staff/reservations/{reserva.pk}/pickup/"')
    assertRedirects(respuesta, "/staff/reservations/")
    assertContains(respuesta, "Recojo registrado: EQ-01 entregado a c01.")
    assert list(respuesta.context["reservations"]) == []

    # Comprobar: lo guardado
    reserva.refresh_from_db()
    assert reserva.status == RentalStatus.RENTED
    assert reserva.handed_over_by == op01


def test_el_operador_registra_la_devolucion_y_el_equipo_pasa_a_revision(op01, c01, eq01):
    """Requisito: C3 (#56), registrar la devolucion guarda cuando, quien y como llego.
    Caso:      OP-01 recibe de C-01 el EQ-01 rentado, con la nota "Una pata floja".
    Esperado:  la renta queda "Devuelta", EQ-01 "En revision" y una fila de historial con la nota.
    """
    # Preparar
    renta = register_pickup(reserva_de_c01(c01, eq01, dias_desde_hoy=0), op01)
    rentas, equipos, historial = foto_de_la_base()
    antes_de_devolver = timezone.now()

    # Ejecutar
    devuelta = register_return(renta, op01, "Una pata floja")

    # Comprobar: la respuesta
    assert devuelta.status == RentalStatus.RETURNED

    # Comprobar: lo guardado
    renta.refresh_from_db()
    assert antes_de_devolver <= renta.returned_at <= timezone.now()
    rentas[0].update(
        returned_at=renta.returned_at, received_by_id=op01.pk, return_note="Una pata floja"
    )
    equipos[0].update(status=EquipmentStatus.IN_REVIEW)
    cambio = StatusChange.objects.get()
    historial.append(
        {
            "pk": cambio.pk,
            "equipment_id": eq01.pk,
            "old_status": EquipmentStatus.AVAILABLE,
            "new_status": EquipmentStatus.IN_REVIEW,
            "changed_by_id": op01.pk,
            "changed_at": cambio.changed_at,
            "comment": "Una pata floja",
        }
    )
    assert foto_de_la_base() == (rentas, equipos, historial)


def test_una_devolucion_repetida_se_rechaza_con_la_fecha_de_la_primera(op01, c01, eq01):
    """Requisito: C3 (#56), una renta se devuelve una sola vez.
    Caso:      OP-01 ya registro la devolucion de EQ-01 e intenta registrarla otra vez.
    Esperado:  AlreadyReturnedError con la fecha; EQ-01 sigue "En revision" con un solo cambio.
    """
    # Preparar
    renta = register_pickup(reserva_de_c01(c01, eq01, dias_desde_hoy=0), op01)
    renta = register_return(renta, op01, "Sin danos")
    devuelta = timezone.localtime(renta.returned_at)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(AlreadyReturnedError) as error:
        register_return(renta, op01, "Sin danos")

    # Comprobar: la respuesta
    assert str(error.value) == f"La renta de EQ-01 ya fue devuelta el {devuelta:%d/%m/%Y %H:%M}."

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes
    assert StatusChange.objects.filter(new_status=EquipmentStatus.IN_REVIEW).count() == 1


def test_una_devolucion_sin_nota_se_rechaza(op01, c01, eq01):
    """Requisito: C3 (#56), la nota de como llego el equipo es obligatoria.
    Caso:      OP-01 intenta registrar la devolucion de EQ-01 con una nota de solo espacios.
    Esperado:  IncompleteReturnError con la causa; la base queda igual.
    """
    # Preparar
    renta = register_pickup(reserva_de_c01(c01, eq01, dias_desde_hoy=0), op01)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(IncompleteReturnError) as error:
        register_return(renta, op01, "   ")

    # Comprobar: la respuesta
    assert str(error.value) == "Escribe cómo llegó el equipo."

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes
