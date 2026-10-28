"""Convierte equipos, rentas, deudas y usuarios en diccionarios para JSON: fechas ISO 8601 con zona y montos con dos decimales."""
from django.utils import timezone

from .. import rules


def money(amount):
    """Escribe un monto como texto con dos decimales, por ejemplo «40.00»."""
    return f"{amount.quantize(rules.MONEY_STEP)}"


def moment(value):
    """Escribe un momento en ISO 8601 con la zona de La Paz, o None si falta."""
    if value is None:
        return None
    return timezone.localtime(value).isoformat()


def user_data(user):
    """Datos públicos de un usuario: nunca la contraseña."""
    return {
        "id": user.pk,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.code,
        "role_name": user.role.name,
    }


def equipment_data(equipment):
    """Datos de un equipo con su estado y su precio por día de hoy."""
    return {
        "inventory_id": equipment.inventory_id,
        "name": equipment.name,
        "status": equipment.status,
        "status_label": equipment.get_status_display(),
        "daily_price": money(equipment.daily_price),
    }


def period_data(rental):
    """El periodo de una renta: desde cuándo se recoge y hasta cuándo se devuelve."""
    return {"start": moment(rental.start_datetime), "end": moment(rental.end_datetime)}


def catalog_entry_data(entry):
    """Un equipo del catálogo con sus próximos periodos ocupados (CU-03)."""
    return {
        **equipment_data(entry.equipment),
        "busy_periods": [period_data(rental) for rental in entry.busy_rentals],
    }


def rental_data(rental):
    """Datos de una renta con su estado calculado, su pago y sus momentos."""
    status = rental.status
    return {
        "id": rental.pk,
        "equipment": {"inventory_id": rental.equipment.inventory_id, "name": rental.equipment.name},
        "client": rental.client.username,
        **period_data(rental),
        "status": status.value,
        "status_label": status.label,
        "rental_days": rental.rental_days,
        "daily_price": money(rental.daily_price),
        "total_price": money(rental.total_price),
        "is_paid": rental.is_paid,
        "payment_label": rental.payment_label,
        "client_can_change": rental.client_can_change,
        "registered_by": username_or_none(rental.registered_by),
        "picked_up_at": moment(rental.picked_up_at),
        "returned_at": moment(rental.returned_at),
        "cancelled_at": moment(rental.cancelled_at),
    }


def debt_data(debt):
    """Datos de una deuda con su renta: cliente, equipo, motivo y monto."""
    return {
        "id": debt.pk,
        "rental_id": debt.rental_id,
        "client": debt.rental.client.username,
        "equipment": debt.rental.equipment.inventory_id,
        "reason": debt.reason,
        "reason_label": debt.get_reason_display(),
        "amount": money(debt.amount),
        "created_at": moment(debt.created_at),
        "paid_at": moment(debt.paid_at),
    }


def client_total_data(row):
    """Una fila de «quién debe cuánto»: usuario, nombre y deuda total."""
    return {
        "username": row["rental__client__username"],
        "first_name": row["rental__client__first_name"],
        "last_name": row["rental__client__last_name"],
        "total": money(row["total"]),
    }


def username_or_none(user):
    """Devuelve el usuario o None si la renta no tiene a esa persona."""
    return user.username if user else None
