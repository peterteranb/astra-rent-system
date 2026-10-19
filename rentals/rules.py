"""Business rules for renting one unit (PRE-CU-01, step 7).

Pure functions: they only compare the values they receive and never
read or write the database, so they can be tested without it.
All datetimes must be in local time (America/La_Paz); the service
converts them before calling these functions.

# ASSUMPTION: no rule rejects dates in the past. ENT-17 says there is no
# limit on how far in advance a rental can be made ("puede ser al
# instante"), and no document asks to reject past dates.
"""
from datetime import datetime, time, timedelta

from .statuses import EquipmentStatus, ReturnResult

# ENT-19 and ENT-52: units are picked up from 18:00 and returned by 09:00.
# They are "from" and "until" limits, so the client may choose any time
# inside this window, and times outside it are rejected.
EARLIEST_PICKUP_TIME = time(18, 0)
LATEST_RETURN_TIME = time(9, 0)

# ENT-63 and ENT-65 (client, 17/10): "tienen q devolver el equipo hasta las 9
# sin multas"; after 09:00 and until 12:00 a fine is charged, and from 12:01
# one more day. There is no tolerance: 09:00:01 already has a fine.
RETURN_FINE_LIMIT = time(12, 0)

# ASSUMPTION: ENT-18 says a rental lasts 5 days by default (2 weeks for
# frequent clients, who are not defined yet, ENT-20). It is pending
# whether a longer rental is rejected (Sesión 07 §7); we reject it.
MAX_RENTAL_DURATION = timedelta(days=5)

# Client, 17/10: "Si el equipo no es recogido hasta las doce del dia queda
# disponible para ser rentado por otros"; "el sistema detecta por la hora
# que sigue en reserva y lo cambia a las 12:01". So 12:00 is still on time.
PICKUP_DEADLINE = time(12, 0)


def periods_overlap(new_start, new_end, existing_start, existing_end) -> bool:
    """Return True if the new period overlaps an existing one (PRE-RF-01).

    A period that starts exactly when the other ends does not overlap.
    """
    # Strict "<" and ">" so that touching edges (end == start) are allowed.
    return new_start < existing_end and new_end > existing_start


def is_rentable_status(status: str) -> bool:
    """Return True if a unit with this status can be rented (PRE-RF-04).

    Only "available" units can be rented; "in review", "in repair"
    and "retired" units cannot (ENT-33).
    """
    return status == EquipmentStatus.AVAILABLE


def ends_after_start(start, end) -> bool:
    """Return True if the period ends strictly after it starts."""
    return end > start


def is_within_max_duration(start, end) -> bool:
    """Return True if the period lasts at most MAX_RENTAL_DURATION (ENT-18)."""
    return end - start <= MAX_RENTAL_DURATION


def is_pickup_time_allowed(start) -> bool:
    """Return True if the pickup time is at or after EARLIEST_PICKUP_TIME (ENT-19)."""
    return start.time() >= EARLIEST_PICKUP_TIME


def is_return_time_allowed(end) -> bool:
    """Return True if the return time is at or before LATEST_RETURN_TIME (ENT-19)."""
    return end.time() <= LATEST_RETURN_TIME


def is_pickup_expired(start, now) -> bool:
    """Return True if now is past PICKUP_DEADLINE of the day after start."""
    next_day = start.date() + timedelta(days=1)
    deadline = datetime.combine(next_day, PICKUP_DEADLINE, tzinfo=start.tzinfo)
    return now > deadline


def classify_return(returned_at, due_date) -> ReturnResult:
    """Say whether a return on due_date was on time, with a fine or charged one more day (C4).

    It compares with 09:00 of due_date, not with the return time the client
    chose, because the client's rule is "hasta las 9 sin multas" (ENT-63).
    """
    if returned_at <= datetime.combine(due_date, LATEST_RETURN_TIME, tzinfo=returned_at.tzinfo):
        return ReturnResult.ON_TIME
    if returned_at <= datetime.combine(due_date, RETURN_FINE_LIMIT, tzinfo=returned_at.tzinfo):
        return ReturnResult.WITH_FINE
    return ReturnResult.EXTRA_DAY
