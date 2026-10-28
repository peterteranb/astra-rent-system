"""Prueba rentals/use_cases/renting.py con la base: modify_rental(), cambiar las fechas de una reserva con la
misma cantidad de días (CU-06, ENT-81)."""
from decimal import Decimal

import pytest

from rentals.errors import EquipmentNotAvailableError, InvalidModificationError
from rentals.models import Rental
from rentals.use_cases.renting import create_rental, modify_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_el_cliente_mueve_su_reserva_con_los_mismos_dias(cl01, mes01):
    # cl01 mueve su reserva de 2 días de hoy+7 a hoy+10 -> se guardan las fechas nuevas y el precio no cambia
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    modify_rental(reserva, dentro_de(10, 18), dentro_de(12, 9), cl01)
    guardada = Rental.objects.get(pk=reserva.pk)
    # Comprueba las fechas nuevas
    assert (guardada.start_datetime, guardada.end_datetime) == (dentro_de(10, 18), dentro_de(12, 9))
    # Comprueba que el precio sigue igual: 2 días a 20 Bs
    assert (guardada.daily_price, guardada.total_price) == (Decimal("20.00"), Decimal("40.00"))


def test_la_reserva_se_puede_mover_sobre_sus_propias_fechas(cl01, mes01):
    # cl01 corre su reserva un día, pisando sus propias fechas -> se guarda, no choca consigo misma
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    modify_rental(reserva, dentro_de(8, 18), dentro_de(10, 9), cl01)
    assert Rental.objects.get(pk=reserva.pk).start_datetime == dentro_de(8, 18)


def test_cambiar_la_cantidad_de_dias_se_rechaza_y_la_base_no_cambia(cl01, mes01):
    # cl01 tiene 2 días y pide 3 -> rechazado con qué hacer y no se guarda nada (ENT-81)
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    antes = foto_de_la_base()
    with pytest.raises(InvalidModificationError) as error:
        modify_rental(reserva, dentro_de(7, 18), dentro_de(10, 9), cl01)
    # Comprueba el mensaje con los días y qué hacer
    assert str(error.value) == (
        "La reserva es de 2 días. Elige fechas con la misma cantidad de días; "
        "para cambiarla, cancela y renta de nuevo."
    )
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_mover_la_reserva_sobre_otra_renta_se_rechaza(cl01, cl02, mes01):
    # cl02 tiene MES-00001 de hoy+12 a hoy+14 y cl01 quiere mover la suya ahí -> rechazado y nada cambia
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    create_rental(cl02, mes01, dentro_de(12, 18), dentro_de(14, 9))
    antes = foto_de_la_base()
    with pytest.raises(EquipmentNotAvailableError):
        modify_rental(reserva, dentro_de(12, 18), dentro_de(14, 9), cl01)
    assert foto_de_la_base() == antes
