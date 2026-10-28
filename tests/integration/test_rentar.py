"""Prueba rentals/renting.py con la base: create_rental() en línea y en tienda (CU-01, CU-02)
y find_clients(), la búsqueda de clientes del operador (RF-06)."""
from decimal import Decimal

import pytest

from rentals.errors import EquipmentNotAvailableError
from rentals.models import Equipment, Rental
from rentals.renting import cancel_rental, create_rental, find_clients
from rentals.statuses import RentalStatus
from tests.helpers import dentro_de, foto_de_la_base


def test_create_rental_guarda_una_reserva(cl01, mes01):
    # cl01 pide MES-00001 de hoy+7 18:00 a hoy+9 09:00 y está libre -> se guarda una renta «Reservada»
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    guardada = Rental.objects.get()
    # Comprueba que la renta devuelta es la guardada
    assert guardada.pk == renta.pk
    # Comprueba el cliente, el equipo y las fechas guardadas
    assert (guardada.client, guardada.equipment, guardada.start_datetime, guardada.end_datetime) == (
        cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)
    )
    # Comprueba que nace reservada
    assert guardada.status == RentalStatus.RESERVED


def test_el_precio_por_dia_se_fija_al_rentar_y_no_cambia_con_el_valor(cl01, mes01):
    # MES-00001 vale 400 Bs al rentar y después sube a 500 Bs -> la renta sigue a 20 Bs por día (ENT-71)
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    Equipment.objects.filter(pk=mes01.pk).update(value=Decimal("500.00"))
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba el precio por día y el total de 2 días
    assert (guardada.daily_price, guardada.total_price) == (Decimal("20.00"), Decimal("40.00"))


def test_un_cruce_de_fechas_se_rechaza_y_la_base_no_cambia(cl01, cl02, mes01):
    # cl01 ya tiene MES-00001 de hoy+7 a hoy+9 y cl02 pide hoy+8 -> rechazado y no se guarda nada (RF-01)
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    antes = foto_de_la_base()
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(cl02, mes01, dentro_de(8, 18), dentro_de(9, 9))
    # Comprueba que el mensaje nombra el equipo ocupado
    assert "El equipo MES-00001 está ocupado del" in str(error.value)
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_las_fechas_de_una_reserva_cancelada_se_pueden_rentar(cl01, cl02, op01, mes01):
    # La reserva de cl01 se canceló y cl02 pide las mismas fechas -> se guarda (ENT-55)
    cancel_rental(create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)), op01)
    renta = create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9))
    # Comprueba que la renta nueva quedó guardada a nombre de cl02
    assert Rental.objects.get(pk=renta.pk).client == cl02
    # Comprueba que en la base hay dos rentas: la cancelada y la nueva
    assert Rental.objects.count() == 2


def test_se_lo_lleva_ahora_nace_rentada_con_el_operador_que_entrego(cl02, op01, mes01):
    # op01 registra en tienda una renta de cl02 y marca «Se lo lleva ahora» -> nace «Rentada» (ENT-57)
    renta = create_rental(
        cl02, mes01, dentro_de(0, 18), dentro_de(2, 9), registered_by=op01, picked_up_now=True
    )
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba que está rentada
    assert guardada.status == RentalStatus.RENTED
    # Comprueba quién la registró y quién la entregó
    assert (guardada.registered_by, guardada.handed_over_by) == (op01, op01)


def test_find_clients_encuentra_por_apellido_y_no_devuelve_personal(cl01, cl02, op01):
    # op01 busca «rojas» y luego «op01» -> encuentra a Diego Rojas y nunca a alguien del personal
    # Comprueba que encuentra al cliente por su apellido
    assert list(find_clients("rojas")) == [cl02]
    # Comprueba que el operador no aparece aunque su usuario coincida
    assert list(find_clients("op01")) == []
