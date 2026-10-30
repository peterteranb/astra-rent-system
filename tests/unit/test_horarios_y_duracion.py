"""Prueba rentals/rules.py: restricciones de fechas, horarios, duración máxima y solapamientos."""
from datetime import timedelta
from decimal import Decimal

from rentals.models import Rental
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


def test_reglas_de_fechas_y_horarios_de_recojo_y_devolucion():
    # Pide recoger hoy a las 18:00 (permitido hasta medianoche), mañana permitido, y ayer rechazado -> validación correcta de fechas
    # Comprueba que el recojo de hoy a las 18:00 es válido hasta medianoche
    assert is_pickup_date_allowed(INICIO, local_datetime(2026, 10, 9, 23, 59)) is True
    # Comprueba que el recojo del día siguiente está permitido
    assert is_pickup_date_allowed(local_datetime(2026, 10, 10, 18, 0), local_datetime(2026, 10, 9, 10, 0)) is True
    # Comprueba que elegir un recojo de fecha pasada se rechaza
    assert is_pickup_date_allowed(INICIO, local_datetime(2026, 10, 10, 0, 0)) is False

    # Recoge a las 18:00 (permitido) vs 17:59 (rechazado); devuelve a las 09:00 (permitido) vs 09:01 (rechazado) -> límites horarios
    # Comprueba la hora mínima de recojo permitida (18:00)
    assert is_pickup_time_allowed(local_datetime(2026, 10, 9, 18, 0)) is True
    # Comprueba que un minuto antes de las 18:00 se rechaza
    assert is_pickup_time_allowed(local_datetime(2026, 10, 9, 17, 59)) is False
    # Comprueba la hora máxima de devolución permitida (09:00)
    assert is_return_time_allowed(local_datetime(2026, 10, 12, 9, 0)) is True
    # Comprueba que pasarse por un minuto en la devolución se rechaza
    assert is_return_time_allowed(local_datetime(2026, 10, 12, 9, 1)) is False


def test_duracion_dias_y_consistencia_temporal_de_la_renta():
    # Recoge el 09/10 a las 18:00 y devuelve el 11/10 a las 09:00 -> son 2 días exactos de cálculo
    # Comprueba el cálculo correcto de días de renta
    assert rental_days(INICIO, local_datetime(2026, 10, 11, 9, 0)) == 2

    # Renta de 5 días (permitida) vs 6 días (rechazada), y fin igual o posterior al inicio -> validación de duración máxima
    # Comprueba que una renta de 5 días justos está permitida
    assert is_within_max_duration(INICIO, local_datetime(2026, 10, 14, 9, 0)) is True
    # Comprueba que una renta de 6 días excede el límite y se rechaza
    assert is_within_max_duration(INICIO, local_datetime(2026, 10, 15, 9, 0)) is False
    # Comprueba que devolver en el mismo instante de inicio se rechaza
    assert ends_after_start(INICIO, INICIO) is False
    # Comprueba que devolver después del inicio es aceptado
    assert ends_after_start(INICIO, INICIO + timedelta(minutes=1)) is True


def test_recojo_a_las_18_00_y_devolucion_al_dia_siguiente_a_las_09_00_es_un_dia():
    # Mesa de 20 Bs por día: recoge el 09/10 a las 18:00 y devuelve el 10/10 a las 09:00 -> 1 día, 20 Bs
    renta = Rental(start_datetime=INICIO, end_datetime=local_datetime(2026, 10, 10, 9, 0), daily_price=Decimal("20.00"))
    assert (renta.rental_days, renta.total_price) == (1, Decimal("20.00"))


def test_renta_de_5_dias_cobra_5_veces_el_precio_por_dia():
    # Mesa de 20 Bs por día: recoge el 09/10 a las 18:00 y devuelve el 14/10 a las 09:00 -> 5 días, 100 Bs
    renta = Rental(start_datetime=INICIO, end_datetime=local_datetime(2026, 10, 14, 9, 0), daily_price=Decimal("20.00"))
    assert (renta.rental_days, renta.total_price) == (5, Decimal("100.00"))
