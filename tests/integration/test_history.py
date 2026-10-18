"""Pruebas de INTEGRACION del historial de estados de un equipo (rentals/history.py)."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.history import change_status
from rentals.models import Equipment, StatusChange
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base

pytestmark = pytest.mark.django_db


def test_cambiar_el_estado_deja_una_fila_en_el_historial(mt01, eq03_in_review):
    """Requisito: ENT-34, cada cambio de estado guarda quien, cuando, antes, despues y comentario.
    Caso:      MT-01 revisa EQ-03 ("en revision") y lo deja "disponible" con un comentario.
    Esperado:  EQ-03 queda "disponible" y hay UNA fila con MT-01, ambos estados y el comentario.
    """
    # Ejecutar
    cambio = change_status(eq03_in_review, EquipmentStatus.AVAILABLE, mt01, "Revisada, sin daños")

    # Comprobar: la respuesta
    assert cambio.pk is not None

    # Comprobar: lo guardado
    guardado = StatusChange.objects.get()
    assert guardado.pk == cambio.pk
    assert guardado.equipment == eq03_in_review
    assert guardado.changed_by == mt01
    assert (guardado.old_status, guardado.new_status) == (
        EquipmentStatus.IN_REVIEW,
        EquipmentStatus.AVAILABLE,
    )
    assert guardado.comment == "Revisada, sin daños"
    assert guardado.changed_at is not None
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.AVAILABLE


def test_un_equipo_dado_de_baja_no_cambia_de_estado(mt01, eq01):
    """Requisito: ENT-34, la baja es definitiva.
    Caso:      MT-01 intenta poner "disponible" a EQ-01, que esta dado de baja.
    Esperado:  InvalidStatusChangeError con la causa; la base queda igual.
    """
    # Preparar
    Equipment.objects.filter(pk=eq01.pk).update(status=EquipmentStatus.RETIRED)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(InvalidStatusChangeError) as error:
        change_status(eq01, EquipmentStatus.AVAILABLE, mt01)

    # Comprobar: la respuesta
    assert str(error.value) == (
        "El equipo EQ-01 está dado de baja; su estado ya no puede cambiar."
    )

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes
