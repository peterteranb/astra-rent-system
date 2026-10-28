"""Prueba las deudas con la base: la devolución con atraso (CU-09, ENT-73), la revisión con daño (CU-10, ENT-74),
el bloqueo por deuda al rentar (ENT-77) y el registro del pago de una deuda (CU-11, ENT-76)."""
from decimal import Decimal

import pytest

from rentals.errors import DebtPendingError, DebtStateError
from rentals.models import Debt
from rentals.statuses import DebtReason, EquipmentStatus, RentalStatus
from rentals.use_cases.handover import register_return
from rentals.use_cases.payments import pay_debt
from rentals.use_cases.renting import create_rental
from rentals.use_cases.review import review_equipment
from tests.helpers import con_la_hora, dentro_de, foto_de_la_base, local_datetime

INICIO = local_datetime(2026, 10, 1, 18, 0)
VENCE = local_datetime(2026, 10, 3, 9, 0)


def renta_recogida(cliente, operador, equipo):
    """Renta en tienda del 01/10 18:00 al 03/10 09:00, ya recogida; MES-00001 cuesta 20 Bs por día."""
    return create_rental(cliente, equipo, INICIO, VENCE, registered_by=operador, picked_up_now=True)


def devolver_a_las(renta, operador, momento):
    """Registra la devolución de la renta como si fuera momento."""
    with con_la_hora(momento):
        return register_return(renta, operador, "Llegó con una pata floja")


def deuda_de(cliente, operador, equipo):
    """Deja al cliente con una deuda de 20 Bs por atraso."""
    renta = renta_recogida(cliente, operador, equipo)
    return Debt.objects.create(rental=renta, reason=DebtReason.LATE_RETURN, amount=Decimal("20.00"))


def test_devolver_a_las_12_01_crea_la_deuda_de_un_dia(cl01, op01, mes01):
    # Vence el 03/10 y vuelve a las 12:01 -> deuda de 1 día × 20 Bs para esa renta (ENT-73)
    renta = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 12, 1))
    deuda = Debt.objects.get()
    assert (deuda.rental, deuda.reason, deuda.amount) == (renta, DebtReason.LATE_RETURN, Decimal("20.00"))


def test_devolver_a_las_12_00_no_crea_deuda(cl01, op01, mes01):
    # Vence el 03/10 y vuelve a las 12:00 -> tolerancia, sin deuda
    devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 12, 0))
    assert Debt.objects.count() == 0


def test_un_cliente_con_deuda_no_puede_rentar_en_linea(cl01, op01, mes01, mes02):
    # cl01 debe 20 Bs y pide otra renta en línea -> rechazado con el monto y la base no cambia (ENT-77)
    deuda_de(cl01, op01, mes01)
    antes = foto_de_la_base()
    with pytest.raises(DebtPendingError) as error:
        create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9))
    # Comprueba el mensaje con el monto y qué hacer
    assert str(error.value) == "Tienes una deuda pendiente de 20,00 Bs. Págala en la tienda para volver a rentar."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_en_la_tienda_el_operador_ve_la_deuda_del_cliente(cl01, op01, mes01, mes02):
    # op01 quiere rentarle a cl01, que debe 20 Bs -> rechazado con un mensaje para el operador (ENT-77)
    deuda_de(cl01, op01, mes01)
    with pytest.raises(DebtPendingError) as error:
        create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9), registered_by=op01)
    assert str(error.value) == (
        "El cliente cl01 tiene una deuda pendiente de 20,00 Bs. Cóbrala antes de registrar otra renta."
    )


def test_pagar_la_deuda_la_cierra_y_el_cliente_vuelve_a_rentar(cl01, op01, mes01, mes02):
    # op01 cobra la deuda de cl01 -> queda pagada con op01 y cl01 puede rentar otra vez
    pay_debt(deuda_de(cl01, op01, mes01), op01)
    guardada = Debt.objects.get()
    # Comprueba quién cobró y que tiene la hora del pago
    assert (guardada.paid_received_by, guardada.paid_at is not None) == (op01, True)
    # Comprueba que cl01 ya puede rentar
    assert create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9)).client == cl01


