"""Prueba rentals/rules.py: is_pickup_expired(), el vencimiento de una reserva no recogida
(ENT-69: si nadie la recoge, a la medianoche de su día de inicio queda «No recogida»)."""
from rentals.rules import is_pickup_expired
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_a_las_23_00_del_mismo_dia_la_reserva_no_vence():
    # Empieza el 09/10 a las 18:00 y son las 23:00 del mismo día -> no venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 9, 23, 0)) is False


def test_a_las_23_59_del_mismo_dia_la_reserva_no_vence():
    # Son las 23:59 del 09/10, el último minuto para recoger -> no venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 9, 23, 59)) is False


def test_a_la_medianoche_la_reserva_vence():
    # Son las 00:00 del 10/10 -> venció
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 10, 0, 0)) is True
