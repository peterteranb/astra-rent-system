"""Prueba rentals/use_cases/renting.py con la base: cancel_rental(), cancelación de reservas y liberación de fechas."""
import pytest

from rentals.errors import DeadlinePassedError
from rentals.models import Rental
from rentals.statuses import RentalStatus
from rentals.use_cases.renting import cancel_rental, create_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_operaciones_de_cancelacion_de_reservas_y_plazos_limite(cl01, cl02, op01, mes01):
    # Operador o cliente cancelan con anticipación -> reserva cancelada, datos de autor/fecha guardados y fechas liberadas para otro cliente
    # Comprueba que el operador cancela una reserva y esta queda registrada con su autor, fecha y libera el equipo
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(reserva, op01)
    guardada = Rental.objects.get(pk=reserva.pk)
    assert guardada.status == RentalStatus.CANCELLED
    assert guardada.cancelled_by == op01
    assert guardada.cancelled_at is not None
    assert create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9)).client == cl02

    # Comprueba que el cliente puede cancelar su propia reserva con la debida anticipación
    reserva_cliente = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(reserva_cliente, cl01)
    guardada_cliente = Rental.objects.get(pk=reserva_cliente.pk)
    assert (guardada_cliente.status, guardada_cliente.cancelled_by) == (RentalStatus.RentalStatus if False else RentalStatus.CANCELLED, cl01)

    # Cliente intenta cancelar una reserva para el mismo día (menos de 24h) -> rechazado por plazo vencido y base intacta
    # Comprueba que la cancelación a menos de 24 horas del recojo se rechaza y no altera la base de datos
    reserva_hoy = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9))
    antes = foto_de_la_base()
    with pytest.raises(DeadlinePassedError):
        cancel_rental(reserva_hoy, cl01)
    assert foto_de_la_base() == antes