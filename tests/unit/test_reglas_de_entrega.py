"""Prueba rentals/handover.py: check_can_pick_up() y check_can_return(), cuándo se rechaza
una entrega o una devolución, con rentas sin guardar del 09/10/2026 18:00 al 12/10/2026 09:00."""
import pytest

from rentals.errors import RentalStateError
from rentals.handover import check_can_pick_up, check_can_return
from rentals.models import Equipment, Rental
from tests.helpers import local_datetime

EQ01 = Equipment(inventory_id="EQ-01")
INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)


def test_no_se_entrega_una_renta_cancelada():
    # La reserva se canceló el 08/10 a las 10:00 -> no se entrega y el mensaje dice cuándo se canceló
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, cancelled_at=local_datetime(2026, 10, 8, 10, 0))
    with pytest.raises(RentalStateError) as error:
        check_can_pick_up(renta, local_datetime(2026, 10, 9, 18, 30))
    assert str(error.value) == "La renta de EQ-01 ya fue cancelada el 08/10/2026 10:00."


def test_no_se_entrega_dos_veces_y_el_mensaje_tiene_la_fecha():
    # Ya se entregó el 09/10 a las 18:30 -> no se entrega otra vez y el mensaje dice cuándo
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, picked_up_at=local_datetime(2026, 10, 9, 18, 30))
    with pytest.raises(RentalStateError) as error:
        check_can_pick_up(renta, local_datetime(2026, 10, 9, 19, 0))
    assert str(error.value) == "La renta de EQ-01 ya fue entregada el 09/10/2026 18:30."


def test_no_se_entrega_una_reserva_vencida():
    # Nadie la recogió y son las 12:01 del 10/10 -> no se entrega (ENT-59)
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN)
    with pytest.raises(RentalStateError) as error:
        check_can_pick_up(renta, local_datetime(2026, 10, 10, 12, 1))
    assert str(error.value) == "La reserva de EQ-01 venció a las 12:00."


def test_no_se_devuelve_dos_veces():
    # Ya se devolvió el 12/10 a las 08:30 -> no se devuelve otra vez y el mensaje dice cuándo
    renta = Rental(
        equipment=EQ01, start_datetime=INICIO, end_datetime=FIN,
        picked_up_at=local_datetime(2026, 10, 9, 18, 30), returned_at=local_datetime(2026, 10, 12, 8, 30),
    )
    with pytest.raises(RentalStateError) as error:
        check_can_return(renta)
    assert str(error.value) == "La renta de EQ-01 ya fue devuelta el 12/10/2026 08:30."


def test_no_se_devuelve_una_renta_cancelada():
    # La reserva se canceló el 08/10 a las 10:00 -> no se devuelve
    renta = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, cancelled_at=local_datetime(2026, 10, 8, 10, 0))
    with pytest.raises(RentalStateError) as error:
        check_can_return(renta)
    assert str(error.value) == "La renta de EQ-01 ya fue cancelada el 08/10/2026 10:00."
