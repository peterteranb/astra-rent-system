"""Prueba rentals/use_cases/review.py: check_review_result() y rentals/use_cases/history.py: check_status_can_change(),
qué estados puede elegir mantenimiento y qué cambios se rechazan (RF-10, ENT-49)."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.history import check_status_can_change
from rentals.use_cases.review import check_review_result


def test_disponible_es_un_resultado_valido_de_la_revision():
    # Mantenimiento deja MES-00001 «Disponible» -> se acepta, no lanza error
    equipo = Equipment(inventory_id="MES-00001", status=EquipmentStatus.IN_REVIEW)
    assert check_review_result(equipo, EquipmentStatus.AVAILABLE) is None


def test_en_revision_no_es_un_resultado_de_la_revision():
    # Mantenimiento intenta dejar MES-00001 «En revisión» -> rechazado con las opciones válidas
    equipo = Equipment(inventory_id="MES-00001", status=EquipmentStatus.IN_REPAIR)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_review_result(equipo, EquipmentStatus.IN_REVIEW)
    assert str(error.value) == "El equipo MES-00001 solo puede pasar a disponible, en reparación o baja."


def test_un_equipo_de_baja_no_cambia_de_estado():
    # MES-00001 está de baja y lo quieren dejar disponible -> rechazado (ENT-49: la baja es definitiva)
    equipo = Equipment(inventory_id="MES-00001", status=EquipmentStatus.RETIRED)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_status_can_change(equipo, EquipmentStatus.AVAILABLE)
    assert str(error.value) == "El equipo MES-00001 está dado de baja; su estado ya no puede cambiar."


def test_no_se_pasa_al_mismo_estado():
    # MES-00001 ya está disponible y lo quieren marcar disponible -> rechazado, no deja una fila sin cambio
    equipo = Equipment(inventory_id="MES-00001", status=EquipmentStatus.AVAILABLE)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_status_can_change(equipo, EquipmentStatus.AVAILABLE)
    assert str(error.value) == "El equipo MES-00001 ya está «Disponible»."
