"""Prueba rentals/rules.py: is_pickup_expired(), validando el vencimiento de reservas no recogidas a la medianoche."""
from rentals.rules import is_pickup_expired
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_evaluacion_de_vencimiento_de_reserva_segun_la_hora():
    # A las 23:00 o 23:59 del mismo día la reserva sigue vigentes; a las 00:00 del día siguiente se considera vencida -> límites de expiración
    # Comprueba que a las 23:00 del día de recojo la reserva aún no ha vencido
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 9, 23, 0)) is False
    # Comprueba que en el último minuto del día (23:59) la reserva sigue activa
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 9, 23, 59)) is False
    # Comprueba que al llegar exactamente a la medianoche (00:00 del día siguiente) la reserva expira
    assert is_pickup_expired(INICIO, local_datetime(2026, 10, 10, 0, 0)) is True