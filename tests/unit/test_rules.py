"""Pruebas UNITARIAS de las reglas de negocio de la renta.

Archivo que se prueba: rentals/rules.py
Tipo de prueba:        unitaria (no usa base de datos, ni paginas, ni Django por dentro).

Que es rules.py:
    Es el archivo donde viven TODAS las reglas de la renta, escritas como
    funciones "puras": reciben fechas u otros valores y devuelven True o False.
    No leen ni escriben la base de datos. Por eso estas pruebas solo llaman a la
    funcion con valores fijos y comparan la respuesta con lo esperado.

Como funciona cada prueba:
    Usamos @pytest.mark.parametrize, que repite la MISMA prueba con varias filas
    de datos. Cada fila es un caso: (entrada, resultado esperado).
    pytest muestra cada fila como un caso aparte, con el nombre que le damos en
    "ids", por ejemplo: test_cruce_de_periodos[mismo periodo].

Periodo base usado en todo el archivo (escenario de la Sesion 6, PRE-RF-01):
    C-01 ya tiene EQ-01 desde el 09/10/2026 18:00 hasta el 12/10/2026 09:00.

Las fechas se escriben sin zona horaria porque estas reglas solo comparan
horas de reloj; el servicio les entrega siempre la hora local de La Paz.
"""
from datetime import date, datetime

import pytest

from rentals.models import EquipmentStatus
from rentals.rules import (
    classify_return,
    is_pickup_time_allowed,
    is_rentable_status,
    is_return_time_allowed,
    is_within_max_duration,
    periods_overlap,
)
from rentals.statuses import ReturnResult

# Renta que ya existe: C-01 tiene EQ-01 en este periodo.
INICIO_EXISTENTE = datetime(2026, 10, 9, 18, 0)   # 09/10/2026 18:00
FIN_EXISTENTE = datetime(2026, 10, 12, 9, 0)      # 12/10/2026 09:00


@pytest.mark.parametrize(
    "nuevo_inicio, nuevo_fin, se_cruza",
    [
        (datetime(2026, 10, 9, 18, 0), datetime(2026, 10, 12, 9, 0), True),
        (datetime(2026, 10, 12, 9, 0), datetime(2026, 10, 13, 9, 0), False),
        (datetime(2026, 10, 20, 18, 0), datetime(2026, 10, 22, 9, 0), False),
    ],
    ids=[
        "mismo periodo",
        "empieza justo cuando la otra termina",
        "totalmente despues",
    ],
)
def test_cruce_de_periodos(nuevo_inicio, nuevo_fin, se_cruza):
    """Decide si una renta nueva se cruza con la renta que ya existe.

    Caso:               otro cliente pide EQ-01 en fechas que pueden chocar con las de C-01.
    Entrada:            el periodo nuevo (inicio y fin) y el periodo existente.
    Condiciones:        C-01 tiene EQ-01 del 09/10 18:00 al 12/10 09:00.
    Resultado esperado: True si comparten aunque sea un minuto; False si solo se
                        tocan en el borde o no se tocan.
    Requisito:          PRE-RF-01 (el primero en confirmar se queda el equipo;
                        una segunda renta que se cruza se rechaza).
    Codigo que cubre:   rentals/rules.py -> periods_overlap().
    Por que importa:    esta es LA regla que impide rentar dos veces el mismo
                        equipo. Los casos de borde ("justo cuando termina")
                        prueban que se usa < y > estrictos.
    """
    # Ejecutar: preguntamos a la regla si los dos periodos se cruzan
    resultado = periods_overlap(nuevo_inicio, nuevo_fin, INICIO_EXISTENTE, FIN_EXISTENTE)

    # Comprobar: la respuesta debe ser exactamente la esperada en esta fila
    assert resultado is se_cruza


@pytest.mark.parametrize(
    "estado, se_puede_rentar",
    [
        (EquipmentStatus.AVAILABLE, True),
        (EquipmentStatus.IN_REVIEW, False),
        (EquipmentStatus.RETIRED, False),
    ],
    ids=["disponible", "en revision", "baja"],
)
def test_solo_un_equipo_disponible_se_puede_rentar(estado, se_puede_rentar):
    """Decide si un equipo se puede rentar segun su estado.

    Caso:               el cliente intenta rentar un equipo que tiene cierto estado.
    Entrada:            uno de los cuatro estados del equipo.
    Condiciones:        ninguna; la regla solo mira el estado.
    Resultado esperado: True solo para "disponible"; False para los otros tres.
    Requisito:          PRE-RF-04 (un equipo en revision no se renta) y ENT-33
                        (estados del equipo). Que reparacion y baja tambien
                        bloqueen es un SUPUESTO nuestro (S-12).
    Codigo que cubre:   rentals/rules.py -> is_rentable_status().
    """
    # Ejecutar
    resultado = is_rentable_status(estado)

    # Comprobar
    assert resultado is se_puede_rentar


