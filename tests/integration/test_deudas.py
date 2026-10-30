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
from tests.helpers import con_la_hora, dentro_de, foto_de_la_base, local_datetime, mesa_nueva, renta_entregada

INICIO = local_datetime(2026, 10, 1, 18, 0)
VENCE = local_datetime(2026, 10, 3, 9, 0)


def renta_recogida(cliente, operador, equipo):
    """Crea y entrega una renta de prueba en tienda para el periodo estándar."""
    return renta_entregada(cliente, equipo, INICIO, VENCE, operador)


def devolver_a_las(renta, operador, momento):
    """Registra la devolución de la renta en un momento simulado específico."""
    with con_la_hora(momento):
        return register_return(renta, operador, "Llegó con una pata floja")


def test_gestion_de_deudas_por_atraso_danos_bloqueos_y_cobros(cl01, cl02, op01, mt01, mes01, mes02, caplog):
    # Devolver con atraso (12:01) genera deuda de un día; a las 12:00 (tolerancia) no genera deuda (ENT-73)
    # Comprueba que registrar una devolución con un minuto de atraso genera la deuda correspondiente por día
    renta_atraso = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 12, 1))
    deuda_activa = Debt.objects.get(rental=renta_atraso)
    assert (deuda_activa.reason, deuda_activa.amount) == (DebtReason.LATE_RETURN, Decimal("20.00"))

    # Comprueba que una devolución exacta al mediodía (dentro del periodo de tolerancia) no crea deudas
    devolver_a_las(renta_recogida(cl02, op01, mes02), op01, local_datetime(2026, 10, 3, 12, 0))
    assert Debt.objects.count() == 1

    # Clientes con deudas pendientes ven bloqueadas sus nuevas rentas tanto en línea como en tienda (ENT-77)
    # Comprueba que un cliente con deuda pendiente no puede rentar en línea y recibe el mensaje con el monto
    libre = mesa_nueva(10)
    antes = foto_de_la_base()
    with pytest.raises(DebtPendingError) as error_online:
        create_rental(cl01, libre, dentro_de(7, 18), dentro_de(9, 9))
    assert str(error_online.value) == "Tienes una deuda pendiente de 20,00 Bs. Págala en la tienda para volver a rentar."
    assert foto_de_la_base() == antes

    # Comprueba que en la tienda el operador recibe un aviso específico de deuda del cliente al intentar registrar una renta
    with pytest.raises(DebtPendingError) as error_tienda:
        create_rental(cl01, libre, dentro_de(7, 18), dentro_de(9, 9), registered_by=op01)
    assert str(error_tienda.value) == "El cliente cl01 tiene una deuda pendiente de 20,00 Bs. Cóbrala antes de registrar otra renta."

    # Cobrar la deuda la cierra y permite volver a rentar; cobrarla otra vez se rechaza (CU-11, ENT-76)
    # Comprueba que al pagar la deuda se registra el operador y la fecha, permitiendo que el cliente vuelva a rentar
    with con_la_hora(local_datetime(2026, 10, 28, 10, 0)):
        pay_debt(deuda_activa, op01)
    deuda_activa.refresh_from_db()
    assert (deuda_activa.paid_received_by, deuda_activa.paid_at) == (op01, local_datetime(2026, 10, 28, 10, 0))
    assert create_rental(cl01, libre, dentro_de(7, 18), dentro_de(9, 9)).client == cl01

    # Comprueba que intentar cobrar una deuda ya pagada por segunda vez se rechaza con la fecha del cobro previo
    antes_pago = foto_de_la_base()
    with pytest.raises(DebtStateError) as error_duplicado:
        pay_debt(deuda_activa, op01)
    assert str(error_duplicado.value) == "Esta deuda ya se pagó el 28/10/2026 10:00."
    assert foto_de_la_base() == antes_pago

    # Revisión a reparación sin marcar cobro no genera deuda y escribe DAMAGE_NOT_CHARGED en el log (ENT-90)
    # Comprueba que enviar a reparación sin marcar el cobro no crea deudas y deja constancia en el log de negocio
    sin_cobro = mesa_nueva(11)
    renta_sindeb = devolver_a_las(renta_recogida(cl01, op01, sin_cobro), op01, local_datetime(2026, 10, 3, 8, 0))
    res_sindeb = review_equipment(sin_cobro, mt01, EquipmentStatus.IN_REPAIR, "Daño menor")
    assert (res_sindeb.debt, Debt.objects.filter(rental=renta_sindeb).count()) == (None, 0)
    assert (
        f'DAMAGE_NOT_CHARGED status=in_repair rental={renta_sindeb.pk} equipment=MES-00011 "Mesa plegable 1,80 m" '
        'client=cl01 "Carla Mendoza" period=01/10/2026 18:00-03/10/2026 09:00 amount=40.00 by=mt01' in caplog.messages
    )

    # Dar de baja cobra el 100% al último cliente y cancela las reservas futuras; reparar y luego dar de baja cobra en total el valor
    # Comprueba que dar de baja cobra 400 Bs a cl02 y cancela la reserva de cl01 a nombre de mt01 (CU-10, ENT-74, ENT-88)
    reservada = mesa_nueva(12)
    renta_baja = renta_recogida(cl02, op01, reservada)
    reserva_futura = create_rental(cl01, reservada, dentro_de(7, 18), dentro_de(9, 9))
    devolver_a_las(renta_baja, op01, local_datetime(2026, 10, 3, 8, 0))
    res_baja = review_equipment(reservada, mt01, EquipmentStatus.RETIRED, "Estructura partida", charge_last_client=True)
    reserva_futura.refresh_from_db()
    assert (res_baja.debt.reason, res_baja.debt.amount) == (DebtReason.RETIRED, Decimal("400.00"))
    assert (reserva_futura.status, reserva_futura.cancelled_by, res_baja.cancelled) == (
        RentalStatus.CANCELLED, mt01, [reserva_futura]
    )

    # Comprueba que reparar cobra el 20 % (80 Bs) y la baja posterior solo los 320 Bs que faltan (D-06)
    danada = mesa_nueva(13)
    renta_rep = devolver_a_las(renta_recogida(cl01, op01, danada), op01, local_datetime(2026, 10, 3, 8, 0))
    res_rep = review_equipment(danada, mt01, EquipmentStatus.IN_REPAIR, "Pata rota", charge_last_client=True)
    review_equipment(danada, mt01, EquipmentStatus.RETIRED, "No se pudo reparar", charge_last_client=True)
    guardadas = list(Debt.objects.filter(rental=renta_rep).order_by("created_at").values_list("reason", "amount"))
    assert guardadas == [(DebtReason.REPAIR, Decimal("80.00")), (DebtReason.RETIRED, Decimal("320.00"))]
    assert res_rep.debt.amount == Decimal("80.00")
