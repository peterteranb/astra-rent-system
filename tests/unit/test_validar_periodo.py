"""Prueba rentals/renting.py: check_period(), el mensaje con la causa de cada periodo rechazado (RC-01)."""
import pytest

from rentals.errors import InvalidPeriodError
from rentals.renting import check_period
from tests.helpers import local_datetime


def test_fin_antes_del_inicio_dice_que_la_devolucion_debe_ser_posterior():
    # Recoge el 12/10 18:00 y devuelve el 10/10 09:00 -> rechazado con la causa
    with pytest.raises(InvalidPeriodError) as error:
        check_period(local_datetime(2026, 10, 12, 18, 0), local_datetime(2026, 10, 10, 9, 0))
    assert str(error.value) == "La fecha y hora de devolución debe ser posterior a la de recojo."


def test_mas_de_5_dias_dice_el_maximo():
    # Del 09/10 18:00 al 15/10 09:00 son más de 5 días -> rechazado con la causa
    with pytest.raises(InvalidPeriodError) as error:
        check_period(local_datetime(2026, 10, 9, 18, 0), local_datetime(2026, 10, 15, 9, 0))
    assert str(error.value) == "La renta no puede durar más de 5 días."


def test_recojo_antes_de_las_18_00_dice_desde_cuando():
    # Recoge el 09/10 a las 17:00 -> rechazado con la causa
    with pytest.raises(InvalidPeriodError) as error:
        check_period(local_datetime(2026, 10, 9, 17, 0), local_datetime(2026, 10, 12, 9, 0))
    assert str(error.value) == "El recojo debe ser desde las 18:00."


def test_devolucion_despues_de_las_09_00_dice_hasta_cuando():
    # Devuelve el 12/10 a las 10:00 -> rechazado con la causa
    with pytest.raises(InvalidPeriodError) as error:
        check_period(local_datetime(2026, 10, 9, 18, 0), local_datetime(2026, 10, 12, 10, 0))
    assert str(error.value) == "La devolución debe ser hasta las 09:00."
