"""Prueba rentals/use_cases/payments.py con la base: pay_with_qr() y create_rental() en tienda (pagos en efectivo y QR)."""
import pytest

from rentals.errors import RentalStateError
from rentals.models import Rental
from rentals.statuses import PaymentMethod, RentalStatus
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_procesamiento_de_pagos_por_qr_efectivo_y_validaciones_de_estado(cl01, cl02, op01, mes01):
    # Pago QR aprobado registra timestamp y método QR; pago QR fallido mantiene la reserva pendiente sin alterar la base
    # Comprueba que un pago mediante QR aprobado registra exitosamente la marca de tiempo y el método de pago correspondiente
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    pay_with_qr(renta, approved=True)
    guardada = Rental.objects.get(pk=renta.pk)
    assert (guardada.paid_at is not None, guardada.payment_method) == (True, PaymentMethod.QR)

    # Comprueba que un pago por QR fallido deja la reserva intacta en estado reservado y sin modificar la base de datos
    renta_fallida = create_rental(cl01, mes01, dentro_de(12, 18), dentro_de(14, 9))
    antes_qr = foto_de_la_base()
    pay_with_qr(renta_fallida, approved=False)
    assert foto_de_la_base() == antes_qr
    assert Rental.objects.get(pk=renta_fallida.pk).status == RentalStatus.RESERVED

    # Intentar pagar una renta ya pagada se rechaza; las rentas registradas en tienda nacen pagadas en efectivo con marca temporal
    # Comprueba que reintentar el pago de una renta que ya figuraba como pagada se rechaza informando la causa
    renta_pagada = pay_with_qr(create_rental(cl01, mes01, dentro_de(17, 18), dentro_de(19, 9)), approved=True)
    antes_doble = foto_de_la_base()
    with pytest.raises(RentalStateError) as error_pagadadoble:
        pay_with_qr(renta_pagada, approved=True)
    assert str(error_pagadadoble.value) == "La renta de MES-00001 ya está pagada."
    assert foto_de_la_base() == antes_doble

    # Comprueba que una renta registrada directamente en tienda por un operador nace pagada en efectivo de forma automática
    renta_tienda = create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9), registered_by=op01)
    guardada_tienda = Rental.objects.get(pk=renta_tienda.pk)
    assert (guardada_tienda.payment_method, guardada_tienda.paid_at is not None) == (PaymentMethod.CASH, True)