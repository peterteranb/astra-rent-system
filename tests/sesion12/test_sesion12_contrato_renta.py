"""Sesion 12: contrato de la operacion create_rental (PRE-CU-01, rentar en linea).

Interfaz que se comprueba:
    rentals/services.py -> create_rental(client, equipment, start_datetime, end_datetime)
    - Si acepta: devuelve la Rental y guarda UNA fila nueva; no toca nada mas.
    - Si rechaza: lanza un RentalRejectedError (E1 = EquipmentNotAvailableError)
      y la base queda IGUAL que antes.

Las pruebas llaman directo a la operacion (sin navegador ni teclado) y revisan
la respuesta y los datos guardados. Usan la base temporal test_astra_rent que
crea pytest-django (en CI, un PostgreSQL temporal de GitHub). Los datos salen
de las fixtures de tests/conftest.py.
"""
import pytest

from rentals.errors import EquipmentNotAvailableError, InvalidPeriodError
from rentals.models import EquipmentStatus, Rental
from rentals.services import create_rental
from tests.helpers import foto_de_la_base, local_datetime

pytestmark = pytest.mark.django_db


def test_aceptacion_c01_renta_eq01_y_solo_se_agrega_esa_renta(c01, eq01, eq02, doc_start, doc_end):
    """Aceptacion: C-01 renta EQ-01 del 09/10/2026 18:00 al 12/10/2026 09:00.

    Requisito: PRE-RF-01 caso normal, PRE-CU-01 pasos 5 a 9.
    Esperado:  devuelve la renta; hay UNA renta con esos datos; EQ-01 sigue
               disponible (S-11) y EQ-02 no cambia.
    """
    # Preparar
    _, equipos_antes, _ = foto_de_la_base()

    # Ejecutar
    renta = create_rental(c01, eq01, doc_start, doc_end)

    # Comprobar: la respuesta
    assert renta.pk is not None
    assert (renta.client, renta.equipment) == (c01, eq01)

    # Comprobar: los datos guardados
    guardada = Rental.objects.get()                     # falla si hay 0 o mas de 1
    assert guardada.pk == renta.pk
    assert (guardada.start_datetime, guardada.end_datetime) == (doc_start, doc_end)

    # Comprobar: lo demas se conserva (los equipos no cambian de estado)
    _, equipos_despues, _ = foto_de_la_base()
    assert equipos_despues == equipos_antes
    eq01.refresh_from_db()
    assert eq01.status == EquipmentStatus.AVAILABLE


@pytest.mark.parametrize("quien_repite", ["c01", "c02"], ids=["C-01 repite (doble clic)", "C-02 llega segundo (E1)"])
def test_rechazo_y_repeticion_no_crean_otra_renta_ni_cambian_nada(
    request, c01, c02, eq01, doc_start, doc_end, quien_repite
):
    """Rechazo/repeticion: EQ-01 ya esta rentado en ese periodo y alguien lo pide otra vez.

    Requisito: PRE-CU-01 excepcion E1, PRE-RF-01 (rechazo), PRE-RC-01 (mensaje con la causa).
    Esperado:  EquipmentNotAvailableError con equipo y fechas; la base queda
               identica a la copia tomada antes del intento.
    """
    # Preparar
    create_rental(c01, eq01, doc_start, doc_end)
    antes = foto_de_la_base()
    cliente = request.getfixturevalue(quien_repite)

    # Ejecutar y comprobar la respuesta
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(cliente, eq01, doc_start, doc_end)
    assert "EQ-01" in str(error.value)
    assert "09/10/2026 18:00" in str(error.value)

    # Comprobar: nada cambio
    assert foto_de_la_base() == antes
    assert Rental.objects.count() == 1


def test_limite_la_renta_mas_larga_permitida_se_acepta_y_un_dia_mas_se_rechaza(
    c01, eq01, doc_start
):
    """Limite: la renta mas larga posible dentro de 5 dias.

    Con recojo desde las 18:00 y devolucion hasta las 09:00, la renta mas larga
    es del 09/10/2026 18:00 al 14/10/2026 09:00 (4 dias y 15 horas). Un dia mas
    (15/10 09:00) pasa los 5 dias y se rechaza.
    Requisito: limite de 5 dias y horario 18:00/09:00 (ENT-19; confirmar IDs vigentes).
    Esperado:  la mas larga se guarda; la de un dia mas lanza InvalidPeriodError
               y no agrega nada.
    """
    # Ejecutar: un dia de mas -> rechazo sin cambios
    antes = foto_de_la_base()
    with pytest.raises(InvalidPeriodError):
        create_rental(c01, eq01, doc_start, local_datetime(2026, 10, 15, 9, 0))
    assert foto_de_la_base() == antes

    # Ejecutar: justo en el limite -> se acepta
    fin_limite = local_datetime(2026, 10, 14, 9, 0)
    renta = create_rental(c01, eq01, doc_start, fin_limite)

    # Comprobar: la respuesta y el dato guardado
    guardada = Rental.objects.get()
    assert guardada.pk == renta.pk
    assert (guardada.start_datetime, guardada.end_datetime) == (doc_start, fin_limite)