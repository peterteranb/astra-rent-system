"""Prueba rentals/rules.py: is_rentable_status(), que solo deja rentar un equipo «Disponible»
(ENT-03: lo devuelto pasa por mantenimiento antes de volver a rentarse)."""
from rentals.rules import is_rentable_status
from rentals.statuses import EquipmentStatus


def test_un_equipo_disponible_se_puede_rentar():
    # EQ-01 está «Disponible» -> se puede rentar
    assert is_rentable_status(EquipmentStatus.AVAILABLE) is True


def test_un_equipo_en_revision_no_se_puede_rentar():
    # EQ-01 está «En revisión» -> no se puede rentar
    assert is_rentable_status(EquipmentStatus.IN_REVIEW) is False


def test_un_equipo_en_reparacion_no_se_puede_rentar():
    # EQ-01 está «En reparación» -> no se puede rentar
    assert is_rentable_status(EquipmentStatus.IN_REPAIR) is False


def test_un_equipo_de_baja_no_se_puede_rentar():
    # EQ-01 está de «Baja» -> no se puede rentar
    assert is_rentable_status(EquipmentStatus.RETIRED) is False
