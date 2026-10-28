"""Prueba rentals/use_cases/review.py y history.correct_status() con la base: la decisión de mantenimiento
sobre un equipo, su fila de historial (CU-10) y las reservas que cancela al salir de servicio (CU-13, ENT-88)."""
from decimal import Decimal

import pytest
from django.core import mail

from rentals.errors import InvalidStatusChangeError
from rentals.models import Debt, Equipment, StatusChange
from rentals.statuses import EquipmentStatus, RentalStatus
from rentals.use_cases.history import change_status, correct_status
from rentals.use_cases.renting import create_rental
from rentals.use_cases.review import review_equipment
from tests.helpers import dentro_de, foto_de_la_base


def test_review_equipment_deja_el_equipo_disponible_con_su_historial(mt01, mes03_en_revision):
    # mt01 deja MES-00003 disponible con el comentario «Todo bien» -> disponible y una fila de historial
    review_equipment(mes03_en_revision, mt01, EquipmentStatus.AVAILABLE, "  Todo bien ")
    mes03_en_revision.refresh_from_db()
    cambio = StatusChange.objects.get()
    # Comprueba que el equipo quedó disponible
    assert mes03_en_revision.status == EquipmentStatus.AVAILABLE
    # Comprueba la fila de historial: de qué estado a cuál, quién y el comentario sin espacios
    assert (cambio.old_status, cambio.new_status, cambio.changed_by, cambio.comment) == (
        EquipmentStatus.IN_REVIEW, EquipmentStatus.AVAILABLE, mt01, "Todo bien"
    )


def test_un_equipo_de_baja_se_rechaza_y_la_base_no_cambia(mt01):
    # mt01 intenta dejar disponible a MES-00007, que está de baja -> rechazado y no se guarda nada (ENT-49)
    mes07 = Equipment.objects.create(
        inventory_id="MES-00007", serial_number="SN-MES-00007", name="Mesa redonda 1,20 m",
        value=Decimal("350.00"), status=EquipmentStatus.RETIRED,
    )
    antes = foto_de_la_base()
    with pytest.raises(InvalidStatusChangeError) as error:
        review_equipment(mes07, mt01, EquipmentStatus.AVAILABLE)
    # Comprueba el mensaje con la causa
    assert str(error.value) == "El equipo MES-00007 está dado de baja; su estado ya no puede cambiar."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_mandar_a_reparacion_cancela_las_reservas_y_avisa_al_cliente(cl01, mt01, mes01, django_capture_on_commit_callbacks):
    # cl01 tiene MES-00001 para hoy+7, el equipo pasa a revisión y mt01 lo manda a reparación -> la reserva se cancela y cl01 recibe el motivo (ENT-88)
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    change_status(mes01, EquipmentStatus.IN_REVIEW, mt01)
    with django_capture_on_commit_callbacks(execute=True):
        resultado = review_equipment(mes01, mt01, EquipmentStatus.IN_REPAIR, "Pata rota")
    reserva.refresh_from_db()
    [correo] = mail.outbox
    # Comprueba que la reserva quedó cancelada por mt01
    assert (reserva.status, reserva.cancelled_by, resultado.cancelled) == (RentalStatus.CANCELLED, mt01, [reserva])
    # Comprueba el correo con el motivo
    assert "Motivo: El equipo no está disponible: pasó a reparación." in correo.body


def test_la_baja_del_admin_cancela_las_reservas_sin_cobrar(cl01, ad01, mes01):
    # ad01 da de baja MES-00001, que cl01 tiene reservado para hoy+7 -> la reserva se cancela por ad01 y no hay deuda (ENT-75)
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    correct_status(mes01, EquipmentStatus.RETIRED, ad01)
    reserva.refresh_from_db()
    # Comprueba que la reserva quedó cancelada por ad01
    assert (reserva.status, reserva.cancelled_by) == (RentalStatus.CANCELLED, ad01)
    # Comprueba que la corrección no creó deudas
    assert Debt.objects.count() == 0
