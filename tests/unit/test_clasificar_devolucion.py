"""Prueba rentals/rules.py: classify_return() y late_days(), cómo llegó una devolución y cuántos días de atraso
se cobran (ENT-73: hasta las 09:00 a tiempo, hasta las 12:00 tolerancia sin cobro, desde las 12:01 deuda)."""
from datetime import date

from rentals.rules import classify_return, late_days
from rentals.statuses import ReturnResult
from tests.helpers import local_datetime

VENCE = date(2026, 10, 10)


def test_devolucion_a_las_09_00_llega_a_tiempo():
    # Vence el 10/10 y vuelve a las 09:00 -> a tiempo
    resultado = classify_return(local_datetime(2026, 10, 10, 9, 0), VENCE)
    assert resultado == ReturnResult.ON_TIME


def test_devolucion_a_las_09_01_esta_en_tolerancia():
    # Vence el 10/10 y vuelve a las 09:01 -> tolerancia, sin cobro
    resultado = classify_return(local_datetime(2026, 10, 10, 9, 1), VENCE)
    assert resultado == ReturnResult.TOLERANCE


def test_devolucion_a_las_12_00_todavia_esta_en_tolerancia():
    # Vence el 10/10 y vuelve a las 12:00 -> último minuto de tolerancia
    resultado = classify_return(local_datetime(2026, 10, 10, 12, 0), VENCE)
    assert resultado == ReturnResult.TOLERANCE


def test_devolucion_a_las_12_01_tiene_atraso():
    # Vence el 10/10 y vuelve a las 12:01 -> con atraso
    resultado = classify_return(local_datetime(2026, 10, 10, 12, 1), VENCE)
    assert resultado == ReturnResult.LATE


def test_devolucion_a_las_12_00_no_cobra_dias():
    # Vence el 10/10 y vuelve a las 12:00 -> 0 días de atraso
    assert late_days(local_datetime(2026, 10, 10, 12, 0), VENCE) == 0


def test_devolucion_a_las_12_01_cobra_un_dia():
    # Vence el 10/10 y vuelve a las 12:01 -> pasó el mediodía del 10, 1 día
    assert late_days(local_datetime(2026, 10, 10, 12, 1), VENCE) == 1


def test_devolucion_al_dia_siguiente_a_las_10_00_cobra_un_dia():
    # Vence el 10/10 y vuelve el 11/10 a las 10:00 -> solo pasó el mediodía del 10, 1 día
    assert late_days(local_datetime(2026, 10, 11, 10, 0), VENCE) == 1


def test_devolucion_al_dia_siguiente_a_las_12_01_cobra_dos_dias():
    # Vence el 10/10 y vuelve el 11/10 a las 12:01 -> pasaron dos mediodías, 2 días
    assert late_days(local_datetime(2026, 10, 11, 12, 1), VENCE) == 2


def test_devolucion_antes_del_vencimiento_no_cobra_dias():
    # Vence el 10/10 y vuelve el 09/10 a las 13:00 -> 0 días de atraso
    assert late_days(local_datetime(2026, 10, 9, 13, 0), VENCE) == 0
