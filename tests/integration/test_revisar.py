"""Prueba rentals/review.py con la base: review_equipment(), la decisión de mantenimiento
sobre un equipo devuelto y su fila de historial (CU-05)."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.models import Equipment, StatusChange
from rentals.review import review_equipment
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base


def test_review_equipment_deja_el_equipo_disponible_con_su_historial(mt01, eq03_en_revision):
    # mt01 deja EQ-03 disponible con el comentario «Todo bien» -> disponible y una fila de historial
    review_equipment(eq03_en_revision, mt01, EquipmentStatus.AVAILABLE, "  Todo bien ")
    eq03_en_revision.refresh_from_db()
    cambio = StatusChange.objects.get()
    # Comprueba que el equipo quedó disponible
    assert eq03_en_revision.status == EquipmentStatus.AVAILABLE
    # Comprueba la fila de historial: de qué estado a cuál, quién y el comentario sin espacios
    assert (cambio.old_status, cambio.new_status, cambio.changed_by, cambio.comment) == (
        EquipmentStatus.IN_REVIEW, EquipmentStatus.AVAILABLE, mt01, "Todo bien"
    )


def test_un_equipo_de_baja_se_rechaza_y_la_base_no_cambia(mt01):
    # mt01 intenta dejar disponible a EQ-07, que está de baja -> rechazado y no se guarda nada (ENT-49)
    eq07 = Equipment.objects.create(
        inventory_id="EQ-07", serial_number="SN-C-004", description="Silla Tiffany dorada",
        status=EquipmentStatus.RETIRED,
    )
    antes = foto_de_la_base()
    with pytest.raises(InvalidStatusChangeError) as error:
        review_equipment(eq07, mt01, EquipmentStatus.AVAILABLE)
    # Comprueba el mensaje con la causa
    assert str(error.value) == "El equipo EQ-07 está dado de baja; su estado ya no puede cambiar."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes
