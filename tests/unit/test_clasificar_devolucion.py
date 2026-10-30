"""Prueba rentals/rules.py: clasificación del resultado de devolución y cálculo de días de atraso."""
from datetime import date
from decimal import Decimal

from rentals.models import Rental
from rentals.rules import classify_return, late_days
from rentals.statuses import ReturnResult
from tests.helpers import local_datetime

VENCE = date(2026, 10, 10)


def test_clasificacion_de_la_devolucion_por_horarios():
    # Vence el 10/10: devuelve a las 09:00 (a tiempo), entre 09:01 y 12:00 (tolerancia sin cobro), y desde 12:01 (atraso) -> umbrales de devolución
    # Comprueba que devolver a las 09:00 exactas se clasifica como a tiempo
    assert classify_return(local_datetime(2026, 10, 10, 9, 0), VENCE) == ReturnResult.ON_TIME
    # Comprueba que un minuto después de las 09:00 entra en tolerancia sin cobro
    assert classify_return(local_datetime(2026, 10, 10, 9, 1), VENCE) == ReturnResult.TOLERANCE
    # Comprueba que el último minuto de tolerancia es exactamente a las 12:00
    assert classify_return(local_datetime(2026, 10, 10, 12, 0), VENCE) == ReturnResult.TOLERANCE
    # Comprueba que pasarse al mediodía con un minuto (12:01) registra la devolución con atraso
    assert classify_return(local_datetime(2026, 10, 10, 12, 1), VENCE) == ReturnResult.LATE


def test_calculo_de_dias_de_atraso_por_multa():
    # Vence el 10/10: a las 12:00 son 0 días; a las 12:01 o al día siguiente a las 10:00 cobra 1 día; al día siguiente a las 12:01 cobra 2 días -> cómputo de multas
    # Comprueba que devolver a las 12:00 no genera días de atraso cobrables
    assert late_days(local_datetime(2026, 10, 10, 12, 0), VENCE) == 0
    # Comprueba que pasar el mediodía por un minuto cobra un día de atraso
    assert late_days(local_datetime(2026, 10, 10, 12, 1), VENCE) == 1
    # Comprueba que devolver al día siguiente a las 10:00 cobra un solo día por haber cruzado un mediodía
    assert late_days(local_datetime(2026, 10, 11, 10, 0), VENCE) == 1
    # Comprueba que devolver al día siguiente a las 12:01 cobra dos días de atraso
    assert late_days(local_datetime(2026, 10, 11, 12, 1), VENCE) == 2
    # Comprueba que devolver antes de la fecha de vencimiento no cobra días de atraso
    assert late_days(local_datetime(2026, 10, 9, 13, 0), VENCE) == 0


def renta_que_vence_el_10_10(devuelta):
    """Renta de una mesa de 20 Bs por día que vence el 10/10 a las 09:00 y volvió en el momento devuelta."""
    return Rental(
        start_datetime=local_datetime(2026, 10, 8, 18, 0),
        end_datetime=local_datetime(2026, 10, 10, 9, 0),
        returned_at=devuelta,
        daily_price=Decimal("20.00"),
    )


def test_devolucion_a_las_09_00_es_a_tiempo_sin_deuda():
    # Vence el 10/10 y vuelve a las 09:00 -> a tiempo, 0 días de atraso, sin deuda
    renta = renta_que_vence_el_10_10(local_datetime(2026, 10, 10, 9, 0))
    assert (renta.return_result, renta.late_days, renta.late_charge) == (ReturnResult.ON_TIME, 0, Decimal("0.00"))


def test_devolucion_a_las_09_01_entra_en_tolerancia_sin_deuda():
    # Vence el 10/10 y vuelve a las 09:01 -> en tolerancia, 0 días de atraso, sin deuda
    renta = renta_que_vence_el_10_10(local_datetime(2026, 10, 10, 9, 1))
    assert (renta.return_result, renta.late_days, renta.late_charge) == (ReturnResult.TOLERANCE, 0, Decimal("0.00"))


def test_devolucion_al_dia_siguiente_a_las_10_00_cobra_un_dia():
    # Vence el 10/10 y vuelve el 11/10 a las 10:00 -> con atraso, pasó un mediodía: 1 día, 20 Bs
    renta = renta_que_vence_el_10_10(local_datetime(2026, 10, 11, 10, 0))
    assert (renta.return_result, renta.late_days, renta.late_charge) == (ReturnResult.LATE, 1, Decimal("20.00"))


def test_devolucion_5_dias_despues_a_las_10_00_cobra_5_dias():
    # Vence el 10/10 y vuelve el 15/10 a las 10:00 -> con atraso, pasaron 5 mediodías: 5 días, 100 Bs
    renta = renta_que_vence_el_10_10(local_datetime(2026, 10, 15, 10, 0))
    assert (renta.return_result, renta.late_days, renta.late_charge) == (ReturnResult.LATE, 5, Decimal("100.00"))
