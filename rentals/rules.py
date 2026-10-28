"""Reglas puras de la renta: solo comparan los valores que reciben y nunca tocan la base.

Todas las fechas llegan en hora local (America/La_Paz); el caso de uso las convierte antes.
No se rechazan fechas pasadas: ENT-17 dice que no hay límite de anticipación («puede ser al instante»).
"""
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

from .statuses import DebtReason, EquipmentStatus, ReturnResult

# ENT-19 y ENT-52: se recoge desde las 18:00 y se devuelve hasta las 09:00.
# Son límites «desde» y «hasta»: el cliente elige cualquier hora dentro.
EARLIEST_PICKUP_TIME = time(18, 0)
LATEST_RETURN_TIME = time(9, 0)

# ENT-73: de 09:00 a 12:00 es tolerancia sin cobro; desde las 12:01 hay deuda por atraso.
RETURN_TOLERANCE_LIMIT = time(12, 0)

# ENT-18 y ENT-72: como máximo 5 días, contados entre la fecha de recojo y la de devolución.
MAX_RENTAL_DAYS = 5

# ENT-80: el cliente cancela o modifica en línea hasta 24 h antes del recojo.
CLIENT_CHANGE_NOTICE = timedelta(hours=24)

# Los montos se guardan en bolivianos con centavos.
MONEY_STEP = Decimal("0.01")


def periods_overlap(new_start, new_end, existing_start, existing_end) -> bool:
    """Devuelve True si el periodo nuevo se cruza con otro (RF-01)."""
    # «<» y «>» estrictos: un periodo que empieza justo cuando el otro termina no se cruza.
    return new_start < existing_end and new_end > existing_start


def is_rentable_status(status: str) -> bool:
    """Devuelve True si un equipo con este estado se puede rentar: solo «Disponible» (ENT-03, ENT-33)."""
    return status == EquipmentStatus.AVAILABLE


def next_statuses(current) -> list:
    """Devuelve los estados a los que puede pasar un equipo: cualquiera menos el actual; desde la baja, ninguno (ENT-49, ENT-90)."""
    if current == EquipmentStatus.RETIRED:
        return []
    return [status for status in EquipmentStatus if status != current]


def ends_after_start(start, end) -> bool:
    """Devuelve True si el periodo termina después de empezar."""
    return end > start


def rental_days(start, end) -> int:
    """Devuelve los días de renta: los que hay entre la fecha de recojo y la de devolución (ENT-72)."""
    return (end.date() - start.date()).days


def is_within_max_duration(start, end) -> bool:
    """Devuelve True si la renta dura como máximo MAX_RENTAL_DAYS días (ENT-18)."""
    return rental_days(start, end) <= MAX_RENTAL_DAYS


def is_pickup_time_allowed(start) -> bool:
    """Devuelve True si el recojo es desde EARLIEST_PICKUP_TIME (ENT-19)."""
    return start.time() >= EARLIEST_PICKUP_TIME


def is_return_time_allowed(end) -> bool:
    """Devuelve True si la devolución es hasta LATEST_RETURN_TIME (ENT-19)."""
    return end.time() <= LATEST_RETURN_TIME


def start_of_day(moment):
    """Devuelve la medianoche con que empezó el día de moment."""
    return datetime.combine(moment.date(), time(0, 0), tzinfo=moment.tzinfo)


def combine_local(day, clock_time):
    """Junta una fecha y una hora de reloj en un momento de La Paz, por ejemplo el 09/10 a las 18:00."""
    # make_aware usa el TIME_ZONE del proyecto (America/La_Paz).
    return timezone.make_aware(datetime.combine(day, clock_time))


def is_pickup_expired(start, now) -> bool:
    """Devuelve True si en now ya pasó la medianoche que cierra el día de inicio (ENT-69)."""
    return now >= start_of_day(start) + timedelta(days=1)


def can_client_change(start, now) -> bool:
    """Devuelve True si faltan al menos 24 h para el recojo: el cliente aún cancela o modifica en línea (ENT-80)."""
    return now <= start - CLIENT_CHANGE_NOTICE


def charge_for(value, rate) -> Decimal:
    """Devuelve rate del valor del equipo, redondeado a centavos (0,005 sube)."""
    return (value * rate).quantize(MONEY_STEP, rounding=ROUND_HALF_UP)


def daily_price_for(value) -> Decimal:
    """Devuelve el precio por día: DAILY_RATE del valor del equipo (ENT-71)."""
    return charge_for(value, settings.DAILY_RATE)


def damage_reason_and_rate(new_status):
    """Devuelve (motivo, tasa) del daño que deja una revisión, o None si el equipo queda disponible (ENT-74)."""
    if new_status == EquipmentStatus.IN_REPAIR:
        return DebtReason.REPAIR, settings.REPAIR_CHARGE_RATE
    if new_status == EquipmentStatus.RETIRED:
        return DebtReason.RETIRED, settings.RETIRE_CHARGE_RATE
    return None


def damage_charge(value, new_status, already_charged=Decimal("0")):
    """Devuelve (motivo, monto) de la deuda que deja una revisión, o None si no hay nada que cobrar (ENT-74).

    already_charged es lo que la renta ya debe por daño: la baja después de una reparación
    cobra solo lo que falta para llegar al valor del equipo (D-06).
    """
    damage = damage_reason_and_rate(new_status)
    if damage is None:
        return None
    reason, rate = damage
    amount = cap_damage(charge_for(value, rate), value, already_charged)
    if amount == 0:
        return None
    return reason, amount


def cap_damage(amount, value, already_charged) -> Decimal:
    """Recorta amount para que las deudas por daño de una renta no sumen más que el valor del equipo (D-06)."""
    return min(amount, max(value - already_charged, Decimal("0")))


def classify_return(returned_at, due_date) -> ReturnResult:
    """Dice si una devolución del día due_date llegó a tiempo, en tolerancia o con atraso (RF-09).

    Compara con las 09:00 de due_date y no con la hora que eligió el cliente,
    porque la regla es «hasta las 9 sin multas» (ENT-65, ENT-73).
    """
    if returned_at <= datetime.combine(due_date, LATEST_RETURN_TIME, tzinfo=returned_at.tzinfo):
        return ReturnResult.ON_TIME
    if returned_at <= datetime.combine(due_date, RETURN_TOLERANCE_LIMIT, tzinfo=returned_at.tzinfo):
        return ReturnResult.TOLERANCE
    return ReturnResult.LATE


def late_days(returned_at, due_date) -> int:
    """Cuenta los mediodías (12:00) vencidos entre el día de vencimiento y returned_at (ENT-73).

    Vence el 10: vuelve el 10 a las 12:01 -> 1; el 11 a las 10:00 -> 1; el 11 a las 12:01 -> 2.
    """
    days_after_due = (returned_at.date() - due_date).days
    noon_passed = 1 if returned_at.time() > RETURN_TOLERANCE_LIMIT else 0
    return max(days_after_due + noon_passed, 0)
