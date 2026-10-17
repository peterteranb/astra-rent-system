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
