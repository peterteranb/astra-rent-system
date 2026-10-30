"""Prueba rentals/use_cases/renting.py: check_period(), validando las causas de rechazo ante periodos de renta inválidos."""
import pytest

from rentals.errors import InvalidPeriodError
from rentals.use_cases.renting import check_period
from tests.helpers import con_la_hora, local_datetime

AHORA = local_datetime(2026, 10, 9, 10, 0)


def test_mensajes_de_rechazo_para_periodos_invalidos_de_renta():
    # Recojo en día pasado, devolución anterior al inicio, duración mayor a 5 días, o horas fuera de rango (antes de 18:00 o después de 09:00) -> excepciones descriptivas
    # Comprueba que elegir un día de recojo anterior al actual rechaza el periodo con su causa
    with con_la_hora(AHORA), pytest.raises(InvalidPeriodError) as error_pasado:
        check_period(local_datetime(2026, 10, 8, 18, 0), local_datetime(2026, 10, 10, 9, 0))
    assert str(error_pasado.value) == "La fecha de recojo ya pasó. Elige hoy o un día siguiente."

    # Comprueba que fijar una devolución previa al inicio rechaza el periodo
    with con_la_hora(AHORA), pytest.raises(InvalidPeriodError) as error_inverso:
        check_period(local_datetime(2026, 10, 12, 18, 0), local_datetime(2026, 10, 10, 9, 0))
    assert str(error_inverso.value) == "La fecha y hora de devolución debe ser posterior a la de recojo."

    # Comprueba que exceder el límite de 5 días de duración rechaza la solicitud
    with con_la_hora(AHORA), pytest.raises(InvalidPeriodError) as error_duracion:
        check_period(local_datetime(2026, 10, 9, 18, 0), local_datetime(2026, 10, 15, 9, 0))
    assert str(error_duracion.value) == "La renta no puede durar más de 5 días."

    # Comprueba que intentar recoger antes de las 18:00 genera un rechazo informando la restricción horaria
    with con_la_hora(AHORA), pytest.raises(InvalidPeriodError) as error_hora_recojo:
        check_period(local_datetime(2026, 10, 9, 17, 0), local_datetime(2026, 10, 12, 9, 0))
    assert str(error_hora_recojo.value) == "El recojo debe ser desde las 18:00."

    # Comprueba que devolver después de las 09:00 rechaza la selección con el mensaje correspondiente
    with con_la_hora(AHORA), pytest.raises(InvalidPeriodError) as error_hora_dev:
        check_period(local_datetime(2026, 10, 9, 18, 0), local_datetime(2026, 10, 12, 10, 0))
    assert str(error_hora_dev.value) == "La devolución debe ser hasta las 09:00."