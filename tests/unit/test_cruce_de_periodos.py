"""Prueba rentals/rules.py: periods_overlap(), la regla que impide rentar dos veces un equipo (RF-01).
La renta que ya existe va del 09/10/2026 18:00 al 12/10/2026 09:00."""
from rentals.rules import periods_overlap
from tests.helpers import local_datetime

INICIO_EXISTENTE = local_datetime(2026, 10, 9, 18, 0)
FIN_EXISTENTE = local_datetime(2026, 10, 12, 9, 0)


def test_el_mismo_periodo_se_cruza():
    # Piden exactamente las mismas fechas -> se cruza
    resultado = periods_overlap(INICIO_EXISTENTE, FIN_EXISTENTE, INICIO_EXISTENTE, FIN_EXISTENTE)
    assert resultado is True


def test_un_periodo_que_empieza_dentro_de_otra_renta_se_cruza():
    # Piden del 11/10 18:00 al 13/10 09:00, dentro de la otra renta -> se cruza
    resultado = periods_overlap(
        local_datetime(2026, 10, 11, 18, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    )
    assert resultado is True


def test_un_periodo_que_contiene_a_otra_renta_se_cruza():
    # Piden del 08/10 18:00 al 13/10 09:00, que envuelve a la otra renta -> se cruza
    resultado = periods_overlap(
        local_datetime(2026, 10, 8, 18, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    )
    assert resultado is True


def test_un_periodo_que_comparte_un_minuto_se_cruza():
    # Piden desde el 12/10 08:59 y la otra termina a las 09:00 -> comparten un minuto y se cruza
    resultado = periods_overlap(
        local_datetime(2026, 10, 12, 8, 59), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    )
    assert resultado is True


def test_un_periodo_que_empieza_justo_cuando_la_otra_termina_no_se_cruza():
    # Piden desde el 12/10 09:00, justo cuando termina la otra -> no se cruza
    resultado = periods_overlap(
        local_datetime(2026, 10, 12, 9, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    )
    assert resultado is False


def test_periodos_separados_no_se_cruzan():
    # Piden del 20/10 al 22/10, lejos de la otra renta -> no se cruza
    resultado = periods_overlap(
        local_datetime(2026, 10, 20, 18, 0), local_datetime(2026, 10, 22, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    )
    assert resultado is False
