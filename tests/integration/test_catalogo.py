"""Prueba rentals/renting.py con la base: catalog_entries(), lo que ve el cliente en el catálogo
(ENT-64: el equipo dice cuándo está ocupado; una reserva cancelada no lo ocupa)."""
from django.utils import timezone

from rentals.renting import cancel_rental, catalog_entries, create_rental
from tests.helpers import dentro_de


def test_el_catalogo_muestra_el_periodo_ocupado_y_omite_la_reserva_cancelada(cl01, cl02, op01, mes01):
    # MES-00001 tiene una reserva de cl01 y otra cancelada de cl02 -> el catálogo muestra solo la de cl01
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(create_rental(cl02, mes01, dentro_de(12, 18), dentro_de(13, 9)), op01)
    [entrada] = catalog_entries(timezone.now())
    # Comprueba que la entrada es de MES-00001
    assert entrada.equipment == mes01
    # Comprueba que el único periodo ocupado es la reserva vigente
    assert entrada.busy_rentals == [reserva]