def test_una_deuda_pagada_no_se_cobra_dos_veces(cl01, op01, mes01):
    # op01 cobró la deuda a las 10:00 y otro clic la quiere cobrar otra vez -> rechazado y la base no cambia
    deuda = deuda_de(cl01, op01, mes01)
    with con_la_hora(local_datetime(2026, 10, 28, 10, 0)):
        pay_debt(deuda, op01)
    antes = foto_de_la_base()
    with pytest.raises(DebtStateError) as error:
        pay_debt(deuda, op01)
    # Comprueba el mensaje con la fecha del pago
    assert str(error.value) == "Esta deuda ya se pagó el 28/10/2026 10:00."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_mandar_a_reparacion_cobra_el_20_por_ciento_al_ultimo_cliente(cl01, op01, mt01, mes01):
    # MES-00001 (400 Bs) vuelve a tiempo de la renta de cl01 y mt01 lo manda a reparación -> deuda de 80 Bs (ENT-74)
    renta = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 8, 0))
    resultado = review_equipment(mes01, mt01, EquipmentStatus.IN_REPAIR, "Pata rota")
    deuda = Debt.objects.get()
    # Comprueba la deuda guardada
    assert (deuda.rental, deuda.reason, deuda.amount) == (renta, DebtReason.REPAIR, Decimal("80.00"))
    # Comprueba que la revisión devuelve esa deuda
    assert resultado.debt == deuda


def test_dar_de_baja_cobra_el_valor_y_cancela_las_reservas_futuras(cl01, cl02, op01, mt01, mes01):
    # cl02 tiene MES-00001 reservado para hoy+7; vuelve de cl01 y mt01 lo da de baja -> deuda de 400 Bs y la reserva cancelada
    renta = renta_recogida(cl01, op01, mes01)
    reserva = create_rental(cl02, mes01, dentro_de(7, 18), dentro_de(9, 9))
    devolver_a_las(renta, op01, local_datetime(2026, 10, 3, 8, 0))
    resultado = review_equipment(mes01, mt01, EquipmentStatus.RETIRED, "Estructura partida")
    reserva.refresh_from_db()
    # Comprueba la deuda del 100 % del valor
    assert (resultado.debt.reason, resultado.debt.amount) == (DebtReason.RETIRED, Decimal("400.00"))
    # Comprueba que la reserva de cl02 quedó cancelada por mt01
    assert (reserva.status, reserva.cancelled_by, resultado.cancelled) == (RentalStatus.CANCELLED, mt01, [reserva])


def test_reparar_y_despues_dar_de_baja_cobra_en_total_el_valor_del_equipo(cl01, op01, mt01, mes01):
    # MES-00001 (400 Bs) vuelve de cl01, va a reparación (80 Bs) y después se da de baja -> la baja cobra 320 Bs (D-06)
    renta = devolver_a_las(renta_recogida(cl01, op01, mes01), op01, local_datetime(2026, 10, 3, 8, 0))
    review_equipment(mes01, mt01, EquipmentStatus.IN_REPAIR, "Pata rota")
    resultado = review_equipment(mes01, mt01, EquipmentStatus.RETIRED, "No se pudo reparar")
    guardadas = list(Debt.objects.filter(rental=renta).order_by("created_at").values_list("reason", "amount"))
    # Comprueba las dos deudas guardadas de la misma renta
    assert guardadas == [(DebtReason.REPAIR, Decimal("80.00")), (DebtReason.RETIRED, Decimal("320.00"))]
    # Comprueba que la revisión devuelve la deuda de la baja
    assert resultado.debt.amount == Decimal("320.00")


def test_un_equipo_que_nunca_se_rento_va_a_reparacion_sin_deuda(mt01, mes03_en_revision):
    # MES-00003 nunca volvió de una renta y mt01 lo manda a reparación -> no hay a quién cobrar
    resultado = review_equipment(mes03_en_revision, mt01, EquipmentStatus.IN_REPAIR, "Revisión de rutina")
    assert (resultado.debt, Debt.objects.count()) == (None, 0)
