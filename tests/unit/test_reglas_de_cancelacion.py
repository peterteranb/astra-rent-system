"""Prueba rentals/use_cases/reservation_changes.py: check_can_cancel() y check_can_modify(), validando plazos y roles de cancelación."""
import pytest

from accounts.models import User
from rentals.errors import DeadlinePassedError, RentalStateError
from rentals.models import Equipment, Rental
from rentals.use_cases.reservation_changes import check_can_cancel, check_can_modify
from tests.helpers import local_datetime

MES01 = Equipment(inventory_id="MES-00001")
CL01 = User(pk=1, username="cl01")
OP01 = User(pk=2, username="op01")
INICIO = local_datetime(2026, 10, 9, 18, 0)
FIN = local_datetime(2026, 10, 12, 9, 0)
DOS_DIAS_ANTES = local_datetime(2026, 10, 7, 18, 0)
UNA_HORA_ANTES = local_datetime(2026, 10, 9, 17, 0)


def reserva(**momentos):
    """Crea una reserva de prueba con los momentos específicos solicitados."""
    return Rental(equipment=MES01, client=CL01, start_datetime=INICIO, end_datetime=FIN, **momentos)


def test_validacion_de_plazos_y_permisos_para_cancelar_o_modificar():
    # Cliente cancela con anticipación (permitido) vs una hora antes (rechazado); operador puede cancelar o modificar a una hora del inicio -> plazos y privilegios
    # Comprueba que el cliente puede cancelar con dos días de anticipación sin restricciones
    assert check_can_cancel(reserva(), CL01, DOS_DIAS_ANTES) is None

    # Comprueba que el cliente no puede cancelar en línea a una hora del recojo (plazo vencido)
    with pytest.raises(DeadlinePassedError) as error_cancel_cliente:
        check_can_cancel(reserva(), CL01, UNA_HORA_ANTES)
    assert str(error_cancel_cliente.value) == "Ya no puedes cancelar en línea; comunícate con la tienda."

    # Comprueba que el operador sí puede cancelar la reserva a una hora del inicio (el plazo restrictivo aplica solo al cliente)
    assert check_can_cancel(reserva(), OP01, UNA_HORA_ANTES) is None

    # Comprueba que el cliente no puede modificar una reserva a una hora del recojo
    with pytest.raises(DeadlinePassedError) as error_mod_cliente:
        check_can_modify(reserva(), CL01, UNA_HORA_ANTES)
    assert str(error_mod_cliente.value) == "Ya no puedes modificar en línea; comunícate con la tienda."

    # Comprueba que el operador puede modificar los detalles a una hora del inicio
    assert check_can_modify(reserva(), OP01, UNA_HORA_ANTES) is None

    # Intentar modificar tras la hora de inicio o sobre rentas ya entregadas/canceladas se rechaza -> consistencia del ciclo de vida
    # Comprueba que el operador no puede modificar una reserva una vez que la hora de inicio ya transcurrió
    with pytest.raises(DeadlinePassedError) as error_inicio:
        check_can_modify(reserva(), OP01, INICIO)
    assert str(error_inicio.value) == "La reserva de MES-00001 ya empezó el 09/10/2026 18:00; ya no se puede modificar."

    # Comprueba que una renta ya entregada no puede ser cancelada ni por el operador
    with pytest.raises(RentalStateError) as error_entregada:
        check_can_cancel(reserva(picked_up_at=local_datetime(2026, 10, 9, 18, 30)), OP01, UNA_HORA_ANTES)
    assert str(error_entregada.value) == "La renta de MES-00001 ya fue entregada el 09/10/2026 18:30."

    # Comprueba que una reserva previamente cancelada no permite una segunda cancelación redundante
    with pytest.raises(RentalStateError) as error_cancelada:
        check_can_cancel(reserva(cancelled_at=local_datetime(2026, 10, 8, 10, 0)), OP01, UNA_HORA_ANTES)
    assert str(error_cancelada.value) == "La renta de MES-00001 ya fue cancelada el 08/10/2026 10:00."