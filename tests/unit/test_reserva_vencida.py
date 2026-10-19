"""Prueba rentals/rules.py: is_pickup_expired(), el vencimiento de una reserva no recogida
(ENT-59: si no se recoge hasta las 12:00 del día siguiente, queda libre a las 12:01)."""
from rentals.rules import is_pickup_expired
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_el_mismo_dia_la_reserva_no_vence():
    # Empieza el 09/10 a las 18:00 y son las 23:00 del mismo día -> no venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 9, 23, 0)) is False


def test_a_las_12_00_del_dia_siguiente_la_reserva_no_vence():
    # Son las 12:00 del 10/10, el último minuto para recoger -> no venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 10, 12, 0)) is False


def test_a_las_12_01_del_dia_siguiente_la_reserva_vence():
    # Son las 12:01 del 10/10 -> venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 10, 12, 1)) is True
