"""Textos para el usuario que comparten los casos de uso, las páginas y la API: fechas, montos, estados y avisos de éxito."""
from django.utils import timezone
from django.utils.formats import number_format

from ..statuses import RentalStatus, ReturnResult


def local_text(moment):
    """Escribe un momento como «dd/mm/aaaa hh:mm» en hora de La Paz."""
    return f"{timezone.localtime(moment):%d/%m/%Y %H:%M}"


def money_text(amount):
    """Escribe un monto en bolivianos con coma decimal, por ejemplo «40,00 Bs»."""
    return f"{number_format(amount, 2, force_grouping=True)} Bs"


def days_text(days):
    """Escribe una cantidad de días con su plural, por ejemplo «1 día» o «3 días»."""
    return f"{days} día" + ("s" if days > 1 else "")


def client_debt_message(total):
    """Le dice al cliente cuánto debe y qué hacer para volver a rentar (ENT-77)."""
    return f"Tienes una deuda pendiente de {money_text(total)}. Págala en la tienda para volver a rentar."


def rental_state_message(rental, status):
    """Dice por qué la renta ya no está «Reservada», con el momento en que dejó de estarlo."""
    inventory_id = rental.equipment.inventory_id
    if status == RentalStatus.CANCELLED:
        return f"La renta de {inventory_id} ya fue cancelada el {local_text(rental.cancelled_at)}."
    if status == RentalStatus.RETURNED:
        return f"La renta de {inventory_id} ya fue devuelta el {local_text(rental.returned_at)}."
    if status == RentalStatus.RENTED:
        return f"La renta de {inventory_id} ya fue entregada el {local_text(rental.picked_up_at)}."
    return f"La reserva de {inventory_id} venció a la medianoche."


def account_created_message(user):
    """Aviso de la cuenta creada en la web: ya puede iniciar sesión."""
    return f"Cuenta creada. Ya puedes iniciar sesión con {user.username}."


def store_account_message(registration):
    """Aviso de la cuenta creada en la tienda: si salió el correo para crear la contraseña o qué hacer si no (ENT-102)."""
    if not registration.email_sent:
        return (
            "La cuenta se creó, pero no se pudo enviar el correo. "
            'Pide al cliente que use "Olvidé mi contraseña" con su correo.'
        )
    return (
        f"Cuenta creada para {registration.user.username}. Le enviamos un correo para crear su contraseña. "
        "Ya puedes registrar su renta."
    )


def equipment_registered_message(equipment):
    """Aviso del equipo nuevo, con su código y su nombre."""
    return f"Equipo registrado: {equipment}."


def payment_result_message(approved):
    """Dice al cliente si el pago QR se completó o si paga al recoger (ENT-67)."""
    if approved:
        return "Pago recibido. Tu renta está confirmada."
    return "Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo."


def modified_message(rental):
    """Aviso de una reserva modificada, con sus fechas nuevas."""
    return (
        f"Reserva modificada: {rental.equipment.inventory_id} ahora va del "
        f"{local_text(rental.start_datetime)} al {local_text(rental.end_datetime)}."
    )


def cancelled_message(rental):
    """Aviso de una reserva cancelada."""
    return f"Reserva cancelada: {rental.equipment.inventory_id} de {rental.client.username}."


def pickup_message(rental, was_pending):
    """Aviso del recojo; si se cobró en ese momento, empieza con el cobro."""
    handed_over = f"{rental.equipment.inventory_id} entregado a {rental.client.username}."
    if was_pending:
        return f"Cobro de {money_text(rental.total_price)} en efectivo y recojo registrados: {handed_over}"
    return f"Recojo registrado: {handed_over}"


def return_message(rental):
    """Aviso de una devolución, que termina con cómo llegó y, con atraso, la deuda (RF-09)."""
    received = f"Devolución registrada: {rental.equipment.inventory_id} recibido de {rental.client.username}."
    if rental.return_result != ReturnResult.LATE:
        return f"{received} {rental.return_result.label}."
    return f"{received} Con {days_text(rental.late_days)} de atraso: deuda de {money_text(rental.late_charge)}."


def debt_paid_message(debt):
    """Aviso del pago de una deuda en la tienda."""
    return f"Pago registrado: deuda de {money_text(debt.amount)} de {debt.rental.client.username}."


def charge_label(rental):
    """Texto de la casilla de mantenimiento, por ejemplo «Cobrar el daño al último cliente (cl02, renta del 25/10)»."""
    start = timezone.localtime(rental.start_datetime)
    return f"Cobrar el daño al último cliente ({rental.client.username}, renta del {start:%d/%m})"


def review_message(outcome):
    """Aviso de la revisión: el estado nuevo, la deuda y las reservas canceladas."""
    change = outcome.change
    message = f"{change.equipment.inventory_id} ahora está «{change.get_new_status_display()}»."
    if outcome.debt:
        message += f" Deuda de {money_text(outcome.debt.amount)} para {outcome.debt.rental.client.username}."
    if outcome.cancelled:
        message += f" Reservas futuras canceladas: {len(outcome.cancelled)}."
    return message
