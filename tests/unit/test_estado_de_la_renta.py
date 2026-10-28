"""Prueba rentals/models.py: Rental.status_at(), Rental.return_result y Rental.occupies_equipment_at()
con rentas sin guardar del 09/10/2026 18:00 al 12/10/2026 09:00 (RF-08)."""
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


def test_sin_momentos_la_renta_esta_reservada():
    # Nadie la recogió, devolvió ni canceló y todavía no empieza -> reservada
    renta = Rental(start_datetime=INICIO, end_datetime=FIN)
    assert renta.status_at(ANTES_DEL_INICIO) == RentalStatus.RESERVED


def test_con_recojo_la_renta_esta_rentada():
    # El cliente la recogió el 09/10 a las 18:30 -> rentada
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO)
    assert renta.status_at(DEVOLUCION) == RentalStatus.RENTED


def test_con_devolucion_la_renta_esta_devuelta():
    # La recogió y la devolvió el 12/10 a las 08:30 -> devuelta
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION)
    assert renta.status_at(DEVOLUCION) == RentalStatus.RETURNED


def test_la_cancelacion_gana_aunque_tenga_recojo():
    # Tiene recojo y también cancelación -> cancelada, la cancelación es definitiva
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, cancelled_at=CANCELACION)
    assert renta.status_at(DEVOLUCION) == RentalStatus.CANCELLED


def test_vencida_sin_recojo_queda_no_recogida():
    # Nadie la recogió y es la medianoche del 10/10 -> no recogida (ENT-69)
    renta = Rental(start_datetime=INICIO, end_datetime=FIN)
    assert renta.status_at(VENCIDA) == RentalStatus.NOT_PICKED_UP


def test_return_result_vacio_si_el_equipo_no_volvio():
    # Está rentada y el equipo no volvió -> no hay resultado de devolución
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO)
    assert renta.return_result is None


def test_return_result_a_tiempo_si_volvio_antes_de_las_09_00():
    # Vence el 12/10 y volvió a las 08:30 -> a tiempo
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION)
    assert renta.return_result == ReturnResult.ON_TIME


def test_una_renta_reservada_ocupa_el_equipo():
    # Está reservada -> ocupa sus fechas
    renta = Rental(start_datetime=INICIO, end_datetime=FIN)
    assert renta.occupies_equipment_at(ANTES_DEL_INICIO) is True


def test_una_renta_rentada_ocupa_el_equipo():
    # Está rentada -> ocupa sus fechas
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO)
    assert renta.occupies_equipment_at(DEVOLUCION) is True


def test_una_renta_cancelada_no_ocupa_el_equipo():
    # Está cancelada -> sus fechas quedan libres (ENT-55)
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, cancelled_at=CANCELACION)
    assert renta.occupies_equipment_at(ANTES_DEL_INICIO) is False


def test_una_renta_devuelta_no_ocupa_el_equipo():
    # Está devuelta -> sus fechas quedan libres
    renta = Rental(start_datetime=INICIO, end_datetime=FIN, picked_up_at=RECOJO, returned_at=DEVOLUCION)
    assert renta.occupies_equipment_at(DEVOLUCION) is False


def test_una_renta_no_recogida_no_ocupa_el_equipo():
    # Venció sin recojo a la medianoche del 10/10 -> sus fechas quedan libres (ENT-69)
    renta = Rental(start_datetime=INICIO, end_datetime=FIN)
    assert renta.occupies_equipment_at(VENCIDA) is False
