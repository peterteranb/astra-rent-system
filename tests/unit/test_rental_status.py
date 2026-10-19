"""Pruebas UNITARIAS del estado calculado de la renta (Rental.status_at)."""
import pytest

from rentals.models import Equipment, Rental
from rentals.statuses import RentalStatus
from tests.helpers import local_datetime


@pytest.mark.parametrize(
    "momento, estado",
    [
        (local_datetime(2026, 10, 10, 12, 0), RentalStatus.RESERVED),
        (local_datetime(2026, 10, 10, 12, 1), RentalStatus.NOT_PICKED_UP),
    ],
    ids=["10/10 12:00 sigue reservada", "10/10 12:01 no recogida"],
)
def test_la_reserva_vence_a_las_12_00_del_dia_siguiente(doc_start, doc_end, momento, estado):
    """Requisito: A1 (#42), la reserva sin recojo vence a las 12:00 del dia siguiente al inicio.
    Caso:      renta de EQ-01 con inicio el 09/10/2026 18:00, sin recojo, consultada en cada momento.
    Esperado:  a las 12:00 sigue "Reservada"; a las 12:01 pasa a "No recogida".
    """
    # Preparar
    renta = Rental(equipment=Equipment(inventory_id="EQ-01"), start_datetime=doc_start, end_datetime=doc_end)

    # Ejecutar
    resultado = renta.status_at(momento)

    # Comprobar
    assert resultado == estado


def renta_de_eq01(doc_start, doc_end, **momentos):
    """Renta de EQ-01 sin guardar, del 09/10/2026 18:00 al 12/10/2026 09:00, con los momentos dados."""
    return Rental(
        equipment=Equipment(inventory_id="EQ-01"),
        start_datetime=doc_start,
        end_datetime=doc_end,
        **momentos,
    )


def test_una_renta_cancelada_no_ocupa_el_equipo(doc_start, doc_end):
    """Requisito: B2 (#48) y ENT-55, una reserva cancelada deja libres sus fechas.
    Caso:      renta de EQ-01 cancelada el 08/10/2026, consultada el 10/10/2026 a las 08:00.
    Esperado:  occupies_equipment_at devuelve False.
    Ejemplo:   cancelled_at = 08/10/2026 10:00 -> False.
    """
    # Preparar
    renta = renta_de_eq01(doc_start, doc_end, cancelled_at=local_datetime(2026, 10, 8, 10, 0))

    # Ejecutar
    ocupa = renta.occupies_equipment_at(local_datetime(2026, 10, 10, 8, 0))

    # Comprobar
    assert ocupa is False


def test_una_renta_devuelta_no_ocupa_el_equipo(doc_start, doc_end):
    """Requisito: B2 (#48), un equipo devuelto ya no esta afuera; su estado lo decide mantenimiento.
    Caso:      renta de EQ-01 recogida el 09/10 y devuelta el 11/10/2026, consultada el 11/10 a las 10:00.
    Esperado:  occupies_equipment_at devuelve False.
    Ejemplo:   returned_at = 11/10/2026 08:00 -> False.
    """
    # Preparar
    renta = renta_de_eq01(
        doc_start,
        doc_end,
        picked_up_at=local_datetime(2026, 10, 9, 18, 30),
        returned_at=local_datetime(2026, 10, 11, 8, 0),
    )

    # Ejecutar
    ocupa = renta.occupies_equipment_at(local_datetime(2026, 10, 11, 10, 0))

    # Comprobar
    assert ocupa is False


def test_una_reserva_no_recogida_a_las_12_01_ya_no_ocupa_el_equipo(doc_start, doc_end):
    """Requisito: B2 (#48) y ENT-59, sin recojo hasta las 12:00 del dia siguiente el equipo queda libre.
    Caso:      reserva de EQ-01 que empieza el 09/10/2026 18:00, sin recojo, consultada el 10/10 a las 12:01.
    Esperado:  occupies_equipment_at devuelve False.
    Ejemplo:   ahora = 10/10/2026 12:01 -> False.
    """
    # Preparar
    renta = renta_de_eq01(doc_start, doc_end)

    # Ejecutar
    ocupa = renta.occupies_equipment_at(local_datetime(2026, 10, 10, 12, 1))

    # Comprobar
    assert ocupa is False


def test_una_reserva_a_las_12_00_todavia_ocupa_el_equipo(doc_start, doc_end):
    """Requisito: B2 (#48), las 12:00 del dia siguiente todavia es a tiempo para recoger.
    Caso:      reserva de EQ-01 que empieza el 09/10/2026 18:00, sin recojo, consultada el 10/10 a las 12:00.
    Esperado:  occupies_equipment_at devuelve True.
    Ejemplo:   ahora = 10/10/2026 12:00 -> True.
    """
    # Preparar
    renta = renta_de_eq01(doc_start, doc_end)

    # Ejecutar
    ocupa = renta.occupies_equipment_at(local_datetime(2026, 10, 10, 12, 0))

    # Comprobar
    assert ocupa is True


def test_una_renta_rentada_ocupa_el_equipo(doc_start, doc_end):
    """Requisito: B2 (#48), un equipo que el cliente se llevo sigue ocupado hasta que vuelva.
    Caso:      renta de EQ-01 recogida el 09/10/2026 18:30, consultada el 11/10 a las 10:00.
    Esperado:  occupies_equipment_at devuelve True.
    Ejemplo:   picked_up_at = 09/10/2026 18:30, sin devolucion -> True.
    """
    # Preparar
    renta = renta_de_eq01(doc_start, doc_end, picked_up_at=local_datetime(2026, 10, 9, 18, 30))

    # Ejecutar
    ocupa = renta.occupies_equipment_at(local_datetime(2026, 10, 11, 10, 0))

    # Comprobar
    assert ocupa is True
