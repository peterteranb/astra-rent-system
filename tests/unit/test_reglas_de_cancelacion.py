"""Prueba rentals/use_cases/renting.py: check_can_cancel() y check_can_modify(), quién cancela o modifica una reserva
y hasta cuándo (ENT-80, ENT-95), con rentas sin guardar del 09/10/2026 18:00 al 12/10/2026 09:00."""
import pytest

from accounts.models import User
from rentals.errors import DeadlinePassedError, RentalStateError
from rentals.models import Equipment, Rental
from rentals.use_cases.renting import check_can_cancel, check_can_modify
from tests.helpers import local_datetime

MES01 = Equipment(inventory_id="MES-00001")
CL01 = User(pk=1, username="cl01")
OP01 = User(pk=2, username="op01")
INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)
DOS_DIAS_ANTES = local_datetime(2026, 10, 7, 18, 0)
UNA_HORA_ANTES = local_datetime(2026, 10, 9, 17, 0)


def reserva(**momentos):
    """Reserva de cl01 para MES-00001, con los momentos que se pidan."""
    return Rental(equipment=MES01, client=CL01, start_datetime=INICIO, end_datetime=FIN, **momentos)


def test_el_cliente_cancela_su_reserva_con_dos_dias_de_anticipacion():
    # cl01 cancela el 07/10, dos días antes del recojo -> se puede, no lanza error
    assert check_can_cancel(reserva(), CL01, DOS_DIAS_ANTES) is None


def test_el_cliente_no_cancela_una_hora_antes():
    # cl01 cancela el 09/10 a las 17:00, a una hora del recojo -> rechazado con qué hacer (ENT-80)
    with pytest.raises(DeadlinePassedError) as error:
        check_can_cancel(reserva(), CL01, UNA_HORA_ANTES)
    assert str(error.value) == "Ya no puedes cancelar en línea; comunícate con la tienda."


def test_el_operador_cancela_una_hora_antes():
    # op01 cancela la reserva de cl01 a una hora del recojo -> se puede, el plazo es solo del cliente
    assert check_can_cancel(reserva(), OP01, UNA_HORA_ANTES) is None


def test_el_cliente_no_modifica_una_hora_antes():
    # cl01 quiere cambiar las fechas a una hora del recojo -> rechazado con qué hacer (ENT-80)
    with pytest.raises(DeadlinePassedError) as error:
        check_can_modify(reserva(), CL01, UNA_HORA_ANTES)
    assert str(error.value) == "Ya no puedes modificar en línea; comunícate con la tienda."


def test_el_operador_modifica_una_hora_antes():
    # op01 cambia las fechas de la reserva de cl01 a una hora del inicio -> se puede (ENT-95)
    assert check_can_modify(reserva(), OP01, UNA_HORA_ANTES) is None


def test_el_operador_no_modifica_cuando_la_reserva_ya_empezo():
    # Son las 18:00 del 09/10, la hora de inicio, y op01 quiere cambiar las fechas -> rechazado (ENT-95: solo antes de que empiece)
    with pytest.raises(DeadlinePassedError) as error:
        check_can_modify(reserva(), OP01, INICIO)
    assert str(error.value) == "La reserva de MES-00001 ya empezó el 09/10/2026 18:00; ya no se puede modificar."


def test_una_renta_entregada_no_se_puede_cancelar():
    # El cliente se la llevó el 09/10 a las 18:30 -> ni el operador la cancela, y el mensaje dice cuándo
    with pytest.raises(RentalStateError) as error:
        check_can_cancel(reserva(picked_up_at=local_datetime(2026, 10, 9, 18, 30)), OP01, UNA_HORA_ANTES)
    assert str(error.value) == "La renta de MES-00001 ya fue entregada el 09/10/2026 18:30."


def test_una_renta_ya_cancelada_no_se_puede_cancelar_otra_vez():
    # Se canceló el 08/10 a las 10:00 -> no se cancela otra vez
    with pytest.raises(RentalStateError) as error:
        check_can_cancel(reserva(cancelled_at=local_datetime(2026, 10, 8, 10, 0)), OP01, UNA_HORA_ANTES)
    assert str(error.value) == "La renta de MES-00001 ya fue cancelada el 08/10/2026 10:00."
