"""Pruebas de INTEGRACION de la revision de mantenimiento (rentals/review.py)."""
import pytest

from rentals.errors import InvalidStatusChangeError
from rentals.models import StatusChange
from rentals.review import review_equipment
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base

pytestmark = pytest.mark.django_db


def test_mantenimiento_deja_disponible_un_equipo_en_revision_sin_comentario(mt01, eq03_in_review):
    """Requisito: PRE-RF-04 y ENT-34, mantenimiento aprueba el equipo y el comentario es opcional.
    Caso:      MT-01 revisa EQ-03 ("en revision") y lo deja "disponible" sin comentario.
    Esperado:  EQ-03 queda "disponible" y hay UNA fila de historial con MT-01 y comentario vacio.
    """
    # Ejecutar
    cambio = review_equipment(eq03_in_review, mt01, EquipmentStatus.AVAILABLE)

    # Comprobar: la respuesta
    assert cambio.pk is not None

    # Comprobar: lo guardado
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.AVAILABLE
    guardado = StatusChange.objects.get()
    assert (guardado.old_status, guardado.new_status) == (
        EquipmentStatus.IN_REVIEW,
        EquipmentStatus.AVAILABLE,
    )
    assert guardado.changed_by == mt01
    assert guardado.comment == ""


def test_la_baja_se_registra_con_su_comentario_y_es_definitiva(mt01, eq03_in_review):
    """Requisito: PRE-RF-04 y ENT-34, la baja es el ultimo estado posible.
    Caso:      MT-01 da de baja EQ-03 y despues intenta dejarlo "disponible".
    Esperado:  la baja queda guardada con su comentario; el segundo intento lanza
               InvalidStatusChangeError y la base no cambia.
    """
    # Preparar
    review_equipment(eq03_in_review, mt01, EquipmentStatus.RETIRED, "No enciende")
    despues_de_la_baja = foto_de_la_base()

    # Ejecutar
    with pytest.raises(InvalidStatusChangeError):
        review_equipment(eq03_in_review, mt01, EquipmentStatus.AVAILABLE)

    # Comprobar: lo guardado
    assert foto_de_la_base() == despues_de_la_baja
    assert StatusChange.objects.get().comment == "No enciende"
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.RETIRED


def test_mantenimiento_no_puede_dejar_un_equipo_en_revision(mt01, eq03_in_review):
    """Requisito: PRE-RF-04, mantenimiento solo deja un equipo disponible, en reparacion o de baja.
    Caso:      MT-01 intenta dejar EQ-03 "en revision".
    Esperado:  InvalidStatusChangeError con la causa; la base queda igual.
    """
    # Preparar
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(InvalidStatusChangeError) as error:
        review_equipment(eq03_in_review, mt01, EquipmentStatus.IN_REVIEW)

    # Comprobar: la respuesta
    assert str(error.value) == (
        "El equipo EQ-03 solo puede pasar a disponible, en reparación o baja."
    )

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes