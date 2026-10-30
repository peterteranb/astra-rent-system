"""Prueba rentals/use_cases/handover.py: check_can_pick_up() y check_can_return(), validando restricciones de entrega y devolución."""
import pytest

from rentals.errors import RentalStateError
from rentals.models import Equipment, Rental
from rentals.use_cases.handover import check_can_pick_up, check_can_return
from tests.helpers import local_datetime

EQ01 = Equipment(inventory_id="MES-00001")
INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)


def test_validaciones_de_bloqueo_para_entregas_y_devoluciones():
    # Intento de entregar una renta cancelada, entregada previamente o vencida a medianoche -> rechazos de recojo
    # Comprueba que no se puede entregar una renta que ya fue cancelada previamente
    renta_cancelada = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, cancelled_at=local_datetime(2026, 10, 8, 10, 0))
    with pytest.raises(RentalStateError) as error_cancel:
        check_can_pick_up(renta_cancelada, local_datetime(2026, 10, 9, 18, 30))
    assert str(error_cancel.value) == "La renta de MES-00001 ya fue cancelada el 08/10/2026 10:00."

    # Comprueba que no se permite una doble entrega del mismo equipo
    renta_entregada_prev = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN, picked_up_at=local_datetime(2026, 10, 9, 18, 30))
    with pytest.raises(RentalStateError) as error_doble:
        check_can_pick_up(renta_entregada_prev, local_datetime(2026, 10, 9, 19, 0))
    assert str(error_doble.value) == "La renta de MES-00001 ya fue entregada el 09/10/2026 18:30."

    # Comprueba que una reserva sin recoger expira a la medianoche impidiendo su entrega
    renta_vencida = Rental(equipment=EQ01, start_datetime=INICIO, end_datetime=FIN)
    with pytest.raises(RentalStateError) as error_vencida:
        check_can_pick_up(renta_vencida, local_datetime(2026, 10, 10, 0, 0))
    assert str(error_vencida.value) == "La reserva de MES-00001 venció a la medianoche."

    # Devolución duplicada o de rentas canceladas -> rechazos de retorno
    # Comprueba que no se puede registrar una doble devolución de un equipo ya retornado
    renta_devuelta_prev = Rental(
        equipment=EQ01, start_datetime=INICIO, end_datetime=FIN,
        picked_up_at=local_datetime(2026, 10, 9, 18, 30), returned_at=local_datetime(2026, 10, 12, 8, 30),
    )
    with pytest.raises(RentalStateError) as error_retorno_doble:
        check_can_return(renta_devuelta_prev)
    assert str(error_retorno_doble.value) == "La renta de MES-00001 ya fue devuelta el 12/10/2026 08:30."

    # Comprueba que una renta cancelada no permite registrar procesos de devolución
    with pytest.raises(RentalStateError) as error_retorno_cancel:
        check_can_return(renta_cancelada)
    assert str(error_retorno_cancel.value) == "La renta de MES-00001 ya fue cancelada el 08/10/2026 10:00."