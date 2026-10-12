"""Pruebas UNITARIAS de la revision del periodo pedido.

Archivo que se prueba: rentals/services.py -> check_period()
Tipo de prueba:        unitaria (no usa base de datos).

Que hace check_period():
    Antes de guardar una renta, el servicio revisa si el PERIODO pedido es valido,
    sin importar que equipo sea. Revisa, en este orden:
        1. que la devolucion sea despues del recojo,
        2. que no dure mas de 5 dias,
        3. que el recojo sea desde las 18:00,
        4. que la devolucion sea hasta las 09:00.
    Si algo falla, LANZA un error (una excepcion) con un mensaje en espanol para el
    cliente. Si todo esta bien, no devuelve nada (None).

Diferencia con test_rules.py:
    test_rules.py prueba cada regla suelta (True o False).
    Este archivo prueba que el servicio usa esas reglas y que el cliente recibe
    el TIPO de error correcto y el MENSAJE exacto que vera en pantalla.

Como se comprueba un error (sin "pytest.raises" vacio):
    with pytest.raises(...) as error:  -> atrapa el error que se lanza
    assert type(error.value) is ...    -> comprueba que es el tipo esperado
    assert str(error.value) == "..."   -> comprueba el mensaje exacto
"""
import pytest

from rentals.errors import InvalidPeriodError, OutsideRentalHoursError, RentalRejectedError
from rentals.services import check_period
from tests.helpers import local_datetime

# Periodo del escenario de los documentos (Sesion 6, PRE-RF-01), en hora de La Paz.
RECOJO = local_datetime(2026, 10, 9, 18, 0)        # 09/10/2026 18:00
DEVOLUCION = local_datetime(2026, 10, 12, 9, 0)    # 12/10/2026 09:00


def test_el_periodo_de_los_documentos_es_valido():
    """El periodo del escenario de los documentos pasa todas las revisiones.

    Caso:               C-01 pide del 09/10/2026 18:00 al 12/10/2026 09:00.
    Entrada:            recojo 09/10 18:00, devolucion 12/10 09:00.
    Condiciones:        dura 2 dias y 15 horas; las horas estan dentro del horario.
    Resultado esperado: no lanza ningun error; devuelve None.
    Requisito:          PRE-RF-01 (caso normal) y ENT-18, ENT-19.
    Codigo que cubre:   rentals/services.py -> check_period().
    """
    # Ejecutar
    resultado = check_period(RECOJO, DEVOLUCION)

    # Comprobar: si no hubo error, la funcion termina y devuelve None
    assert resultado is None


@pytest.mark.parametrize(
    "recojo, devolucion, error_esperado, mensaje_esperado",
    [
        (
            DEVOLUCION,
            RECOJO,
            InvalidPeriodError,
            "La fecha y hora de devolución debe ser posterior a la de recojo.",
        ),
        (
            RECOJO,
            local_datetime(2026, 10, 15, 9, 0),
            InvalidPeriodError,
            "La renta no puede durar más de 5 días.",
        ),
        (
            local_datetime(2026, 10, 9, 17, 0),
            DEVOLUCION,
            OutsideRentalHoursError,
            "El recojo debe ser desde las 18:00.",
        ),
        (
            RECOJO,
            local_datetime(2026, 10, 12, 10, 0),
            OutsideRentalHoursError,
            "La devolución debe ser hasta las 09:00.",
        ),
    ],
    ids=[
        "devolucion antes del recojo",
        "mas de 5 dias (09/10 al 15/10)",
        "recojo a las 17:00",
        "devolucion a las 10:00",
    ],
)
def test_un_periodo_invalido_se_rechaza_con_su_mensaje(
    recojo, devolucion, error_esperado, mensaje_esperado
):
    """Un periodo que rompe una regla se rechaza con el error y el mensaje correctos.

    Caso:               el cliente pide fechas u horas que no cumplen una regla.
    Entrada:            un recojo y una devolucion (cada fila rompe una regla distinta).
    Condiciones:        ninguna renta previa; solo se revisa el periodo.
    Resultado esperado: se lanza el tipo de error de la fila y su mensaje exacto.
    Requisito:          ENT-18 (5 dias), ENT-19 (18:00 y 09:00) y PRE-RC-01
                        (el rechazo dice la causa concreta, no solo "Error").
    Codigo que cubre:   rentals/services.py -> check_period(), que usa rules.py,
                        y las clases de rentals/errors.py.
    """
    # Ejecutar: atrapamos cualquier rechazo (todos heredan de RentalRejectedError)
    with pytest.raises(RentalRejectedError) as error:
        check_period(recojo, devolucion)

    # Comprobar: el tipo exacto de error y el mensaje que vera el cliente
    assert type(error.value) is error_esperado
    assert str(error.value) == mensaje_esperado