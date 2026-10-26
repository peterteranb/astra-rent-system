"""Prueba rentals/review.py: check_review_result() y rentals/history.py: check_status_can_change(),
qué estados puede elegir mantenimiento y qué cambios se rechazan (RF-04, ENT-49)."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.history import check_status_can_change
from rentals.models import Equipment
from rentals.review import check_review_result
from rentals.statuses import EquipmentStatus


def test_disponible_es_un_resultado_valido_de_la_revision():
    # Mantenimiento deja EQ-01 «Disponible» -> se acepta, no lanza error
    equipo = Equipment(inventory_id="EQ-01", status=EquipmentStatus.IN_REVIEW)
    assert check_review_result(equipo, EquipmentStatus.AVAILABLE) is None


def test_en_revision_no_es_un_resultado_de_la_revision():
    # Mantenimiento intenta dejar EQ-01 «En revisión» -> rechazado con las opciones válidas
    equipo = Equipment(inventory_id="EQ-01", status=EquipmentStatus.IN_REPAIR)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_review_result(equipo, EquipmentStatus.IN_REVIEW)
    assert str(error.value) == "El equipo EQ-01 solo puede pasar a disponible, en reparación o baja."


def test_un_equipo_de_baja_no_cambia_de_estado():
    # EQ-01 está de baja y lo quieren dejar disponible -> rechazado (ENT-49: la baja es definitiva)
    equipo = Equipment(inventory_id="EQ-01", status=EquipmentStatus.RETIRED)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_status_can_change(equipo, EquipmentStatus.AVAILABLE)
    assert str(error.value) == "El equipo EQ-01 está dado de baja; su estado ya no puede cambiar."


def test_no_se_pasa_al_mismo_estado():
    # EQ-01 ya está disponible y lo quieren marcar disponible -> rechazado, no deja una fila sin cambio
    equipo = Equipment(inventory_id="EQ-01", status=EquipmentStatus.AVAILABLE)
    with pytest.raises(InvalidStatusChangeError) as error:
        check_status_can_change(equipo, EquipmentStatus.AVAILABLE)
    assert str(error.value) == "El equipo EQ-01 ya está «Disponible»."
