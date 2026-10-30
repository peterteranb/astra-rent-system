"""Prueba rentals/models.py: Rental.status_at(), Rental.return_result y Rental.occupies_equipment_at() en diferentes momentos."""
from rentals.models import Rental
from rentals.statuses import RentalStatus, ReturnResult
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)
ANTES_DEL_INICIO = local_datetime(2026, 10, 9, 12, 0)
RECOJO = local_datetime(2026, 10, 9, 18, 30)
DEVOLUCION = local_datetime(2026, 10, 12, 8, 30)
CANCELACION = local_datetime(2026, 10, 8, 10, 0)
VENCIDA = local_datetime(2026, 10, 10, 0, 0)


def test_determinacion_de_estado_y_ocupacion_temporal_de_la_renta():
    # Sin momentos registrados (reservada), con recojo (rentada), con devolución (devuelta) y cancelación prioritaria -> evolución de estados
    # Comprueba que una renta sin eventos previos se encuentra en estado reservada antes de su inicio
    assert Rental(start_datetime=INICIO, end_datetime=FIN).status_at(ANTES_DEL_INICIO) == RentalStatus.RESERVED
    # Comprueba que al registrarse el recojo la renta pasa a estar rentada
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO).status_at(DEVOLUCION) == RentalStatus.RENTED
    # Comprueba que al registrar la devolución el estado pasa a devuelta
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION).status_at(DEVOLUCION) == RentalStatus.RETURNED
    # Comprueba que la cancelación se impone como estado definitivo aunque exista un recojo previo
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, cancelled_at=CANCELACION).status_at(DEVOLUCION) == RentalStatus.CANCELLED
    # Comprueba que si llega la medianoche sin recojo la reserva pasa a no recogida
    assert Rental(start_datetime=INICIO, end_datetime=FIN).status_at(VENCIDA) == RentalStatus.NOT_PICKED_UP

    # Vueltas a tiempo vs sin retorno, y verificación de si la renta continúa ocupando el equipo -> vigencia y resultados de devolución
    # Comprueba que una renta activa sin devolución no arroja un resultado de retorno
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO).return_result is None
    # Comprueba que retornar antes del límite de las 09:00 califica como devolución a tiempo
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION).return_result == ReturnResult.ON_TIME
    # Comprueba que las rentas reservadas u ocupadas retienen el equipo
    assert Rental(start_datetime=INICIO, end_datetime=FIN).occupies_equipment_at(ANTES_DEL_INICIO) is True
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO).occupies_equipment_at(DEVOLUCION) is True
    # Comprueba que las rentas canceladas, devueltas o no recogidas liberan el equipo
    assert Rental(start_datetime=INICIO, end_datetime=FIN, cancelled_at=CANCELACION).occupies_equipment_at(ANTES_DEL_INICIO) is False
    assert Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION).occupies_equipment_at(DEVOLUCION) is False
    assert Rental(start_datetime=INICIO, end_datetime=FIN).occupies_equipment_at(VENCIDA) is False