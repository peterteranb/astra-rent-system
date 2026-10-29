"""Prueba rentals/use_cases/renting.py: busy_message(), generando el mensaje explicativo cuando hay un cruce de fechas."""
from rentals.models import Equipment, Rental
from rentals.use_cases.renting import busy_message
from tests.helpers import local_datetime

EQ01 = Equipment(inventory_id="MES-00001")
OTRA_RENTA = Rental(
    equipment=EQ01,
    start_datetime=local_datetime(2026, 10, 20, 18, 0),
    end_datetime=local_datetime(2026, 10, 22, 9, 0),
)


def test_generacion_de_mensajes_de_ocupacion_segun_solapamiento():
    # Petición antes de la otra renta muestra hasta cuándo está libre; petición durante o después de inicio omite la disponibilidad previa -> claridad de avisos de bloqueo
    # Comprueba que si la renta existente empieza después, el mensaje detalla el periodo ocupado y el tiempo libre previo
    mensaje_con_libre = busy_message(EQ01, OTRA_RENTA, local_datetime(2026, 10, 18, 18, 0))
    assert mensaje_con_libre == (
        "El equipo MES-00001 está ocupado del 20/10/2026 18:00 al 22/10/2026 09:00. "
        "Está libre hasta el 20/10/2026 a las 09:00."
    )

    # Comprueba que si la petición se solapa cuando la otra renta ya comenzó, el mensaje solo indica el bloqueo vigente sin fechas libres
    mensaje_sin_libre = busy_message(EQ01, OTRA_RENTA, local_datetime(2026, 10, 21, 18, 0))
    assert mensaje_sin_libre == "El equipo MES-00001 está ocupado del 20/10/2026 18:00 al 22/10/2026 09:00."