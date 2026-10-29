"""Prueba rentals/use_cases/renting.py con la base: modify_rental(), modificación de fechas y duraciones de reservas."""
from decimal import Decimal

import pytest
from django.core import mail

from rentals.errors import EquipmentNotAvailableError, InvalidModificationError
from rentals.models import Rental
from rentals.use_cases.renting import create_rental, modify_rental
from tests.helpers import dentro_de, foto_de_la_base


def test_operaciones_de_modificacion_de_reservas_y_validacion_de_plazos(cl01, cl02, op01, mes01, django_capture_on_commit_callbacks):
    # Modificar fechas manteniendo la misma cantidad de días actualiza el registro sin alterar el importe; modificaciones del operador notifican por correo
    # Comprueba que el cliente puede trasladar su reserva a nuevas fechas si respeta la misma cantidad de días original
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    modify_rental(reserva, dentro_de(10, 18), dentro_de(12, 9), cl01)
    guardada = Rental.objects.get(pk=reserva.pk)
    assert (guardada.start_datetime, guardada.end_datetime) == (dentro_de(10, 18), dentro_de(12, 9))
    assert (guardada.daily_price, guardada.total_price) == (Decimal("20.00"), Decimal("40.00"))

    # Comprueba que si el operador modifica la reserva, el sistema notifica al cliente por correo con las fechas nuevas
    reserva_op = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    with django_capture_on_commit_callbacks(execute=True):
        modify_rental(reserva_op, dentro_de(10, 18), dentro_de(12, 9), op01)
    [correo_mod] = mail.outbox
    assert (correo_mod.to, correo_mod.subject) == (["cl01@correo.com"], "Reserva modificada: MES-00001")
    assert f"Recojo desde: {dentro_de(10, 18):%d/%m/%Y %H:%M}" in correo_mod.body

    # Mover sobre las propias fechas se permite; alterar la cantidad de días o solapar con otra reserva se rechazan y preservan la base intacta
    # Comprueba que mover la reserva sobre sus propias fechas superpuestas se procesa sin conflictos de disponibilidad
    reserva_propia = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    modify_rental(reserva_propia, dentro_de(8, 18), dentro_de(10, 9), cl01)
    assert Rental.objects.get(pk=reserva_propia.pk).start_datetime == dentro_de(8, 18)

    # Comprueba que cambiar la cantidad de días en la modificación se rechaza con un mensaje orientativo y no altera la base
    reserva_dias = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    antes_mod = foto_de_la_base()
    with pytest.raises(InvalidModificationError) as error_dias:
        modify_rental(reserva_dias, dentro_de(7, 18), dentro_de(10, 9), cl01)
    assert str(error_dias.value) == "La reserva es de 2 días. Elige fechas con la misma cantidad de días; para cambiarla, cancela y renta de nuevo."
    assert foto_de_la_base() == antes_mod

    # Comprueba que intentar mover la reserva sobre el periodo ocupado por otro cliente se rechaza y mantiene la base intacta
    reserva_choque = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    create_rental(cl02, mes01, dentro_de(12, 18), dentro_de(14, 9))
    antes_choque = foto_de_la_base()
    with pytest.raises(EquipmentNotAvailableError):
        modify_rental(reserva_choque, dentro_de(12, 18), dentro_de(14, 9), cl01)
    assert foto_de_la_base() == antes_choque