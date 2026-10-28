"""Prueba rentals/rules.py: is_pickup_date_allowed(), is_pickup_time_allowed(), is_return_time_allowed(),
rental_days(), is_within_max_duration() y ends_after_start() (ENT-18, ENT-19, ENT-72, ENT-94)."""
from datetime import timedelta

from rentals.rules import (
    ends_after_start,
    is_pickup_date_allowed,
    is_pickup_time_allowed,
    is_return_time_allowed,
    is_within_max_duration,
    rental_days,
)
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_recojo_de_hoy_a_las_18_00_vale_hasta_la_medianoche():
    # Son las 23:59 del 09/10 y pide recoger el 09/10 a las 18:00 -> permitido (ENT-94: puede recogerlo hasta la medianoche)
    assert is_pickup_date_allowed(INICIO, local_datetime(2026, 10, 9, 23, 59)) is True


def test_recojo_de_manana_permitido():
    # Es el 09/10 a las 10:00 y pide recoger el 10/10 -> permitido
    assert is_pickup_date_allowed(local_datetime(2026, 10, 10, 18, 0), local_datetime(2026, 10, 9, 10, 0)) is True


def test_recojo_de_ayer_rechazado():
    # Ya es la medianoche del 10/10 y pide recoger el 09/10 -> rechazado (ENT-94: no se elige una fecha pasada)
    assert is_pickup_date_allowed(INICIO, local_datetime(2026, 10, 10, 0, 0)) is False


def test_recojo_a_las_18_00_permitido():
    # Recoge el 09/10 a las 18:00 -> permitido (ENT-19: se entrega desde las 18:00)
    assert is_pickup_time_allowed(local_datetime(2026, 10, 9, 18, 0)) is True


def test_recojo_a_las_17_59_rechazado():
    # Recoge el 09/10 a las 17:59 -> rechazado, falta un minuto
    assert is_pickup_time_allowed(local_datetime(2026, 10, 9, 17, 59)) is False


def test_devolucion_a_las_09_00_permitida():
    # Devuelve el 12/10 a las 09:00 -> permitido (ENT-19: se devuelve hasta las 09:00)
    assert is_return_time_allowed(local_datetime(2026, 10, 12, 9, 0)) is True


def test_devolucion_a_las_09_01_rechazada():
    # Devuelve el 12/10 a las 09:01 -> rechazado, se pasa un minuto
    assert is_return_time_allowed(local_datetime(2026, 10, 12, 9, 1)) is False


def test_recojo_el_09_y_devolucion_el_11_son_dos_dias():
    # Recoge el 09/10 a las 18:00 y devuelve el 11/10 a las 09:00 -> 2 días (ENT-72)
    assert rental_days(INICIO, local_datetime(2026, 10, 11, 9, 0)) == 2


def test_renta_de_5_dias_permitida():
    # Recoge el 09/10 y devuelve el 14/10 -> 5 días justos, permitido (ENT-18: máximo 5 días)
    assert is_within_max_duration(INICIO, local_datetime(2026, 10, 14, 9, 0)) is True


def test_renta_de_6_dias_rechazada():
    # Recoge el 09/10 y devuelve el 15/10 -> 6 días, rechazado
    assert is_within_max_duration(INICIO, local_datetime(2026, 10, 15, 9, 0)) is False


def test_fin_igual_al_inicio_rechazado():
    # Devuelve en el mismo momento en que recoge -> rechazado
    assert ends_after_start(INICIO, INICIO) is False


def test_fin_despues_del_inicio_aceptado():
    # Devuelve un minuto después de recoger -> aceptado
    assert ends_after_start(INICIO, INICIO + timedelta(minutes=1)) is True