@pytest.mark.parametrize(
    "fin, se_permite",
    [
        (datetime(2026, 10, 12, 9, 0), True),
        (datetime(2026, 10, 14, 18, 0), True),
        (datetime(2026, 10, 14, 18, 1), False),
    ],
    ids=[
        "2 dias y 15 horas (escenario de los documentos)",
        "exactamente 5 dias (el limite se acepta)",
        "5 dias y 1 minuto (se pasa del limite)",
    ],
)
def test_una_renta_dura_como_maximo_5_dias(fin, se_permite):
    """Decide si la renta respeta la duracion maxima de 5 dias.

    Caso:               el cliente elige una fecha de devolucion lejana.
    Entrada:            recojo 09/10/2026 18:00 y distintas devoluciones.
    Condiciones:        el maximo es 5 dias (constante MAX_RENTAL_DURATION).
    Resultado esperado: hasta 5 dias exactos se permite; un minuto mas, no.
    Requisito:          ENT-18 (5 dias por defecto). Rechazar lo que pasa de
                        5 dias es un SUPUESTO nuestro (S-07).
    Codigo que cubre:   rentals/rules.py -> is_within_max_duration().
    """
    # Ejecutar
    resultado = is_within_max_duration(INICIO_EXISTENTE, fin)

    # Comprobar
    assert resultado is se_permite


@pytest.mark.parametrize(
    "recojo, se_permite",
    [
        (datetime(2026, 10, 9, 18, 0), True),
        (datetime(2026, 10, 9, 23, 59), True),
        (datetime(2026, 10, 9, 17, 59), False),
    ],
    ids=[
        "18:00 en punto",
        "23:59 (ultimo minuto del dia)",
        "17:59 (un minuto antes)",
    ],
)
def test_el_recojo_es_desde_las_18_00(recojo, se_permite):
    """Decide si la hora de recojo esta dentro del horario de entrega.

    Caso:               el cliente elige a que hora recoge el equipo.
    Entrada:            una fecha y hora de recojo.
    Condiciones:        se entrega desde las 18:00 (constante EARLIEST_PICKUP_TIME).
    Resultado esperado: de 18:00 a 23:59 se permite; antes de las 18:00 no.
                        Las 00:30 se rechaza porque en su propio dia es antes de las 18:00.
    Requisito:          ENT-19 (se entrega desde las 18:00). Rechazar en vez de
                        corregir la hora es un SUPUESTO nuestro (S-08).
    Codigo que cubre:   rentals/rules.py -> is_pickup_time_allowed().
    """
    # Ejecutar
    resultado = is_pickup_time_allowed(recojo)

    # Comprobar
    assert resultado is se_permite


@pytest.mark.parametrize(
    "devolucion, se_permite",
    [
        (datetime(2026, 10, 12, 0, 0), True),
        (datetime(2026, 10, 12, 9, 0), True),
        (datetime(2026, 10, 12, 9, 1), False),
    ],
    ids=["00:00 (medianoche)", "09:00 en punto", "09:01 (un minuto tarde)"],
)
def test_la_devolucion_es_hasta_las_09_00(devolucion, se_permite):
    """Decide si la hora de devolucion pedida esta dentro del horario.

    Caso:               el cliente elige a que hora devuelve el equipo.
    Entrada:            una fecha y hora de devolucion.
    Condiciones:        se devuelve hasta las 09:00 (constante LATEST_RETURN_TIME).
    Resultado esperado: hasta las 09:00 en punto se permite; 09:01 no.
    Requisito:          ENT-19 (devolucion hasta las 9:00). Ya no hay tolerancia de
                        5 minutos (ENT-31); la regla vigente es ENT-63/ENT-65: a las
                        09:00:01 ya hay multa.
    Codigo que cubre:   rentals/rules.py -> is_return_time_allowed().
    """
    # Ejecutar
    resultado = is_return_time_allowed(devolucion)

    # Comprobar
    assert resultado is se_permite


# Dia en que vence la renta del escenario (12/10/2026, a las 09:00).
DIA_DE_DEVOLUCION = date(2026, 10, 12)


def test_una_devolucion_a_las_09_00_esta_a_tiempo():
    """Requisito: C4 (#57) y ENT-63, se devuelve hasta las 9 sin multa.
    Caso:      la renta vence el 12/10 y el equipo vuelve el 12/10 a las 09:00.
    Esperado:  ON_TIME.
    """
    # Ejecutar
    resultado = classify_return(datetime(2026, 10, 12, 9, 0), DIA_DE_DEVOLUCION)

    # Comprobar
    assert resultado == ReturnResult.ON_TIME


def test_una_devolucion_a_las_12_00_tiene_multa():
    """Requisito: C4 (#57) y ENT-65, hasta las 12:00 se cobra multa.
    Caso:      la renta vence el 12/10 y el equipo vuelve el 12/10 a las 12:00.
    Esperado:  WITH_FINE.
    """
    # Ejecutar
    resultado = classify_return(datetime(2026, 10, 12, 12, 0), DIA_DE_DEVOLUCION)

    # Comprobar
    assert resultado == ReturnResult.WITH_FINE


def test_una_devolucion_a_las_12_01_cobra_un_dia_mas():
    """Requisito: C4 (#57) y ENT-65, desde las 12:01 se cobra un dia mas.
    Caso:      la renta vence el 12/10 y el equipo vuelve el 12/10 a las 12:01.
    Esperado:  EXTRA_DAY.
    """
    # Ejecutar
    resultado = classify_return(datetime(2026, 10, 12, 12, 1), DIA_DE_DEVOLUCION)

    # Comprobar
    assert resultado == ReturnResult.EXTRA_DAY
