"""Prueba rentals/use_cases/handover.py con la base: register_pickup() y register_return(),
entregar el equipo, cobrando si el pago está pendiente, y recibirlo de vuelta (CU-08, CU-09)."""
import pytest

from rentals.errors import IncompleteReturnError, PaymentRequiredError
from rentals.models import Rental, StatusChange
from rentals.statuses import EquipmentStatus, PaymentMethod, RentalStatus
from rentals.use_cases.handover import register_pickup, register_return
from rentals.use_cases.history import change_status
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, foto_de_la_base, renta_entregada


def test_register_pickup_guarda_la_hora_y_el_operador(cl01, op01, mes01):
    # op01 entrega la reserva pagada con QR de cl01 -> la renta queda «Rentada» con la hora y op01 (ENT-56)
    renta = pay_with_qr(create_rental(cl01, mes01, dentro_de(1, 18), dentro_de(2, 9)), approved=True)
    register_pickup(renta, op01)
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba que se guardó la hora del recojo
    assert guardada.picked_up_at is not None
    # Comprueba que se guardó quién entregó
    assert guardada.handed_over_by == op01
    # Comprueba que ahora está rentada
    assert guardada.status == RentalStatus.RENTED


def test_entregar_sin_cobrar_el_pago_pendiente_se_rechaza_y_la_base_no_cambia(cl01, op01, mes01):
    # El QR de cl01 falló y op01 intenta entregar sin cobrar -> rechazado con el monto y no se guarda nada (ENT-68)
    renta = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    antes = foto_de_la_base()
    with pytest.raises(PaymentRequiredError) as error:
        register_pickup(renta, op01)
    # Comprueba el mensaje con el monto y qué hacer
    assert str(error.value) == (
        "Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga."
    )
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_entregar_cobrando_en_efectivo_guarda_el_pago_y_el_recojo(cl01, op01, mes01):
    # El QR de cl01 falló y op01 cobra en efectivo al entregar -> pagada en efectivo y rentada (ENT-68)
    renta = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    register_pickup(renta, op01, paid_now=True)
    guardada = Rental.objects.get(pk=renta.pk)
    # Comprueba la forma de pago y que el pago y el recojo son del mismo momento
    assert (guardada.payment_method, guardada.paid_at) == (PaymentMethod.CASH, guardada.picked_up_at)
    # Comprueba que quedó rentada
    assert guardada.status == RentalStatus.RENTED


def test_register_return_deja_la_renta_devuelta_y_el_equipo_en_revision(cl01, op01, mes01):
    # op01 recibe MES-00001 con la nota «Pata floja» -> renta devuelta, equipo en revisión y una fila de historial
    renta = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), op01)
    register_return(renta, op01, "  Pata floja  ")
    guardada = Rental.objects.get(pk=renta.pk)
    cambio = StatusChange.objects.get()
    mes01.refresh_from_db()
    # Comprueba que la renta quedó devuelta con quién la recibió y la nota sin espacios
    assert (guardada.status, guardada.received_by, guardada.return_note) == (
        RentalStatus.RETURNED, op01, "Pata floja"
    )
    # Comprueba que el equipo pasó a revisión
    assert mes01.status == EquipmentStatus.IN_REVIEW
    # Comprueba la fila de historial con su autor y la misma nota
    assert (cambio.new_status, cambio.changed_by, cambio.comment) == (
        EquipmentStatus.IN_REVIEW, op01, "Pata floja"
    )


def test_una_devolucion_sin_nota_se_rechaza_y_la_base_no_cambia(cl01, op01, mes01):
    # op01 deja la observación en blanco -> rechazado con la causa y no se guarda nada
    renta = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), op01)
    antes = foto_de_la_base()
    with pytest.raises(IncompleteReturnError) as error:
        register_return(renta, op01, "   ")
    # Comprueba el mensaje con la causa
    assert str(error.value) == "Escribe cómo llegó el equipo."
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_devolver_una_renta_nunca_recogida_con_el_equipo_ya_en_revision(cl01, op01, mt01, mes01):
    # MES-00001 ya está en revisión y vuelve una reserva nunca recogida -> se guarda la devolución sin otra fila de historial (ENT-60)
    renta = create_rental(cl01, mes01, dentro_de(1, 18), dentro_de(2, 9))
    change_status(mes01, EquipmentStatus.IN_REVIEW, mt01, "Revisión de rutina")
    register_return(renta, op01, "Nunca se recogió")
    guardada = Rental.objects.get(pk=renta.pk)
    mes01.refresh_from_db()
    # Comprueba que la renta quedó devuelta con su nota
    assert (guardada.status, guardada.return_note) == (RentalStatus.RETURNED, "Nunca se recogió")
    # Comprueba que el equipo sigue en revisión
    assert mes01.status == EquipmentStatus.IN_REVIEW
    # Comprueba que el historial solo tiene el cambio anterior
    assert StatusChange.objects.count() == 1
