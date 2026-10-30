"""Prueba rentals/models.py: Rental.payment_label, que dice solo «Pagado» o «Pago pendiente» sin la forma de pago
(ENT-104)."""
from rentals.models import Rental
from rentals.statuses import PaymentMethod
from tests.helpers import local_datetime

PAGO = local_datetime(2026, 10, 29, 19)


def test_pagada_con_qr_dice_solo_pagado():
    # La renta se pagó con QR -> la etiqueta es «Pagado», sin «(QR)»
    assert Rental(paid_at=PAGO, payment_method=PaymentMethod.QR).payment_label == "Pagado"


def test_pagada_en_efectivo_dice_solo_pagado():
    # La renta se pagó en efectivo en la tienda -> la etiqueta es «Pagado», sin «(efectivo)»
    assert Rental(paid_at=PAGO, payment_method=PaymentMethod.CASH).payment_label == "Pagado"


def test_sin_pagar_dice_pago_pendiente():
    # La renta todavía no se pagó -> la etiqueta es «Pago pendiente»
    assert Rental().payment_label == "Pago pendiente"
