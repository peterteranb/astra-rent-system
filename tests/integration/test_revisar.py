"""Prueba rentals/use_cases/review.py con la base: review_equipment(), transición de equipos desde revisión a disponible o reparación."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.models import StatusChange
from rentals.statuses import EquipmentStatus
from rentals.use_cases.review import review_equipment
from tests.helpers import foto_de_la_base


def test_flujo_de_revision_mantenimiento_y_transiciones_de_estado(mt01, mes03_en_revision):
    # Personal de mantenimiento marca equipo en revisión como disponible (registra historial); transiciones inválidas se rechazan
    # Comprueba que el personal de mantenimiento aprueba un equipo en revisión, pasándolo a disponible y registrando el cambio
    review_equipment(mes03_en_revision, mt01, EquipmentStatus.AVAILABLE, "Todo en orden")
    mes03_en_revision.refresh_from_db()
    cambio = StatusChange.objects.get(equipment=mes03_en_revision)
    assert (mes03_en_revision.status, cambio.changed_by, cambio.comment) == (EquipmentStatus.AVAILABLE, mt01, "Todo en orden")

    # Comprueba que intentar transicionar un equipo hacia un estado no permitido durante la revisión es rechazado y no altera la base
    antes = foto_de_la_base()
    with pytest.raises(InvalidStatusChangeError):
        review_equipment(mes03_en_revision, mt01, "estado_invalido", "Fallo")
    assert foto_de_la_base() == antes