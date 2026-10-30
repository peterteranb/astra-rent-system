"""Prueba rentals/services/events.py: rental_context(), los datos de una renta que lleva cada línea del log
(ENT-101: cada línea se entiende sin buscar en la base)."""
from decimal import Decimal

from accounts.models import User
from rentals.models import Equipment, Rental
from rentals.services.events import log_event, rental_context
from tests.helpers import local_datetime

SILLA = Equipment(inventory_id="SIL-00003", name="Silla blanca plegable")
CARLA = User(username="cl01", first_name="Carla", last_name="Mendoza")
INICIO = local_datetime(2026, 10, 30, 18)
FIN = local_datetime(2026, 11, 1, 9)


def test_una_renta_guardada_lleva_id_equipo_cliente_periodo_monto_y_quien(caplog):
    # La renta 60 de 2 días a 4 Bs la paga cl01 -> la línea dice todo, como el ejemplo del cliente
    renta = Rental(pk=60, equipment=SILLA, client=CARLA, start_datetime=INICIO, end_datetime=FIN, daily_price=Decimal("4.00"))
    log_event("PAYMENT_APPROVED", **rental_context(renta, "cl01"))
    assert caplog.messages == [
        (
            'PAYMENT_APPROVED rental=60 equipment=SIL-00003 "Silla blanca plegable" client=cl01 "Carla Mendoza" '
            "period=30/10/2026 18:00-01/11/2026 09:00 amount=8.00 by=cl01"
        )
    ]


def test_un_pedido_sin_guardar_no_lleva_id_ni_monto():
    # Un pedido rechazado todavía no tiene id ni precio -> solo equipo, cliente, periodo y quién
    pedido = Rental(equipment=SILLA, client=CARLA, start_datetime=INICIO, end_datetime=FIN)
    assert list(rental_context(pedido, "cl01")) == ["equipment", "client", "period", "by"]
