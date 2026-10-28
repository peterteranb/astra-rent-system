"""Prueba rentals/rules.py: daily_price_for(), charge_for() y damage_charge(), el precio por día y los cargos
por daño (ENT-71, ENT-74), Rental.total_price (ENT-72) y can_client_change(), el plazo de 24 h del cliente (ENT-80)."""
from datetime import timedelta
from decimal import Decimal

from rentals.models import Rental
from rentals.rules import can_client_change, charge_for, daily_price_for, damage_charge
from rentals.statuses import DebtReason, EquipmentStatus
from tests.helpers import local_datetime

INICIO = local_datetime(2026, 10, 9, 18, 0)


def test_el_dia_de_una_mesa_de_400_bs_cuesta_20_bs():
    # Una mesa vale 400 Bs -> su día cuesta el 5 %: 20 Bs
    assert daily_price_for(Decimal("400.00")) == Decimal("20.00")


def test_el_precio_por_dia_se_redondea_a_centavos():
    # Una silla vale 85,50 Bs -> 5 % es 4,275 y se guarda 4,28 Bs
    assert daily_price_for(Decimal("85.50")) == Decimal("4.28")


def test_la_reparacion_de_una_silla_de_80_bs_cobra_16_bs():
    # Una silla de 80 Bs va a reparación -> el 20 % es 16 Bs
    assert charge_for(Decimal("80.00"), Decimal("0.20")) == Decimal("16.00")


def test_la_baja_cobra_todo_el_valor():
    # Una mesa de 400 Bs se da de baja -> deuda por baja de 400 Bs
    assert damage_charge(Decimal("400.00"), EquipmentStatus.RETIRED) == (DebtReason.RETIRED, Decimal("400.00"))


def test_dejarlo_disponible_no_cobra_nada():
    # Mantenimiento deja la mesa disponible -> no hay deuda
    assert damage_charge(Decimal("400.00"), EquipmentStatus.AVAILABLE) is None


def test_el_total_son_los_dias_por_el_precio_diario():
    # Del 09/10 18:00 al 11/10 09:00 a 20 Bs por día -> 2 días, 40 Bs
    renta = Rental(start_datetime=INICIO, end_datetime=local_datetime(2026, 10, 11, 9, 0), daily_price=Decimal("20.00"))
    assert renta.total_price == Decimal("40.00")


def test_el_cliente_puede_cambiar_justo_24_horas_antes():
    # Recoge el 09/10 a las 18:00 y son las 18:00 del 08/10 -> todavía puede
    assert can_client_change(INICIO, INICIO - timedelta(hours=24)) is True


def test_el_cliente_no_puede_cambiar_a_23_horas_y_59_minutos():
    # Son las 18:01 del 08/10 -> ya no puede cambiar en línea
    assert can_client_change(INICIO, INICIO - timedelta(hours=23, minutes=59)) is False
