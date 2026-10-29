"""Prueba rentals/use_cases/handover.py con la base: register_pickup() y register_return(), entregas, cobros y recepciones."""
import pytest

from rentals.errors import EquipmentNotAvailableError, IncompleteReturnError, PaymentRequiredError, RentalStateError
from rentals.models import Rental, StatusChange
from rentals.statuses import EquipmentStatus, PaymentMethod, RentalStatus
from rentals.use_cases.handover import register_pickup, register_return
from rentals.use_cases.history import change_status
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, foto_de_la_base, renta_entregada


def test_operaciones_de_entrega_recepcion_y_validaciones_de_mostrador(cl01, op01, mt01, mes01):
    # Entrega de reserva pagada con QR registra hora, operador y pasa a estado rentada; entregar sin pago pendiente se rechaza
    # Comprueba que el operador entrega una reserva pagada por QR registrando la hora, el operador y el estado rentada
    renta_qr = pay_with_qr(create_rental(cl01, mes01, dentro_de(1, 18), dentro_de(2, 9)), approved=True)
    register_pickup(renta_qr, op01)
    guardada_qr = Rental.objects.get(pk=renta_qr.pk)
    assert guardada_qr.picked_up_at is not None
    assert guardada_qr.handed_over_by == op01
    assert guardada_qr.status == RentalStatus.RENTED

    # Comprueba que intentar entregar una reserva sin pago aprobado se rechaza con el monto y no altera la base
    renta_impaga = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    antes = foto_de_la_base()
    with pytest.raises(PaymentRequiredError) as error_pago:
        register_pickup(renta_impaga, op01)
    assert str(error_pago.value) == "Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga."
    assert foto_de_la_base() == antes

    # Cobrar en efectivo al entregar registra el pago y la entrega simultáneamente; devoluciones registran notas e historial
    # Comprueba que el operador puede cobrar en efectivo al momento de entregar, registrando el pago y la renta con éxito
    renta_efectivo = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    register_pickup(renta_efectivo, op01, paid_now=True)
    guardada_efect = Rental.objects.get(pk=renta_efectivo.pk)
    assert (guardada_efect.payment_method, guardada_efect.paid_at) == (PaymentMethod.CASH, guardada_efect.picked_up_at)
    assert guardada_efect.status == RentalStatus.RENTED

    # Comprueba que recibir un equipo de vuelta con una observación registra la devolución, el historial y pasa el equipo a revisión
    renta_activa = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), op01)
    register_return(renta_activa, op01, "  Pata floja  ")
    devuelta_db = Rental.objects.get(pk=renta_activa.pk)
    cambio_db = StatusChange.objects.get()
    mes01.refresh_from_db()
    assert (devuelta_db.status, devuelta_db.received_by, devuelta_db.return_note) == (RentalStatus.RETURNED, op01, "Pata floja")
    assert mes01.status == EquipmentStatus.IN_REVIEW
    assert (cambio_db.new_status, cambio_db.changed_by, cambio_db.comment) == (EquipmentStatus.IN_REVIEW, op01, "Pata floja")

    # Devoluciones sin nota, de reservas no entregadas o de equipos en revisión se rechazan con sus respectivas causas
    # Comprueba que registrar una devolución sin nota obligatoria es rechazada y preserva la base intacta
    renta_activa_dos = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), op01)
    antes_nota = foto_de_la_base()
    with pytest.raises(IncompleteReturnError) as error_nota:
        register_return(renta_activa_dos, op01, "   ")
    assert str(error_nota.value) == "Escribe cómo llegó el equipo."
    assert foto_de_la_base() == antes_nota

    # Comprueba que intentar devolver una reserva que nunca fue recogida por el cliente se rechaza con su causa
    reserva_noreal = create_rental(cl01, mes01, dentro_de(1, 18), dentro_de(2, 9))
    with pytest.raises(RentalStateError) as error_norecogida:
        register_return(reserva_noreal, op01, "Nunca se recogió")
    assert str(error_norecogida.value) == "La renta de MES-00001 nunca se entregó: solo se devuelve una renta «Rentada»."

    # Comprueba que entregar un equipo que pasó a revisión mientras estaba reservado se rechaza informando la causa
    reserva_revision = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), registered_by=op01)
    change_status(mes01, EquipmentStatus.IN_REVIEW, mt01, "Revisión de rutina")
    with pytest.raises(EquipmentNotAvailableError) as error_enrev:
        register_pickup(reserva_revision, op01)
    assert str(error_enrev.value) == "El equipo MES-00001 está en revisión. Espera a que mantenimiento lo revise o cancela la reserva."