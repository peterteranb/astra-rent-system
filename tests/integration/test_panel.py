"""Prueba rentals/use_cases/dashboard.py con la base: manager_summary(), el panel del responsable (CU-15, ENT-87),
y el filtro «situación» del admin al que enlaza cada lista."""
from decimal import Decimal

from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from rentals.models import Debt
from rentals.statuses import DebtReason
from rentals.use_cases.dashboard import manager_summary
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, renta_entregada


def test_visualizacion_y_gestion_de_paneles_del_personal_y_responsable(client, cl01, cl02, op01, ad01, mes01, mes02):
    # MES-00001 debió volver ayer y debe 100 Bs; MES-00002 se recoge hoy sin pagar -> cada una en su lista del panel
    vencida = renta_entregada(cl01, mes01, dentro_de(-3, 18), dentro_de(-1, 9), op01)
    pendiente = create_rental(cl02, mes02, dentro_de(0, 18), dentro_de(1, 9))
    Debt.objects.create(rental=vencida, reason=DebtReason.LATE_RETURN, amount=Decimal("20.00"))
    Debt.objects.create(rental=vencida, reason=DebtReason.REPAIR, amount=Decimal("80.00"))
    resumen = manager_summary(timezone.now())

    # Comprueba que la vencida no cuenta como activa
    assert (resumen.overdue.rows, resumen.active.total) == ([vencida], 0)

    # Comprueba que la reserva de hoy sin pagar está en las dos listas
    assert (resumen.today.rows, resumen.pending_payment.rows) == ([pendiente], [pendiente])

    # Comprueba que las deudas de cl01 se suman por cliente
    [fila] = resumen.debts_by_client.rows
    assert (fila["rental__client__username"], fila["total"], resumen.debt_total) == (
        "cl01", Decimal("100.00"), Decimal("100.00")
    )

    # Comprueba que ad01 abre el panel y el enlace «Vencidas» del admin muestra solo la renta vencida
    client.force_login(ad01)
    assertContains(client.get("/manager/"), "Panel del responsable")
    respuesta = client.get("/admin/rentals/rental/?situacion=vencidas")
    assertContains(respuesta, "MES-00001 · Mesa plegable")
    assertNotContains(respuesta, "MES-00002 · Mesa plegable")
