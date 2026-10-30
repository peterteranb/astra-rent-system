"""Prueba rentals/rules.py: is_rentable_status(), validando qué estados permiten la renta de equipos."""
from rentals.rules import is_rentable_status
from rentals.statuses import EquipmentStatus


def test_validacion_de_disponibilidad_para_renta_segun_estado_del_equipo():
    # Equipo disponible habilitado para renta; equipos en revisión, reparación o baja bloqueados -> filtros de disponibilidad
    # Comprueba que un equipo con estado disponible permite iniciar una nueva renta
    assert is_rentable_status(EquipmentStatus.AVAILABLE) is True
    # Comprueba que un equipo en revisión bloquea la renta y requiere pasar por mantenimiento
    assert is_rentable_status(EquipmentStatus.IN_REVIEW) is False
    # Comprueba que un equipo en reparación no puede ser rentado
    assert is_rentable_status(EquipmentStatus.IN_REPAIR) is False
    # Comprueba que un equipo dado de baja rechaza permanentemente cualquier intento de renta
    assert is_rentable_status(EquipmentStatus.RETIRED) is False