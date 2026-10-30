"""Prueba rentals/use_cases/review.py y equipment_status.correct_status() con la base: la decisión de mantenimiento
sobre un equipo, su fila de historial (CU-10) y las reservas que cancela al salir de servicio (CU-13, ENT-88)."""
import pytest
from django.core import mail

from rentals.errors import InvalidStatusChangeError
from rentals.models import Debt, StatusChange
from rentals.statuses import EquipmentStatus, RentalStatus
from rentals.use_cases.equipment_status import change_status, correct_status
from rentals.use_cases.renting import create_rental
from rentals.use_cases.review import review_equipment
from tests.helpers import dentro_de, foto_de_la_base


def test_flujo_de_revision_mantenimiento_y_transiciones_de_estado(
    cl01, mt01, ad01, mes01, mes02, mes03_en_revision, django_capture_on_commit_callbacks
):
    # Mantenimiento deja disponible un equipo revisado o lo manda a reparación; el admin da de baja; un estado inválido se rechaza
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

    # Comprueba que mandar a reparación cancela la reserva de cl01 y le manda el motivo por correo (ENT-88, RF-20)
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    change_status(mes01, EquipmentStatus.IN_REVIEW, mt01)
    with django_capture_on_commit_callbacks(execute=True):
        resultado = review_equipment(mes01, mt01, EquipmentStatus.IN_REPAIR, "Pata rota")
    reserva.refresh_from_db()
    [correo] = mail.outbox
    assert (reserva.status, reserva.cancelled_by, resultado.cancelled) == (RentalStatus.CANCELLED, mt01, [reserva])
    assert (correo.subject, "Motivo: El equipo no está disponible: pasó a reparación." in correo.body) == (
        "Renta cancelada: MES-00001", True
    )

    # Comprueba que la baja que corrige el admin cancela la reserva a su nombre y no cobra a nadie (RF-21, ENT-75)
    reserva_baja = create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9))
    correct_status(mes02, EquipmentStatus.RETIRED, ad01)
    reserva_baja.refresh_from_db()
    assert (reserva_baja.status, reserva_baja.cancelled_by, Debt.objects.count()) == (RentalStatus.CANCELLED, ad01, 0)
    assert StatusChange.objects.filter(equipment=mes02, new_status=EquipmentStatus.RETIRED, changed_by=ad01).exists()
