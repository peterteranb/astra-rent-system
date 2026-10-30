"""Prueba rentals/models.py: Rental.payment_label, que dice solo «Pagado» o «Pago pendiente» sin la forma de pago
(ENT-104)."""
import pytest

from rentals.models import Rental
from rentals.statuses import PaymentMethod
from tests.helpers import local_datetime

PAGO = local_datetime(2026, 10, 29, 19)


@pytest.mark.parametrize(
    ("pagada_el", "forma", "etiqueta"),
    [(PAGO, PaymentMethod.QR, "Pagado"), (PAGO, PaymentMethod.CASH, "Pagado"), (None, "", "Pago pendiente")],
)
def test_la_etiqueta_de_pago_no_dice_la_forma_de_pago(pagada_el, forma, etiqueta):
    # Pagada con QR o en efectivo -> «Pagado», sin la forma; sin pagar -> «Pago pendiente»
    assert Rental(paid_at=pagada_el, payment_method=forma).payment_label == etiqueta
