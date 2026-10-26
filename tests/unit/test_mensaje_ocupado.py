"""Prueba rentals/renting.py: busy_message(), lo que se le dice al cliente cuando las fechas chocan
(ENT-36 y ENT-51: el sistema dice cuándo está ocupado y hasta cuándo está libre)."""
from rentals.models import Equipment, Rental
from rentals.renting import busy_message
from tests.helpers import local_datetime

EQ01 = Equipment(inventory_id="EQ-01")
OTRA_RENTA = Rental(
    equipment=EQ01,
    start_datetime=local_datetime(2026, 10, 20, 18, 0),
    end_datetime=local_datetime(2026, 10, 22, 9, 0),
)


def test_si_la_otra_renta_empieza_despues_dice_hasta_cuando_esta_libre():
    # Pide desde el 18/10 y la otra renta empieza el 20/10 -> dice que está libre hasta el 20/10 a las 09:00
    mensaje = busy_message(EQ01, OTRA_RENTA, local_datetime(2026, 10, 18, 18, 0))
    assert mensaje == (
        "El equipo EQ-01 está ocupado del 20/10/2026 18:00 al 22/10/2026 09:00. "
        "Está libre hasta el 20/10/2026 a las 09:00."
    )


def test_si_la_otra_renta_empezo_antes_no_dice_hasta_cuando_esta_libre():
    # Pide desde el 21/10 y la otra renta empezó el 20/10 -> solo dice cuándo está ocupado
    mensaje = busy_message(EQ01, OTRA_RENTA, local_datetime(2026, 10, 21, 18, 0))
    assert mensaje == "El equipo EQ-01 está ocupado del 20/10/2026 18:00 al 22/10/2026 09:00."
