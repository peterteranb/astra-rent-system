"""Pruebas UNITARIAS de la regla que decide si una renta se puede cancelar (renting.check_can_cancel)."""
import pytest

from rentals.errors import RentalStateError
from rentals.models import Equipment, Rental
from rentals.renting import check_can_cancel
from tests.helpers import local_datetime


def test_una_renta_ya_entregada_no_se_puede_cancelar(doc_start, doc_end):
    """Requisito: B3 (#49), solo se cancela una reserva que todavia no se recogio.
    Caso:      renta de EQ-01 entregada el 09/10/2026 18:30; se intenta cancelar el 10/10 a las 08:00.
    Esperado:  RentalStateError con la fecha de la entrega.
    Ejemplo:   picked_up_at = 09/10/2026 18:30 -> "La renta de EQ-01 ya fue entregada el 09/10/2026 18:30."
    """
    # Preparar
    renta = Rental(
        equipment=Equipment(inventory_id="EQ-01"),
        start_datetime=doc_start,
        end_datetime=doc_end,
        picked_up_at=local_datetime(2026, 10, 9, 18, 30),
    )

    # Ejecutar
    with pytest.raises(RentalStateError) as error:
        check_can_cancel(renta, local_datetime(2026, 10, 10, 8, 0))

    # Comprobar
    assert str(error.value) == "La renta de EQ-01 ya fue entregada el 09/10/2026 18:30."
