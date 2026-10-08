"""Business rules for renting one unit (PRE-CU-01, step 7).

Pure functions: they only compare the values they receive and never
read or write the database, so they can be tested without it.
All datetimes must be in local time (America/La_Paz); the service
converts them before calling these functions.

# ASSUMPTION: no rule rejects dates in the past. ENT-17 says there is no
# limit on how far in advance a rental can be made ("puede ser al
# instante"), and no document asks to reject past dates.
"""
from datetime import time, timedelta

from .models import EquipmentStatus

# ASSUMPTION: ENT-19 says units are handed over from 18:00 and returned
# by 09:00. It is still pending whether the client chooses the time
# (Sesión 07 §7, Sesión 08-09 §2); we let the client choose any time
# inside this window and reject times outside it.
EARLIEST_PICKUP_TIME = time(18, 0)
# ASSUMPTION: the 5-minute tolerance of ENT-31 applies when the return
# is registered (PRE-RF-02), not when the rental is requested, so the
# requested return time must be 09:00 or earlier.
LATEST_RETURN_TIME = time(9, 0)

# ASSUMPTION: ENT-18 says a rental lasts 5 days by default (2 weeks for
# frequent clients, who are not defined yet, ENT-20). It is pending
# whether a longer rental is rejected (Sesión 07 §7); we reject it.
MAX_RENTAL_DURATION = timedelta(days=5)


def periods_overlap(new_start, new_end, existing_start, existing_end) -> bool:
    """Return True if the new period overlaps an existing one (PRE-RF-01).

    A period that starts exactly when the other ends does not overlap.
    """
    # Strict "<" and ">" so that touching edges (end == start) are allowed.
    return new_start < existing_end and new_end > existing_start


def is_rentable_status(status: str) -> bool:
    """Return True if a unit with this status can be rented (PRE-RF-04).

    Only "available" units can be rented; "in review", "in repair",
    "rented" and "retired" units cannot (ENT-33).
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
