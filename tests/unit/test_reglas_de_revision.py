"""Prueba rentals/rules.py y use_cases/review.py: opciones de estados de mantenimiento y validaciones de transiciones."""
import pytest

from rentals import rules
from rentals.errors import InvalidStatusChangeError
from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.equipment_status import check_status_can_change
from rentals.use_cases.review import check_review_result


def test_validaciones_y_opciones_permitidas_en_revision_de_equipos():
    # Resultados válidos en revisión (ej. disponible) vs estados inexistentes; opciones desde disponible vs baja definitiva -> control de mantenimiento
    # Comprueba que marcar un equipo en revisión como disponible es una opción válida
    equipo_revision = Equipment(inventory_id="MES-00001", status=EquipmentStatus.IN_REVIEW)
    assert check_review_result(equipo_revision, EquipmentStatus.AVAILABLE) is None

    # Comprueba que un estado inexistente o inválido para revisión es rechazado con las opciones permitidas
    with pytest.raises(InvalidStatusChangeError) as error_estado:
        check_review_result(Equipment(inventory_id="MES-00001", status=EquipmentStatus.IN_REPAIR), "reserved")
    assert str(error_estado.value) == "El equipo MES-00001 solo puede pasar a disponible, en revisión, en reparación o baja."

    # Comprueba que desde el estado disponible se puede transicionar a revisión, reparación o baja
    assert rules.next_statuses(EquipmentStatus.AVAILABLE) == [
        EquipmentStatus.IN_REVIEW, EquipmentStatus.IN_REPAIR, EquipmentStatus.RETIRED
    ]

    # Comprueba que desde el estado de baja no existen opciones de cambio adicionales (baja definitiva)
    assert rules.next_statuses(EquipmentStatus.RETIRED) == []

    # Transiciones prohibidas sobre equipos dados de baja o duplicidad de estados -> rechazos de cambio
    # Comprueba que intentar cambiar de estado un equipo dado de baja lanza un error de restricción
    equipo_baja = Equipment(inventory_id="MES-00001", status=EquipmentStatus.RETIRED)
    with pytest.raises(InvalidStatusChangeError) as error_baja:
        check_status_can_change(equipo_baja, EquipmentStatus.AVAILABLE)
    assert str(error_baja.value) == "El equipo MES-00001 está dado de baja; su estado ya no puede cambiar."

    # Comprueba que no se permite transicionar un equipo hacia el mismo estado en el que ya se encuentra
    equipo_disponible = Equipment(inventory_id="MES-00001", status=EquipmentStatus.AVAILABLE)
    with pytest.raises(InvalidStatusChangeError) as error_mismo:
        check_status_can_change(equipo_disponible, EquipmentStatus.AVAILABLE)
    assert str(error_mismo.value) == "El equipo MES-00001 ya está «Disponible»."