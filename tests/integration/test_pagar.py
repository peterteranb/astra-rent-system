"""Prueba rentals/payments.py con la base: pay_with_qr(), el QR simulado de la renta en línea (CU-04,
ENT-66, ENT-67), y create_rental() en tienda, que nace pagada en efectivo (CU-05, ENT-70)."""
import pytest

from rentals.errors import RentalStateError
from rentals.models import Rental
from rentals.payments import pay_with_qr
from rentals.renting import create_rental
from rentals.statuses import PaymentMethod, RentalStatus
from tests.helpers import dentro_de, foto_de_la_base


def test_el_pago_qr_exitoso_guarda_la_hora_y_el_metodo(cl01, mes01):
    # cl01 reserva MES-00001 y el QR se aprueba -> la renta queda pagada con QR
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    pay_with_qr(renta, approved=True)
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba que se guardó la hora del pago y el método
    assert (guardada.paid_at is not None, guardada.payment_method) == (True, PaymentMethod.QR)


def test_el_pago_qr_fallido_deja_la_reserva_hecha_con_el_pago_pendiente(cl01, mes01):
    # cl01 reserva MES-00001 y el QR falla -> la reserva sigue y nada cambia en la base (ENT-67)
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    antes = foto_de_la_base()
    pay_with_qr(renta, approved=False)
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes
    # Comprueba que la reserva sigue reservada
    assert Rental.objects.get(pk=renta.pk).status == RentalStatus.RESERVED


def test_una_renta_ya_pagada_no_se_paga_otra_vez(cl01, mes01):
    # cl01 ya pagó con QR y vuelve a presionar el botón -> rechazado y la base no cambia
    renta = pay_with_qr(create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)), approved=True)
    antes = foto_de_la_base()
    with pytest.raises(RentalStateError) as error:
        pay_with_qr(renta, approved=True)
    # Comprueba el mensaje con la causa
    assert str(error.value) == "La renta de MES-00001 ya está pagada."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_la_renta_en_tienda_nace_pagada_en_efectivo(cl02, op01, mes01):
    # op01 registra en la tienda una renta de cl02 -> nace pagada en efectivo (ENT-70)
    renta = create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9), registered_by=op01)
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba la forma de pago y que tiene la hora del pago
    assert (guardada.payment_method, guardada.paid_at is not None) == (PaymentMethod.CASH, True)
