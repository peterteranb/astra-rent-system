"""Prueba rentals/renting.py con la base: cancel_rental(), cancelar una reserva y liberar
sus fechas (CU-06, ENT-55)."""
from rentals.models import Rental
from rentals.renting import cancel_rental, create_rental
from rentals.statuses import RentalStatus
from tests.helpers import dentro_de


def test_cancel_rental_guarda_quien_y_cuando_y_libera_las_fechas(cl01, cl02, op01, eq01):
    # op01 cancela la reserva de cl01 -> queda cancelada por op01 y cl02 puede rentar esas mismas fechas
    reserva = create_rental(cl01, eq01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(reserva, op01)
    guardada = Rental.objects.get(pk=reserva.pk)
    # Comprueba que quedó cancelada
    assert guardada.status == RentalStatus.CANCELLED
    # Comprueba quién canceló
    assert guardada.cancelled_by == op01
    # Comprueba que se guardó cuándo
    assert guardada.cancelled_at is not None
    # Comprueba que las fechas quedaron libres para otro cliente
    assert create_rental(cl02, eq01, dentro_de(7, 18), dentro_de(9, 9)).client == cl02
