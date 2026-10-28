"""Prueba rentals/use_cases/dashboard.py con la base: manager_summary(), el panel del responsable (CU-15, ENT-87),
y el filtro «situación» del admin al que enlaza cada lista."""
from decimal import Decimal

from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from rentals.models import Debt
from rentals.statuses import DebtReason
from rentals.use_cases.dashboard import manager_summary
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_el_panel_separa_vencidas_reservas_de_hoy_y_pagos_pendientes(cl01, cl02, op01, mes01, mes02):
    # MES-00001 debió volver ayer y MES-00002 se recoge hoy sin pagar -> cada una en su lista
    vencida = create_rental(cl01, mes01, dentro_de(-3, 18), dentro_de(-1, 9), registered_by=op01, picked_up_now=True)
    pendiente = create_rental(cl02, mes02, dentro_de(0, 18), dentro_de(1, 9))
    resumen = manager_summary(timezone.now())
    # Comprueba que la vencida no cuenta como activa
    assert (resumen.overdue.rows, resumen.active.total) == ([vencida], 0)
    # Comprueba que la reserva de hoy sin pagar está en las dos listas
    assert (resumen.today.rows, resumen.pending_payment.rows) == ([pendiente], [pendiente])


def test_el_panel_suma_las_deudas_por_cliente(cl01, op01, mes01):
    # cl01 debe 20 Bs por atraso y 80 Bs por reparación -> el panel muestra 100 Bs para cl01
    renta = create_rental(cl01, mes01, dentro_de(-3, 18), dentro_de(-1, 9), registered_by=op01, picked_up_now=True)
    Debt.objects.create(rental=renta, reason=DebtReason.LATE_RETURN, amount=Decimal("20.00"))
    Debt.objects.create(rental=renta, reason=DebtReason.REPAIR, amount=Decimal("80.00"))
    resumen = manager_summary(timezone.now())
    [fila] = resumen.debts_by_client.rows
    assert (fila["rental__client__username"], fila["total"], resumen.debt_total) == (
        "cl01", Decimal("100.00"), Decimal("100.00")
    )


def test_el_enlace_de_vencidas_lleva_al_admin_filtrado(client, ad01, cl01, cl02, op01, mes01, mes02):
    # ad01 abre «Vencidas» en el admin -> ve la renta vencida de cl01 y no la reserva de cl02
    create_rental(cl01, mes01, dentro_de(-3, 18), dentro_de(-1, 9), registered_by=op01, picked_up_now=True)
    create_rental(cl02, mes02, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(ad01)
    respuesta = client.get("/admin/rentals/rental/?situacion=vencidas")
    # Comprueba que aparece la vencida
    assertContains(respuesta, "MES-00001 · Mesa plegable")
    # Comprueba que no aparece la reserva futura
    assertNotContains(respuesta, "MES-00002 · Mesa plegable")
