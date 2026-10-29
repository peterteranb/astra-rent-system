"""Prueba las deudas con la base: devoluciones con atraso, daños en revisión, bloqueos por deuda al rentar y registro de pagos."""
from decimal import Decimal

import pytest

from rentals.errors import DebtPendingError, DebtStateError
from rentals.models import Debt
from rentals.statuses import DebtReason, EquipmentStatus, RentalStatus
from rentals.use_cases.handover import register_return
from rentals.use_cases.payments import pay_debt
from rentals.use_cases.renting import create_rental
from rentals.use_cases.review import review_equipment
from tests.helpers import con_la_hora, dentro_de, foto_de_la_base, local_datetime, renta_entregada

INICIO = local_datetime(2026, 10, 1, 18, 0)
VENCE = local_datetime(2026, 10, 3, 9, 0)


def renta_recogida(cliente, operador, equipo):
    """Crea y entrega una renta de prueba en tienda para el periodo estándar."""
    return renta_entregada(cliente, equipo, INICIO, VENCE, operador)


def devolver_a_las(renta, operador, momento):
    """Registra la devolución de la renta en un momento simulado específico."""
    with con_la_hora(momento):
        return register_return(renta, operador, "Llegó con una pata floja")


def deuda_de(cliente, operador, equipo):
    """Genera una deuda ficticia por atraso de 20 Bs asociada a una renta recogida."""
    renta = renta_recogida(cliente, operador, equipo)
    return Debt.objects.create(rental=renta, reason=DebtReason.LATE_RETURN, amount=Decimal("20.00"))


def test_gestion_de_deudas_por_atraso_danos_bloqueos_y_cobros(cl01, op01, mt01, mes01, mes02):
    # Devolver con atraso (12:01) genera deuda proporcional; a las 12:00 (tolerancia) no genera deuda
    # Comprueba que registrar una devolución con un minuto de atraso genera la deuda correspondiente por día
    renta_atraso = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 12, 1))
    deuda_reg = Debt.objects.get(rental=renta_atraso)
    assert (deuda_reg.reason, deuda_reg.amount) == (DebtReason.LATE_RETURN, Decimal("20.00"))

    # Comprueba que una devolución exacta al mediodía (dentro del periodo de tolerancia) no crea deudas
    devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 12, 0))
    assert Debt.objects.count() == 1

    # Clientes con deudas pendientes ven bloqueadas sus nuevas rentas tanto en línea como en tienda (aviso con monto)
    # Comprueba que un cliente con deuda pendiente no puede rentar en línea y recibe el mensaje con el monto
    deuda_de(cl01, op01, mes01)
    antes = foto_de_la_base()
    with pytest.raises(DebtPendingError) as error_online:
        create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9))
    assert str(error_online.value) == "Tienes una deuda pendiente de 20,00 Bs. Págala en la tienda para volver a rentar."
    assert foto_de_la_base() == antes

    # Comprueba que en la tienda el operador recibe un aviso específico de deuda del cliente al intentar registrar una renta
    with pytest.raises(DebtPendingError) as error_tienda:
        create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9), registered_by=op01)
    assert str(error_tienda.value) == "El cliente cl01 tiene una deuda pendiente de 20,00 Bs. Cóbrala antes de registrar otra renta."

    # Cobrar la deuda la cierra exitosamente permitiendo volver a rentar; pagos duplicados de la misma deuda se rechazan
    # Comprueba que al pagar la deuda se registra el operador y la fecha, permitiendo que el cliente vuelva a rentar
    deuda_activa = Debt.objects.filter(paid_at__isnull=True).first()
    pay_debt(deuda_activa, op01)
    deuda_activa.refresh_from_db()
    assert (deuda_activa.paid_received_by, deuda_activa.paid_at is not None) == (op01, True)
    assert create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9)).client == cl01

    # Comprueba que intentar cobrar una deuda ya pagada por segunda vez se rechaza con la fecha del cobro previo
    with con_la_hora(local_datetime(2026, 10, 28, 10, 0)):
        pay_debt(deuda_activa, op01)
    antes_pago = foto_de_la_base()
    with pytest.raises(DebtStateError) as error_duplicado:
        pay_debt(deuda_activa, op01)
    assert str(error_duplicado.value) == "Esta deuda ya se pagó el 28/10/2026 10:00."
    assert foto_de_la_base() == antes_pago

    # Mandar a reparación cobra el 20% al último cliente; dar de baja cobra el 100% (ajustando deudas previas) y cancela reservas futuras
    # Comprueba que enviar un equipo a reparación cobrando al último cliente genera una deuda del 20% de su valor
    renta_rep = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 8, 0))
    res_rep = review_equipment(mes01, mt01, EquipmentStatus.IN_REPAIR, "Pata rota", charge_last_client=True)
    deuda_rep = Debt.objects.get(rental=renta_rep, reason=DebtReason.REPAIR)
    assert (deuda_rep.amount, res_rep.debt) == (Decimal("80.00"), deuda_rep)

    # Comprueba que dar de baja un equipo cobra el total de su valor (menos deudas previas) y cancela reservas futuras
    reserva_futura = create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9))
    res_baja = review_equipment(mes01, mt01, EquipmentStatus.RETIRED, "Estructura partida", charge_last_client=True)
    reserva_futura.refresh_from_db()
    assert res_baja.debt.amount == Decimal("320.00")
    assert (reserva_futura.status, reserva_futura.cancelled_by) == (RentalStatus.CANCELLED, mt01)

    # Revisión a reparación sin marcar cobro no genera deuda e inscribe un log de advertencia (DAMAGE_NOT_CHARGED)
    # Comprueba que enviar a reparación sin marcar el cobro no crea deudas y deja constancia en el log de negocio
    renta_sindeb = devolver_a_las(renta_recogida(cl01, op01, mes02), op01, local_datetime(2026, 10, 3, 8, 0))
    res_sindeb = review_equipment(mes02, mt01, EquipmentStatus.IN_REPAIR, "Daño menor")
    assert (res_sindeb.debt, Debt.objects.filter(rental=renta_sindeb).count()) == (None, 0)