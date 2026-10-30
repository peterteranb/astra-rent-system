"""Prueba rentals/rules.py: precios diarios, recargos por daño/baja y plazo de modificación del cliente."""
from datetime import timedelta
from decimal import Decimal

from rentals.models import Rental
from rentals.rules import can_client_change, charge_for, daily_price_for, damage_charge
from rentals.statuses import DebtReason, EquipmentStatus
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_calculo_de_precios_diarios_y_cargos_por_dano_o_baja():
    # Una mesa de 400 Bs da un 5% de 20 Bs diarios; una silla de 85.50 Bs redondea su 5% a 4.28 Bs -> precisión monetaria
    # Comprueba el precio diario estándar (5%) para una mesa de 400 Bs
    assert daily_price_for(Decimal("400.00")) == Decimal("20.00")
    # Comprueba el redondeo a centavos para una silla de 85.50 Bs
    assert daily_price_for(Decimal("85.50")) == Decimal("4.28")

    # Silla de 80 Bs con daño cobra 20% (16 Bs); baja de equipo cobra el 100% ajustando deudas previas de reparación -> topes de deuda
    # Comprueba el cargo por reparación del 20% sobre 80 Bs
    assert charge_for(Decimal("80.00"), Decimal("0.20")) == Decimal("16.00")
    # Comprueba que la baja de un equipo de 400 Bs sin deudas previas cobra el total
    assert damage_charge(Decimal("400.00"), EquipmentStatus.RETIRED) == (DebtReason.RETIRED, Decimal("400.00"))
    # Comprueba que si ya debí 80 Bs por reparación, la baja cobra únicamente el saldo restante (320 Bs)
    assert damage_charge(Decimal("400.00"), EquipmentStatus.RETIRED, Decimal("80.00")) == (
        DebtReason.RETIRED, Decimal("320.00")
    )
    # Comprueba que dejar el equipo disponible no genera ningún cargo
    assert damage_charge(Decimal("400.00"), EquipmentStatus.AVAILABLE) is None


def test_plazos_y_calculo_total_de_renta():
    # Renta de 2 días a 20 Bs da un total de 40 Bs -> cálculo del importe total
    # Comprueba el precio total de la renta en función de los días y la tarifa diaria
    renta = Rental(start_datetime=INICIO, end_datetime=local_datetime(2026, 10, 11, 9, 0), daily_price=Decimal("20.00"))
    assert renta.total_price == Decimal("40.00")

    # Modificación exacta a 24 horas antes permitida vs 23 horas 59 minutos rechazada -> límite de anticipación del cliente
    # Comprueba que el cliente puede modificar exactamente a 24 horas de anticipación
    assert can_client_change(INICIO, INICIO - timedelta(hours=24)) is True
    # Comprueba que un minuto antes del límite de 24 horas rechaza la modificación en línea
    assert can_client_change(INICIO, INICIO - timedelta(hours=23, minutes=59)) is False