"""Prueba rentals/rules.py: periods_overlap(), la regla que impide cruzar periodos de renta para un mismo equipo."""
from rentals.rules import periods_overlap
from tests.helpers import local_datetime

INICIO_EXISTENTE = local_datetime(2026, 10, 9, 18, 0)
FIN_EXISTENTE = local_datetime(2026, 10, 12, 9, 0)


def test_deteccion_de_cruces_y_solapamientos_de_periodos():
    # Mismo periodo exacto, periodos internos, solapamiento envolvente y coincidencia exacta de un minuto -> se cruzan correctamente
    # Comprueba que solicitar el mismo periodo exacto se detecta como solapamiento
    assert periods_overlap(INICIO_EXISTENTE, FIN_EXISTENTE, INICIO_EXISTENTE, FIN_EXISTENTE) is True
    # Comprueba que un periodo contenido totalmente dentro de otro se cruza
    assert periods_overlap(
        local_datetime(2026, 10, 11, 18, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    ) is True
    # Comprueba que un periodo que envuelve completamente al existente se cruza
    assert periods_overlap(
        local_datetime(2026, 10, 8, 18, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    ) is True
    # Comprueba que compartir un solo minuto en el límite se detecta como cruce
    assert periods_overlap(
        local_datetime(2026, 10, 12, 8, 59), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    ) is True

    # Empezar justo cuando termina la otra (sin solapar) y periodos totalmente separados -> no hay cruce
    # Comprueba que empezar justo en el instante en que termina la otra renta no genera cruce
    assert periods_overlap(
        local_datetime(2026, 10, 12, 9, 0), local_datetime(2026, 10, 13, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    ) is False
    # Comprueba que periodos futuros o lejanos sin coincidencia no se cruzan
    assert periods_overlap(
        local_datetime(2026, 10, 20, 18, 0), local_datetime(2026, 10, 22, 9, 0),
        INICIO_EXISTENTE, FIN_EXISTENTE,
    ) is False