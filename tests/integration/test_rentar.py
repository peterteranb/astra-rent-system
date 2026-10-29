"""Prueba rentals/use_cases/renting.py con la base: create_rental(), validaciones de solapamiento y registro de reservas."""
import pytest
from django.core import mail

from rentals.errors import EquipmentNotAvailableError, InvalidPeriodError
from rentals.models import Rental
from rentals.statuses import RentalStatus
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_creacion_de_reservas_notificaciones_y_bloqueos_por_cruces(cl01, cl02, op01, mes01, django_capture_on_commit_callbacks):
    # Crear reserva en línea guarda estado reservada, precios calculados y notifica por correo; solapamientos idénticos o parciales se rechazan
    # Comprueba que un cliente crea una reserva en línea con éxito, registrando importes, estado inicial y correo de confirmación
    inicio, fin = dentro_de(7, 18), dentro_de(9, 9)
    with django_capture_on_commit_callbacks(execute=True):
        reserva = create_rental(cl01, mes01, inicio, fin)
    guardada = Rental.objects.get(pk=reserva.pk)
    assert (guardada.status, guardada.total_price, guardada.client) == (RentalStatus.RESERVED, "40.00", cl01)
    [correo] = mail.outbox
    assert (correo.to, correo.subject) == (["cl01@correo.com"], "Reserva confirmada: MES-00001")

    # Comprueba que intentar registrar una reserva exactamente en el mismo periodo ocupado por otro cliente se rechaza y preserva la base
    antes = foto_de_la_base()
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(cl02, mes01, inicio, fin)
    assert foto_de_la_base() == antes

    # Comprueba que un solapamiento parcial envolvente o interno con otra reserva existente es rechazado por el sistema
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(cl02, mes01, dentro_de(6, 18), dentro_de(10, 9))

    # Operador registra reserva en tienda con cliente y operador especificados; periodos pasados o inválidos lanzan InvalidPeriodError
    # Comprueba que el operador registra una reserva directamente en mostrador asociando el operador responsable
    reserva_tienda = create_rental(cl01, mes01, dentro_de(12, 18), dentro_de(14, 9), registered_by=op01)
    assert Rental.objects.get(pk=reserva_tienda.pk).registered_by == op01

    # Comprueba que intentar crear una reserva con un periodo de fechas pasado o inválido lanza una excepción descriptiva
    antes_periodo = foto_de_la_base()
    with pytest.raises(InvalidPeriodError) as error_periodo:
        create_rental(cl01, mes01, dentro_de(-2, 18), dentro_de(-1, 9))
    assert str(error_periodo.value) == "La fecha de recojo ya pasó. Elige hoy o un día siguiente."
    assert foto_de_la_base() == antes_periodo