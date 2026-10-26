"""Prueba rentals/renting.py: check_can_cancel(), solo se cancela una renta «Reservada» (HU-06),
con rentas sin guardar del 09/10/2026 18:00 al 12/10/2026 09:00."""
import pytest

from rentals.errors import RentalStateError
from rentals.models import Equipment, Rental
from rentals.renting import check_can_cancel
from tests.helpers import local_datetime

EQ01 = Equipment(inventory_id="EQ-01")
INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)
AHORA = local_datetime(2026, 10, 9, 19, 0)


def test_una_renta_reservada_se_puede_cancelar():
    # Nadie la recogió y no venció -> se puede cancelar, no lanza error
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN)
    assert check_can_cancel(renta, AHORA) is None


def test_una_renta_entregada_no_se_puede_cancelar():
    # El cliente se la llevó el 09/10 a las 18:30 -> no se cancela y el mensaje dice cuándo
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, picked_up_at=local_datetime(2026, 10, 9, 18, 30))
    with pytest.raises(RentalStateError) as error:
        check_can_cancel(renta, AHORA)
    assert str(error.value) == "La renta de EQ-01 ya fue entregada el 09/10/2026 18:30."


def test_una_renta_ya_cancelada_no_se_puede_cancelar_otra_vez():
    # Se canceló el 08/10 a las 10:00 -> no se cancela otra vez
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, cancelled_at=local_datetime(2026, 10, 8, 10, 0))
    with pytest.raises(RentalStateError) as error:
        check_can_cancel(renta, AHORA)
    assert str(error.value) == "La renta de EQ-01 ya fue cancelada el 08/10/2026 10:00."
