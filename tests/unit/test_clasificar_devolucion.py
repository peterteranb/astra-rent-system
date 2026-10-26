"""Prueba rentals/rules.py: classify_return(), cómo llegó una devolución (RF-02)
(ENT-63: hasta las 09:00 sin multa, hasta las 12:00 con multa, después un día más)."""
from datetime import date

from rentals.rules import classify_return
from rentals.statuses import ReturnResult
from tests.helpers import local_datetime

VENCE = date(2026, 10, 12)


def test_devolucion_a_las_09_00_llega_a_tiempo():
    # Vence el 12/10 y vuelve a las 09:00 -> a tiempo
    resultado = classify_return(local_datetime(2026, 10, 12, 9, 0), VENCE)
    assert resultado == ReturnResult.ON_TIME


def test_devolucion_a_las_09_01_tiene_multa():
    # Vence el 12/10 y vuelve a las 09:01 -> con multa, no hay tolerancia
    resultado = classify_return(local_datetime(2026, 10, 12, 9, 1), VENCE)
    assert resultado == ReturnResult.WITH_FINE


def test_devolucion_a_las_12_00_tiene_multa():
    # Vence el 12/10 y vuelve a las 12:00 -> todavía con multa
    resultado = classify_return(local_datetime(2026, 10, 12, 12, 0), VENCE)
    assert resultado == ReturnResult.WITH_FINE


def test_devolucion_a_las_12_01_cobra_un_dia_mas():
    # Vence el 12/10 y vuelve a las 12:01 -> se cobra un día más (ENT-63: «aunque sean las 12:01»)
    resultado = classify_return(local_datetime(2026, 10, 12, 12, 1), VENCE)
    assert resultado == ReturnResult.EXTRA_DAY


def test_devolucion_al_dia_siguiente_a_las_08_00_cobra_un_dia_mas():
    # Vence el 12/10 y vuelve el 13/10 a las 08:00 -> se cobra un día más
    resultado = classify_return(local_datetime(2026, 10, 13, 8, 0), VENCE)
    assert resultado == ReturnResult.EXTRA_DAY
