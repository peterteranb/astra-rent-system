"""Reglas puras de la renta: solo comparan los valores que reciben y nunca tocan la base.

Todas las fechas llegan en hora local (America/La_Paz); el caso de uso las convierte antes.
No se rechazan fechas pasadas: ENT-17 dice que no hay límite de anticipación («puede ser al instante»).
"""
from datetime import datetime, time, timedelta

from .statuses import EquipmentStatus, ReturnResult

# ENT-19 y ENT-52: se recoge desde las 18:00 y se devuelve hasta las 09:00.
# Son límites «desde» y «hasta»: el cliente elige cualquier hora dentro.
EARLIEST_PICKUP_TIME = time(18, 0)
LATEST_RETURN_TIME = time(9, 0)

# ENT-63: hasta las 09:00 sin multa, hasta las 12:00 con multa y desde las 12:01 un día más.
RETURN_FINE_LIMIT = time(12, 0)

# ENT-18: una renta dura como máximo 5 días (las 2 semanas del cliente frecuente siguen pendientes, ENT-20).
MAX_RENTAL_DURATION = timedelta(days=5)

# ENT-59: una reserva no recogida hasta las 12:00 del día siguiente queda libre a las 12:01.
PICKUP_DEADLINE = time(12, 0)


def periods_overlap(new_start, new_end, existing_start, existing_end) -> bool:
    """Devuelve True si el periodo nuevo se cruza con otro (RF-01)."""
    # «<» y «>» estrictos: un periodo que empieza justo cuando el otro termina no se cruza.
    return new_start < existing_end and new_end > existing_start


def is_rentable_status(status: str) -> bool:
    """Devuelve True si un equipo con este estado se puede rentar: solo «Disponible» (ENT-03, ENT-33)."""
    return status == EquipmentStatus.AVAILABLE


def ends_after_start(start, end) -> bool:
    """Devuelve True si el periodo termina después de empezar."""
    return end > start


def is_within_max_duration(start, end) -> bool:
    """Devuelve True si el periodo dura como máximo MAX_RENTAL_DURATION (ENT-18)."""
    return end - start <= MAX_RENTAL_DURATION


def is_pickup_time_allowed(start) -> bool:
    """Devuelve True si el recojo es desde EARLIEST_PICKUP_TIME (ENT-19)."""
    return start.time() >= EARLIEST_PICKUP_TIME


def is_return_time_allowed(end) -> bool:
    """Devuelve True si la devolución es hasta LATEST_RETURN_TIME (ENT-19)."""
    return end.time() <= LATEST_RETURN_TIME


def is_pickup_expired(start, now) -> bool:
    """Devuelve True si now pasó las PICKUP_DEADLINE del día siguiente al inicio (RF-03)."""
    next_day = start.date() + timedelta(days=1)
    deadline = datetime.combine(next_day, PICKUP_DEADLINE, tzinfo=start.tzinfo)
    return now > deadline


def classify_return(returned_at, due_date) -> ReturnResult:
    """Dice si una devolución del día due_date llegó a tiempo, con multa o con un día más (RF-02).

    Compara con las 09:00 de due_date y no con la hora que eligió el cliente,
    porque la regla es «hasta las 9 sin multas» (ENT-63, ENT-65).
    """
    if returned_at <= datetime.combine(due_date, LATEST_RETURN_TIME, tzinfo=returned_at.tzinfo):
        return ReturnResult.ON_TIME
    if returned_at <= datetime.combine(due_date, RETURN_FINE_LIMIT, tzinfo=returned_at.tzinfo):
        return ReturnResult.WITH_FINE
    return ReturnResult.EXTRA_DAY
