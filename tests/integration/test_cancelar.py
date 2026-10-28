"""Prueba rentals/use_cases/renting.py con la base: cancel_rental(), cancelar una reserva y liberar
sus fechas, con el plazo de 24 h del cliente (CU-07, ENT-80)."""
import pytest

from rentals.errors import DeadlinePassedError
from rentals.models import Rental
from rentals.statuses import RentalStatus
from rentals.use_cases.renting import cancel_rental, create_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_cancel_rental_guarda_quien_y_cuando_y_libera_las_fechas(cl01, cl02, op01, mes01):
    # op01 cancela la reserva de cl01 -> queda cancelada por op01 y cl02 puede rentar esas mismas fechas
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(reserva, op01)
    guardada = Rental.objects.get(pk=reserva.pk)
    # Comprueba que quedó cancelada
    assert guardada.status == RentalStatus.CANCELLED
    # Comprueba quién canceló
    assert guardada.cancelled_by == op01
    # Comprueba que se guardó cuándo
    assert guardada.cancelled_at is not None
    # Comprueba que las fechas quedaron libres para otro cliente
    assert create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9)).client == cl02


def test_el_cliente_cancela_su_reserva_de_la_proxima_semana(cl01, mes01):
    # cl01 cancela su reserva de hoy+7 -> queda cancelada por cl01
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(reserva, cl01)
    guardada = Rental.objects.get(pk=reserva.pk)
    assert (guardada.status, guardada.cancelled_by) == (RentalStatus.CANCELLED, cl01)


def test_el_cliente_no_cancela_la_reserva_de_hoy_y_la_base_no_cambia(cl01, mes01):
    # cl01 quiere cancelar su reserva de hoy a las 18:00, a menos de 24 h -> rechazado y nada cambia (ENT-80)
    reserva = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9))
    antes = foto_de_la_base()
    with pytest.raises(DeadlinePassedError):
        cancel_rental(reserva, cl01)
    assert foto_de_la_base() == antes
